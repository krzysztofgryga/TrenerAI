"""
Invitation API endpoints.

Endpoints:
- POST /api/invitations/generate - Trainer generates invitation code
- POST /api/invitations/join - Client uses code to join trainer
- GET /api/invitations/my - Trainer views their active invitations
"""
from datetime import datetime, timedelta
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.database.models import User, UserRole, Invitation, TrainerClient
from app.services.auth_service import get_current_user


router = APIRouter(prefix="/api/invitations", tags=["Invitations"])


# =============================================================================
# Schemas
# =============================================================================

class InvitationGenerateRequest(BaseModel):
    """Request to generate invitation code."""
    expires_hours: int = 24  # Default 24 hours


class InvitationResponse(BaseModel):
    """Invitation code response."""
    code: str
    expires_at: datetime
    is_used: bool
    created_at: datetime


class InvitationJoinRequest(BaseModel):
    """Request to join trainer using code."""
    code: str


class InvitationJoinResponse(BaseModel):
    """Response after joining trainer."""
    success: bool
    trainer_name: str
    message: str


# =============================================================================
# Helper Functions
# =============================================================================

def generate_code(length: int = 6) -> str:
    """Generate a random alphanumeric code (uppercase)."""
    alphabet = string.ascii_uppercase + string.digits
    # Remove confusing characters (0, O, I, 1)
    alphabet = alphabet.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# =============================================================================
# Endpoints
# =============================================================================

@router.post("/generate", response_model=InvitationResponse)
async def generate_invitation(
    request: InvitationGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a new invitation code (trainers only).

    The code can be shared with a client who can use it to join this trainer.
    """
    # Only trainers can generate codes
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tylko trenerzy mogą generować kody zaproszeń"
        )

    # Generate unique code
    max_attempts = 10
    code = None
    for _ in range(max_attempts):
        candidate = generate_code()
        existing = db.query(Invitation).filter(Invitation.code == candidate).first()
        if not existing:
            code = candidate
            break

    if not code:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nie udało się wygenerować unikalnego kodu"
        )

    # Create invitation
    expires_at = datetime.utcnow() + timedelta(hours=request.expires_hours)
    invitation = Invitation(
        trainer_id=current_user.id,
        code=code,
        expires_at=expires_at
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    return InvitationResponse(
        code=invitation.code,
        expires_at=invitation.expires_at,
        is_used=invitation.is_used,
        created_at=invitation.created_at
    )


@router.post("/join", response_model=InvitationJoinResponse)
async def join_trainer(
    request: InvitationJoinRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Join a trainer using invitation code (clients only).

    Creates a trainer-client relationship.
    """
    # Only clients can join trainers
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tylko klienci mogą dołączać do trenerów"
        )

    # Normalize code (uppercase, strip whitespace)
    code = request.code.strip().upper()

    # Find invitation
    invitation = db.query(Invitation).filter(Invitation.code == code).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nieprawidłowy kod zaproszenia"
        )

    if invitation.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ten kod został już wykorzystany"
        )

    if invitation.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ten kod wygasł"
        )

    # Check if relationship already exists
    existing = db.query(TrainerClient).filter(
        TrainerClient.trainer_id == invitation.trainer_id,
        TrainerClient.client_id == current_user.id
    ).first()

    if existing:
        if existing.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Jesteś już klientem tego trenera"
            )
        else:
            # Reactivate relationship
            existing.is_active = True
            existing.updated_at = datetime.utcnow()
    else:
        # Create new trainer-client relationship
        relationship = TrainerClient(
            trainer_id=invitation.trainer_id,
            client_id=current_user.id,
            can_generate_training=False,
            can_view_history=True,
            is_active=True
        )
        db.add(relationship)

    # Mark invitation as used
    invitation.is_used = True
    invitation.used_by_id = current_user.id
    invitation.used_at = datetime.utcnow()

    db.commit()

    # Get trainer name
    trainer = db.query(User).filter(User.id == invitation.trainer_id).first()

    return InvitationJoinResponse(
        success=True,
        trainer_name=trainer.name if trainer else "Trener",
        message=f"Dołączyłeś do trenera {trainer.name if trainer else ''}"
    )


@router.get("/my", response_model=list[InvitationResponse])
async def get_my_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all invitations created by current trainer.

    Returns active (non-expired, non-used) invitations first.
    """
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tylko trenerzy mogą przeglądać zaproszenia"
        )

    invitations = db.query(Invitation).filter(
        Invitation.trainer_id == current_user.id
    ).order_by(Invitation.created_at.desc()).limit(20).all()

    return [
        InvitationResponse(
            code=inv.code,
            expires_at=inv.expires_at,
            is_used=inv.is_used,
            created_at=inv.created_at
        )
        for inv in invitations
    ]


@router.delete("/{code}")
async def delete_invitation(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an invitation code (trainers only, own codes only).
    """
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tylko trenerzy mogą usuwać zaproszenia"
        )

    invitation = db.query(Invitation).filter(
        Invitation.code == code.upper(),
        Invitation.trainer_id == current_user.id
    ).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono zaproszenia"
        )

    db.delete(invitation)
    db.commit()

    return {"message": "Zaproszenie usunięte"}
