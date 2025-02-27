from passlib.context import CryptContext


class PasswordManager:
    def __init__(self) -> None:
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def get_hash(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return self.pwd_context.hash(password)

    def verify_password(
        self, plain_password: str, hashed_password: str
    ) -> bool:
        """Verify if a password matches the stored hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
