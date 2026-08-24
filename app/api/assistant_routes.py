import json
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
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
    regenerate: bool = False


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

        assistant_message_id: str | None = None
        if request.regenerate:
            regeneration = conversation_manager.get_regeneration_context(limit=10)
            question = regeneration["question"]
            conversation_history = regeneration["conversation_history"]
            assistant_message_id = regeneration["assistant_message_id"]
        else:
            conversation_history = conversation_manager.get_llm_history(limit=10)
            conversation_manager.add_user_message(question)

        rag_service = RAGService(
            workspace_id=workspace_id
        )

        result = (
            rag_service.answer_question_with_sources(
                question=question,
                customer_id=request.customer_id,
                customer_context=customer_context,
                conversation_history=conversation_history,
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

        if assistant_message_id:
            conversation_manager.replace_assistant_message(
                message_id=assistant_message_id,
                message=answer,
                sources=sources,
            )
        else:
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


def _encode_stream_event(event: dict) -> str:
    return json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"


@router.post("/chat/stream")
def stream_chat_with_knowledge(
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
    ensure_workspace_access(current_user=current_user, workspace_id=workspace_id)

    customer_context = None
    if request.customer_id:
        customer_context = CustomerService(workspace_id).build_assistant_context(
            request.customer_id
        )
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
        assistant_message_id: str | None = None
        if request.regenerate:
            regeneration = conversation_manager.get_regeneration_context(limit=10)
            question = regeneration["question"]
            conversation_history = regeneration["conversation_history"]
            assistant_message_id = regeneration["assistant_message_id"]
        else:
            conversation_history = conversation_manager.get_llm_history(limit=10)
            conversation_manager.add_user_message(question)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    def event_stream() -> Iterator[str]:
        answer_parts: list[str] = []
        sources: list[dict] = []
        saved = False

        def save_answer() -> None:
            nonlocal saved
            answer = "".join(answer_parts).strip()
            if saved or not answer:
                return
            if assistant_message_id:
                conversation_manager.replace_assistant_message(
                    message_id=assistant_message_id,
                    message=answer,
                    sources=sources,
                )
            else:
                conversation_manager.add_assistant_message(
                    message=answer,
                    sources=sources,
                )
            saved = True

        try:
            yield _encode_stream_event(
                {
                    "type": "start",
                    "conversation_id": conversation_manager.conversation_id,
                }
            )
            yield _encode_stream_event(
                {"type": "status", "message": "Searching customer information…"}
            )
            rag_service = RAGService(workspace_id=workspace_id)
            for event in rag_service.stream_answer_question_with_sources(
                question=question,
                customer_id=request.customer_id,
                customer_context=customer_context,
                conversation_history=conversation_history,
            ):
                if event.get("type") == "delta":
                    answer_parts.append(str(event.get("delta", "")))
                elif event.get("type") == "metadata":
                    sources = event.get("sources", [])
                yield _encode_stream_event(event)
            save_answer()
            yield _encode_stream_event(
                {
                    "type": "complete",
                    "conversation_id": conversation_manager.conversation_id,
                    "answer": "".join(answer_parts).strip(),
                    "sources": sources,
                }
            )
        except GeneratorExit:
            save_answer()
            raise
        except Exception:
            save_answer()
            yield _encode_stream_event(
                {
                    "type": "error",
                    "message": "Atlas could not complete this answer. Please try again.",
                }
            )

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
