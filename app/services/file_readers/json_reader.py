import json
from pathlib import Path

from app.services.file_readers.base_reader import BaseFileReader


class JSONReader(BaseFileReader):
    """
    Extracts readable text from JSON files.
    """

    def extract_text(self, file_path: str) -> str:

        json_path = Path(file_path)

        if not json_path.exists():
            raise FileNotFoundError(
                f"JSON file not found: {file_path}"
            )

        with open(
            json_path,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return json.dumps(
            data,
            indent=4,
            ensure_ascii=False,
        )