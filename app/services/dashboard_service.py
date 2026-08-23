from pathlib import Path

from app.services.document_registry import DocumentRegistry
from app.services.workspace_storage_service import WorkspaceStorageService


class DashboardService:

    def __init__(
        self,
        workspace_id: str,
    ):
        self.storage = WorkspaceStorageService(workspace_id)

        self.registry = DocumentRegistry(
            workspace_id=workspace_id
        )

    def get_dashboard_metrics(self):

        documents = self.registry.get_all_documents()

        total_documents = len(documents)

        indexed_chunks = sum(
            document.get(
                "chunk_count",
                0,
            )
            for document in documents
        )

        total_storage = sum(
            document.get(
                "file_size",
                0,
            )
            for document in documents
        )

        if total_storage < 1024 * 1024:

            storage = f"{total_storage / 1024:.1f} KB"

        else:

            storage = f"{total_storage / (1024 * 1024):.1f} MB"

        if documents:

            last_upload = max(
                document["uploaded_at"]
                for document in documents
            )

        else:

            last_upload = "No uploads"

        return {
            "documents": total_documents,
            "indexed_chunks": indexed_chunks,
            "storage": storage,
            "last_upload": last_upload,
        }