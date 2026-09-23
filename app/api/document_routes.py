from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.auth.auth_dependencies import get_current_user
from app.auth.user_model import User
from app.auth.user_service import UserService
from app.customers.customer_service import CustomerService
from app.services.document_management_service import (
    DocumentManagementService,
)
from app.services.document_processing_service import (
    DocumentProcessingService,
)
from app.services.document_registry import DocumentRegistry
from app.services.workspace_storage_service import WorkspaceStorageService
from app.workspaces.workspace_service import WorkspaceService


router = APIRouter(
    prefix="/workspaces/{workspace_id}/documents",
    tags=["Documents"],
)

user_service = UserService()
workspace_service = WorkspaceService()


class DocumentResponse(BaseModel):
    id: int
    name: str
    file_size: int
    chunk_count: int
    indexed: bool
    status: str
    uploaded_at: str | None
    last_indexed: str | None
    error_message: str | None
    customer_id: str | None
    category: str


class _UploadedFileAdapter:
    """
    DocumentProcessingService/DocumentManagementService were written
    against Streamlit's UploadedFile object (.name, .size,
    .getbuffer()). This adapts FastAPI's UploadFile to that same
    small interface so we can reuse those services unchanged.
    """

    def __init__(self, filename: str, contents: bytes):
        self.name = filename
        self._contents = contents
        self.size = len(contents)

    def getbuffer(self) -> memoryview:
        return memoryview(self._contents)


def ensure_workspace_access(
    current_user: User,
    workspace_id: str,
) -> None:
    workspace = workspace_service.get_workspace(
        workspace_id
    )

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found.",
        )

    has_access = user_service.user_has_workspace(
        user_id=current_user.id,
        workspace_id=workspace_id,
    )

    if not has_access and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this workspace.",
        )


def _to_response(document: dict) -> DocumentResponse:
    return DocumentResponse(
        id=document["id"],
        name=document["name"],
        file_size=document["file_size"],
        chunk_count=document["chunk_count"],
        indexed=document["indexed"],
        status=document["status"],
        uploaded_at=document["uploaded_at"],
        last_indexed=document["last_indexed"],
        error_message=document.get("error_message"),
        customer_id=document.get("customer_id"),
        category=document.get("category") or "Other",
    )


@router.get(
    "",
    response_model=list[DocumentResponse],
)
def list_documents(
    workspace_id: str,
    customer_id: str | None = None,
    current_user: User = Depends(get_current_user),
):
    ensure_workspace_access(
        current_user=current_user,
        workspace_id=workspace_id,
    )

    registry = DocumentRegistry(
        workspace_id=workspace_id
    )

    return [
        _to_response(document)
        for document in registry.get_all_documents(customer_id=customer_id)
    ]


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    workspace_id: str,
    file: UploadFile = File(...),
    customer_id: str | None = Form(default=None),
    category: str = Form(default="Other"),
    current_user: User = Depends(get_current_user),
):
    ensure_workspace_access(
        current_user=current_user,
        workspace_id=workspace_id,
    )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded file has no name.",
        )

    allowed_categories = {"Contract", "Invoice", "Consumption", "Procedure", "Other"}
    if category not in allowed_categories:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported document category.",
        )

    if customer_id and CustomerService(workspace_id).get_customer(customer_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found in this workspace.",
        )

    registry = DocumentRegistry(
        workspace_id=workspace_id
    )

    if registry.document_exists(file.filename):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"{file.filename} has already been "
                "uploaded to this workspace."
            ),
        )

    contents = await file.read()
    adapted_file = _UploadedFileAdapter(
        filename=file.filename,
        contents=contents,
    )

    processing_service = DocumentProcessingService(
        workspace_id=workspace_id
    )

    try:
        processing_service.upload_document(
            adapted_file,
            customer_id=customer_id,
            category=category,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The document could not be processed.",
        ) from error

    document = registry.get_document_by_name(
        adapted_file.name
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Document was processed but could not "
                "be found afterward."
            ),
        )

    return _to_response(document)


@router.get("/{document_id}/file")
def open_document_file(
    workspace_id: str,
    document_id: int,
    current_user: User = Depends(get_current_user),
):
    """Return an original document only after workspace authorization."""

    ensure_workspace_access(current_user=current_user, workspace_id=workspace_id)
    document = DocumentRegistry(workspace_id).get_document_by_id(document_id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    source_path = Path(str(document["source_file"])).resolve()
    documents_root = WorkspaceStorageService(workspace_id).get_documents_path().resolve()
    if not source_path.is_relative_to(documents_root) or not source_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The original document is unavailable.",
        )
    return FileResponse(
        path=source_path,
        filename=document["name"],
        content_disposition_type="inline",
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document(
    workspace_id: str,
    document_id: int,
    current_user: User = Depends(get_current_user),
):
    ensure_workspace_access(
        current_user=current_user,
        workspace_id=workspace_id,
    )

    registry = DocumentRegistry(
        workspace_id=workspace_id
    )

    document = registry.get_document_by_id(
        document_id
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    management_service = DocumentManagementService(
        workspace_id=workspace_id
    )

    deleted = management_service.delete_document(
        document["name"]
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The document could not be deleted.",
        )
