import {
  api,
  getApiErrorMessage,
} from "../lib/api";

export interface AssistantSource {
  // Display order
  rank: number;

  // Document information
  document_name: string;
  source_file?: string | null;
  file_extension?: string | null;

  // Chunk information
  chunk_id?: number | string | null;
  section_chunk_id?: number | null;

  // Relevance score
  score?: number | null;

  // Preview shown in the citation card
  preview: string;

  // PDF metadata
  page_number?: number | null;
  total_pages?: number | null;

  // Generic section metadata
  section_type?: string | null;
  section_number?: number | null;
  section_title?: string | null;

  // Optional heading
  heading?: string | null;

  // PowerPoint metadata
  slide_number?: number | null;

  // Spreadsheet metadata
  sheet_number?: number | null;
  sheet_name?: string | null;

  document_id?: number | null;
  category?: string | null;
  customer_id?: string | null;
  customer_name?: string | null;
  scope?: string | null;
}

export interface AssistantChatRequest {
  workspace_id: string;
  question: string;
  conversation_id?: string | null;
  customer_id?: string | null;
  regenerate?: boolean;
}

export interface AssistantChatResponse {
  conversation_id: string;
  answer: string;
  sources: AssistantSource[];
}

export type AssistantStreamEvent =
  | { type: "start"; conversation_id: string }
  | { type: "status"; message: string }
  | { type: "metadata"; sources: AssistantSource[] }
  | { type: "delta"; delta: string }
  | (AssistantChatResponse & { type: "complete" })
  | { type: "error"; message: string };

export async function streamAssistantMessage(
  payload: AssistantChatRequest,
  onEvent: (event: AssistantStreamEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("access_token")
      : null;
  const baseUrl = String(api.defaults.baseURL || "").replace(/\/$/, "");
  const response = await fetch(`${baseUrl}/assistant/chat/stream`, {
    method: "POST",
    headers: {
      Accept: "application/x-ndjson",
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    let message = "Atlas could not complete this request.";
    try {
      const body = (await response.json()) as { detail?: string };
      message = body.detail || message;
    } catch {
      // Keep the safe fallback when the response is not JSON.
    }
    throw new Error(message);
  }
  if (!response.body) {
    throw new Error("The assistant stream could not be opened.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffered = "";

  const emitLines = (text: string) => {
    buffered += text;
    const lines = buffered.split("\n");
    buffered = lines.pop() || "";
    for (const line of lines) {
      if (!line.trim()) continue;
      onEvent(JSON.parse(line) as AssistantStreamEvent);
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    emitLines(decoder.decode(value, { stream: true }));
  }
  emitLines(decoder.decode());
  if (buffered.trim()) {
    onEvent(JSON.parse(buffered) as AssistantStreamEvent);
  }
}

function isTimeoutError(error: unknown): boolean {
  if (typeof error !== "object" || error === null) {
    return false;
  }

  const anyError = error as {
    code?: string;
    message?: string;
  };

  return (
    anyError.code === "ECONNABORTED" ||
    Boolean(
      anyError.message
        ?.toLowerCase()
        .includes("timeout")
    )
  );
}

async function postChat(
  payload: AssistantChatRequest,
  timeoutMs?: number
): Promise<AssistantChatResponse> {
  const response =
    await api.post<AssistantChatResponse>(
      "/assistant/chat",
      payload,
      timeoutMs ? { timeout: timeoutMs } : undefined
    );

  return response.data;
}

export async function sendAssistantMessage(
  payload: AssistantChatRequest
): Promise<AssistantChatResponse> {
  try {
    return await postChat(payload);
  } catch (error) {
    if (!isTimeoutError(error)) {
      throw new Error(
        getApiErrorMessage(
          error,
          "The assistant could not complete this request."
        )
      );
    }

    // The first request after a cold start can be genuinely slow
    // (e.g. an embedding model loading for the first time) rather
    // than actually stuck. Retry once with a longer timeout instead
    // of surfacing the timeout to the user.
    try {
      return await postChat(payload, 90_000);
    } catch (retryError) {
      throw new Error(
        getApiErrorMessage(
          retryError,
          "The assistant could not complete this request."
        )
      );
    }
  }
}
