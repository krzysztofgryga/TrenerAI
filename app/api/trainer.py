"""
Trainer API endpoints.

Endpoints for trainers to manage their clients and groups.
All endpoints require TRAINER role.

Clients:
- GET /api/trainer/clients - List my clients
- POST /api/trainer/clients - Add client to my roster
- GET /api/trainer/clients/{id} - Get client details
- PUT /api/trainer/clients/{id} - Update client permissions
- DELETE /api/trainer/clients/{id} - Remove client from roster

Groups:
- GET /api/trainer/groups - List my groups
- POST /api/trainer/groups - Create group
- GET /api/trainer/groups/{id} - Get group with members
- PUT /api/trainer/groups/{id} - Update group
- DELETE /api/trainer/groups/{id} - Delete group
- POST /api/trainer/groups/{id}/members - Add member
- DELETE /api/trainer/groups/{id}/members/{client_id} - Remove member
"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database.connection import get_db
from app.database.models import (
    User, UserRole, ClientProfile, TrainerClient, Group, GroupMember
)
from app.schemas import (
    UserResponse, ClientWithProfile, ClientProfileResponse, ClientProfileUpdate,
    TrainerClientCreate, TrainerClientUpdate, TrainerClientResponse,
    GroupCreate, GroupUpdate, GroupResponse, GroupWithMembers,
    GroupMemberAdd, GroupMemberResponse,
    TrainerDashboard
)
from app.services.auth_service import (
    get_current_trainer, require_trainer_owns_client, require_trainer_owns_group
)

router = APIRouter(prefix="/api/trainer", tags=["Trainer"])


# =============================================================================
# Dashboard
# =============================================================================

@router.get("/dashboard", response_model=TrainerDashboard)
async def get_dashboard(
    trainer: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Get trainer dashboard with summary stats."""
    # Count clients
    total_clients = db.query(TrainerClient).filter(
        TrainerClient.trainer_id == trainer.id
    ).count()

    active_clients = db.query(TrainerClient).filter(
        TrainerClient.trainer_id == trainer.id,
        TrainerClient.is_active == True
    ).count()

    # Count groups
    total_groups = db.query(Group).filter(
        Group.trainer_id == trainer.id,
        Group.is_active == True
    ).count()

    # Recent clients (last 5)
    recent_relationships = db.query(TrainerClient).filter(
        TrainerClient.trainer_id == trainer.id,
        TrainerClient.is_active == True
    ).order_by(TrainerClient.created_at.desc()).limit(5).all()

    recent_clients = []
    for rel in recent_relationships:
        client = db.query(User).filter(User.id == rel.client_id).first()
        if client:
            profile = db.query(ClientProfile).filter(
                ClientProfile.user_id == client.id
            ).first()
            recent_clients.append(ClientWithProfile(
                id=client.id,
                email=client.email,
                name=client.name,
                role=client.role,
                is_active=client.is_active,
                created_at=client.created_at,
                profile=profile
            ))

    return TrainerDashboard(
        total_clients=total_clients,
        active_clients=active_clients,
        total_groups=total_groups,
        trainings_this_week=0,  # TODO: implement
        recent_clients=recent_clients
    )


# =============================================================================
# Client Management
# =============================================================================

@router.get("/clients", response_model=List[TrainerClientResponse])
async def list_clients(
    active_only: bool = True,
    trainer: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """List all clients assigned to this trainer."""
    query = db.query(TrainerClient).filter(
        TrainerClient.trainer_id == trainer.id
    )

    if active_only:
        query = query.filter(TrainerClient.is_active == True)

    relationships = query.order_by(TrainerClient.created_at.desc()).all()

    result = []
    for rel in relationships:
        client = db.query(User).filter(User.id == rel.client_id).first()
        result.append(TrainerClientResponse(
            id=rel.id,
            trainer_id=rel.trainer_id,
            client_id=rel.client_id,
            can_generate_training=rel.can_generate_training,
            can_view_history=rel.can_view_history,
            is_active=rel.is_active,
            created_at=rel.created_at,
            client=UserResponse.model_validate(client) if client else None
        ))

    return result


@router.post("/clients", response_model=TrainerClientResponse, status_code=status.HTTP_201_CREATED)
async def add_client(
    data: TrainerClientCreate,
    trainer: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Add a client to trainer's roster."""
    # Check client exists and is a CLIENT
    client = db.query(User).filter(User.id == data.client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Klient nie istnieje"
        )

    if client.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Użytkownik nie jest klientem"
        )

    # Check if relationship already exists
    existing = db.query(TrainerClient).filter(
        TrainerClient.trainer_id == trainer.id,
        TrainerClient.client_id == data.client_id
    ).first()

    if existing:
        if existing.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Klient jest już przypisany do Ciebie"
            )
        else:
            # Reactivate existing relationship
            existing.is_active = True
            existing.can_generate_training = data.can_generate_training
            existing.can_view_history = data.can_view_history
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return TrainerClientResponse(
                id=existing.id,
                trainer_id=existing.trainer_id,
                client_id=existing.client_id,
                can_generate_training=existing.can_generate_training,
                can_view_history=existing.can_view_history,
                is_active=existing.is_active,
                created_at=existing.created_at,
                client=UserResponse.model_validate(client)
            )

    # Create new relationship
    relationship = TrainerClient(
        trainer_id=trainer.id,
        client_id=data.client_id,
        can_generate_training=data.can_generate_training,
        can_view_history=data.can_view_history
    )
    db.add(relationship)
    db.commit()
    db.refresh(relationship)

    return TrainerClientResponse(
        id=relationship.id,
        trainer_id=relationship.trainer_id,
        client_id=relationship.client_id,
        can_generate_training=relationship.can_generate_training,
        can_view_history=relationship.can_view_history,
        is_active=relationship.is_active,
        created_at=relationship.created_at,
        client=UserResponse.model_validate(client)
    )


@router.get("/clients/{client_id}", response_model=ClientWithProfile)
async def get_client(
    client_id: int,
    trainer: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Get client details with profile."""
    require_trainer_owns_client(db, trainer, client_id)

    client = db.query(User).filter(User.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Klient nie istnieje"
        )

    profile = db.query(ClientProfile).filter(
        ClientProfile.user_id == client_id
    ).first()

    return ClientWithProfile(
        id=client.id,
        email=client.email,
        name=client.name,
        role=client.role,
        is_active=client.is_active,
        created_at=client.created_at,
        profile=profile
    )


@router.put("/clients/{client_id}", response_model=TrainerClientResponse)
async def update_client_permissions(
    client_id: int,
    data: TrainerClientUpdate,
    trainer: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Update client permissions."""
    require_trainer_owns_client(db, trainer, client_id)

    relationship = db.query(TrainerClient).filter(
        TrainerClient.trainer_id == trainer.id,
        TrainerClient.client_id == client_id
    ).first()

    if data.can_generate_training is not None:
        relationship.can_generate_training = data.can_generate_training
    if data.can_view_history is not None:
        relationship.can_view_history = data.can_view_history
    if data.is_active is not None:
        relationship.is_active = data.is_active

    relationship.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(relationship)

    client = db.query(User).filter(User.id == client_id).first()

    return TrainerClientResponse(
        id=relationship.id,
        trainer_id=relationship.trainer_id,
        client_id=relationship.client_id,
        can_generate_training=relationship.can_generate_training,
        can_view_history=relationship.can_view_history,
        is_active=relationship.is_active,
        created_at=relationship.created_at,
        client=UserResponse.model_validate(client) if client else None
    )


@router.put("/clients/{client_id}/profile", response_model=ClientProfileResponse)
async def update_client_profile(
    client_id: int,
    data: ClientProfileUpdate,
    trainer: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Update client's profile (trainer can add notes)."""
    require_trainer_owns_client(db, trainer, client_id)

    profile = db.query(ClientProfile).filter(
        ClientProfile.user_id == client_id
    ).first()

    if not profile:
        profile = ClientProfile(user_id=client_id)
        db.add(profile)

    # Update fields
    if data.age is not None:
        profile.age = data.age
    if data.weight is not None:
        profile.weight = data.weight
    if data.height is not None:
        profile.height = data.height
    if data.goals is not None:
        profile.goals = data.goals
    if data.contraindications is not None:
        profile.contraindications = data.contraindications
    if data.preferred_difficulty is not None:
        profile.preferred_difficulty = data.preferred_difficulty
    if data.trainer_notes is not None:
        profile.trainer_notes = data.trainer_notes

    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)

    return profile


@router.delete("/clients/{client_id}")
async def remove_client(
    client_id: int,
    trainer: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Remove client from trainer's roster (soft delete)."""
    require_trainer_owns_client(db, trainer, client_id)

    relationship = db.query(TrainerClient).filter(
        TrainerClient.trainer_id == trainer.id,
        TrainerClient.client_id == client_id
    ).first()

    relationship.is_active = False
    relationship.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Klient został usunięty z listy"}


# =============================================================================
# Group Management
# =============================================================================

@router.get("/groups", response_model=List[GroupResponse])
async def list_groups(
    active_only: bool = True,
    trainer: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """List all groups owned by this trainer."""
    query = db.query(Group).filter(Group.trainer_id == trainer.id)

    if active_only:
        query = query.filter(Group.is_active == True)

    groups = query.order_by(Group.created_at.desc()).all()

    result = []
    for group in groups:
        member_count = db.query(GroupMember).filter(
            GroupMember.group_id == group.id,
            GroupMember.is_active == True
        ).count()

        result.append(GroupResponse(
            id=group.id,
            trainer_id=group.trainer_id,
            name=group.name,
            description=group.description,
            max_members=group.max_members,
            is_active=group.is_active,
            created_at=group.created_at,
            member_count=member_count
        ))

    return result


@router.post("/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    trainer: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Create a new client group."""
    group = Group(
        trainer_id=trainer.id,
        name=data.name,
        description=data.description,
        max_members=data.max_members
    )
    db.add(group)
    db.commit()
    db.refresh(group)

    return GroupResponse(
        id=group.id,
        trainer_id=group.trainer_id,
        name=group.name,
        description=group.description,
        max_members=group.max_members,
        is_active=group.is_active,
        created_at=group.created_at,
        member_count=0
    )


@router.get("/groups/{group_id}", response_model=GroupWithMembers)
async def get_group(
    group_id: int,
    trainer: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Get group details with members."""
    require_trainer_owns_group(db, trainer, group_id)

    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupa nie istnieje"
        )

    memberships = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.is_active == True
    ).all()

    members = []
    for membership in memberships:
        client = db.query(User).filter(User.id == membership.client_id).first()
        members.append(GroupMemberResponse(
            id=membership.id,
            group_id=membership.group_id,
            client_id=membership.client_id,
            joined_at=membership.joined_at,
            is_active=membership.is_active,
            client=UserResponse.model_validate(client) if client else None
        ))

    return GroupWithMembers(
        id=group.id,
        trainer_id=group.trainer_id,
        name=group.name,
        description=group.description,
        max_members=group.max_members,
        is_active=group.is_active,
        created_at=group.created_at,
        member_count=len(members),
        members=members
    )


@router.put("/groups/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    data: GroupUpdate,
    trainer: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Update group details."""
    require_trainer_owns_group(db, trainer, group_id)

    group = db.query(Group).filter(Group.id == group_id).first()

    if data.name is not None:
        group.name = data.name
    if data.description is not None:
        group.description = data.description
    if data.max_members is not None:
        group.max_members = data.max_members
    if data.is_active is not None:
        group.is_active = data.is_active

    group.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(group)

    member_count = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.is_active == True
    ).count()

    return GroupResponse(
        id=group.id,
        trainer_id=group.trainer_id,
        name=group.name,
        description=group.description,
        max_members=group.max_members,
        is_active=group.is_active,
        created_at=group.created_at,
        member_count=member_count
    )


@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: int,
    trainer: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Delete group (soft delete)."""
    require_trainer_owns_group(db, trainer, group_id)

    group = db.query(Group).filter(Group.id == group_id).first()
    group.is_active = False
    group.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Grupa została usunięta"}


# =============================================================================
# Group Members
# =============================================================================

@router.post("/groups/{group_id}/members", response_model=GroupMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_group_member(
    group_id: int,
    data: GroupMemberAdd,
    trainer: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Add client to group."""
    require_trainer_owns_group(db, trainer, group_id)
    require_trainer_owns_client(db, trainer, data.client_id)

    group = db.query(Group).filter(Group.id == group_id).first()

    # Check max members
    if group.max_members:
        current_count = db.query(GroupMember).filter(
            GroupMember.group_id == group_id,
            GroupMember.is_active == True
        ).count()
        if current_count >= group.max_members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Grupa osiągnęła maksymalną liczbę członków ({group.max_members})"
            )

    # Check if already member
    existing = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.client_id == data.client_id
    ).first()

    if existing:
        if existing.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Klient jest już członkiem tej grupy"
            )
        else:
            existing.is_active = True
            existing.joined_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            client = db.query(User).filter(User.id == data.client_id).first()
            return GroupMemberResponse(
                id=existing.id,
                group_id=existing.group_id,
                client_id=existing.client_id,
                joined_at=existing.joined_at,
                is_active=existing.is_active,
                client=UserResponse.model_validate(client) if client else None
            )

    membership = GroupMember(
        group_id=group_id,
        client_id=data.client_id
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)

    client = db.query(User).filter(User.id == data.client_id).first()

    return GroupMemberResponse(
        id=membership.id,
        group_id=membership.group_id,
        client_id=membership.client_id,
        joined_at=membership.joined_at,
        is_active=membership.is_active,
        client=UserResponse.model_validate(client) if client else None
    )


@router.delete("/groups/{group_id}/members/{client_id}")
async def remove_group_member(
    group_id: int,
    client_id: int,
    trainer: User = Depends(get_current_trainer),
    db: Session = Depends(get_db)
):
    """Remove client from group."""
    require_trainer_owns_group(db, trainer, group_id)

    membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.client_id == client_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Klient nie jest członkiem tej grupy"
        )

    membership.is_active = False
    db.commit()

    return {"message": "Klient został usunięty z grupy"}
