from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.database import get_session
from src.schemas.auth import SignupRequest, TokenResponse
from src.schemas.user import UserCreateSchema, UserResponseSchema
from src.services.auth import AuthService
from src.services.user import UserService
from src.utils.password_manager import PasswordManager

router = APIRouter(prefix="/auth", tags=["authentication"])

db_dependency = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/signup",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def signup(
    user_data: SignupRequest,
    db: db_dependency,
    password_manager: PasswordManager = Depends(PasswordManager),
) -> UserResponseSchema:
    """
    Register a new user in the system.
    """
    user_service = UserService(db)
    existing_user = await user_service.get_user_by_email_or_username(
        email=user_data.email, username=user_data.username
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists",
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
    db: db_dependency, form_data: OAuth2PasswordRequestForm = Depends()
) -> TokenResponse:
    """
    Authenticate user and return access and refresh tokens.
    Login can be done with username or email.
    """
    auth_service = AuthService(db)
    user = await auth_service.authenticate_user(
        login=form_data.username, password=form_data.password
    )
    return user


@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token() -> None:
    pass


@router.post("/reset-password")
async def reset_password() -> None:
    pass
