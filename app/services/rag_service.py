import logging
import time
from collections.abc import Iterator

from app.configuration.workspace_settings_service import WorkspaceSettingsService
from app.customers.customer_service import CustomerService
from app.llm_client import ask_llm, stream_llm
from app.prompts import BASIC_ASSISTANT_PROMPT
from app.services.document_registry import DocumentRegistry
from app.services.rag_helpers import (
    build_retrieval_question,
    prune_retrieved_chunks,
)
from app.services.vector_search_service import VectorSearchService


logger = logging.getLogger(__name__)

GROUNDING_INSTRUCTIONS = (
    "Answer only from the supplied context. Cite document statements inline "
    "using [Source 1], [Source 2], and so on. Structured customer facts use "
    "[Customer profile]. If the context is insufficient, say so clearly. "
    "Prefer a direct explanation in plain business language."
)
MAX_CONTEXT_CHARACTERS = 6000


class RAGService:
    """Grounded workspace retrieval with optional customer scoping."""

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.vector_search = VectorSearchService(workspace_id=workspace_id)
        self.settings = WorkspaceSettingsService().get_or_create_settings(
            workspace_id=workspace_id
        )

    def retrieve_context(
        self,
        question: str,
        customer_id: str | None = None,
        conversation_history: list[dict] | None = None,
    ) -> list[dict]:
        retrieval_question = build_retrieval_question(
            question=question,
            conversation_history=conversation_history,
        )
        chunks = self.vector_search.search(
            question=retrieval_question,
            top_k=self.settings.top_k,
            where={"customer_id": customer_id} if customer_id else None,
        )
        return prune_retrieved_chunks(chunks)

    @staticmethod
    def build_context(
        retrieved_chunks: list[dict],
        max_context_characters: int = MAX_CONTEXT_CHARACTERS,
    ) -> str:
        sections: list[str] = []
        running_length = 0
        for index, chunk in enumerate(retrieved_chunks, start=1):
            text = str(chunk.get("text") or "").strip()
            if not text:
                continue
            metadata = chunk.get("metadata", {}) or {}
            document_name = metadata.get(
                "document_name", metadata.get("source_file", "Unknown document")
            )
            location = (
                metadata.get("section_title")
                or (
                    f"Page {metadata['page_number']}"
                    if metadata.get("page_number") is not None
                    else None
                )
                or (
                    f"Slide {metadata['slide_number']}"
                    if metadata.get("slide_number") is not None
                    else None
                )
                or metadata.get("sheet_name")
                or "Document"
            )
            section = (
                f"[Source {index}: {document_name}]\n"
                f"Location: {location}\n{text}"
            )
            if running_length + len(section) > max_context_characters and sections:
                break
            sections.append(section)
            running_length += len(section)
        return "\n\n".join(sections)

    def build_sources(self, retrieved_chunks: list[dict]) -> list[dict]:
        documents = DocumentRegistry(self.workspace_id).get_all_documents()
        documents_by_source = {
            str(document.get("source_file") or ""): document
            for document in documents
        }
        customers = CustomerService(self.workspace_id).list_customers()
        customer_names = {
            str(customer["id"]): str(customer["company_name"])
            for customer in customers
        }
        metadata_fields = (
            "file_extension",
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
        )
        sources: list[dict] = []
        for index, chunk in enumerate(retrieved_chunks, start=1):
            metadata = chunk.get("metadata", {}) or {}
            source_file = str(metadata.get("source_file") or "")
            document = documents_by_source.get(source_file)
            customer_id = metadata.get("customer_id") or (
                document.get("customer_id") if document else None
            )
            source = {
                "rank": index,
                "document_id": document.get("id") if document else None,
                "document_name": metadata.get("document_name")
                or (document.get("name") if document else "Unknown document"),
                "source_file": source_file or None,
                "chunk_id": metadata.get("chunk_id"),
                "score": chunk.get("score"),
                "preview": str(chunk.get("text") or "")[:300],
                "category": metadata.get("category")
                or (document.get("category") if document else "Other"),
                "customer_id": customer_id,
                "customer_name": customer_names.get(str(customer_id))
                if customer_id
                else None,
                "scope": "retrieved_passage",
            }
            for field in metadata_fields:
                source[field] = metadata.get(field)
            sources.append(source)
        return sources

    def _prepare(
        self,
        *,
        question: str,
        customer_id: str | None,
        customer_context: str | None,
        conversation_history: list[dict] | None,
    ) -> dict:
        chunks = self.retrieve_context(
            question,
            customer_id=customer_id,
            conversation_history=conversation_history,
        )
        if not chunks and not customer_context:
            return {
                "empty_answer": (
                    "I couldn't find relevant information in the available "
                    "customer records or documents."
                ),
                "sources": [],
            }

        context = self.build_context(chunks)
        if customer_context:
            context = (
                f"[Customer profile]\n{customer_context}\n\n{context}"
                if context
                else f"[Customer profile]\n{customer_context}"
            )
        base_system_prompt = (
            self.settings.system_prompt.strip()
            if self.settings.system_prompt.strip()
            else BASIC_ASSISTANT_PROMPT
        )
        sources = self.build_sources(chunks)
        if customer_context:
            customer = (
                CustomerService(self.workspace_id).get_customer(customer_id)
                if customer_id
                else None
            )
            sources.insert(
                0,
                {
                    "rank": 0,
                    "document_id": None,
                    "document_name": "Customer profile",
                    "chunk_id": None,
                    "score": 1.0,
                    "preview": customer_context[:300],
                    "category": "Customer Profile",
                    "customer_id": customer_id,
                    "customer_name": customer.get("company_name") if customer else None,
                    "scope": "customer_profile",
                },
            )
        return {
            "prompt": f"Context:\n\n{context}\n\nQuestion:\n\n{question}",
            "system_prompt": f"{base_system_prompt}\n\n{GROUNDING_INSTRUCTIONS}",
            "sources": sources,
        }

    def answer_question(self, question: str) -> str:
        return self.answer_question_with_sources(question=question)["answer"]

    def answer_question_with_sources(
        self,
        question: str,
        customer_id: str | None = None,
        customer_context: str | None = None,
        conversation_history: list[dict] | None = None,
    ) -> dict:
        started = time.perf_counter()
        prepared = self._prepare(
            question=question,
            customer_id=customer_id,
            customer_context=customer_context,
            conversation_history=conversation_history,
        )
        if "empty_answer" in prepared:
            return {"answer": prepared["empty_answer"], "sources": []}
        answer = ask_llm(
            prompt=prepared["prompt"],
            system_prompt=prepared["system_prompt"],
            conversation_history=conversation_history,
            model=self.settings.llm_model,
            temperature=self.settings.temperature,
        )
        logger.info(
            "RAG answer generated | workspace=%s | sources=%s | duration=%.2fs",
            self.workspace_id,
            len(prepared["sources"]),
            time.perf_counter() - started,
        )
        return {"answer": answer, "sources": prepared["sources"]}

    def stream_answer_question_with_sources(
        self,
        *,
        question: str,
        customer_id: str | None = None,
        customer_context: str | None = None,
        conversation_history: list[dict] | None = None,
    ) -> Iterator[dict]:
        prepared = self._prepare(
            question=question,
            customer_id=customer_id,
            customer_context=customer_context,
            conversation_history=conversation_history,
        )
        if "empty_answer" in prepared:
            yield {"type": "delta", "delta": prepared["empty_answer"]}
            yield {"type": "metadata", "sources": []}
            return

        yield {"type": "metadata", "sources": prepared["sources"]}
        for delta in stream_llm(
            prompt=prepared["prompt"],
            system_prompt=prepared["system_prompt"],
            conversation_history=conversation_history,
            model=self.settings.llm_model,
            temperature=self.settings.temperature,
        ):
            yield {"type": "delta", "delta": delta}
