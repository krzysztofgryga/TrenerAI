"""
Authentication API endpoints.

Endpoints:
- POST /api/auth/register - Register new user
- POST /api/auth/login - Login and get JWT token
- GET /api/auth/me - Get current user info
- PUT /api/auth/me - Update current user
- POST /api/auth/change-password - Change password
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User, UserRole, ClientProfile
from app.schemas import (
    UserRegister, UserLogin, TokenResponse, UserResponse, UserUpdate,
    ClientProfileCreate, ClientProfileResponse
)
from app.services.auth_service import (
    hash_password, verify_password, create_access_token,
    authenticate_user, get_current_user
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# =============================================================================
# Registration
# =============================================================================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user.

    - **email**: Unique email address
    - **password**: Min 8 characters
    - **name**: User's display name
    - **role**: trainer or client (default: client)

    Returns JWT token on success.
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email jest już zarejestrowany"
        )

    # Create user
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        name=user_data.name,
        role=UserRole(user_data.role.value),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # If client, create empty profile
    if user.role == UserRole.CLIENT:
        profile = ClientProfile(user_id=user.id)
        db.add(profile)
        db.commit()

    # Generate token
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role.value}
    )

    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        role=user.role
    )


# =============================================================================
# Login
# =============================================================================

@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.

    Returns JWT token on success.
    """
    user = authenticate_user(db, credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy email lub hasło",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.id, "role": user.role.value}
    )

    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        role=user.role
    )


@router.post("/login/form", response_model=TokenResponse)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login using OAuth2 form (for Swagger UI).

    Username field accepts email.
    """
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy email lub hasło",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.id, "role": user.role.value}
    )

    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        role=user.role
    )


# =============================================================================
# Current User
# =============================================================================

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """Get current logged-in user info."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's basic info."""
    if update_data.name is not None:
        current_user.name = update_data.name

    if update_data.email is not None:
        # Check if new email is taken
        existing = db.query(User).filter(
            User.email == update_data.email,
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email jest już zajęty"
            )
        current_user.email = update_data.email

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return current_user


# =============================================================================
# Password Change
# =============================================================================

class PasswordChange(UserLogin):
    """Schema for password change."""
    new_password: str


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change current user's password."""
    # Verify current password
    if not verify_password(data.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Obecne hasło jest nieprawidłowe"
        )

    # Validate new password
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nowe hasło musi mieć co najmniej 8 znaków"
        )

    # Update password
    current_user.password_hash = hash_password(data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Hasło zostało zmienione"}


# =============================================================================
# Client Profile (for clients only)
# =============================================================================

@router.get("/me/profile", response_model=ClientProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current client's profile (clients only)."""
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tylko klienci mają profile"
        )

    profile = db.query(ClientProfile).filter(
        ClientProfile.user_id == current_user.id
    ).first()

    if not profile:
        # Create empty profile if doesn't exist
        profile = ClientProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return profile


@router.put("/me/profile", response_model=ClientProfileResponse)
async def update_my_profile(
    profile_data: ClientProfileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current client's profile (clients only)."""
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tylko klienci mają profile"
        )

    profile = db.query(ClientProfile).filter(
        ClientProfile.user_id == current_user.id
    ).first()

    if not profile:
        profile = ClientProfile(user_id=current_user.id)
        db.add(profile)

    # Update fields
    if profile_data.age is not None:
        profile.age = profile_data.age
    if profile_data.weight is not None:
        profile.weight = profile_data.weight
    if profile_data.height is not None:
        profile.height = profile_data.height
    if profile_data.goals is not None:
        profile.goals = profile_data.goals
    if profile_data.contraindications is not None:
        profile.contraindications = profile_data.contraindications
    if profile_data.preferred_difficulty is not None:
        profile.preferred_difficulty = profile_data.preferred_difficulty

    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)

    return profile
