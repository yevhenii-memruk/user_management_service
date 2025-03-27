from typing import Optional

from fastapi import HTTPException, status


class InvalidCredentialsException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidAuthorizationTokenError(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authorization token",
        )


class InvalidTokenError(Exception):
    """Raised when a token is invalid, expired, or blacklisted"""

    pass


class InvalidTokenDataError(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token data",
        )


class UserBlockedError(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is blocked",
        )


class NotEnoughPermissionsError(HTTPException):
    def __init__(self, detail: Optional[str] = None) -> None:
        detail = detail or "Not enough permissions"
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class UserNotFoundError(HTTPException):
    """Exception raised when a user is not found."""

    def __init__(self, user_id: Optional[str] = None):
        if user_id is None:
            detail = "User not found"
        else:
            detail = f"User with ID {user_id} not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UserAlreadyExistsError(HTTPException):
    """Exception raised when a user already exists."""

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email, username or phone number already exists",
        )


class GroupNotExistError(HTTPException):
    """Exception raised when a group is not found."""

    def __init__(self, group_id: int):
        detail = f"Group with ID {group_id} not found"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST, detail=detail
        )


class InternalServerError(HTTPException):
    """Exception raised when an internal server error occurs."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )


class S3UploadError(HTTPException):
    """Exception raised when S3 upload fails"""

    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
        )
