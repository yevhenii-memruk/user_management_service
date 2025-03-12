from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.settings import settings
from src.utils.exceptions import (
    InvalidAuthorizationTokenError,
    PayloadDecodeError,
)
from src.utils.jwt_manager import JWTManager

jwt_manager_data = JWTManager(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
    expires_minutes=settings.JWT_EXPIRE_MINUTES,
)


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.jwt_manager = jwt_manager_data

    async def __call__(self, request: Request) -> dict:
        credentials: HTTPAuthorizationCredentials = await super().__call__(
            request
        )
        if not credentials:
            raise InvalidAuthorizationTokenError()

        try:
            payload = self.jwt_manager.decode_jwt_token(
                token=credentials.credentials
            )
        except HTTPException:
            raise PayloadDecodeError()

        return payload
