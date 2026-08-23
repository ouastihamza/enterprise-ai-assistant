from pathlib import Path

from pypdf import PdfReader

from app.services.file_readers.base_reader import (
    BaseFileReader,
    ExtractedSection,
)


class PDFReader(BaseFileReader):
    """
    Extracts PDF content page by page.

    Each page is preserved as a structured section so the final
    RAG pipeline can return accurate page citations.
    """

    def extract_sections(
        self,
        file_path: str,
    ) -> list[ExtractedSection]:
        pdf_file = Path(file_path)

        if not pdf_file.exists():
            raise FileNotFoundError(
                f"PDF file not found: {file_path}"
            )

        reader = PdfReader(pdf_file)

        sections: list[ExtractedSection] = []

        for page_index, page in enumerate(
            reader.pages,
            start=1,
        ):
            page_text = page.extract_text()

            if not page_text:
                continue

            clean_page_text = page_text.strip()

            if not clean_page_text:
                continue

            sections.append(
                ExtractedSection(
                    text=clean_page_text,
                    section_type="page",
                    section_number=page_index,
                    section_title=f"Page {page_index}",
                    metadata={
                        "page_number": page_index,
                        "total_pages": len(reader.pages),
                    },
                )
            )

        if not sections:
            raise ValueError(
                f"No readable text found in PDF: {pdf_file.name}"
            )

        return sections