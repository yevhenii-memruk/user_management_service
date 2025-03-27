import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import get_current_active_user
from src.api.dependencies.database import get_session
from src.aws.s3_service import S3Service, get_s3_service
from src.db.models.user import User
from src.schemas.user import (
    UserImageS3PathSchema,
    UserResponseSchema,
    UserUpdateSchema,
)
from src.services.user import UserService
from src.utils.exceptions import InternalServerError, UserNotFoundError

logger = logging.getLogger(f"ums.{__name__}")

router = APIRouter()

# Dependencies
user_from_jwt = Annotated[User, Depends(get_current_active_user)]
db_dependency = Annotated[AsyncSession, Depends(get_session)]
s3_service_dependency = Annotated[S3Service, Depends(get_s3_service)]


# GET /user/me
@router.get("/me", response_model=UserResponseSchema)
async def get_current_user_info(
    current_user: user_from_jwt,
) -> UserResponseSchema:
    """
    Get current user info.
    """
    return UserResponseSchema.model_validate(current_user)


# PATCH /user/me
@router.patch("/me", response_model=UserResponseSchema)
async def update_current_user(
    current_user: user_from_jwt,
    db: db_dependency,
    s3_service: s3_service_dependency,
    user_update: UserUpdateSchema = Depends(UserUpdateSchema.as_form),
    file: UploadFile = File(default=None),
) -> UserResponseSchema:
    """
    Update current user's information.
    """
    user_service = UserService(db)
    updated_user = await user_service.update_user(
        current_user.id, user_update, s3_service, file=file
    )

    return UserResponseSchema.model_validate(updated_user)


# DELETE /user/me
@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: user_from_jwt, db: db_dependency
) -> JSONResponse:
    """
    Delete the current user's account.
    """
    user_service = UserService(db)
    await user_service.delete_user(current_user.id)

    return JSONResponse(status_code=204, content="User deleted")


# GET /user/{user_id}
@router.get("/{user_id}", response_model=UserResponseSchema)
async def get_user(
    user_id: UUID, db: db_dependency, current_user: user_from_jwt
) -> UserResponseSchema:
    """
    Returns the user info based on the user_id.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)

    # Check permissions
    await user_service.check_user_access_permissions(current_user, user)

    return UserResponseSchema.model_validate(user)


# PATCH /user/{user_id}
@router.patch("/{user_id}", response_model=UserResponseSchema)
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
    user_service = UserService(db)

    # Check permissions
    await user_service.check_admin_access_permissions(current_user)

    updated_user = await user_service.update_user(user_id, user_update)

    return UserResponseSchema.model_validate(updated_user)


# POST /me/image
@router.post("/me/image", response_model=UserImageS3PathSchema)
async def upload_user_image(
    current_user: user_from_jwt,
    db: db_dependency,
    s3_service: s3_service_dependency,
    file: UploadFile = File(...),
) -> UserImageS3PathSchema:
    """
    Upload a profile image for the current user
    """
    # Validate file type
    await s3_service.validate_user_image(file, current_user)

    # Upload to S3
    s3_path = await s3_service.upload_user_image(
        current_user.id, file.file, file.content_type
    )

    # Update user record with new image path
    user_service = UserService(db)
    user = await user_service.update_user_field(
        current_user.id, "image_s3_path", s3_path
    )

    return UserImageS3PathSchema.model_validate(user)


# GET /{user_id}/image-url
@router.get("/{user_id}/image-url", response_model=UserImageS3PathSchema)
async def get_user_image_url(
    user_id: UUID,
    current_user: user_from_jwt,
    db: db_dependency,
    s3_service: s3_service_dependency,
) -> UserImageS3PathSchema:
    """
    Get a presigned URL for a user's profile image
    """
    # Get the user
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id=user_id)

    if not user:
        raise UserNotFoundError()

    # Verify permissions
    await user_service.check_user_access_permissions(current_user, user)

    # Generate presigned URL
    image_url = await s3_service.get_user_image_url(user.image_s3_path)

    return UserImageS3PathSchema(
        id=user.id, username=user.username, image_url=image_url
    )


# DELETE /me/image
@router.delete("/me/image", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_image(
    current_user: user_from_jwt,
    db: db_dependency,
    s3_service: s3_service_dependency,
) -> JSONResponse:
    """
    Delete the current user's profile image
    """
    # Delete from S3
    deleted = await s3_service.delete_user_image(current_user.image_s3_path)
    if not deleted:
        raise InternalServerError("Error deleting image")

    # Update user record
    user_service = UserService(db)
    await user_service.update_user_field(
        current_user.id, "image_s3_path", None
    )

    return JSONResponse(status_code=204, content="User deleted")
