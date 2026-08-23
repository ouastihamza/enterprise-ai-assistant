import json
from datetime import datetime
from typing import List, Optional

import psycopg2
import psycopg2.extras

from app.auth.user_model import User
from app.config import DB_DSN


class UserService:
    """PostgreSQL-backed user service using table `tbl_users`.

    This implementation will create the table if it does not exist and
    expose the same interface used by the rest of the application.
    """

    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS tbl_users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        workspace_ids JSONB NOT NULL DEFAULT '[]',
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL
    );
    """

    def __init__(self, dsn: Optional[str] = None):
        self.dsn = dsn or DB_DSN
        self._ensure_table()

    def _get_conn(self):
        return psycopg2.connect(self.dsn)

    def _ensure_table(self) -> None:
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(self.CREATE_TABLE_SQL)
        finally:
            conn.close()

    def _row_to_user(self, row: dict) -> User:
        return User(
            id=row["id"],
            email=row["email"],
            full_name=row["full_name"],
            password_hash=row["password_hash"],
            workspace_ids=row.get("workspace_ids") or [],
            is_active=row.get("is_active", True),
            is_superuser=row.get("is_superuser", False),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def create_user(
        self,
        email: str,
        full_name: str,
        password_hash: str,
        workspace_ids: Optional[List[str]] = None,
        is_superuser: bool = False,
    ) -> Optional[User]:
        if self.get_user_by_email(email) is not None:
            return None

        now = datetime.now()
        user = User(
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            workspace_ids=workspace_ids or [],
            is_superuser=is_superuser,
        )

        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO tbl_users
                        (id, email, full_name, password_hash, workspace_ids, is_active, is_superuser, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
                        """,
                        (
                            user.id,
                            user.email,
                            user.full_name,
                            user.password_hash,
                            json.dumps(user.workspace_ids),
                            user.is_active,
                            user.is_superuser,
                            now,
                            now,
                        ),
                    )
        finally:
            conn.close()

        return user

    def list_users(self) -> List[User]:
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT * FROM tbl_users ORDER BY created_at ASC")
                    rows = cur.fetchall()
                    return [self._row_to_user(row) for row in rows]
        finally:
            conn.close()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT * FROM tbl_users WHERE id = %s", (user_id,))
                    row = cur.fetchone()
                    if row:
                        return self._row_to_user(row)
                    return None
        finally:
            conn.close()

    def get_user_by_email(self, email: str) -> Optional[User]:
        normalized = email.lower().strip()
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT * FROM tbl_users WHERE lower(email) = %s", (normalized,))
                    row = cur.fetchone()
                    if row:
                        return self._row_to_user(row)
                    return None
        finally:
            conn.close()

    def update_user(
        self,
        user_id: str,
        full_name: Optional[str] = None,
        workspace_ids: Optional[List[str]] = None,
        is_active: Optional[bool] = None,
        is_superuser: Optional[bool] = None,
    ) -> Optional[User]:
        parts = []
        values = []

        if full_name is not None:
            parts.append("full_name = %s")
            values.append(full_name)

        if workspace_ids is not None:
            parts.append("workspace_ids = %s::jsonb")
            values.append(json.dumps(workspace_ids))

        if is_active is not None:
            parts.append("is_active = %s")
            values.append(is_active)

        if is_superuser is not None:
            parts.append("is_superuser = %s")
            values.append(is_superuser)

        if not parts:
            return self.get_user_by_id(user_id)

        parts.append("updated_at = %s")
        values.append(datetime.now())

        sql = f"UPDATE tbl_users SET {', '.join(parts)} WHERE id = %s RETURNING *"
        values.append(user_id)

        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(sql, tuple(values))
                    row = cur.fetchone()
                    if row:
                        return self._row_to_user(row)
                    return None
        finally:
            conn.close()

    def assign_workspace(self, user_id: str, workspace_id: str) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        workspace_ids = list(user.workspace_ids)
        if workspace_id not in workspace_ids:
            workspace_ids.append(workspace_id)

        return self.update_user(user_id=user_id, workspace_ids=workspace_ids)

    def remove_workspace(self, user_id: str, workspace_id: str) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        workspace_ids = [w for w in user.workspace_ids if w != workspace_id]
        return self.update_user(user_id=user_id, workspace_ids=workspace_ids)

    def user_has_workspace(self, user_id: str, workspace_id: str) -> bool:
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        if user.is_superuser:
            return True
        return workspace_id in user.workspace_ids