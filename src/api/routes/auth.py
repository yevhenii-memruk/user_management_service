import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.database import get_session
from src.api.dependencies.rabbitmq import (
    RabbitMQPublisher,
    get_rabbitmq_publisher,
)
from src.api.dependencies.redis import get_redis
from src.schemas.auth import (
    PasswordResetRequest,
    SignupRequest,
    TokenRefreshRequest,
    TokenResponse,
)
from src.schemas.user import UserResponseSchema
from src.services.auth import AuthService
from src.services.password_reset import PasswordResetService
from src.services.user import UserService

logger = logging.getLogger(f"ums.{__name__}")
router = APIRouter()

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
    user_data: SignupRequest, db: db_dependency
) -> UserResponseSchema:
    """
    Register a new user in the system.
    """
    user_service = UserService(db)
    created_user = await user_service.create_user(user_data)

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
    user_tokens = await auth_service.authenticate_user(
        login=form_data.username, password=form_data.password
    )

    return user_tokens


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
    new_tokens = await auth_service.process_token_refresh(
        request.refresh_token
    )
    return new_tokens


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
