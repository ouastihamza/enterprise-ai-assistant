from pathlib import Path
import re


class TextService:
    """
    Handles text cleaning and saving.
    """

    def clean_text(self, text: str) -> str:
        # Replace multiple spaces/tabs with one space
        text = re.sub(r"[ \t]+", " ", text)

        # Replace too many new lines with two new lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def save_text(self, text: str, output_path: str) -> Path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as file:
            file.write(text)

        return output_file