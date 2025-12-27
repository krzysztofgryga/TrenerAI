"""
Authentication service for TrenerAI.

Handles:
- Password hashing (bcrypt)
- JWT token creation/verification
- User authentication
"""
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import User, UserRole


# =============================================================================
# Configuration
# =============================================================================

# Secret key for JWT - in production, use environment variable!
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# =============================================================================
# Password Functions
# =============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# =============================================================================
# JWT Functions
# =============================================================================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data (usually {"sub": user_id, "role": role})
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    import logging
    logger = logging.getLogger(__name__)

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    logger.info(f"CREATE: Using SECRET_KEY: {SECRET_KEY[:10]}...")
    logger.info(f"CREATE: Payload: {to_encode}")
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"CREATE: Token created, length: {len(encoded_jwt)}")
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.

    Returns:
        Token payload if valid, None otherwise
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"DECODE: Using SECRET_KEY: {SECRET_KEY[:10]}...")
        logger.info(f"DECODE: Token length: {len(token)}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"DECODE: Success! Payload: {payload}")
        return payload
    except JWTError as e:
        logger.error(f"DECODE: JWTError: {type(e).__name__}: {e}")
        return None
    except Exception as e:
        logger.error(f"DECODE: Unexpected error: {type(e).__name__}: {e}")
        return None


# =============================================================================
# User Authentication
# =============================================================================

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate user by email and password.

    Returns:
        User if credentials valid, None otherwise
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None

    return user


# =============================================================================
# Dependencies
# =============================================================================

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from JWT token.

    Raises:
        HTTPException 401 if token invalid or user not found
    """
    import logging
    logger = logging.getLogger(__name__)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nieprawidłowy token autoryzacji",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        logger.warning("AUTH: No token provided")
        raise credentials_exception

    logger.info(f"AUTH: Token received (first 20 chars): {token[:20] if len(token) > 20 else token}...")

    payload = decode_access_token(token)
    if payload is None:
        logger.warning("AUTH: Token decode failed")
        raise credentials_exception

    logger.info(f"AUTH: Payload decoded: {payload}")

    user_id = payload.get("sub")
    if user_id is None:
        logger.warning("AUTH: No 'sub' in payload")
        raise credentials_exception

    # Ensure user_id is int (JWT may return it as string)
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        logger.warning(f"AUTH: Could not convert user_id to int: {user_id}")
        raise credentials_exception

    logger.info(f"AUTH: Looking for user with id={user_id}")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        logger.warning(f"AUTH: User not found with id={user_id}")
        raise credentials_exception

    logger.info(f"AUTH: User found: {user.email}")

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Konto jest nieaktywne"
        )

    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if token provided, None otherwise.
    Useful for endpoints that work both with and without auth.
    """
    if not token:
        return None

    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None


async def get_current_trainer(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require current user to be a trainer.

    Raises:
        HTTPException 403 if user is not a trainer
    """
    if current_user.role != UserRole.TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tylko trenerzy mają dostęp do tej funkcji"
        )
    return current_user


async def get_current_client(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require current user to be a client.

    Raises:
        HTTPException 403 if user is not a client
    """
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tylko klienci mają dostęp do tej funkcji"
        )
    return current_user


# =============================================================================
# Permission Helpers
# =============================================================================

def check_trainer_owns_client(
    db: Session,
    trainer: User,
    client_id: int
) -> bool:
    """Check if trainer has this client assigned."""
    from app.database.models import TrainerClient

    relationship = db.query(TrainerClient).filter(
        TrainerClient.trainer_id == trainer.id,
        TrainerClient.client_id == client_id,
        TrainerClient.is_active == True
    ).first()

    return relationship is not None


def check_trainer_owns_group(
    db: Session,
    trainer: User,
    group_id: int
) -> bool:
    """Check if trainer owns this group."""
    from app.database.models import Group

    group = db.query(Group).filter(
        Group.id == group_id,
        Group.trainer_id == trainer.id
    ).first()

    return group is not None


def require_trainer_owns_client(
    db: Session,
    trainer: User,
    client_id: int
) -> None:
    """Raise 403 if trainer doesn't own client."""
    if not check_trainer_owns_client(db, trainer, client_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nie masz dostępu do tego klienta"
        )


def require_trainer_owns_group(
    db: Session,
    trainer: User,
    group_id: int
) -> None:
    """Raise 403 if trainer doesn't own group."""
    if not check_trainer_owns_group(db, trainer, group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nie masz dostępu do tej grupy"
        )
