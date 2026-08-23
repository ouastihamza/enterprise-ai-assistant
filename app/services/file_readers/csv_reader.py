from pathlib import Path
import csv

from app.services.file_readers.base_reader import BaseFileReader


class CSVReader(BaseFileReader):
    """
    Extracts readable text from CSV files.
    """

    def extract_text(self, file_path: str) -> str:
        csv_path = Path(file_path)

        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        rows_as_text = []

        with open(csv_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row_number, row in enumerate(reader, start=1):
                row_text = f"Row {row_number}: "

                values = []

                for column, value in row.items():
                    values.append(f"{column}: {value}")

                row_text += " | ".join(values)
                rows_as_text.append(row_text)

        return "\n".join(rows_as_text)