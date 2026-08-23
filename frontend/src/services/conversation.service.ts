import {
  api,
  getApiErrorMessage,
} from "../lib/api";

export interface ConversationMessage {
  id?: string;
  role: "user" | "assistant" | string;
  content?: string;
  message?: string;
  sources?: unknown[];
  created_at?: string;
}

export interface Conversation {
  id: string;
  workspace_id: string;
  user_id: string;
  title: string;
  status: string;
  created_at: string;
  updated_at: string;
  message_count?: number | null;
}

export interface ConversationDetail
  extends Conversation {
  messages: ConversationMessage[];
}

export interface CreateConversationRequest {
  workspace_id: string;
  title?: string;
}

export interface RenameConversationRequest {
  workspace_id: string;
  title: string;
}

export interface DeleteConversationResponse {
  deleted: boolean;
  conversation_id: string;
  active_conversation_id: string;
}

export async function listConversations(
  workspaceId: string,
  limit = 50
): Promise<Conversation[]> {
  try {
    const response = await api.get<
      Conversation[]
    >("/conversations", {
      params: {
        workspace_id: workspaceId,
        limit,
      },
    });

    return response.data;
  } catch (error) {
    throw new Error(
      getApiErrorMessage(
        error,
        "The conversations could not be loaded."
      )
    );
  }
}

export async function getConversation(
  workspaceId: string,
  conversationId: string
): Promise<ConversationDetail> {
  try {
    const response =
      await api.get<ConversationDetail>(
        `/conversations/${conversationId}`,
        {
          params: {
            workspace_id: workspaceId,
          },
        }
      );

    return response.data;
  } catch (error) {
    throw new Error(
      getApiErrorMessage(
        error,
        "The conversation could not be loaded."
      )
    );
  }
}

export async function createConversation(
  payload: CreateConversationRequest
): Promise<Conversation> {
  try {
    const response =
      await api.post<Conversation>(
        "/conversations",
        {
          workspace_id:
            payload.workspace_id,
          title:
            payload.title ||
            "New conversation",
        }
      );

    return response.data;
  } catch (error) {
    throw new Error(
      getApiErrorMessage(
        error,
        "The conversation could not be created."
      )
    );
  }
}

export async function renameConversation(
  conversationId: string,
  payload: RenameConversationRequest
): Promise<Conversation> {
  try {
    const response =
      await api.patch<Conversation>(
        `/conversations/${conversationId}`,
        payload
      );

    return response.data;
  } catch (error) {
    throw new Error(
      getApiErrorMessage(
        error,
        "The conversation could not be renamed."
      )
    );
  }
}

export async function deleteConversation(
  workspaceId: string,
  conversationId: string
): Promise<DeleteConversationResponse> {
  try {
    const response =
      await api.delete<DeleteConversationResponse>(
        `/conversations/${conversationId}`,
        {
          params: {
            workspace_id: workspaceId,
          },
        }
      );

    return response.data;
  } catch (error) {
    throw new Error(
      getApiErrorMessage(
        error,
        "The conversation could not be deleted."
      )
    );
  }
}

export function getLatestConversation(
  conversations: Conversation[]
): Conversation | null {
  if (
    !conversations ||
    conversations.length === 0
  ) {
    return null;
  }

  return [...conversations].sort(
    (first, second) => {
      const firstTimestamp =
        new Date(
          first.updated_at
        ).getTime();

      const secondTimestamp =
        new Date(
          second.updated_at
        ).getTime();

      return (
        secondTimestamp -
        firstTimestamp
      );
    }
  )[0];
}