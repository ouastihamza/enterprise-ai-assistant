import logging
import time
from pathlib import Path
from typing import Protocol

from app.configuration.workspace_settings_service import (
    WorkspaceSettingsService,
)
from app.services.document_registry import DocumentRegistry
from app.services.indexing_service import IndexingService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.workspace_storage_service import WorkspaceStorageService
from scripts.process_document import process_document


logger = logging.getLogger(__name__)


class UploadedDocument(Protocol):
    name: str
    size: int

    def getbuffer(self) -> memoryview:
        ...


class DocumentProcessingService:
    """
    Final workspace-aware ingestion service.

    Pipeline:
    validate
    save
    process
    chunk
    update knowledge base
    embed
    index
    register
    """

    def __init__(
        self,
        workspace_id: str,
    ):
        self.workspace_id = workspace_id

        self.storage = WorkspaceStorageService(
            workspace_id
        )

        self.registry = DocumentRegistry(
            workspace_id=workspace_id
        )

        self.knowledge_base = KnowledgeBaseService(
            knowledge_base_path=str(
                self.storage.get_knowledge_base_path()
            )
        )

        self.indexing = IndexingService(
            workspace_id=workspace_id
        )

        self.settings_service = WorkspaceSettingsService()

    def upload_document(
        self,
        uploaded_file: UploadedDocument,
    ) -> int | None:
        if self.registry.document_exists(
            uploaded_file.name
        ):
            return None

        settings = (
            self.settings_service
            .get_or_create_settings(
                workspace_id=self.workspace_id
            )
        )

        self._validate_upload(
            uploaded_file=uploaded_file,
            allowed_file_types=settings.allowed_file_types,
            max_upload_size_mb=settings.max_upload_size_mb,
        )

        total_start = time.perf_counter()

        saved_file_path = (
            self.storage.get_documents_path()
            / uploaded_file.name
        )

        if saved_file_path.exists():
            return None

        chunks_path: Path | None = None

        try:
            saved_file_path.write_bytes(
                uploaded_file.getbuffer()
            )

            output_name = (
                saved_file_path.stem
                .replace(" ", "_")
                .lower()
            )

            chunks_path = process_document(
                file_path=str(saved_file_path),
                output_name=output_name,
                output_folder=str(
                    self.storage.get_processed_path()
                ),
                chunk_size=settings.chunk_size,
                overlap=settings.chunk_overlap,
            )

            self.knowledge_base.add_chunks_from_file(
                str(chunks_path)
            )

            indexed_count = self.indexing.index_chunks(
                chunks_json_path=str(chunks_path)
            )

            self.registry.register_document(
                name=uploaded_file.name,
                source_file=str(saved_file_path),
                chunks_file=str(chunks_path),
                chunk_count=indexed_count,
                file_size=uploaded_file.size,
            )

            elapsed = (
                time.perf_counter()
                - total_start
            )

            logger.info(
                "Document ingested | workspace=%s | file=%s | "
                "chunks=%s | duration=%.2fs",
                self.workspace_id,
                uploaded_file.name,
                indexed_count,
                elapsed,
            )

            return indexed_count

        except Exception:
            self._rollback_failed_upload(
                saved_file_path=saved_file_path,
                chunks_path=chunks_path,
            )

            logger.exception(
                "Document ingestion failed | workspace=%s | file=%s",
                self.workspace_id,
                uploaded_file.name,
            )

            raise

    def _validate_upload(
        self,
        uploaded_file: UploadedDocument,
        allowed_file_types: list[str],
        max_upload_size_mb: int,
    ) -> None:
        extension = (
            Path(uploaded_file.name)
            .suffix
            .lower()
            .lstrip(".")
        )

        allowed_types = {
            file_type.lower().lstrip(".")
            for file_type in allowed_file_types
        }

        if extension not in allowed_types:
            raise ValueError(
                f"File type .{extension} is not allowed."
            )

        maximum_size_bytes = (
            max_upload_size_mb
            * 1024
            * 1024
        )

        if uploaded_file.size > maximum_size_bytes:
            raise ValueError(
                f"{uploaded_file.name} exceeds the "
                f"{max_upload_size_mb} MB upload limit."
            )

        if uploaded_file.size <= 0:
            raise ValueError(
                "The uploaded file is empty."
            )

    def _rollback_failed_upload(
        self,
        saved_file_path: Path,
        chunks_path: Path | None,
    ) -> None:
        try:
            self.knowledge_base.remove_chunks_by_source_file(
                source_file=str(saved_file_path)
            )
        except Exception:
            logger.exception(
                "Failed to rollback knowledge base entries."
            )

        try:
            self.indexing.delete_document_vectors(
                source_file=str(saved_file_path)
            )
        except Exception:
            logger.exception(
                "Failed to rollback vector entries."
            )

        if chunks_path and chunks_path.exists():
            chunks_path.unlink()

        extracted_text_path = (
            self.storage.get_processed_path()
            / (
                saved_file_path.stem
                .replace(" ", "_")
                .lower()
                + "_extracted.txt"
            )
        )

        if extracted_text_path.exists():
            extracted_text_path.unlink()

        if saved_file_path.exists():
            saved_file_path.unlink()
