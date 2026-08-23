from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.auth_dependencies import get_current_user
from app.auth.user_model import User
from app.configuration.workspace_settings_schemas import (
    WorkspaceSettingsResponse,
    WorkspaceSettingsUpdate,
)
from app.configuration.workspace_settings_service import (
    WorkspaceSettingsService,
)


router = APIRouter(
    prefix="/workspace/settings",
    tags=["Workspace Settings"],
)

settings_service = WorkspaceSettingsService()


def get_active_workspace_id(
    current_user: User,
) -> str:
    """
    For now, each user uses the first assigned workspace.

    Later, when workspace switching exists, the active workspace
    will come from the UI/session/header instead.
    """

    if not current_user.workspace_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No workspace assigned to this user.",
        )

    return current_user.workspace_ids[0]


@router.get(
    "",
    response_model=WorkspaceSettingsResponse,
)
def get_workspace_settings(
    current_user: User = Depends(get_current_user),
):
    workspace_id = get_active_workspace_id(
        current_user=current_user
    )

    settings = settings_service.get_or_create_settings(
        workspace_id=workspace_id
    )

    return WorkspaceSettingsResponse(
        **settings.__dict__
    )


@router.put(
    "",
    response_model=WorkspaceSettingsResponse,
)
def update_workspace_settings(
    request: WorkspaceSettingsUpdate,
    current_user: User = Depends(get_current_user),
):
    workspace_id = get_active_workspace_id(
        current_user=current_user
    )

    existing_settings = settings_service.get_or_create_settings(
        workspace_id=workspace_id
    )

    settings = settings_service.update_settings(
        workspace_id=existing_settings.workspace_id,
        assistant_name=request.assistant_name,
        company_logo=request.company_logo,
        primary_color=request.primary_color,
        theme=request.theme,
        llm_model=request.llm_model,
        temperature=request.temperature,
        chunk_size=request.chunk_size,
        chunk_overlap=request.chunk_overlap,
        top_k=request.top_k,
        max_upload_size_mb=request.max_upload_size_mb,
        allowed_file_types=request.allowed_file_types,
        welcome_message=request.welcome_message,
        system_prompt=request.system_prompt,
    )

    if settings is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Workspace settings could not be updated.",
        )

    return WorkspaceSettingsResponse(
        **settings.__dict__
    )