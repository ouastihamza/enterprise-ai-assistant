import json
import time
from pathlib import Path
from typing import Any

from app.services.chunking_service import ChunkingService
from app.services.file_readers.base_reader import ExtractedSection
from app.services.file_readers.reader_factory import ReaderFactory
from app.services.text_service import TextService


def _clean_section(
    section: ExtractedSection,
    text_service: TextService,
) -> ExtractedSection | None:
    clean_text = text_service.clean_text(
        section.text
    )

    if not clean_text or not clean_text.strip():
        return None

    return ExtractedSection(
        text=clean_text.strip(),
        section_type=section.section_type,
        section_number=section.section_number,
        section_title=section.section_title,
        metadata=section.metadata.copy(),
    )


def _build_location_metadata(
    section: ExtractedSection,
) -> dict[str, Any]:
    metadata = {
        "section_type": section.section_type,
        "section_number": section.section_number,
        "section_title": section.section_title,
    }

    metadata.update(section.metadata)

    if section.section_type == "page":
        metadata["page_number"] = section.section_number

    elif section.section_type == "slide":
        metadata["slide_number"] = section.section_number

    elif section.section_type == "sheet":
        metadata["sheet_number"] = section.section_number

    return {
        key: value
        for key, value in metadata.items()
        if value is not None
    }


def process_document(
    file_path: str,
    output_name: str,
    output_folder: str = "storage/processed",
    chunk_size: int = 1000,
    overlap: int = 200,
) -> Path:
    """
    Final structured knowledge-ingestion pipeline.

    Preserves source locations such as:
    - PDF pages
    - PowerPoint slides
    - Excel sheets
    - DOCX sections

    Legacy readers that only return plain text remain supported.
    """

    if chunk_size <= 0:
        raise ValueError(
            "Chunk size must be greater than zero."
        )

    if overlap < 0:
        raise ValueError(
            "Chunk overlap cannot be negative."
        )

    if overlap >= chunk_size:
        raise ValueError(
            "Chunk overlap must be smaller than chunk size."
        )

    total_start = time.perf_counter()

    source_path = Path(file_path).resolve()

    if not source_path.exists():
        raise FileNotFoundError(
            f"File not found: {source_path}"
        )

    if not source_path.is_file():
        raise ValueError(
            f"Knowledge source is not a file: {source_path}"
        )

    reader = ReaderFactory.get_reader(
        str(source_path)
    )

    text_service = TextService()
    chunking_service = ChunkingService()

    processed_folder = Path(output_folder)
    processed_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    extracted_text_path = (
        processed_folder
        / f"{output_name}_extracted.txt"
    )

    chunks_path = (
        processed_folder
        / f"{output_name}_chunks.json"
    )

    extraction_start = time.perf_counter()

    extracted_sections = reader.extract_sections(
        str(source_path)
    )

    extraction_time = (
        time.perf_counter() - extraction_start
    )

    if not extracted_sections:
        raise ValueError(
            f"No readable content extracted from: "
            f"{source_path.name}"
        )

    cleaning_start = time.perf_counter()

    cleaned_sections: list[ExtractedSection] = []

    for section in extracted_sections:
        cleaned_section = _clean_section(
            section=section,
            text_service=text_service,
        )

        if cleaned_section is not None:
            cleaned_sections.append(
                cleaned_section
            )

    cleaning_time = (
        time.perf_counter() - cleaning_start
    )

    if not cleaned_sections:
        raise ValueError(
            f"No readable content remained after cleaning: "
            f"{source_path.name}"
        )

    flattened_text = "\n\n".join(
        section.text
        for section in cleaned_sections
    )

    save_text_start = time.perf_counter()

    text_service.save_text(
        flattened_text,
        str(extracted_text_path),
    )

    save_text_time = (
        time.perf_counter() - save_text_start
    )

    chunking_start = time.perf_counter()

    chunk_data: list[dict[str, Any]] = []
    global_chunk_number = 1

    for section_index, section in enumerate(
        cleaned_sections,
        start=1,
    ):
        section_chunks = chunking_service.chunk_text(
            text=section.text,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        location_metadata = (
            _build_location_metadata(section)
        )

        for local_chunk_number, chunk in enumerate(
            section_chunks,
            start=1,
        ):
            clean_chunk = chunk.strip()

            if not clean_chunk:
                continue

            chunk_data.append(
                {
                    "chunk_id": global_chunk_number,
                    "section_chunk_id": local_chunk_number,
                    "source_file": str(source_path),
                    "document_name": source_path.name,
                    "file_extension": (
                        source_path.suffix
                        .lower()
                        .lstrip(".")
                    ),
                    "text": clean_chunk,
                    "char_count": len(clean_chunk),
                    "chunk_size": chunk_size,
                    "chunk_overlap": overlap,
                    "source_section_index": section_index,
                    **location_metadata,
                }
            )

            global_chunk_number += 1

    chunking_time = (
        time.perf_counter() - chunking_start
    )

    if not chunk_data:
        raise ValueError(
            f"No searchable chunks created from: "
            f"{source_path.name}"
        )

    save_chunks_start = time.perf_counter()

    temporary_chunks_path = (
        chunks_path.with_suffix(".json.tmp")
    )

    temporary_chunks_path.write_text(
        json.dumps(
            chunk_data,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    temporary_chunks_path.replace(
        chunks_path
    )

    save_chunks_time = (
        time.perf_counter() - save_chunks_start
    )

    total_time = (
        time.perf_counter() - total_start
    )

    print(
        f"\nKnowledge ingestion: {source_path.name}\n"
        f"Extraction..............{extraction_time:.2f}s\n"
        f"Cleaning................{cleaning_time:.2f}s\n"
        f"Save extracted text.....{save_text_time:.2f}s\n"
        f"Chunking................{chunking_time:.2f}s\n"
        f"Save chunks.............{save_chunks_time:.2f}s\n"
        f"Total processing........{total_time:.2f}s\n"
        f"Sections extracted......{len(cleaned_sections)}\n"
        f"Chunks created..........{len(chunk_data)}\n"
    )

    return chunks_path
