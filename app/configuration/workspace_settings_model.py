from dataclasses import dataclass, field
from typing import List


@dataclass
class WorkspaceSettings:
    """
    Configurable settings for a workspace.

    These settings control branding,
    AI behavior, limits, and appearance.
    """

    workspace_id: str

    # Branding
    assistant_name: str = "AI Knowledge Assistant"
    company_logo: str = ""
    primary_color: str = "#2563EB"
    theme: str = "light"

    # AI
    llm_model: str = "gpt-5.5"
    temperature: float = 0.2
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 3

    # Storage
    max_upload_size_mb: int = 500

    # File Types
    allowed_file_types: List[str] = field(
        default_factory=lambda: [
            "pdf",
            "docx",
            "txt",
            "md",
            "csv",
            "xlsx",
            "html",
            "json",
            "xml",
            "pptx",
        ]
    )

    # Prompt
    welcome_message: str = (
        "Ask questions about your company's knowledge."
    )

    system_prompt: str = (
        "You are a helpful AI assistant that only answers using the company's uploaded knowledge."
    )