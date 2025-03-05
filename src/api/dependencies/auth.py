from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.database import get_session
from src.db.models.user import Role, User
from src.schemas.auth import TokenData
from src.services.user import UserService
from src.utils.jwt_manager import JWTManager

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(
    token: str = Depends(oauth2_bearer),
    db: AsyncSession = Depends(get_session),
    jwt_manager: JWTManager = Depends(JWTManager),
) -> User:
    """
    Dependency to get the current user from the JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt_manager.decode_jwt_token(token)
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)

    except HTTPException:
        raise credentials_exception

    user_service = UserService(db)
    user = await user_service.get_user_by_username(token_data.username)

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to get the current active user.
    """
    if current_user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User is blocked"
        )
    return current_user


async def check_admin_access(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to check if the current user has admin role.
    """
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


async def check_moderator_access(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to check if the current user has moderator or admin role.
    """
    if current_user.role not in [Role.ADMIN, Role.MODERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
