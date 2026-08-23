from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from app.config import JWT_ALGORITHM, JWT_SECRET_KEY


class JWTService:
    """
    Handles JWT token creation and validation.
    """

    def create_access_token(
        self,
        subject: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        if expires_delta is None:
            expires_delta = timedelta(hours=24)

        expire = datetime.utcnow() + expires_delta

        payload = {
            "sub": subject,
            "exp": expire,
        }

        return jwt.encode(
            payload,
            JWT_SECRET_KEY,
            algorithm=JWT_ALGORITHM,
        )

    def verify_access_token(
        self,
        token: str,
    ) -> Optional[str]:
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM],
            )

            subject = payload.get("sub")

            if subject is None:
                return None

            return subject

        except JWTError:
            return None