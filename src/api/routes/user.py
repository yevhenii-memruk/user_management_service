from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import get_current_active_user
from src.api.dependencies.database import get_session
from src.db.models.user import Role, User
from src.schemas.user import UserResponseSchema, UserUpdateSchema
from src.services.user import UserService

router = APIRouter(tags=["users"])

user_from_jwt = Annotated[User, Depends(get_current_active_user)]
db_dependency = Annotated[AsyncSession, Depends(get_session)]


# GET /user/me
@router.get("/user/me", response_model=UserResponseSchema)
async def get_current_user_info(
    current_user: user_from_jwt,
) -> UserResponseSchema:
    """
    Get current user info.
    """
    return UserResponseSchema.model_validate(current_user)


# PATCH /user/me
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


# DELETE /user/me
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

    return JSONResponse(status_code=204, content="User deleted")


# GET /user/{user_id}
@router.get("/user/{user_id}", response_model=UserResponseSchema)
async def get_user(
    user_id: UUID, db: db_dependency, current_user: user_from_jwt
) -> UserResponseSchema:
    """
    Returns the user info based on the user_id.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if (
        current_user.role == "MODERATOR"
        and current_user.group_id != user.group_id
    ):
        raise HTTPException(status_code=403, detail="Not allowed")
    if current_user.role == "USER":
        raise HTTPException(status_code=403, detail="Not allowed")

    return UserResponseSchema.model_validate(user)


# PATCH /user/{user_id}
@router.patch("/user/{user_id}", response_model=UserResponseSchema)
async def update_user(
    user_id: UUID,
    user_update: UserUpdateSchema,
    db: db_dependency,
    current_user: user_from_jwt,
) -> UserResponseSchema:
    """
    Accepts new values for the fields to update
    and returns the updated user info.
    """
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Not allowed")

    user_service = UserService(db)
    updated_user = await user_service.update_user(user_id, user_update)

    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponseSchema.model_validate(updated_user)


# GET /users
@router.get("/users", response_model=List[UserResponseSchema])
async def get_users_list(
    current_user: user_from_jwt,
    db: db_dependency,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(30, ge=1, le=100, description="Items per page"),
    filter_by_name: Optional[str] = Query(
        None, description="Filter by name or surname"
    ),
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    order_by: str = Query("asc", description="Sort order"),
) -> List[UserResponseSchema]:
    """
    Get a list of users with pagination, filtering, and sorting.
    - ADMIN: can see all users
    - MODERATOR: can only see users in their group
    - Other roles: not authorized
    """
    user_service = UserService(db)

    if current_user.role not in [Role.ADMIN, Role.MODERATOR]:
        raise HTTPException(
            status_code=403, detail="Not authorized to view user list"
        )

    try:
        users = await user_service.get_all_users(
            current_user=current_user,
            page=page,
            limit=limit,
            filter_by_name=filter_by_name,
            sort_by=sort_by,
            order_by=order_by,
        )
        return users
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
