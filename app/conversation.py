import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import psycopg2
import psycopg2.extras

from app.config import DB_DSN
from app.services.conversation_helpers import build_regeneration_context


class ConversationManager:
    """
    PostgreSQL-backed conversation manager.

    Isolation hierarchy:
        workspace
            → user
                → conversation
                    → messages

    PostgreSQL is the permanent source of truth.
    Redis will later cache recent messages without replacing this layer.
    """

    CREATE_CONVERSATIONS_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS tbl_conversations (
        id TEXT PRIMARY KEY,
        workspace_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        created_at TIMESTAMPTZ NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL
    );
    """

    CREATE_MESSAGES_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS tbl_conversation_messages (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        workspace_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        sources JSONB NOT NULL DEFAULT '[]'::jsonb,
        created_at TIMESTAMPTZ NOT NULL,

        CONSTRAINT fk_conversation_messages_conversation
            FOREIGN KEY (conversation_id)
            REFERENCES tbl_conversations(id)
            ON DELETE CASCADE,

        CONSTRAINT valid_conversation_message_role
            CHECK (role IN ('user', 'assistant', 'system'))
    );
    """

    CREATE_INDEXES_SQL = """
    CREATE INDEX IF NOT EXISTS idx_conversations_workspace_user
    ON tbl_conversations(workspace_id, user_id, updated_at DESC);

    CREATE INDEX IF NOT EXISTS idx_messages_conversation_created
    ON tbl_conversation_messages(conversation_id, created_at ASC);

    CREATE INDEX IF NOT EXISTS idx_messages_workspace_user
    ON tbl_conversation_messages(workspace_id, user_id);
    """

    def __init__(
        self,
        workspace_id: str,
        user_id: str,
        conversation_id: str | None = None,
        dsn: str | None = None,
    ):
        if not workspace_id or not workspace_id.strip():
            raise ValueError(
                "workspace_id cannot be empty."
            )

        if not user_id or not user_id.strip():
            raise ValueError(
                "user_id cannot be empty."
            )

        self.workspace_id = workspace_id.strip()
        self.user_id = user_id.strip()
        self.dsn = dsn or DB_DSN

        self._ensure_tables()

        self.conversation_id = (
            conversation_id
            if conversation_id
            else self._get_or_create_active_conversation()
        )

        self._ensure_conversation_access(
            conversation_id=self.conversation_id
        )

        self.messages = self.load_history()

    def _get_conn(self):
        return psycopg2.connect(
            self.dsn
        )

    def _ensure_tables(self) -> None:
        with self._get_conn() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    self.CREATE_CONVERSATIONS_TABLE_SQL
                )

                cursor.execute(
                    self.CREATE_MESSAGES_TABLE_SQL
                )

                cursor.execute(
                    self.CREATE_INDEXES_SQL
                )

    def _ensure_conversation_access(
        self,
        conversation_id: str,
    ) -> None:
        with self._get_conn() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 1
                    FROM tbl_conversations
                    WHERE id = %s
                      AND workspace_id = %s
                      AND user_id = %s
                    """,
                    (
                        conversation_id,
                        self.workspace_id,
                        self.user_id,
                    ),
                )

                exists = cursor.fetchone()

        if exists is None:
            raise PermissionError(
                "Conversation not found or access denied."
            )

    def _get_or_create_active_conversation(
        self,
    ) -> str:
        with self._get_conn() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM tbl_conversations
                    WHERE workspace_id = %s
                      AND user_id = %s
                      AND status = 'active'
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """,
                    (
                        self.workspace_id,
                        self.user_id,
                    ),
                )

                row = cursor.fetchone()

        if row:
            return row[0]

        conversation = self.create_conversation()

        return conversation["id"]

    def create_conversation(
        self,
        title: str = "New conversation",
    ) -> dict:
        conversation_id = str(uuid4())
        now = datetime.now(timezone.utc)

        clean_title = (
            title.strip()
            if title and title.strip()
            else "New conversation"
        )

        with self._get_conn() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    """
                    INSERT INTO tbl_conversations (
                        id,
                        workspace_id,
                        user_id,
                        title,
                        status,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s,
                        'active', %s, %s
                    )
                    RETURNING *
                    """,
                    (
                        conversation_id,
                        self.workspace_id,
                        self.user_id,
                        clean_title,
                        now,
                        now,
                    ),
                )

                row = cursor.fetchone()

        return self._conversation_row_to_dict(row)

    def start_new_conversation(
        self,
        title: str = "New conversation",
    ) -> str:
        conversation = self.create_conversation(
            title=title
        )

        self.conversation_id = conversation["id"]
        self.messages = []

        return self.conversation_id

    def list_conversations(
        self,
        limit: int = 50,
    ) -> list[dict]:
        safe_limit = max(
            1,
            min(limit, 200),
        )

        with self._get_conn() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    """
                    SELECT
                        conversation.*,
                        COUNT(message.id) AS message_count
                    FROM tbl_conversations conversation
                    LEFT JOIN tbl_conversation_messages message
                        ON message.conversation_id = conversation.id
                    WHERE conversation.workspace_id = %s
                      AND conversation.user_id = %s
                    GROUP BY conversation.id
                    ORDER BY conversation.updated_at DESC
                    LIMIT %s
                    """,
                    (
                        self.workspace_id,
                        self.user_id,
                        safe_limit,
                    ),
                )

                rows = cursor.fetchall()

        return [
            self._conversation_row_to_dict(row)
            for row in rows
        ]

    def switch_conversation(
        self,
        conversation_id: str,
    ) -> list[dict[str, Any]]:
        self._ensure_conversation_access(
            conversation_id=conversation_id
        )

        self.conversation_id = conversation_id
        self.messages = self.load_history()

        return self.messages

    def rename_conversation(
        self,
        title: str,
    ) -> bool:
        clean_title = title.strip()

        if not clean_title:
            raise ValueError(
                "Conversation title cannot be empty."
            )

        with self._get_conn() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE tbl_conversations
                    SET title = %s,
                        updated_at = %s
                    WHERE id = %s
                      AND workspace_id = %s
                      AND user_id = %s
                    """,
                    (
                        clean_title[:200],
                        datetime.now(timezone.utc),
                        self.conversation_id,
                        self.workspace_id,
                        self.user_id,
                    ),
                )

                return cursor.rowcount > 0

    def delete_conversation(
        self,
        conversation_id: str | None = None,
    ) -> bool:
        target_id = (
            conversation_id
            or self.conversation_id
        )

        self._ensure_conversation_access(
            conversation_id=target_id
        )

        with self._get_conn() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM tbl_conversations
                    WHERE id = %s
                      AND workspace_id = %s
                      AND user_id = %s
                    """,
                    (
                        target_id,
                        self.workspace_id,
                        self.user_id,
                    ),
                )

                deleted = cursor.rowcount > 0

        if deleted and target_id == self.conversation_id:
            self.start_new_conversation()

        return deleted

    def load_history(
        self,
    ) -> list[dict[str, Any]]:
        with self._get_conn() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    """
                    SELECT
                        id,
                        role,
                        content,
                        sources,
                        created_at
                    FROM tbl_conversation_messages
                    WHERE conversation_id = %s
                      AND workspace_id = %s
                      AND user_id = %s
                    ORDER BY created_at ASC
                    """,
                    (
                        self.conversation_id,
                        self.workspace_id,
                        self.user_id,
                    ),
                )

                rows = cursor.fetchall()

        return [
            self._message_row_to_dict(row)
            for row in rows
        ]

    def add_message(
        self,
        role: str,
        content: str,
        sources: list[dict] | None = None,
    ) -> dict:
        normalized_role = role.strip().lower()

        if normalized_role not in {
            "user",
            "assistant",
            "system",
        }:
            raise ValueError(
                "Message role must be user, assistant, or system."
            )

        clean_content = content.strip()

        if not clean_content:
            raise ValueError(
                "Message content cannot be empty."
            )

        message_id = str(uuid4())
        now = datetime.now(timezone.utc)
        safe_sources = sources or []

        with self._get_conn() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    """
                    INSERT INTO tbl_conversation_messages (
                        id,
                        conversation_id,
                        workspace_id,
                        user_id,
                        role,
                        content,
                        sources,
                        created_at
                    )
                    VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s::jsonb, %s
                    )
                    RETURNING *
                    """,
                    (
                        message_id,
                        self.conversation_id,
                        self.workspace_id,
                        self.user_id,
                        normalized_role,
                        clean_content,
                        json.dumps(
                            safe_sources,
                            ensure_ascii=False,
                        ),
                        now,
                    ),
                )

                row = cursor.fetchone()

                cursor.execute(
                    """
                    UPDATE tbl_conversations
                    SET updated_at = %s
                    WHERE id = %s
                      AND workspace_id = %s
                      AND user_id = %s
                    """,
                    (
                        now,
                        self.conversation_id,
                        self.workspace_id,
                        self.user_id,
                    ),
                )

        message = self._message_row_to_dict(row)
        self.messages.append(message)

        self._generate_title_from_first_message(
            role=normalized_role,
            content=clean_content,
        )

        return message

    def add_user_message(
        self,
        message: str,
    ) -> dict:
        return self.add_message(
            role="user",
            content=message,
        )

    def add_assistant_message(
        self,
        message: str,
        sources: list[dict] | None = None,
    ) -> dict:
        return self.add_message(
            role="assistant",
            content=message,
            sources=sources,
        )

    def get_llm_history(
        self,
        limit: int = 10,
    ) -> list[dict]:
        safe_limit = max(
            1,
            min(limit, 100),
        )

        history = self.messages[
            -safe_limit:
        ]

        return [
            {
                "role": message["role"],
                "content": message["content"],
            }
            for message in history
            if message.get("role")
            in {
                "user",
                "assistant",
                "system",
            }
        ]

    def get_regeneration_context(self, limit: int = 10) -> dict:
        self.messages = self.load_history()
        return build_regeneration_context(self.messages, limit=limit)

    def replace_assistant_message(
        self,
        message_id: str,
        message: str,
        sources: list[dict] | None = None,
    ) -> dict:
        clean_content = message.strip()
        if not clean_content:
            raise ValueError("Message content cannot be empty.")

        now = datetime.now(timezone.utc)
        with self._get_conn() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            ) as cursor:
                cursor.execute(
                    """
                    UPDATE tbl_conversation_messages
                    SET content = %s, sources = %s::jsonb, created_at = %s
                    WHERE id = %s AND conversation_id = %s
                      AND workspace_id = %s AND user_id = %s
                      AND role = 'assistant'
                    RETURNING *
                    """,
                    (
                        clean_content,
                        json.dumps(sources or [], ensure_ascii=False),
                        now,
                        message_id,
                        self.conversation_id,
                        self.workspace_id,
                        self.user_id,
                    ),
                )
                row = cursor.fetchone()
                if row is None:
                    raise ValueError("The answer selected for regeneration no longer exists.")
                cursor.execute(
                    """
                    UPDATE tbl_conversations SET updated_at = %s
                    WHERE id = %s AND workspace_id = %s AND user_id = %s
                    """,
                    (now, self.conversation_id, self.workspace_id, self.user_id),
                )
        self.messages = self.load_history()
        return self._message_row_to_dict(row)

    def clear_history(self) -> None:
        """
        Starts a new conversation.

        Existing conversations remain stored in PostgreSQL.
        """

        self.start_new_conversation()

    def _generate_title_from_first_message(
        self,
        role: str,
        content: str,
    ) -> None:
        if role != "user":
            return

        user_message_count = sum(
            1
            for message in self.messages
            if message.get("role") == "user"
        )

        if user_message_count != 1:
            return

        generated_title = content.replace(
            "\n",
            " ",
        ).strip()

        if len(generated_title) > 70:
            generated_title = (
                generated_title[:67].rstrip()
                + "..."
            )

        self.rename_conversation(
            generated_title
        )

    @staticmethod
    def _message_row_to_dict(
        row: dict,
    ) -> dict:
        sources = row.get("sources") or []

        if isinstance(sources, str):
            try:
                sources = json.loads(sources)
            except json.JSONDecodeError:
                sources = []

        return {
            "id": row["id"],
            "role": row["role"],
            "content": row["content"],
            "sources": sources,
            "created_at": row["created_at"].isoformat(),
        }

    @staticmethod
    def _conversation_row_to_dict(
        row: dict,
    ) -> dict:
        result = {
            "id": row["id"],
            "workspace_id": row["workspace_id"],
            "user_id": row["user_id"],
            "title": row["title"],
            "status": row["status"],
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat(),
        }

        if "message_count" in row:
            result["message_count"] = int(
                row["message_count"]
            )

        return result
