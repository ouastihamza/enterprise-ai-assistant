from pathlib import Path
import xml.etree.ElementTree as ET

from app.services.file_readers.base_reader import BaseFileReader


class XMLReader(BaseFileReader):
    """
    Extracts readable text from XML files.
    """

    def extract_text(self, file_path: str) -> str:
        xml_path = Path(file_path)

        if not xml_path.exists():
            raise FileNotFoundError(f"XML file not found: {file_path}")

        tree = ET.parse(xml_path)
        root = tree.getroot()

        extracted_text = []

        def walk(node):
            if node.text and node.text.strip():
                extracted_text.append(node.text.strip())

            for child in node:
                walk(child)

        walk(root)

        return "\n".join(extracted_text)