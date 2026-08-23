from pathlib import Path

from app.services.file_readers.base_reader import BaseFileReader


class MarkdownReader(BaseFileReader):
    """
    Extracts text from Markdown files.
    """

    def extract_text(self, file_path: str) -> str:
        markdown_file = Path(file_path)

        if not markdown_file.exists():
            raise FileNotFoundError(f"Markdown file not found: {file_path}")

        return markdown_file.read_text(encoding="utf-8").strip()