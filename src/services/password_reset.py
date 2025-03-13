from fastapi import HTTPException

from src.api.dependencies.rabbitmq import RabbitMQPublisher
from src.schemas.auth import PasswordResetRequest
from src.services.auth import create_rabbitmq_message
from src.services.user import UserService


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
