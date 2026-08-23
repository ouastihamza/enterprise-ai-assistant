from abc import ABC
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ExtractedSection:
    """
    One structured section extracted from a knowledge source.

    Examples:
    - PDF page
    - PowerPoint slide
    - Excel sheet
    - DOCX section
    - Plain-text document section
    """

    text: str
    section_type: str = "section"
    section_number: int | None = None
    section_title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BaseFileReader(ABC):
    """
    Final reader interface for all supported knowledge sources.

    Every reader must return structured sections so citations and
    source locations can be preserved throughout the RAG pipeline.

    A reader only needs to override ONE of extract_sections() or
    extract_text() — whichever fits the format. Readers that can
    expose real structure (pages, slides, sheets, headings) should
    override extract_sections() directly. Readers that only produce
    flat text can override extract_text() instead and get a single
    document-level section here for free.
    """

    def extract_sections(
        self,
        file_path: str,
    ) -> list[ExtractedSection]:
        """
        Extract structured content from a file.

        Default implementation for readers that only implement
        extract_text(): wraps the flattened text in one section.
        """

        text = self.extract_text(file_path)

        if not text or not text.strip():
            return []

        return [
            ExtractedSection(
                text=text.strip(),
                section_type="document",
            )
        ]

    def extract_text(
        self,
        file_path: str,
    ) -> str:
        """
        Backward-compatible flattened text extraction.

        Existing code can continue calling extract_text(), while the
        final ingestion pipeline uses extract_sections().
        """

        sections = self.extract_sections(file_path)

        return "\n\n".join(
            section.text.strip()
            for section in sections
            if section.text and section.text.strip()
        )