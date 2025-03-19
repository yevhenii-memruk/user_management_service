from typing import Annotated, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import get_current_active_user
from src.api.dependencies.database import get_session
from src.db.models.user import Role, User
from src.schemas.user import UserResponseSchema
from src.services.user import UserService
from src.utils.exceptions import NotEnoughPermissionsError

router = APIRouter()

user_from_jwt = Annotated[User, Depends(get_current_active_user)]
db_dependency = Annotated[AsyncSession, Depends(get_session)]


# GET /users
@router.get("/", response_model=List[UserResponseSchema])
async def get_users_list(
    current_user: user_from_jwt,
    db: db_dependency,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(30, ge=1, le=100, description="Items per page"),
    filter_by_name: Optional[str] = Query(
        None, description="Filter by name or surname"
    ),
    sort_by: Optional[
        Literal["id", "name", "surname", "email", "created_at"]
    ] = Query(None, description="Field to sort by"),
    order_by: Literal["asc", "desc"] = Query("asc", description="Sort order"),
) -> List[UserResponseSchema]:
    """
    Get a list of users with pagination, filtering, and sorting.
    - ADMIN: can see all users
    - MODERATOR: can only see users in their group
    - Other roles: not authorized
    """
    if current_user.role not in [Role.ADMIN, Role.MODERATOR]:
        raise NotEnoughPermissionsError()

    user_service = UserService(db)
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
        raise HTTPException(status_code=404, detail=str(e))
