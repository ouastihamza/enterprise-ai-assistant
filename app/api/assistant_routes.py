from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.auth_dependencies import get_current_user
from app.auth.user_model import User
from app.auth.user_service import UserService
from app.conversation import ConversationManager
from app.customers.customer_service import CustomerService
from app.services.rag_service import RAGService
from app.workspaces.workspace_service import WorkspaceService


router = APIRouter(
    prefix="/assistant",
    tags=["AI Assistant"],
)

user_service = UserService()
workspace_service = WorkspaceService()


class AssistantChatRequest(BaseModel):
    workspace_id: str = Field(
        min_length=1,
    )

    question: str = Field(
        min_length=1,
        max_length=20_000,
    )

    conversation_id: str | None = None
    customer_id: str | None = None


class AssistantChatResponse(BaseModel):
    conversation_id: str
    answer: str
    sources: list[dict]


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


@router.post(
    "/chat",
    response_model=AssistantChatResponse,
)
def chat_with_knowledge(
    request: AssistantChatRequest,
    current_user: User = Depends(get_current_user),
):
    workspace_id = request.workspace_id.strip()
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Question cannot be empty.",
        )

    ensure_workspace_access(
        current_user=current_user,
        workspace_id=workspace_id,
    )

    customer_context = None
    if request.customer_id:
        customer_service = CustomerService(workspace_id)
        customer_context = customer_service.build_assistant_context(request.customer_id)
        if customer_context is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found in this workspace.",
            )

    try:
        conversation_manager = ConversationManager(
            workspace_id=workspace_id,
            user_id=current_user.id,
            conversation_id=request.conversation_id,
        )

        conversation_history = (
            conversation_manager.get_llm_history(
                limit=10
            )
        )

        conversation_manager.add_user_message(
            question
        )

        rag_service = RAGService(
            workspace_id=workspace_id
        )

        result = (
            rag_service.answer_question_with_sources(
                question=question,
                customer_id=request.customer_id,
                customer_context=customer_context,
            )
        )

        answer = str(
            result.get(
                "answer",
                "",
            )
        ).strip()

        sources = result.get(
            "sources",
            [],
        )

        if not answer:
            answer = (
                "The assistant could not generate an answer "
                "for this request."
            )

        conversation_manager.add_assistant_message(
            message=answer,
            sources=sources,
        )

        return AssistantChatResponse(
            conversation_id=(
                conversation_manager.conversation_id
            ),
            answer=answer,
            sources=sources,
        )

    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "The AI assistant could not complete "
                "the request."
            ),
        ) from error
