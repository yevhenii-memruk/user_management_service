import logging
from typing import BinaryIO, Optional
from uuid import UUID

import aioboto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, UploadFile, status

from src.db.models import User
from src.settings import settings
from src.utils.exceptions import InternalServerError, S3UploadError

logger = logging.getLogger(f"ums.{__name__}")


class S3Service:
    """Service for handling S3 operations"""

    def __init__(
        self,
        aws_access_key: str,
        aws_secret_key: str,
        region: str,
        bucket_name: str,
    ) -> None:
        self.session = aioboto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region,
        )
        self.bucket_name = bucket_name

    async def upload_user_image(
        self, user_id: UUID, file: BinaryIO, content_type: str
    ) -> str:
        """
        Upload a user profile image to S3

        Args:
            user_id: The user's UUID
            file: The file object to upload
            content_type: The content type of the file

        Returns:
            The S3 path of the uploaded file
        """
        file_path = (
            f"user-images/{user_id}/profile.{content_type.split('/')[-1]}"
        )

        try:
            async with self.session.client("s3") as s3:
                await s3.upload_fileobj(
                    file,
                    self.bucket_name,
                    file_path,
                    ExtraArgs={"ContentType": content_type},
                )
                logger.info(
                    f"Successfully uploaded image for user {user_id} to S3"
                )
                return file_path
        except ClientError as e:
            logger.error(f"S3 ClientError: {e}")
            raise S3UploadError(detail="Failed to upload image to S3")
        except BotoCoreError as e:
            logger.error(f"S3 BotoCoreError: {e}")
            raise S3UploadError(detail="AWS S3 encountered an internal issue")
        except Exception as e:
            logger.error(f"Error uploading image to S3: {str(e)}")
            raise S3UploadError(detail="Unexpected error during file upload")

    async def get_user_image_url(
        self, s3_path: str, expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate a presigned URL for a user's image

        Args:
            s3_path: The S3 path of the file
            expiration: URL expiration time in seconds (default: 1 hour)
        """
        if not s3_path:
            return None

        try:
            logger.info("Getting image URL for user's image")
            async with self.session.client("s3") as s3:
                url = await s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": s3_path},
                    ExpiresIn=expiration,
                )
                if not url:
                    raise InternalServerError(
                        "Failed to generate pre-signed URL for S3 object."
                    )
                return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return None

    async def delete_user_image(self, s3_path: str) -> bool:
        """Delete a user profile image from S3"""
        if not s3_path:
            return False

        try:
            async with self.session.client("s3") as s3:
                await s3.delete_object(Bucket=self.bucket_name, Key=s3_path)
                logger.info(f"Successfully deleted image at {s3_path} from S3")
                return True
        except Exception as e:
            logger.error(f"Error deleting image from S3: {str(e)}")
            return False

    async def validate_user_image(self, file: UploadFile, user: User) -> None:
        """Validate file type, check file size, delete image if exists."""
        allowed_types = ["image/jpeg", "image/png", "image/gif"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. "
                f"Allowed types: {', '.join(allowed_types)}",
            )

        # Check file size (limit to 5MB)
        file_size = 0
        contents = await file.read()
        file_size = len(contents)
        await file.seek(0)  # Reset file position

        if file_size > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size too large. Maximum size: 5MB",
            )

        # Delete old image if exists
        if user.image_s3_path:
            await self.delete_user_image(user.image_s3_path)


def get_s3_service() -> S3Service:
    return S3Service(
        aws_access_key=settings.AWS_ACCESS_KEY_ID,
        aws_secret_key=settings.AWS_SECRET_ACCESS_KEY,
        region=settings.AWS_REGION,
        bucket_name=settings.AWS_S3_BUCKET,
    )
