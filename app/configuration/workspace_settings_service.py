import json
from datetime import datetime
from typing import Optional

import psycopg2
import psycopg2.extras

from app.configuration.workspace_settings_model import WorkspaceSettings
from app.config import DB_DSN


class WorkspaceSettingsService:
    """PostgreSQL-backed workspace settings service using table `tbl_workspace_settings`."""

    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS tbl_workspace_settings (
        workspace_id TEXT PRIMARY KEY,
        assistant_name TEXT NOT NULL,
        company_logo TEXT,
        primary_color TEXT NOT NULL,
        theme TEXT NOT NULL,
        llm_model TEXT NOT NULL,
        temperature FLOAT NOT NULL,
        chunk_size INT NOT NULL,
        chunk_overlap INT NOT NULL,
        top_k INT NOT NULL,
        max_upload_size_mb INT NOT NULL,
        allowed_file_types JSONB NOT NULL,
        welcome_message TEXT NOT NULL,
        system_prompt TEXT NOT NULL,
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

    def _row_to_settings(self, row: dict) -> WorkspaceSettings:
        return WorkspaceSettings(
            workspace_id=row["workspace_id"],
            assistant_name=row["assistant_name"],
            company_logo=row.get("company_logo", ""),
            primary_color=row["primary_color"],
            theme=row["theme"],
            llm_model=row["llm_model"],
            temperature=row["temperature"],
            chunk_size=row["chunk_size"],
            chunk_overlap=row["chunk_overlap"],
            top_k=row["top_k"],
            max_upload_size_mb=row["max_upload_size_mb"],
            allowed_file_types=row.get("allowed_file_types") or [],
            welcome_message=row["welcome_message"],
            system_prompt=row["system_prompt"],
        )

    def create_default_settings(
        self,
        workspace_id: str,
    ) -> WorkspaceSettings:
        existing = self.get_settings(workspace_id)
        if existing:
            return existing

        now = datetime.now()
        settings = WorkspaceSettings(workspace_id=workspace_id)

        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO tbl_workspace_settings
                        (workspace_id, assistant_name, company_logo, primary_color, theme, 
                         llm_model, temperature, chunk_size, chunk_overlap, top_k,
                         max_upload_size_mb, allowed_file_types, welcome_message, system_prompt,
                         created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
                        """,
                        (
                            settings.workspace_id,
                            settings.assistant_name,
                            settings.company_logo,
                            settings.primary_color,
                            settings.theme,
                            settings.llm_model,
                            settings.temperature,
                            settings.chunk_size,
                            settings.chunk_overlap,
                            settings.top_k,
                            settings.max_upload_size_mb,
                            json.dumps(settings.allowed_file_types),
                            settings.welcome_message,
                            settings.system_prompt,
                            now,
                            now,
                        ),
                    )
        finally:
            conn.close()

        return settings

    def get_settings(
        self,
        workspace_id: str,
    ) -> Optional[WorkspaceSettings]:
        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(
                        "SELECT * FROM tbl_workspace_settings WHERE workspace_id = %s",
                        (workspace_id,)
                    )
                    row = cur.fetchone()
                    if row:
                        return self._row_to_settings(row)
                    return None
        finally:
            conn.close()

    def get_or_create_settings(
        self,
        workspace_id: str,
    ) -> WorkspaceSettings:
        settings = self.get_settings(workspace_id)
        if settings:
            return settings
        return self.create_default_settings(workspace_id)

    def update_settings(
        self,
        workspace_id: str,
        assistant_name: Optional[str] = None,
        company_logo: Optional[str] = None,
        primary_color: Optional[str] = None,
        theme: Optional[str] = None,
        llm_model: Optional[str] = None,
        temperature: Optional[float] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        top_k: Optional[int] = None,
        max_upload_size_mb: Optional[int] = None,
        allowed_file_types: Optional[list[str]] = None,
        welcome_message: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Optional[WorkspaceSettings]:
        parts = []
        values = []

        if assistant_name is not None:
            parts.append("assistant_name = %s")
            values.append(assistant_name)
        if company_logo is not None:
            parts.append("company_logo = %s")
            values.append(company_logo)
        if primary_color is not None:
            parts.append("primary_color = %s")
            values.append(primary_color)
        if theme is not None:
            parts.append("theme = %s")
            values.append(theme)
        if llm_model is not None:
            parts.append("llm_model = %s")
            values.append(llm_model)
        if temperature is not None:
            parts.append("temperature = %s")
            values.append(temperature)
        if chunk_size is not None:
            parts.append("chunk_size = %s")
            values.append(chunk_size)
        if chunk_overlap is not None:
            parts.append("chunk_overlap = %s")
            values.append(chunk_overlap)
        if top_k is not None:
            parts.append("top_k = %s")
            values.append(top_k)
        if max_upload_size_mb is not None:
            parts.append("max_upload_size_mb = %s")
            values.append(max_upload_size_mb)
        if allowed_file_types is not None:
            parts.append("allowed_file_types = %s::jsonb")
            values.append(json.dumps(allowed_file_types))
        if welcome_message is not None:
            parts.append("welcome_message = %s")
            values.append(welcome_message)
        if system_prompt is not None:
            parts.append("system_prompt = %s")
            values.append(system_prompt)

        if not parts:
            return self.get_settings(workspace_id)

        parts.append("updated_at = %s")
        values.append(datetime.now())

        sql = f"UPDATE tbl_workspace_settings SET {', '.join(parts)} WHERE workspace_id = %s RETURNING *"
        values.append(workspace_id)

        conn = self._get_conn()
        try:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(sql, tuple(values))
                    row = cur.fetchone()
                    if row:
                        return self._row_to_settings(row)
                    return None
        finally:
            conn.close()