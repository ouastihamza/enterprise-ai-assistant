import bcrypt


class PasswordService:
    """
    Handles password hashing and verification.
    """

    def hash_password(
        self,
        password: str,
    ) -> str:
        password_bytes = password.encode("utf-8")

        hashed_password = bcrypt.hashpw(
            password_bytes,
            bcrypt.gensalt(),
        )

        return hashed_password.decode("utf-8")

    def verify_password(
        self,
        plain_password: str,
        password_hash: str,
    ) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )