from passlib.context import CryptContext


class PasswordManager:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @classmethod
    def get_hash(cls, password: str) -> str:
        """Hash a password using bcrypt."""
        return cls.pwd_context.hash(password)

    @classmethod
    def verify_password(
        cls, plain_password: str, hashed_password: str
    ) -> bool:
        """Verify if a password matches the stored hash."""
        return cls.pwd_context.verify(plain_password, hashed_password)
