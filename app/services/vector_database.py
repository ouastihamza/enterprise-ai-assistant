import os
from pathlib import Path

import chromadb
from chromadb.config import Settings


# Anchored to the project root instead of a bare relative string, so
# the store resolves to the same place regardless of the working
# directory the process is launched from (streamlit run, Docker
# WORKDIR, a cron job, etc.). This assumes this file lives at
# app/services/vector_database.py — adjust parents[2] or set
# VECTOR_DB_PATH if your layout differs.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = os.environ.get(
    "VECTOR_DB_PATH",
    str(_PROJECT_ROOT / "storage" / "vector_db"),
)


class VectorDatabase:
    """
    Final persistent vector database service.

    Responsibilities:
    - Persist workspace collections
    - Upsert indexed chunks safely
    - Query by embedding
    - Delete vectors by document
    - Reset one collection without affecting other workspaces

    Collections are created with cosine distance explicitly, matching
    the normalized embeddings produced by EmbeddingService. Chroma
    bakes the distance metric into a collection at creation time, so
    this only applies to *new* collections — existing ones need
    reset() + a full re-index (see the platform README / migration
    note) before scores are comparable across workspaces.
    """

    def __init__(
        self,
        database_path: str = DEFAULT_DATABASE_PATH,
        collection_name: str = "knowledge_base",
    ):
        self.database_path = database_path
        self.collection_name = collection_name

        self.client = chromadb.PersistentClient(
            path=database_path,
            settings=Settings(
                anonymized_telemetry=False,
            ),
        )

        self.collection = (
            self.client.get_or_create_collection(
                name=collection_name,
                metadata={
                    "hnsw:space": "cosine",
                },
            )
        )

    def upsert_documents(
        self,
        document_ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        if not document_ids:
            return

        expected_length = len(document_ids)

        if not (
            len(texts) == expected_length
            and len(embeddings) == expected_length
            and len(metadatas) == expected_length
        ):
            raise ValueError(
                "Vector IDs, texts, embeddings and metadata "
                "must contain the same number of items."
            )

        self.collection.upsert(
            ids=document_ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def search(
        self,
        embedding: list[float],
        top_k: int = 5,
        where: dict | None = None,
    ) -> dict:
        if top_k <= 0:
            return self._empty_result()

        collection_size = self.count()

        if collection_size == 0:
            return self._empty_result()

        safe_top_k = min(
            top_k,
            collection_size,
        )

        query_arguments = {
            "query_embeddings": [embedding],
            "n_results": safe_top_k,
            "include": [
                "documents",
                "metadatas",
                "distances",
            ],
        }

        if where:
            query_arguments["where"] = where

        return self.collection.query(
            **query_arguments
        )

    def count(self) -> int:
        return self.collection.count()

    def delete_document(
        self,
        document_id: str,
    ) -> None:
        if not document_id:
            return

        self.collection.delete(
            ids=[document_id]
        )

    def delete_by_source_file(
        self,
        source_file: str,
    ) -> None:
        if not source_file:
            return

        self.collection.delete(
            where={
                "source_file": source_file,
            }
        )

    def reset(self) -> None:
        try:
            self.client.delete_collection(
                name=self.collection_name,
            )
        except Exception:
            pass

        self.collection = (
            self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "hnsw:space": "cosine",
                },
            )
        )

    @staticmethod
    def _empty_result() -> dict:
        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }