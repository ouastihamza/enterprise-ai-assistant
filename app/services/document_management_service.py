from pathlib import Path

from app.configuration.workspace_settings_service import (
    WorkspaceSettingsService,
)
from app.services.document_registry import DocumentRegistry
from app.services.indexing_service import IndexingService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.workspace_storage_service import WorkspaceStorageService
from scripts.process_document import process_document


class DocumentManagementService:
    """
    Final document lifecycle service.

    Handles:
    - Delete
    - Re-index
    - Replace

    All operations are workspace-isolated.
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

    def delete_document(
        self,
        document_name: str,
    ) -> bool:
        document = self.registry.get_document_by_name(
            document_name
        )

        if document is None:
            return False

        source_path = Path(
            document["source_file"]
        )

        self._remove_indexed_assets(
            document=document
        )

        if source_path.exists():
            source_path.unlink()

        return self.registry.delete_document(
            document_id=document["id"]
        )

    def reindex_document(
        self,
        document_name: str,
    ) -> bool:
        document = self.registry.get_document_by_name(
            document_name
        )

        if document is None:
            return False

        source_path = Path(
            document["source_file"]
        )

        if not source_path.exists():
            self.registry.update_document(
                document_id=document["id"],
                indexed=False,
                status="Failed",
                error_message="Source file not found.",
            )
            return False

        return self._process_existing_document(
            document=document,
            source_path=source_path,
            file_size=document["file_size"],
        )

    def replace_document(
        self,
        document_name: str,
        uploaded_file,
    ) -> bool:
        document = self.registry.get_document_by_name(
            document_name
        )

        if document is None:
            return False

        settings = (
            self.settings_service
            .get_or_create_settings(
                workspace_id=self.workspace_id
            )
        )

        self._validate_replacement(
            uploaded_file=uploaded_file,
            original_document_name=document_name,
            allowed_file_types=settings.allowed_file_types,
            max_upload_size_mb=settings.max_upload_size_mb,
        )

        source_path = Path(
            document["source_file"]
        )

        replacement_path = source_path.with_suffix(
            source_path.suffix + ".replacement"
        )

        backup_path = source_path.with_suffix(
            source_path.suffix + ".backup"
        )

        replacement_path.write_bytes(
            uploaded_file.getbuffer()
        )

        try:
            if backup_path.exists():
                backup_path.unlink()

            if source_path.exists():
                source_path.replace(
                    backup_path
                )

            replacement_path.replace(
                source_path
            )

            success = self._process_existing_document(
                document=document,
                source_path=source_path,
                file_size=uploaded_file.size,
            )

            if not success:
                raise RuntimeError(
                    "Replacement processing failed."
                )

            if backup_path.exists():
                backup_path.unlink()

            return True

        except Exception:
            if source_path.exists():
                source_path.unlink()

            if backup_path.exists():
                backup_path.replace(
                    source_path
                )

            if replacement_path.exists():
                replacement_path.unlink()

            return False

    def _process_existing_document(
        self,
        document: dict,
        source_path: Path,
        file_size: int,
    ) -> bool:
        settings = (
            self.settings_service
            .get_or_create_settings(
                workspace_id=self.workspace_id
            )
        )

        try:
            self.registry.update_document(
                document_id=document["id"],
                indexed=False,
                status="Processing",
                clear_error=True,
            )

            self._remove_indexed_assets(
                document=document
            )

            output_name = (
                source_path.stem
                .replace(" ", "_")
                .lower()
            )

            chunks_path = process_document(
                file_path=str(source_path),
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

            self.registry.update_document(
                document_id=document["id"],
                chunks_file=str(chunks_path),
                chunk_count=indexed_count,
                file_size=file_size,
                indexed=True,
                status="Ready",
                clear_error=True,
                update_index_time=True,
            )

            return True

        except Exception as error:
            self.registry.update_document(
                document_id=document["id"],
                indexed=False,
                status="Failed",
                error_message=str(error),
            )

            return False

    def _remove_indexed_assets(
        self,
        document: dict,
    ) -> None:
        source_file = str(
            document["source_file"]
        )

        chunks_file = Path(
            document["chunks_file"]
        )

        self.knowledge_base.remove_chunks_by_source_file(
            source_file=source_file
        )

        self.indexing.delete_document_vectors(
            source_file=source_file
        )

        if chunks_file.exists():
            chunks_file.unlink()

        extracted_text_path = (
            self.storage.get_processed_path()
            / (
                Path(source_file).stem
                .replace(" ", "_")
                .lower()
                + "_extracted.txt"
            )
        )

        if extracted_text_path.exists():
            extracted_text_path.unlink()

    def _validate_replacement(
        self,
        uploaded_file,
        original_document_name: str,
        allowed_file_types: list[str],
        max_upload_size_mb: int,
    ) -> None:
        original_extension = (
            Path(original_document_name)
            .suffix
            .lower()
        )

        replacement_extension = (
            Path(uploaded_file.name)
            .suffix
            .lower()
        )

        if replacement_extension != original_extension:
            raise ValueError(
                "Replacement file must use the same file type "
                "as the original document."
            )

        allowed_types = {
            file_type.lower().lstrip(".")
            for file_type in allowed_file_types
        }

        normalized_extension = (
            replacement_extension.lstrip(".")
        )

        if normalized_extension not in allowed_types:
            raise ValueError(
                f"File type .{normalized_extension} is not allowed."
            )

        maximum_size_bytes = (
            max_upload_size_mb
            * 1024
            * 1024
        )

        if uploaded_file.size > maximum_size_bytes:
            raise ValueError(
                f"Replacement exceeds the "
                f"{max_upload_size_mb} MB upload limit."
            )

        if uploaded_file.size <= 0:
            raise ValueError(
                "The replacement file is empty."
            )