from pathlib import Path

from docx import Document

from app.services.file_readers.base_reader import (
    BaseFileReader,
    ExtractedSection,
)


class DOCXReader(BaseFileReader):
    """
    Extracts Microsoft Word content as structured sections.

    Headings start new sections.
    Paragraphs beneath a heading belong to that section.
    """

    def extract_sections(
        self,
        file_path: str,
    ) -> list[ExtractedSection]:
        document_path = Path(file_path)

        if not document_path.exists():
            raise FileNotFoundError(
                f"Word document not found: {file_path}"
            )

        document = Document(document_path)

        sections: list[ExtractedSection] = []
        current_title: str | None = None
        current_paragraphs: list[str] = []
        section_number = 1

        def flush_section() -> None:
            nonlocal section_number
            nonlocal current_paragraphs
            nonlocal current_title

            section_text = "\n".join(
                paragraph
                for paragraph in current_paragraphs
                if paragraph.strip()
            ).strip()

            if not section_text:
                return

            sections.append(
                ExtractedSection(
                    text=section_text,
                    section_type="section",
                    section_number=section_number,
                    section_title=(
                        current_title
                        or f"Section {section_number}"
                    ),
                    metadata={
                        "heading": current_title,
                    },
                )
            )

            section_number += 1
            current_paragraphs = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if not text:
                continue

            style_name = (
                paragraph.style.name.lower()
                if paragraph.style
                else ""
            )

            is_heading = style_name.startswith("heading")

            if is_heading:
                flush_section()
                current_title = text
                continue

            current_paragraphs.append(text)

        flush_section()

        if not sections:
            raise ValueError(
                f"No readable text found in Word document: "
                f"{document_path.name}"
            )

        return sections