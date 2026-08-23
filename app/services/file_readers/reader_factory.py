from pathlib import Path

from app.services.file_readers.csv_reader import CSVReader
from app.services.file_readers.docx_reader import DOCXReader
from app.services.file_readers.excel_reader import ExcelReader
from app.services.file_readers.html_reader import HTMLReader
from app.services.file_readers.json_reader import JSONReader
from app.services.file_readers.markdown_reader import MarkdownReader
from app.services.file_readers.pdf_reader import PDFReader
from app.services.file_readers.pptx_reader import PPTXReader
from app.services.file_readers.txt_reader import TXTReader
from app.services.file_readers.xml_reader import XMLReader


class ReaderFactory:
    """
    Returns the correct structured reader for a supported file type.
    """

    READERS = {
        ".pdf": PDFReader,
        ".docx": DOCXReader,
        ".txt": TXTReader,
        ".md": MarkdownReader,
        ".csv": CSVReader,
        ".xlsx": ExcelReader,
        ".html": HTMLReader,
        ".htm": HTMLReader,
        ".json": JSONReader,
        ".xml": XMLReader,
        ".pptx": PPTXReader,
    }

    @classmethod
    def get_reader(cls, file_path: str):
        extension = Path(file_path).suffix.lower()

        reader_class = cls.READERS.get(extension)

        if reader_class is None:
            supported_types = ", ".join(
                sorted(cls.READERS.keys())
            )

            raise ValueError(
                f"Unsupported file type: {extension or 'unknown'}. "
                f"Supported types: {supported_types}"
            )

        return reader_class()

    @classmethod
    def is_supported(cls, file_path: str) -> bool:
        extension = Path(file_path).suffix.lower()

        return extension in cls.READERS

    @classmethod
    def supported_extensions(cls) -> list[str]:
        return sorted(cls.READERS.keys())