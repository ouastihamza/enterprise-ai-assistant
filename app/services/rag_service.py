import logging
import time

from app.configuration.workspace_settings_service import (
    WorkspaceSettingsService,
)
from app.llm_client import ask_llm
from app.prompts import BASIC_ASSISTANT_PROMPT
from app.services.vector_search_service import (
    VectorSearchService,
)


logger = logging.getLogger(__name__)


# Layered on top of whatever persona/tone lives in the workspace's
# system_prompt (or BASIC_ASSISTANT_PROMPT), regardless of what that
# text says. This is what stops the model from answering off
# unrelated general knowledge and gives it a citation format to use.
GROUNDING_INSTRUCTIONS = (
    "You must answer using only the information given in the "
    "Context below. When a statement comes from the context, cite "
    "it inline using the matching tag, e.g. [Source 1], [Source 2]. "
    "If the context does not contain enough information to answer "
    "the question, say so clearly instead of guessing."
)

# Rough character budget for assembled context so a large top_k or
# long chunks can't silently blow past the LLM's context window or
# drown the prompt in low-relevance tail content.
MAX_CONTEXT_CHARACTERS = 6000


class RAGService:
    """
    Final Retrieval-Augmented Generation service.

    Workspace aware.
    Uses workspace settings automatically.
    """

    def __init__(
        self,
        workspace_id: str,
    ):
        self.workspace_id = workspace_id

        self.vector_search = VectorSearchService(
            workspace_id=workspace_id
        )

        self.settings = (
            WorkspaceSettingsService()
            .get_or_create_settings(
                workspace_id=workspace_id
            )
        )

    def retrieve_context(
        self,
        question: str,
    ) -> list[dict]:
        return self.vector_search.search(
            question=question,
            top_k=self.settings.top_k,
        )

    @staticmethod
    def build_context(
        retrieved_chunks: list[dict],
        max_context_characters: int = MAX_CONTEXT_CHARACTERS,
    ) -> str:
        labeled_sections = []
        running_length = 0

        for index, chunk in enumerate(
            retrieved_chunks,
            start=1,
        ):
            text = (chunk.get("text") or "").strip()

            if not text:
                continue

            metadata = chunk.get(
                "metadata",
                {},
            ) or {}

            document_name = metadata.get(
                "document_name",
                metadata.get(
                    "source_file",
                    "Unknown document",
                ),
            )

            section = (
                f"[Source {index}: {document_name}]\n{text}"
            )

            would_exceed_budget = (
                running_length + len(section)
                > max_context_characters
            )

            if would_exceed_budget and labeled_sections:
                break

            labeled_sections.append(section)
            running_length += len(section)

        return "\n\n".join(labeled_sections)

    @staticmethod
    def build_sources(
        retrieved_chunks: list[dict],
    ) -> list[dict]:

        sources = []

        for index, chunk in enumerate(
            retrieved_chunks,
            start=1,
        ):
            metadata = chunk.get(
                "metadata",
                {},
            )

            sources.append(
                {
                    "rank": index,
                    "document_name": metadata.get(
                        "document_name",
                        metadata.get(
                            "source_file",
                            "Unknown document",
                        ),
                    ),
                    "chunk_id": metadata.get(
                        "chunk_id",
                    ),
                    "score": chunk.get(
                        "score",
                    ),
                    "preview": chunk.get(
                        "text",
                        "",
                    )[:300],
                }
            )

        return sources

    def answer_question(
        self,
        question: str,
    ) -> str:
        return self.answer_question_with_sources(
            question
        )["answer"]

    def answer_question_with_sources(
        self,
        question: str,
    ) -> dict:

        start_time = time.perf_counter()

        retrieved_chunks = self.retrieve_context(
            question
        )

        if not retrieved_chunks:
            return {
                "answer": (
                    "I couldn't find any relevant information "
                    "in the uploaded company knowledge."
                ),
                "sources": [],
            }

        context = self.build_context(
            retrieved_chunks
        )

        base_system_prompt = (
            self.settings.system_prompt.strip()
            if self.settings.system_prompt.strip()
            else BASIC_ASSISTANT_PROMPT
        )

        system_prompt = (
            f"{base_system_prompt}\n\n{GROUNDING_INSTRUCTIONS}"
        )

        prompt = f"""
Context:

{context}

Question:

{question}
"""

        try:
            answer = ask_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                model=self.settings.llm_model,
                temperature=self.settings.temperature,
            )

        except Exception:
            logger.exception(
                "LLM call failed | workspace=%s",
                self.workspace_id,
            )

            return {
                "answer": (
                    "Something went wrong while generating the "
                    "answer. Please try again in a moment."
                ),
                "sources": self.build_sources(
                    retrieved_chunks
                ),
            }

        elapsed = (
            time.perf_counter()
            - start_time
        )

        logger.info(
            "RAG answer generated | workspace=%s | chunks=%s | "
            "top_score=%s | duration=%.2fs",
            self.workspace_id,
            len(retrieved_chunks),
            retrieved_chunks[0]["score"],
            elapsed,
        )

        return {
            "answer": answer,
            "sources": self.build_sources(
                retrieved_chunks
            ),
        }