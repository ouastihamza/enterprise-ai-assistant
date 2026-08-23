import json
from pathlib import Path


class KnowledgeBaseService:
    """
    Combines chunks from multiple documents into one workspace knowledge base.

    This service is workspace-aware because the knowledge_base_path
    is passed from the selected workspace storage.
    """

    def __init__(self, knowledge_base_path: str):
        self.knowledge_base_path = Path(knowledge_base_path)
        self.knowledge_base_path.parent.mkdir(parents=True, exist_ok=True)

    def load_knowledge_base(self):
        if not self.knowledge_base_path.exists():
            return []

        if self.knowledge_base_path.stat().st_size == 0:
            return []

        with open(self.knowledge_base_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def save_knowledge_base(self, chunks):
        with open(self.knowledge_base_path, "w", encoding="utf-8") as file:
            json.dump(chunks, file, indent=4, ensure_ascii=False)

    def add_chunks_from_file(self, chunks_file_path: str):
        existing_chunks = self.load_knowledge_base()

        with open(chunks_file_path, "r", encoding="utf-8") as file:
            new_chunks = json.load(file)

        start_id = len(existing_chunks) + 1

        for index, chunk in enumerate(new_chunks, start=start_id):
            chunk["global_chunk_id"] = index
            existing_chunks.append(chunk)

        self.save_knowledge_base(existing_chunks)

        return self.knowledge_base_path

    def remove_chunks_by_source_file(self, source_file: str):
        existing_chunks = self.load_knowledge_base()

        updated_chunks = [
            chunk
            for chunk in existing_chunks
            if chunk.get("source_file") != source_file
        ]

        self.save_knowledge_base(updated_chunks)

        return len(existing_chunks) - len(updated_chunks)

    def clear_knowledge_base(self):
        self.save_knowledge_base([])