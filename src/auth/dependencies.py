# src/auth/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jwt.exceptions import DecodeError
import jwt

from src.common.config import settings
from src.common.database.database import get_db_session
from src.models.models import User, UserRole

bearer_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    Dependency to retrieve the current user based on the JWT token provided in the Authorization header.
    """
    token = credentials.credentials  # ✅ extract the raw token string

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except DecodeError:
        raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
    except Exception as e:
        raise credentials_exception from e

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency for admin-only endpoints.

    get_current_user already proves the caller holds a valid token; this adds
    the role check so hospital-wide data is never served to a patient or a
    clinician who simply knows the URL.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This area is restricted to hospital administrators.",
        )
    return current_user
