import re


class ChunkingService:
    """
    Splits text into readable, retrieval-friendly chunks.

    This version is paragraph-aware and sentence-aware.
    It avoids cutting sentences in the middle when possible.
    """

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> list[str]:

        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0.")

        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size.")

        clean_text = text.strip()

        if not clean_text:
            return []

        paragraphs = self._split_into_paragraphs(clean_text)

        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:

            if len(paragraph) > chunk_size:
                sentence_chunks = self._chunk_large_paragraph(
                    paragraph=paragraph,
                    chunk_size=chunk_size,
                    overlap=overlap,
                )

                for sentence_chunk in sentence_chunks:
                    chunks = self._add_chunk_with_overlap(
                        chunks=chunks,
                        chunk=sentence_chunk,
                        overlap=overlap,
                    )

                continue

            proposed_chunk = self._join_text(
                current_chunk,
                paragraph,
            )

            if len(proposed_chunk) <= chunk_size:
                current_chunk = proposed_chunk

            else:
                if current_chunk:
                    chunks = self._add_chunk_with_overlap(
                        chunks=chunks,
                        chunk=current_chunk,
                        overlap=overlap,
                    )

                current_chunk = paragraph

        if current_chunk:
            chunks = self._add_chunk_with_overlap(
                chunks=chunks,
                chunk=current_chunk,
                overlap=overlap,
            )

        return chunks

    def _split_into_paragraphs(self, text: str) -> list[str]:
        paragraphs = re.split(r"\n\s*\n", text)

        return [
            paragraph.strip()
            for paragraph in paragraphs
            if paragraph.strip()
        ]

    def _split_into_sentences(self, text: str) -> list[str]:
        sentences = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        return [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

    def _chunk_large_paragraph(
        self,
        paragraph: str,
        chunk_size: int,
        overlap: int,
    ) -> list[str]:

        sentences = self._split_into_sentences(paragraph)

        chunks = []
        current_chunk = ""

        for sentence in sentences:

            proposed_chunk = self._join_text(
                current_chunk,
                sentence,
            )

            if len(proposed_chunk) <= chunk_size:
                current_chunk = proposed_chunk

            else:
                if current_chunk:
                    chunks.append(current_chunk)

                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _add_chunk_with_overlap(
        self,
        chunks: list[str],
        chunk: str,
        overlap: int,
    ) -> list[str]:

        clean_chunk = chunk.strip()

        if not clean_chunk:
            return chunks

        if not chunks or overlap <= 0:
            chunks.append(clean_chunk)
            return chunks

        previous_chunk = chunks[-1]

        overlap_text = previous_chunk[-overlap:].strip()

        combined_chunk = self._join_text(
            overlap_text,
            clean_chunk,
        )

        chunks.append(combined_chunk)

        return chunks

    def _join_text(
        self,
        first: str,
        second: str,
    ) -> str:

        if not first:
            return second.strip()

        if not second:
            return first.strip()

        return f"{first.strip()}\n\n{second.strip()}"