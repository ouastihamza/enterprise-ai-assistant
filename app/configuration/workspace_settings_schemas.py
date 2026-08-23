from typing import Annotated, Optional

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)


SUPPORTED_FILE_TYPES = {
    "pdf",
    "docx",
    "txt",
    "md",
    "csv",
    "xlsx",
    "html",
    "htm",
    "json",
    "xml",
    "pptx",
}


class WorkspaceSettingsResponse(BaseModel):
    workspace_id: str

    assistant_name: str
    company_logo: str
    primary_color: str
    theme: str

    llm_model: str
    temperature: float

    chunk_size: int
    chunk_overlap: int
    top_k: int

    max_upload_size_mb: int
    allowed_file_types: list[str]

    welcome_message: str
    system_prompt: str


class WorkspaceSettingsUpdate(BaseModel):
    assistant_name: Optional[
        Annotated[
            str,
            Field(
                min_length=1,
                max_length=100,
            ),
        ]
    ] = None

    company_logo: Optional[str] = None

    primary_color: Optional[
        Annotated[
            str,
            Field(
                pattern=r"^#[0-9A-Fa-f]{6}$",
            ),
        ]
    ] = None

    theme: Optional[str] = None

    llm_model: Optional[
        Annotated[
            str,
            Field(
                min_length=1,
                max_length=100,
            ),
        ]
    ] = None

    temperature: Optional[
        Annotated[
            float,
            Field(
                ge=0.0,
                le=2.0,
            ),
        ]
    ] = None

    chunk_size: Optional[
        Annotated[
            int,
            Field(
                ge=200,
                le=5000,
            ),
        ]
    ] = None

    chunk_overlap: Optional[
        Annotated[
            int,
            Field(
                ge=0,
                le=1000,
            ),
        ]
    ] = None

    top_k: Optional[
        Annotated[
            int,
            Field(
                ge=1,
                le=20,
            ),
        ]
    ] = None

    max_upload_size_mb: Optional[
        Annotated[
            int,
            Field(
                ge=1,
                le=10000,
            ),
        ]
    ] = None

    allowed_file_types: Optional[
        list[str]
    ] = None

    welcome_message: Optional[
        Annotated[
            str,
            Field(
                min_length=1,
                max_length=1000,
            ),
        ]
    ] = None

    system_prompt: Optional[
        Annotated[
            str,
            Field(
                max_length=10000,
            ),
        ]
    ] = None

    @field_validator("theme")
    @classmethod
    def validate_theme(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        normalized = value.strip().lower()

        if normalized not in {
            "light",
            "dark",
            "system",
        }:
            raise ValueError(
                "Theme must be light, dark, or system."
            )

        return normalized

    @field_validator(
        "allowed_file_types"
    )
    @classmethod
    def validate_file_types(
        cls,
        value: Optional[list[str]],
    ) -> Optional[list[str]]:
        if value is None:
            return None

        normalized = list(
            dict.fromkeys(
                file_type
                .strip()
                .lower()
                .lstrip(".")
                for file_type in value
                if file_type.strip()
            )
        )

        if not normalized:
            raise ValueError(
                "At least one file type is required."
            )

        invalid_types = (
            set(normalized)
            - SUPPORTED_FILE_TYPES
        )

        if invalid_types:
            invalid_list = ", ".join(
                sorted(invalid_types)
            )

            raise ValueError(
                f"Unsupported file types: {invalid_list}"
            )

        return normalized

    @model_validator(mode="after")
    def validate_chunk_configuration(self):
        if (
            self.chunk_size is not None
            and self.chunk_overlap is not None
            and self.chunk_overlap >= self.chunk_size
        ):
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )

        return self