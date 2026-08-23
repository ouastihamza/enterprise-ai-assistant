from pathlib import Path

from app.services.file_readers.base_reader import BaseFileReader


class TXTReader(BaseFileReader):
    """
    Extracts text from .txt files.
    """

    def extract_text(self, file_path: str) -> str:
        text_file = Path(file_path)

        if not text_file.exists():
            raise FileNotFoundError(f"Text file not found: {file_path}")

        return text_file.read_text(encoding="utf-8").strip()