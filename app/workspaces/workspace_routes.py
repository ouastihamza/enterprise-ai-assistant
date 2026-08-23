from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.auth_dependencies import get_current_user
from app.auth.user_model import User
from app.auth.user_service import UserService
from app.workspaces.workspace_service import WorkspaceService


router = APIRouter(
    prefix="/workspaces",
    tags=["Workspaces"],
)

workspace_service = WorkspaceService()
user_service = UserService()


class CreateWorkspaceRequest(BaseModel):
    name: str
    company_name: str
    industry: Optional[str] = None
    description: Optional[str] = None
    enabled_modules: List[str] = Field(default_factory=list)


class UpdateWorkspaceRequest(BaseModel):
    name: Optional[str] = None
    company_name: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    enabled_modules: Optional[List[str]] = None


def ensure_workspace_access(
    current_user: User,
    workspace_id: str,
):
    has_access = user_service.user_has_workspace(
        user_id=current_user.id,
        workspace_id=workspace_id,
    )

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this workspace.",
        )


@router.post("/")
def create_workspace(
    request: CreateWorkspaceRequest,
    current_user: User = Depends(get_current_user),
):
    workspace = workspace_service.create_workspace(
        name=request.name,
        company_name=request.company_name,
        industry=request.industry,
        description=request.description,
        enabled_modules=request.enabled_modules,
    )

    user_service.assign_workspace(
        user_id=current_user.id,
        workspace_id=workspace.id,
    )

    return workspace


@router.get("/")
def list_workspaces(
    current_user: User = Depends(get_current_user),
):
    workspaces = workspace_service.list_workspaces()

    if current_user.is_superuser:
        return workspaces

    return [
        workspace
        for workspace in workspaces
        if workspace.id in current_user.workspace_ids
    ]


@router.get("/{workspace_id}")
def get_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
):
    workspace = workspace_service.get_workspace(
        workspace_id
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found.",
        )

    ensure_workspace_access(
        current_user=current_user,
        workspace_id=workspace_id,
    )

    return workspace


@router.put("/{workspace_id}")
def update_workspace(
    workspace_id: str,
    request: UpdateWorkspaceRequest,
    current_user: User = Depends(get_current_user),
):
    workspace = workspace_service.get_workspace(
        workspace_id
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found.",
        )

    ensure_workspace_access(
        current_user=current_user,
        workspace_id=workspace_id,
    )

    updated_workspace = workspace_service.update_workspace(
        workspace_id=workspace_id,
        name=request.name,
        company_name=request.company_name,
        industry=request.industry,
        description=request.description,
        enabled_modules=request.enabled_modules,
    )

    return updated_workspace


@router.patch("/{workspace_id}/archive")
def archive_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
):
    workspace = workspace_service.get_workspace(
        workspace_id
    )

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found.",
        )

    ensure_workspace_access(
        current_user=current_user,
        workspace_id=workspace_id,
    )

    archived_workspace = workspace_service.archive_workspace(
        workspace_id
    )

    return archived_workspace