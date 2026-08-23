from datetime import datetime, timezone
from typing import Optional

import psycopg2
import psycopg2.extras

from app.config import DB_DSN


class DocumentRegistry:
    """
    PostgreSQL-backed document registry.

    All document operations are isolated by workspace.
    """

    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS tbl_documents (
        id SERIAL PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        name TEXT NOT NULL,
        source_file TEXT NOT NULL,
        chunks_file TEXT NOT NULL,
        chunk_count INTEGER NOT NULL DEFAULT 0,
        file_size BIGINT NOT NULL DEFAULT 0,
        indexed BOOLEAN NOT NULL DEFAULT FALSE,
        status TEXT NOT NULL DEFAULT 'Processing',
        uploaded_at TIMESTAMPTZ NOT NULL,
        last_indexed TIMESTAMPTZ,
        error_message TEXT,
        UNIQUE(workspace_id, name)
    );
    """

    MIGRATION_SQL = """
    ALTER TABLE tbl_documents
    ADD COLUMN IF NOT EXISTS error_message TEXT;

    ALTER TABLE tbl_documents
    ALTER COLUMN last_indexed DROP NOT NULL;
    """

    def __init__(
        self,
        workspace_id: str,
        dsn: Optional[str] = None,
    ):
        if not workspace_id.strip():
            raise ValueError(
                "workspace_id cannot be empty."
            )

        self.workspace_id = workspace_id
        self.dsn = dsn or DB_DSN

        self._ensure_table()

    def _get_conn(self):
        return psycopg2.connect(
            self.dsn
        )

    def _ensure_table(self) -> None:
        with self._get_conn() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    self.CREATE_TABLE_SQL
                )

                cursor.execute(
                    self.MIGRATION_SQL
                )

    @staticmethod
    def _format_datetime(
        value,
    ) -> str | None:
        if value is None:
            return None

        return value.strftime(
            "%Y-%m-%d %H:%M"
        )

    def _row_to_dict(
        self,
        row: dict,
    ) -> dict:
        return {
            "id": row["id"],
            "workspace_id": row["workspace_id"],
            "name": row["name"],
            "source_file": row["source_file"],
            "chunks_file": row["chunks_file"],
            "chunk_count": row["chunk_count"],
            "file_size": row["file_size"],
            "indexed": row["indexed"],
            "status": row["status"],
            "uploaded_at": self._format_datetime(
                row["uploaded_at"]
            ),
            "last_indexed": self._format_datetime(
                row["last_indexed"]
            ),
            "error_message": row.get(
                "error_message"
            ),
        }

    def register_document(
        self,
        name: str,
        source_file: str,
        chunks_file: str,
        chunk_count: int,
        file_size: int,
    ) -> dict:
        now = datetime.now(
            timezone.utc
        )

        with self._get_conn() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    """
                    INSERT INTO tbl_documents (
                        workspace_id,
                        name,
                        source_file,
                        chunks_file,
                        chunk_count,
                        file_size,
                        indexed,
                        status,
                        uploaded_at,
                        last_indexed,
                        error_message
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        TRUE, 'Ready', %s, %s, NULL
                    )
                    ON CONFLICT (workspace_id, name)
                    DO UPDATE SET
                        source_file = EXCLUDED.source_file,
                        chunks_file = EXCLUDED.chunks_file,
                        chunk_count = EXCLUDED.chunk_count,
                        file_size = EXCLUDED.file_size,
                        indexed = TRUE,
                        status = 'Ready',
                        last_indexed = EXCLUDED.last_indexed,
                        error_message = NULL
                    RETURNING *
                    """,
                    (
                        self.workspace_id,
                        name,
                        source_file,
                        chunks_file,
                        chunk_count,
                        file_size,
                        now,
                        now,
                    ),
                )

                row = cursor.fetchone()

        return self._row_to_dict(row)

    def get_all_documents(
        self,
    ) -> list[dict]:
        with self._get_conn() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM tbl_documents
                    WHERE workspace_id = %s
                    ORDER BY uploaded_at DESC
                    """,
                    (self.workspace_id,),
                )

                rows = cursor.fetchall()

        return [
            self._row_to_dict(row)
            for row in rows
        ]

    def get_document_by_id(
        self,
        document_id: int,
    ) -> Optional[dict]:
        with self._get_conn() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM tbl_documents
                    WHERE id = %s
                    AND workspace_id = %s
                    """,
                    (
                        document_id,
                        self.workspace_id,
                    ),
                )

                row = cursor.fetchone()

        return (
            self._row_to_dict(row)
            if row
            else None
        )

    def get_document_by_name(
        self,
        name: str,
    ) -> Optional[dict]:
        with self._get_conn() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM tbl_documents
                    WHERE workspace_id = %s
                    AND name = %s
                    """,
                    (
                        self.workspace_id,
                        name,
                    ),
                )

                row = cursor.fetchone()

        return (
            self._row_to_dict(row)
            if row
            else None
        )

    def document_exists(
        self,
        name: str,
    ) -> bool:
        return (
            self.get_document_by_name(name)
            is not None
        )

    def update_document(
        self,
        document_id: int,
        *,
        chunks_file: str | None = None,
        chunk_count: int | None = None,
        file_size: int | None = None,
        indexed: bool | None = None,
        status: str | None = None,
        error_message: str | None = None,
        clear_error: bool = False,
        update_index_time: bool = False,
    ) -> Optional[dict]:
        assignments: list[str] = []
        values: list = []

        update_fields = {
            "chunks_file": chunks_file,
            "chunk_count": chunk_count,
            "file_size": file_size,
            "indexed": indexed,
            "status": status,
        }

        for column, value in update_fields.items():
            if value is not None:
                assignments.append(
                    f"{column} = %s"
                )
                values.append(value)

        if clear_error:
            assignments.append(
                "error_message = NULL"
            )

        elif error_message is not None:
            assignments.append(
                "error_message = %s"
            )
            values.append(error_message)

        if update_index_time:
            assignments.append(
                "last_indexed = %s"
            )
            values.append(
                datetime.now(timezone.utc)
            )

        if not assignments:
            return self.get_document_by_id(
                document_id
            )

        values.extend(
            [
                document_id,
                self.workspace_id,
            ]
        )

        with self._get_conn() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    f"""
                    UPDATE tbl_documents
                    SET {", ".join(assignments)}
                    WHERE id = %s
                    AND workspace_id = %s
                    RETURNING *
                    """,
                    tuple(values),
                )

                row = cursor.fetchone()

        return (
            self._row_to_dict(row)
            if row
            else None
        )

    def update_document_status(
        self,
        document_id: int,
        status: str,
        indexed: bool,
        error_message: str | None = None,
    ) -> Optional[dict]:
        return self.update_document(
            document_id=document_id,
            status=status,
            indexed=indexed,
            error_message=error_message,
            clear_error=error_message is None,
            update_index_time=indexed,
        )

    def delete_document(
        self,
        document_id: int,
    ) -> bool:
        with self._get_conn() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM tbl_documents
                    WHERE id = %s
                    AND workspace_id = %s
                    """,
                    (
                        document_id,
                        self.workspace_id,
                    ),
                )

                return cursor.rowcount > 0

    def load(self) -> list[dict]:
        return self.get_all_documents()