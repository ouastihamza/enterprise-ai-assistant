from app.services.rag_helpers import (
    build_retrieval_question,
    prune_retrieved_chunks,
)
from app.services.vector_search_service import VectorSearchService


class _FakeKnowledgeBase:
    def __init__(self, chunks):
        self._chunks = chunks

    def load_knowledge_base(self):
        return self._chunks


def _service_with_chunks(chunks):
    service = object.__new__(VectorSearchService)
    service.workspace_id = "workspace-a"
    service.knowledge_base = _FakeKnowledgeBase(chunks)
    return service


def test_bm25_customer_scope_excludes_other_customer_chunks():
    service = _service_with_chunks(
        [
            {
                "text": "February invoice INV-2026-02 totals EUR 12,900.",
                "source_file": "/docs/a.txt",
                "chunk_id": 1,
                "customer_id": "customer-a",
            },
            {
                "text": "February invoice INV-2026-02 totals EUR 99,999.",
                "source_file": "/docs/b.txt",
                "chunk_id": 1,
                "customer_id": "customer-b",
            },
        ]
    )

    results = service._keyword_candidates(
        "INV-2026-02", 10, {"customer_id": "customer-a"}
    )

    assert len(results) == 1
    assert results[0]["metadata"]["customer_id"] == "customer-a"


def test_exact_identifier_match_is_ranked_first():
    service = _service_with_chunks([])
    exact = {
        "id": "exact",
        "text": "Invoice reference INV-2026-02.",
        "metadata": {"source_file": "/docs/exact.txt", "chunk_id": 1},
        "semantic_score": 0.35,
        "keyword_score": 1.0,
    }
    general = {
        "id": "general",
        "text": "Invoice reference and monthly charges.",
        "metadata": {"source_file": "/docs/general.txt", "chunk_id": 1},
        "semantic_score": 0.55,
        "keyword_score": 0.6,
    }

    ranked = service._fuse_candidates(
        "Explain INV-2026-02", [exact, general], [exact, general], 2
    )

    assert ranked[0]["id"] == "exact"


def test_contextual_follow_up_reuses_previous_user_question():
    retrieval_question = build_retrieval_question(
        question="What about January?",
        conversation_history=[
            {
                "role": "user",
                "content": "Why was the February invoice more expensive?",
            },
            {"role": "assistant", "content": "Consumption increased."},
        ],
    )

    assert "February invoice" in retrieval_question
    assert "What about January?" in retrieval_question


def test_source_pruning_removes_duplicates_and_low_relevance_tail():
    chunks = [
        {
            "text": "Primary evidence",
            "score": 0.9,
            "metadata": {"source_file": "a", "chunk_id": 1},
        },
        {
            "text": "Primary evidence",
            "score": 0.9,
            "metadata": {"source_file": "a", "chunk_id": 1},
        },
        {
            "text": "Supporting evidence",
            "score": 0.78,
            "metadata": {"source_file": "b", "chunk_id": 2},
        },
        {
            "text": "Unrelated tail",
            "score": 0.2,
            "metadata": {"source_file": "c", "chunk_id": 3},
        },
    ]

    pruned = prune_retrieved_chunks(chunks)

    assert [chunk["text"] for chunk in pruned] == [
        "Primary evidence",
        "Supporting evidence",
    ]

