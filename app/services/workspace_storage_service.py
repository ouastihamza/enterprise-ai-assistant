from pathlib import Path


# Anchored to the project root (not a bare relative "storage/..." path) so
# the paths handed out here are byte-identical to what
# Path(file_path).resolve() produces in scripts/process_document.py.
# Document ingestion stores source_file as an absolute, resolved path in
# both ChromaDB metadata and the per-workspace knowledge-base JSON; if this
# service instead returned relative paths, everything derived from a
# document's registry row (e.g. deleting its vectors by source_file) would
# silently fail to match and never actually delete anything.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class WorkspaceStorageService:
    """
    Centralized storage paths for one workspace.
    """

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id

        self.workspace_path = (
            _PROJECT_ROOT / "storage" / "workspaces" / workspace_id
        )
        self.documents_path = self.workspace_path / "documents"
        self.processed_path = self.workspace_path / "processed"
        self.registry_path = self.workspace_path / "registry.json"

        self.documents_path.mkdir(parents=True, exist_ok=True)
        self.processed_path.mkdir(parents=True, exist_ok=True)

    def get_workspace_path(self) -> Path:
        return self.workspace_path

    def get_documents_path(self) -> Path:
        return self.documents_path

    def get_processed_path(self) -> Path:
        return self.processed_path

    def get_knowledge_base_path(self) -> Path:
        return self.processed_path / "knowledge_base_chunks.json"

    def get_registry_path(self) -> Path:
        return self.registry_path