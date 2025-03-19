import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from src.api.dependencies.rabbitmq import RabbitMQPublisher
from src.db.models import User
from src.schemas.auth import PasswordResetRequest
from src.services.user import UserService
from src.settings import settings


def create_rabbitmq_message(user: User) -> dict[str, Any]:
    reset_token = str(uuid.uuid4())

    # Create reset link
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    # Prepare message for RabbitMQ
    message = {
        "email": user.email,
        "subject": "Password Reset Request",
        "body": f"Click the following link "
        f"to reset your password: {reset_link}",
        "datetime": datetime.now(timezone.utc).isoformat(),
        "user_id": str(user.id),
        "reset_token": reset_token,
    }

    return message


class PasswordResetService:
    """Handles password reset logic."""

    def __init__(
        self, user_service: UserService, message_broker: RabbitMQPublisher
    ):
        self.user_service = user_service
        self.message_broker = message_broker

    async def reset_password(
        self, request: PasswordResetRequest
    ) -> dict[str, str]:
        user = await self.user_service.get_user_by_email(request.email)

        if not user:
            return {
                "message": "If your email is registered, "
                "you will receive a password reset link"
            }

        message = create_rabbitmq_message(user)

        try:
            self.message_broker.publish_message(
                "reset-password-stream", message
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process password reset request: {str(e)}",
            )

        return {
            "message": "If your email is registered, "
            "you will receive a password reset link"
        }
