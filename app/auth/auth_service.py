from typing import Optional

from app.auth.jwt_service import JWTService
from app.auth.password_service import PasswordService
from app.auth.user_model import User
from app.auth.user_service import UserService


class AuthService:
    """
    Handles user registration and login.
    """

    def __init__(self):
        self.user_service = UserService()
        self.password_service = PasswordService()
        self.jwt_service = JWTService()

    def register_user(
        self,
        email: str,
        full_name: str,
        password: str,
    ) -> Optional[User]:
        password_hash = self.password_service.hash_password(
            password
        )

        return self.user_service.create_user(
            email=email,
            full_name=full_name,
            password_hash=password_hash,
        )

    def authenticate_user(
        self,
        email: str,
        password: str,
    ) -> Optional[User]:
        user = self.user_service.get_user_by_email(email)

        if not user:
            return None

        password_is_valid = self.password_service.verify_password(
            plain_password=password,
            password_hash=user.password_hash,
        )

        if not password_is_valid:
            return None

        if not user.is_active:
            return None

        return user

    def create_token_for_user(
        self,
        user: User,
    ) -> str:
        return self.jwt_service.create_access_token(
            subject=user.id
        )