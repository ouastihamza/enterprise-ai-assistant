from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.auth.auth_dependencies import get_current_user
from app.auth.user_model import User
from app.auth.user_service import UserService
from app.conversation import ConversationManager
from app.workspaces.workspace_service import WorkspaceService


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)

user_service = UserService()
workspace_service = WorkspaceService()


class CreateConversationRequest(BaseModel):
    workspace_id: str = Field(min_length=1)
    title: str = Field(
        default="New conversation",
        min_length=1,
        max_length=200,
    )


class RenameConversationRequest(BaseModel):
    workspace_id: str = Field(min_length=1)
    title: str = Field(
        min_length=1,
        max_length=200,
    )


class ConversationResponse(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    title: str
    status: str
    created_at: str
    updated_at: str
    message_count: int | None = None


class ConversationDetailResponse(ConversationResponse):
    messages: list[dict]


class DeleteConversationResponse(BaseModel):
    deleted: bool
    conversation_id: str
    active_conversation_id: str


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

    if (
        not has_access
        and not current_user.is_superuser
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have access "
                "to this workspace."
            ),
        )


def get_conversation_manager(
    workspace_id: str,
    current_user: User,
    conversation_id: str | None = None,
) -> ConversationManager:
    ensure_workspace_access(
        current_user=current_user,
        workspace_id=workspace_id,
    )

    try:
        return ConversationManager(
            workspace_id=workspace_id,
            user_id=current_user.id,
            conversation_id=conversation_id,
        )

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        ) from error


@router.get(
    "",
    response_model=list[ConversationResponse],
)
def list_conversations(
    workspace_id: str = Query(
        min_length=1
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    current_user: User = Depends(
        get_current_user
    ),
):
    manager = get_conversation_manager(
        workspace_id=workspace_id.strip(),
        current_user=current_user,
    )

    return manager.list_conversations(
        limit=limit
    )


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    request: CreateConversationRequest,
    current_user: User = Depends(
        get_current_user
    ),
):
    workspace_id = request.workspace_id.strip()
    clean_title = request.title.strip()

    manager = get_conversation_manager(
        workspace_id=workspace_id,
        current_user=current_user,
    )

    conversations = manager.list_conversations(
        limit=200
    )

    active_conversation = next(
        (
            conversation
            for conversation in conversations
            if conversation["id"]
            == manager.conversation_id
        ),
        None,
    )

    can_reuse_active_conversation = (
        active_conversation is not None
        and active_conversation.get(
            "message_count",
            0,
        )
        == 0
        and active_conversation.get(
            "title"
        )
        == "New conversation"
    )

    if can_reuse_active_conversation:
        if clean_title != "New conversation":
            manager.rename_conversation(
                clean_title
            )

        conversation = next(
            conversation
            for conversation
            in manager.list_conversations(
                limit=200
            )
            if conversation["id"]
            == manager.conversation_id
        )

        return conversation

    conversation_id = (
        manager.start_new_conversation(
            title=clean_title
        )
    )

    conversation = next(
        conversation
        for conversation
        in manager.list_conversations(
            limit=200
        )
        if conversation["id"]
        == conversation_id
    )

    return conversation


@router.get(
    "/{conversation_id}",
    response_model=ConversationDetailResponse,
)
def get_conversation(
    conversation_id: str,
    workspace_id: str = Query(
        min_length=1
    ),
    current_user: User = Depends(
        get_current_user
    ),
):
    manager = get_conversation_manager(
        workspace_id=workspace_id.strip(),
        current_user=current_user,
        conversation_id=conversation_id,
    )

    conversation = next(
        (
            item
            for item
            in manager.list_conversations(
                limit=200
            )
            if item["id"]
            == conversation_id
        ),
        None,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    return {
        **conversation,
        "messages": manager.load_history(),
    }


@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def rename_conversation(
    conversation_id: str,
    request: RenameConversationRequest,
    current_user: User = Depends(
        get_current_user
    ),
):
    manager = get_conversation_manager(
        workspace_id=request.workspace_id.strip(),
        current_user=current_user,
        conversation_id=conversation_id,
    )

    try:
        renamed = manager.rename_conversation(
            request.title.strip()
        )

    except ValueError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(error),
        ) from error

    if not renamed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    conversation = next(
        (
            item
            for item
            in manager.list_conversations(
                limit=200
            )
            if item["id"]
            == conversation_id
        ),
        None,
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    return conversation


@router.delete(
    "/{conversation_id}",
    response_model=DeleteConversationResponse,
)
def delete_conversation(
    conversation_id: str,
    workspace_id: str = Query(
        min_length=1
    ),
    current_user: User = Depends(
        get_current_user
    ),
):
    manager = get_conversation_manager(
        workspace_id=workspace_id.strip(),
        current_user=current_user,
        conversation_id=conversation_id,
    )

    deleted = manager.delete_conversation(
        conversation_id=conversation_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    return DeleteConversationResponse(
        deleted=True,
        conversation_id=conversation_id,
        active_conversation_id=(
            manager.conversation_id
        ),
    )