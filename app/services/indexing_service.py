import hashlib
import json
from pathlib import Path

from app.services.embedding_service import EmbeddingService
from app.services.vector_database import VectorDatabase


class IndexingService:
    """
    Final workspace-aware indexing service.

    Responsibilities:
    - Load processed chunks
    - Create embeddings in batches
    - Preserve citation metadata
    - Generate stable vector IDs
    - Upsert vectors safely
    """

    def __init__(
        self,
        workspace_id: str,
    ):
        self.workspace_id = workspace_id
        self.collection_name = (
            f"{workspace_id}_knowledge_base"
        )

        self.embedding_service = EmbeddingService()

        self.vector_database = VectorDatabase(
            collection_name=self.collection_name
        )

    def index_chunks(
        self,
        chunks_json_path: str,
        batch_size: int = 64,
    ) -> int:
        chunks_path = Path(chunks_json_path)

        if not chunks_path.exists():
            raise FileNotFoundError(
                f"Chunks file not found: {chunks_json_path}"
            )

        if batch_size <= 0:
            raise ValueError(
                "Batch size must be greater than zero."
            )

        with chunks_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            chunks = json.load(file)

        if not isinstance(chunks, list):
            raise ValueError(
                "Chunks file must contain a JSON list."
            )

        valid_chunks = [
            chunk
            for chunk in chunks
            if str(chunk.get("text", "")).strip()
        ]

        if not valid_chunks:
            return 0

        total_indexed = 0

        for start_index in range(
            0,
            len(valid_chunks),
            batch_size,
        ):
            batch = valid_chunks[
                start_index:start_index + batch_size
            ]

            texts = [
                str(chunk["text"]).strip()
                for chunk in batch
            ]

            embeddings = (
                self.embedding_service.create_embeddings(
                    texts=texts,
                    batch_size=batch_size,
                )
            )

            document_ids: list[str] = []
            metadatas: list[dict] = []

            for chunk in batch:
                source_file = str(
                    chunk["source_file"]
                )

                chunk_id = int(
                    chunk["chunk_id"]
                )

                source_hash = hashlib.sha256(
                    source_file.encode("utf-8")
                ).hexdigest()[:20]

                document_id = (
                    f"{self.workspace_id}:"
                    f"{source_hash}:"
                    f"{chunk_id}"
                )

                metadata = self._build_metadata(
                    chunk=chunk
                )

                document_ids.append(
                    document_id
                )

                metadatas.append(
                    metadata
                )

            self.vector_database.upsert_documents(
                document_ids=document_ids,
                texts=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )

            total_indexed += len(batch)

        return total_indexed

    def delete_document_vectors(
        self,
        source_file: str,
    ) -> None:
        self.vector_database.delete_by_source_file(
            source_file=source_file
        )

    def _build_metadata(
        self,
        chunk: dict,
    ) -> dict:
        source_file = str(
            chunk["source_file"]
        )

        metadata = {
            "workspace_id": self.workspace_id,
            "source_file": source_file,
            "document_name": str(
                chunk.get(
                    "document_name",
                    Path(source_file).name,
                )
            ),
            "file_extension": str(
                chunk.get(
                    "file_extension",
                    "",
                )
            ),
            "chunk_id": int(
                chunk["chunk_id"]
            ),
            "section_chunk_id": int(
                chunk.get(
                    "section_chunk_id",
                    chunk["chunk_id"],
                )
            ),
            "section_type": str(
                chunk.get(
                    "section_type",
                    "document",
                )
            ),
            "section_number": int(
                chunk.get(
                    "section_number",
                    1,
                )
            ),
            "section_title": str(
                chunk.get(
                    "section_title",
                    "",
                )
            ),
        }

        optional_integer_fields = [
            "page_number",
            "slide_number",
            "sheet_number",
            "total_pages",
        ]

        for field_name in optional_integer_fields:
            value = chunk.get(field_name)

            if value is not None:
                metadata[field_name] = int(value)

        optional_text_fields = [
            "heading",
            "sheet_name",
            "customer_id",
            "category",
        ]

        for field_name in optional_text_fields:
            value = chunk.get(field_name)

            if value:
                metadata[field_name] = str(value)

        return metadata
