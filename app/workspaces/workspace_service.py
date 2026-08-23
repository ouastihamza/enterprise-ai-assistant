import json
from datetime import datetime
from typing import List, Optional

import psycopg2
import psycopg2.extras

from app.config import DB_DSN
from app.workspaces.workspace_model import Workspace


class WorkspaceService:
    """PostgreSQL-backed workspace service using table `tbl_workspaces`.

    This implementation will create the table if it does not exist and
    expose the same interface used by the rest of the application.
    """

    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS tbl_workspaces (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        company_name TEXT NOT NULL,
        industry TEXT,
        description TEXT,
        enabled_modules JSONB NOT NULL DEFAULT '[]',
        status TEXT NOT NULL DEFAULT 'active',
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

    def _row_to_workspace(self, row: dict) -> Workspace:
        return Workspace(
            id=row["id"],
            name=row["name"],
            company_name=row["company_name"],
            industry=row.get("industry"),
            description=row.get("description"),
            enabled_modules=row.get("enabled_modules") or [],
            status=row.get("status", "active"),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def create_workspace(
        self,
        name: str,
        company_name: str,
        industry: Optional[str] = None,
        description: Optional[str] = None,
        enabled_modules: Optional[List[str]] = None,
    ) -> Workspace:
        now = datetime.now()
        workspace = Workspace(
            id=None,
            name=name,
            company_name=company_name,
            industry=industry,
            description=description,
            enabled_modules=enabled_modules or [],
            created_at=now,
            updated_at=now,
        )

        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor
                ) as cur:
                    cur.execute(
                        """
                        INSERT INTO tbl_workspaces
                        (id, name, company_name, industry, description, enabled_modules, status, created_at, updated_at)
                        VALUES (gen_random_uuid()::text, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                        RETURNING *
                        """,
                        (
                            workspace.name,
                            workspace.company_name,
                            workspace.industry,
                            workspace.description,
                            json.dumps(workspace.enabled_modules),
                            workspace.status,
                            workspace.created_at,
                            workspace.updated_at,
                        ),
                    )
                    row = cur.fetchone()
                    return self._row_to_workspace(row)
        finally:
            conn.close()

    def list_workspaces(self) -> List[Workspace]:
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor
                ) as cur:
                    cur.execute(
                        "SELECT * FROM tbl_workspaces ORDER BY created_at ASC"
                    )
                    rows = cur.fetchall()
                    return [self._row_to_workspace(row) for row in rows]
        finally:
            conn.close()

    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor
                ) as cur:
                    cur.execute(
                        "SELECT * FROM tbl_workspaces WHERE id = %s",
                        (workspace_id,),
                    )
                    row = cur.fetchone()
                    if row:
                        return self._row_to_workspace(row)
                    return None
        finally:
            conn.close()

    def update_workspace(
        self,
        workspace_id: str,
        name: Optional[str] = None,
        company_name: Optional[str] = None,
        industry: Optional[str] = None,
        description: Optional[str] = None,
        enabled_modules: Optional[List[str]] = None,
    ) -> Optional[Workspace]:
        parts = []
        values = []

        if name is not None:
            parts.append("name = %s")
            values.append(name)

        if company_name is not None:
            parts.append("company_name = %s")
            values.append(company_name)

        if industry is not None:
            parts.append("industry = %s")
            values.append(industry)

        if description is not None:
            parts.append("description = %s")
            values.append(description)

        if enabled_modules is not None:
            parts.append("enabled_modules = %s::jsonb")
            values.append(json.dumps(enabled_modules))

        if not parts:
            return self.get_workspace(workspace_id)

        parts.append("updated_at = %s")
        values.append(datetime.now())

        sql = (
            f"UPDATE tbl_workspaces SET {', '.join(parts)} "
            "WHERE id = %s RETURNING *"
        )
        values.append(workspace_id)

        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor
                ) as cur:
                    cur.execute(sql, tuple(values))
                    row = cur.fetchone()
                    if row:
                        return self._row_to_workspace(row)
                    return None
        finally:
            conn.close()

    def archive_workspace(self, workspace_id: str) -> Optional[Workspace]:
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor
                ) as cur:
                    cur.execute(
                        """
                        UPDATE tbl_workspaces
                        SET status = 'archived', updated_at = %s
                        WHERE id = %s
                        RETURNING *
                        """,
                        (datetime.now(), workspace_id),
                    )
                    row = cur.fetchone()
                    if row:
                        return self._row_to_workspace(row)
                    return None
        finally:
            conn.close()
