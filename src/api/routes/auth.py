import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.database import get_session
from src.api.dependencies.rabbitmq import (
    RabbitMQPublisher,
    get_rabbitmq_publisher,
)
from src.api.dependencies.redis import get_redis
from src.db.models import User
from src.schemas.auth import (
    PasswordResetRequest,
    SignupRequest,
    TokenRefreshRequest,
    TokenResponse,
)
from src.schemas.user import UserCreateSchema, UserResponseSchema
from src.services.auth import AuthService
from src.services.password_reset import PasswordResetService
from src.services.user import UserService
from src.utils.exceptions import InvalidTokenError
from src.utils.password_manager import PasswordManager

logger = logging.getLogger(f"ums.{__name__}")
router = APIRouter(prefix="/auth", tags=["authentication"])

db_dependency = Annotated[AsyncSession, Depends(get_session)]
rabbitmq_dependency = Annotated[
    RabbitMQPublisher, Depends(get_rabbitmq_publisher)
]
redis_dependency = Annotated[Redis, Depends(get_redis)]


@router.post(
    "/signup",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    user_data: SignupRequest,
    db: db_dependency,
    password_manager: PasswordManager = Depends(PasswordManager),
) -> User:

    logger.debug(f"user_data={user_data}")

    """
    Register a new user in the system.
    """
    user_service = UserService(db)
    try:
        existing_user = await user_service.get_user_by_email_or_username(
            email=user_data.email, username=user_data.username
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists",
        )
    # Validate User group_id, checks if id exists in Group table
    if user_data.group_id:
        group_id = await user_service.check_group_exists(user_data.group_id)
        if not group_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Group not found.",
            )

    # Create new user with hashed password
    hashed_password = password_manager.get_hash(user_data.password)
    user_in = UserCreateSchema(
        **user_data.model_dump(exclude={"password"}), password=hashed_password
    )

    created_user = await user_service.create_user(user_in)
    return created_user


@router.post("/login", response_model=TokenResponse)
async def login(
    db: db_dependency,
    form_data: OAuth2PasswordRequestForm = Depends(),
    redis: Redis = Depends(get_redis),
) -> TokenResponse:
    """
    Authenticate user and return access and refresh tokens.
    Login can be done with username or email.
    """
    auth_service = AuthService(db, redis)
    user = await auth_service.authenticate_user(
        login=form_data.username, password=form_data.password
    )

    return user


# POST /auth/refresh-token
@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    db: db_dependency,
    redis: redis_dependency,
) -> TokenResponse:
    """
    Refresh the access token using a valid refresh token.
    The old refresh token is blacklisted by Redis.
    """
    auth_service = AuthService(db, redis)
    try:
        new_tokens = await auth_service.process_token_refresh(
            request.refresh_token
        )
        return new_tokens
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


# POST /auth/reset-password
@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    request: PasswordResetRequest,
    db: db_dependency,
    rabbitmq_service: rabbitmq_dependency,
) -> dict[str, str]:
    """
    Accepts an email address, verifies it belongs to a registered user,
    and publishes a message to RabbitMQ for further processing.
    """
    user_service = UserService(db)
    password_reset_service = PasswordResetService(
        user_service, rabbitmq_service
    )

    return await password_reset_service.reset_password(request)
