from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.utils.exceptions import (
    InvalidAuthorizationTokenError,
    InvalidCredentialsException,
)
from src.utils.jwt_manager import JWTManager


class JWTBearer(HTTPBearer):
    def __init__(self, jwt_manager: JWTManager, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.jwt_manager = jwt_manager

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
            raise InvalidCredentialsException()

        return payload
