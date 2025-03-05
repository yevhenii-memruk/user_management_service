from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import get_current_active_user
from src.api.dependencies.database import get_session
from src.db.models.user import User
from src.schemas.user import UserResponseSchema, UserUpdateSchema
from src.services.user import UserService

router = APIRouter(tags=["users"])

user_from_jwt = Annotated[User, Depends(get_current_active_user)]
db_dependency = Annotated[AsyncSession, Depends(get_session)]


@router.get("/user/me", response_model=UserResponseSchema)
async def get_current_user_info(
    current_user: user_from_jwt,
) -> UserResponseSchema:
    """
    Get current user info.
    """
    return UserResponseSchema.model_validate(current_user)


@router.patch("/user/me", response_model=UserResponseSchema)
async def update_current_user(
    user_update: UserUpdateSchema,
    current_user: user_from_jwt,
    db: db_dependency,
) -> UserResponseSchema:
    """
    Update current user's information.
    """
    user_service = UserService(db)
    updated_user = await user_service.update_user(current_user.id, user_update)

    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponseSchema.model_validate(updated_user)


@router.delete("/user/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: user_from_jwt, db: db_dependency
) -> JSONResponse:
    """
    Delete the current user's account.
    """
    user_service = UserService(db)
    deleted = await user_service.delete_user(current_user.id)

    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    return JSONResponse(status_code=204, content=None)
