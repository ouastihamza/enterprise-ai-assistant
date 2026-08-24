from app.services.embedding_service import EmbeddingService
from app.services.vector_database import VectorDatabase


class VectorSearchService:
    """
    Final workspace-aware semantic search service.

    Responsibilities:
    - Validate the question
    - Create the query embedding
    - Search only the active workspace collection
    - Convert Chroma cosine distances into relevance scores
    - Drop chunks that fall below the relevance floor
    - Preserve citation metadata
    """

    # Below this cosine similarity, a chunk is treated as noise rather
    # than forced into the prompt just because a top_k slot was free.
    # Tune empirically against a few known question/answer pairs —
    # different embedding models have different score distributions,
    # so re-check this after any model change (see EmbeddingService).
    DEFAULT_MIN_SCORE = 0.2

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

    def search(
        self,
        question: str,
        top_k: int = 5,
        min_score: float | None = None,
        where: dict | None = None,
    ) -> list[dict]:
        cleaned_question = question.strip()

        if not cleaned_question:
            return []

        if top_k <= 0:
            return []

        if self.vector_database.count() == 0:
            return []

        threshold = (
            self.DEFAULT_MIN_SCORE
            if min_score is None
            else min_score
        )

        embedding = (
            self.embedding_service.create_embedding(
                cleaned_question
            )
        )

        results = self.vector_database.search(
            embedding=embedding,
            top_k=top_k,
            where=where,
        )

        documents = (
            results.get("documents") or [[]]
        )[0]

        metadatas = (
            results.get("metadatas") or [[]]
        )[0]

        distances = (
            results.get("distances") or [[]]
        )[0]

        ids = (
            results.get("ids") or [[]]
        )[0]

        retrieved_chunks: list[dict] = []

        for index, document in enumerate(
            documents
        ):
            metadata = (
                metadatas[index]
                if index < len(metadatas)
                else {}
            ) or {}

            distance = (
                distances[index]
                if index < len(distances)
                else None
            )

            vector_id = (
                ids[index]
                if index < len(ids)
                else None
            )

            score = self._distance_to_relevance_score(
                distance
            )

            if score is not None and score < threshold:
                continue

            retrieved_chunks.append(
                {
                    "id": vector_id,
                    "text": document or "",
                    "metadata": metadata,
                    "distance": distance,
                    "score": score,
                }
            )

        return retrieved_chunks

    @staticmethod
    def _distance_to_relevance_score(
        distance,
    ) -> float | None:
        if distance is None:
            return None

        try:
            numeric_distance = float(
                distance
            )
        except (TypeError, ValueError):
            return None

        # The collection is configured for cosine space (see
        # VectorDatabase), so Chroma's distance is exactly
        # (1 - cosine_similarity). Converting back gives a direct,
        # interpretable similarity score instead of the old
        # 1 / (1 + distance) approximation.
        similarity = 1.0 - numeric_distance

        return round(
            similarity,
            4,
        )
