from unittest.mock import MagicMock

import pytest

from src.utils.password_manager import PasswordManager


@pytest.fixture
def password_manager() -> PasswordManager:
    """Fixture to provide an instance of PasswordManager."""
    return PasswordManager()


def test_password_hashing(password_manager: PasswordManager) -> None:
    """Test that the password is hashed correctly."""
    password = "testpassword123"
    hashed_password = password_manager.get_hash(password)

    # Hash should be different from original password
    assert hashed_password != password


def test_password_verification(password_manager: PasswordManager) -> None:
    """Test that the password verification works correctly."""
    password = "testpassword123"
    hashed_password = password_manager.get_hash(password)

    # Verification should work
    assert password_manager.verify_password(password, hashed_password) is True


def test_wrong_password_verification(
    password_manager: PasswordManager,
) -> None:
    """Test that an incorrect password does not pass verification."""
    password = "testpassword123"
    hashed_password = password_manager.get_hash(password)

    # Wrong password should fail verification
    assert (
        password_manager.verify_password("wrongpassword", hashed_password)
        is False
    )


def test_mocked_password_manager() -> None:
    """Test PasswordManager with a mock to ensure it follows expected behavior."""
    mock_manager = MagicMock(spec=PasswordManager)
    mock_manager.get_hash.return_value = "mocked_hashed_password"
    mock_manager.verify_password.side_effect = (
        lambda p, h: p == "testpassword123"
    )

    assert mock_manager.get_hash("testpassword123") == "mocked_hashed_password"
    assert (
        mock_manager.verify_password(
            "testpassword123", "mocked_hashed_password"
        )
        is True
    )
    assert (
        mock_manager.verify_password("wrongpassword", "mocked_hashed_password")
        is False
    )


@pytest.mark.parametrize("password", ["password", "123456", "qwerty"])
def test_weak_passwords(
    password_manager: PasswordManager, password: str
) -> None:
    """Ensure weak passwords are still hashed but different."""
    hashed_password = password_manager.get_hash(password)
    assert hashed_password != password
