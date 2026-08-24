import logging
import math
import re
from collections import Counter
from pathlib import Path

from app.services.embedding_service import EmbeddingService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.vector_database import VectorDatabase
from app.services.workspace_storage_service import WorkspaceStorageService


TOKEN_PATTERN = re.compile(r"[\w]+(?:[-./][\w]+)*", re.UNICODE)
IDENTIFIER_PATTERN = re.compile(
    r"\b(?:[A-Za-z]+[-./])?[A-Za-z0-9]*\d[A-Za-z0-9._/-]*\b"
)
logger = logging.getLogger(__name__)


class VectorSearchService:
    """Workspace-aware hybrid retrieval over semantic and lexical signals."""

    DEFAULT_MIN_SCORE = 0.2
    SEMANTIC_WEIGHT = 0.64
    KEYWORD_WEIGHT = 0.36
    CANDIDATE_MULTIPLIER = 4
    BM25_K1 = 1.5
    BM25_B = 0.75

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.collection_name = f"{workspace_id}_knowledge_base"
        self._embedding_service: EmbeddingService | None = None
        self.vector_database = VectorDatabase(collection_name=self.collection_name)
        storage = WorkspaceStorageService(workspace_id)
        self.knowledge_base = KnowledgeBaseService(
            knowledge_base_path=str(storage.get_knowledge_base_path())
        )

    @property
    def embedding_service(self) -> EmbeddingService:
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    def search(
        self,
        question: str,
        top_k: int = 5,
        min_score: float | None = None,
        where: dict | None = None,
    ) -> list[dict]:
        cleaned_question = question.strip()
        if not cleaned_question or top_k <= 0:
            return []

        candidate_limit = max(top_k, top_k * self.CANDIDATE_MULTIPLIER)
        threshold = self.DEFAULT_MIN_SCORE if min_score is None else min_score
        try:
            semantic = self._semantic_candidates(
                cleaned_question, candidate_limit, threshold, where
            )
        except Exception:
            logger.exception(
                "Semantic retrieval failed; continuing with BM25 | workspace=%s",
                self.workspace_id,
            )
            semantic = []
        keyword = self._keyword_candidates(cleaned_question, candidate_limit, where)
        return self._fuse_candidates(cleaned_question, semantic, keyword, top_k)

    def _semantic_candidates(
        self,
        question: str,
        limit: int,
        threshold: float,
        where: dict | None,
    ) -> list[dict]:
        if self.vector_database.count() == 0:
            return []
        embedding = self.embedding_service.create_embedding(question)
        results = self.vector_database.search(
            embedding=embedding, top_k=limit, where=where
        )
        documents = (results.get("documents") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]
        ids = (results.get("ids") or [[]])[0]
        candidates: list[dict] = []

        for index, document in enumerate(documents):
            metadata = (metadatas[index] if index < len(metadatas) else {}) or {}
            if not self._metadata_matches(metadata, where):
                continue
            distance = distances[index] if index < len(distances) else None
            score = self._distance_to_relevance_score(distance)
            if score is not None and score < threshold:
                continue
            candidates.append(
                {
                    "id": ids[index] if index < len(ids) else None,
                    "text": document or "",
                    "metadata": metadata,
                    "distance": distance,
                    "score": score,
                    "semantic_score": score or 0.0,
                    "keyword_score": 0.0,
                }
            )
        return candidates

    def _keyword_candidates(
        self, question: str, limit: int, where: dict | None
    ) -> list[dict]:
        chunks = [
            chunk
            for chunk in self.knowledge_base.load_knowledge_base()
            if str(chunk.get("text", "")).strip()
            and self._metadata_matches(chunk, where)
        ]
        query_terms = self._tokenize(question)
        if not chunks or not query_terms:
            return []

        tokenized_documents = [
            self._tokenize(self._searchable_text(chunk)) for chunk in chunks
        ]
        document_frequency: Counter[str] = Counter()
        for tokens in tokenized_documents:
            document_frequency.update(set(tokens))
        average_length = sum(map(len, tokenized_documents)) / max(
            len(tokenized_documents), 1
        )
        scored: list[tuple[float, dict]] = []

        for chunk, tokens in zip(chunks, tokenized_documents, strict=True):
            frequencies = Counter(tokens)
            score = 0.0
            for term in query_terms:
                frequency = frequencies.get(term, 0)
                if not frequency:
                    continue
                document_frequency_for_term = document_frequency.get(term, 0)
                inverse_document_frequency = math.log(
                    1
                    + (len(chunks) - document_frequency_for_term + 0.5)
                    / (document_frequency_for_term + 0.5)
                )
                length_normalizer = self.BM25_K1 * (
                    1
                    - self.BM25_B
                    + self.BM25_B * len(tokens) / max(average_length, 1.0)
                )
                score += inverse_document_frequency * (
                    frequency * (self.BM25_K1 + 1)
                ) / (frequency + length_normalizer)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            self._chunk_to_result(chunk, keyword_score=score)
            for score, chunk in scored[:limit]
        ]

    def _fuse_candidates(
        self,
        question: str,
        semantic: list[dict],
        keyword: list[dict],
        top_k: int,
    ) -> list[dict]:
        combined: dict[str, dict] = {}
        maximum_keyword_score = max(
            (float(item.get("keyword_score") or 0.0) for item in keyword),
            default=0.0,
        )
        for candidate in semantic:
            combined[self._candidate_key(candidate)] = dict(candidate)
        for candidate in keyword:
            key = self._candidate_key(candidate)
            normalized_keyword = (
                float(candidate.get("keyword_score") or 0.0)
                / maximum_keyword_score
                if maximum_keyword_score > 0
                else 0.0
            )
            if key in combined:
                combined[key]["keyword_score"] = normalized_keyword
            else:
                combined[key] = {**candidate, "keyword_score": normalized_keyword}

        ranked: list[dict] = []
        for candidate in combined.values():
            semantic_score = max(
                0.0, min(1.0, float(candidate.get("semantic_score") or 0.0))
            )
            keyword_score = max(
                0.0, min(1.0, float(candidate.get("keyword_score") or 0.0))
            )
            fused_score = min(
                1.0,
                self.SEMANTIC_WEIGHT * semantic_score
                + self.KEYWORD_WEIGHT * keyword_score
                + self._exact_match_boost(question, candidate),
            )
            candidate.update(
                semantic_score=round(semantic_score, 4),
                keyword_score=round(keyword_score, 4),
                score=round(fused_score, 4),
                retrieval_method=(
                    "hybrid"
                    if semantic_score and keyword_score
                    else "semantic"
                    if semantic_score
                    else "keyword"
                ),
            )
            ranked.append(candidate)
        ranked.sort(
            key=lambda item: (
                float(item.get("score") or 0.0),
                float(item.get("semantic_score") or 0.0),
            ),
            reverse=True,
        )
        return ranked[:top_k]

    @staticmethod
    def _metadata_matches(metadata: dict, where: dict | None) -> bool:
        if not where:
            return True
        for field, expected in where.items():
            actual = metadata.get(field)
            if isinstance(expected, dict) and "$in" in expected:
                if actual not in expected["$in"]:
                    return False
            elif str(actual) != str(expected):
                return False
        return True

    @staticmethod
    def _tokenize(value: str) -> list[str]:
        return [token.casefold() for token in TOKEN_PATTERN.findall(value)]

    @staticmethod
    def _searchable_text(chunk: dict) -> str:
        return " ".join(
            str(chunk.get(field) or "")
            for field in (
                "document_name",
                "source_file",
                "customer_id",
                "category",
                "section_title",
                "heading",
                "sheet_name",
                "text",
            )
        )

    def _chunk_to_result(self, chunk: dict, *, keyword_score: float) -> dict:
        source_file = str(chunk.get("source_file", ""))
        metadata_fields = (
            "file_extension",
            "chunk_id",
            "section_chunk_id",
            "page_number",
            "total_pages",
            "section_type",
            "section_number",
            "section_title",
            "heading",
            "slide_number",
            "sheet_number",
            "sheet_name",
            "customer_id",
            "category",
        )
        metadata = {
            "workspace_id": self.workspace_id,
            "source_file": source_file,
            "document_name": str(
                chunk.get("document_name") or Path(source_file).name
            ),
        }
        for field in metadata_fields:
            value = chunk.get(field)
            if value is not None:
                metadata[field] = value
        return {
            "id": f"{self.workspace_id}:{source_file}:{chunk.get('chunk_id', '')}",
            "text": str(chunk.get("text", "")),
            "metadata": metadata,
            "distance": None,
            "score": 0.0,
            "semantic_score": 0.0,
            "keyword_score": keyword_score,
        }

    @staticmethod
    def _candidate_key(candidate: dict) -> str:
        metadata = candidate.get("metadata", {}) or {}
        return (
            f"{metadata.get('source_file', '')}:"
            f"{metadata.get('chunk_id', candidate.get('id', ''))}"
        )

    def _exact_match_boost(self, question: str, candidate: dict) -> float:
        haystack = self._searchable_text(
            {**(candidate.get("metadata", {}) or {}), "text": candidate.get("text", "")}
        ).casefold()
        normalized_question = " ".join(self._tokenize(question))
        boost = 0.0
        if len(normalized_question) >= 4 and normalized_question in haystack:
            boost += 0.18
        identifiers = {
            match.group(0).casefold()
            for match in IDENTIFIER_PATTERN.finditer(question)
            if len(match.group(0)) >= 3
        }
        for identifier in identifiers:
            if identifier in haystack:
                boost += 0.12
        return min(boost, 0.3)

    @staticmethod
    def _distance_to_relevance_score(distance) -> float | None:
        if distance is None:
            return None
        try:
            numeric_distance = float(distance)
        except (TypeError, ValueError):
            return None
        return round(1.0 - numeric_distance, 4)
