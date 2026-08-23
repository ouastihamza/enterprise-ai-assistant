from pathlib import Path
from html.parser import HTMLParser

from app.services.file_readers.base_reader import BaseFileReader


class SimpleHTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        clean_data = data.strip()

        if clean_data:
            self.text_parts.append(clean_data)

    def get_text(self):
        return "\n".join(self.text_parts)


class HTMLReader(BaseFileReader):
    """
    Extracts readable text from HTML files.
    """

    def extract_text(self, file_path: str) -> str:
        html_path = Path(file_path)

        if not html_path.exists():
            raise FileNotFoundError(f"HTML file not found: {file_path}")

        html_content = html_path.read_text(encoding="utf-8")

        parser = SimpleHTMLTextExtractor()
        parser.feed(html_content)

        return parser.get_text()