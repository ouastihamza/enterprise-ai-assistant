"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  AlertCircle,
  ArrowUp,
  Building2,
  ChevronDown,
  Copy,
  FileText,
  Loader2,
  MessageSquare,
  Plus,
  RefreshCw,
  Sparkles,
  Square,
  User,
} from "lucide-react";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";

import {
  PageTransition,
} from "../../../components/layout/page-transition";

import {
  useWorkspace,
} from "../../../hooks/use-workspace";

import {
  streamAssistantMessage,
  type AssistantSource,
} from "../../../services/assistant.service";
import { openDocument } from "../../../services/documents.service";

import {
  createConversation,
  getConversation,
  getLatestConversation,
  listConversations,
  type Conversation,
  type ConversationMessage,
} from "../../../services/conversation.service";

import { listCustomers } from "../../../services/customers.service";
import type { Customer } from "../../../types/customer.types";

type ChatRole = "user" | "assistant";

type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  sources?: AssistantSource[];
  isError?: boolean;
  isStreaming?: boolean;
};

function makeId(): string {
  return `${Date.now()}-${Math.random()
    .toString(36)
    .slice(2)}`;
}

function AssistantAvatar() {
  return (
    <div className="assistant-avatar assistant-avatar--bot">
      <Sparkles size={14} />
    </div>
  );
}

function UserAvatar() {
  return (
    <div className="assistant-avatar assistant-avatar--user">
      <User size={14} />
    </div>
  );
}

function getFriendlyDocumentName(
  documentName: string
): string {
  const cleanedName = documentName
    .split("/")
    .pop()
    ?.replace(/%20/g, " ")
    .replace(/\.pdf#page\.pdf$/i, ".pdf")
    .replace(/_/g, " ")
    .trim();

  return cleanedName || "Unknown document";
}

function getSourceLocation(
  source: AssistantSource
): string | null {
  if (source.page_number != null) {
    if (source.total_pages != null) {
      return `Page ${source.page_number} of ${source.total_pages}`;
    }

    return `Page ${source.page_number}`;
  }

  if (source.slide_number != null) {
    return `Slide ${source.slide_number}`;
  }

  if (source.sheet_name) {
    return `Sheet: ${source.sheet_name}`;
  }

  if (source.sheet_number != null) {
    return `Sheet ${source.sheet_number}`;
  }

  if (source.section_title) {
    return source.section_title;
  }

  if (source.section_number != null) {
    return `Section ${source.section_number}`;
  }

  return null;
}

function getSourceScore(
  score?: number | null
): string | null {
  if (
    score == null ||
    Number.isNaN(score)
  ) {
    return null;
  }

  const percentage = Math.max(
    0,
    Math.min(
      100,
      Math.round(score * 100)
    )
  );

  return `${percentage}% match`;
}

function isAssistantSource(
  value: unknown
): value is AssistantSource {
  if (
    !value ||
    typeof value !== "object"
  ) {
    return false;
  }

  const source =
    value as Partial<AssistantSource>;

  return (
    typeof source.document_name ===
      "string" &&
    typeof source.rank === "number"
  );
}

function normalizeSources(
  sources: unknown
): AssistantSource[] {
  if (!Array.isArray(sources)) {
    return [];
  }

  return sources.filter(
    isAssistantSource
  );
}

function normalizeStoredMessage(
  message: ConversationMessage,
  index: number
): ChatMessage | null {
  if (
    message.role !== "user" &&
    message.role !== "assistant"
  ) {
    return null;
  }

  const contentCandidate =
    typeof message.content === "string"
      ? message.content
      : typeof message.message ===
          "string"
        ? message.message
        : "";

  const content =
    contentCandidate.trim();

  if (!content) {
    return null;
  }

  const sources =
    message.role === "assistant"
      ? normalizeSources(
          message.sources
        )
      : [];

  return {
    id:
      message.id ||
      `stored-${index}-${makeId()}`,
    role: message.role,
    content,
    sources:
      sources.length > 0
        ? sources
        : undefined,
  };
}

function formatConversationDate(
  dateValue: string
): string {
  const date = new Date(dateValue);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const now = new Date();

  const isToday =
    date.getFullYear() ===
      now.getFullYear() &&
    date.getMonth() ===
      now.getMonth() &&
    date.getDate() ===
      now.getDate();

  if (isToday) {
    return date.toLocaleTimeString(
      [],
      {
        hour: "2-digit",
        minute: "2-digit",
      }
    );
  }

  return date.toLocaleDateString(
    [],
    {
      month: "short",
      day: "numeric",
    }
  );
}

function SourcesList({
  sources,
  workspaceId,
}: {
  sources: AssistantSource[];
  workspaceId?: string;
}) {
  const [
    isPanelOpen,
    setIsPanelOpen,
  ] = useState(false);

  const [
    expandedSourceIndex,
    setExpandedSourceIndex,
  ] = useState<number | null>(
    null
  );

  const [openError, setOpenError] = useState<string | null>(null);

  const sortedSources = [
    ...sources,
  ].sort(
    (a, b) =>
      (b.score ?? 0) -
      (a.score ?? 0)
  );

  if (sortedSources.length === 0) {
    return null;
  }

  return (
    <div className="assistant-sources">
      <button
        type="button"
        className="assistant-sources-button"
        onClick={() => {
          setIsPanelOpen(
            (current) => {
              const next = !current;

              if (!next) {
                setExpandedSourceIndex(
                  null
                );
              }

              return next;
            }
          );
        }}
      >
        <FileText size={14} />
        <span>
          Sources ·{" "}
          {sortedSources.length}
        </span>
        <ChevronDown
          size={15}
          className={
            isPanelOpen
              ? "rotate"
              : ""
          }
        />
      </button>

      {isPanelOpen && (
        <div className="assistant-sources-panel">
          {sortedSources.map(
            (
              source,
              index
            ) => {
              const location =
                getSourceLocation(
                  source
                );

              const score =
                getSourceScore(
                  source.score
                );

              const isSourceExpanded =
                expandedSourceIndex ===
                index;

              return (
                <div
                  key={`${source.document_name}-${source.chunk_id ?? index}`}
                  className="assistant-source-card"
                >
                  <button
                    type="button"
                    className="assistant-source-row"
                    onClick={() =>
                      setExpandedSourceIndex(
                        (
                          current
                        ) =>
                          current ===
                          index
                            ? null
                            : index
                      )
                    }
                  >
                    <div>
                      <strong>
                        {getFriendlyDocumentName(
                          source.document_name
                        )}
                      </strong>

                      <div className="assistant-source-row-meta">
                        {source.category && (
                          <span>{source.category}</span>
                        )}

                        {source.category && (location || score) && <span>•</span>}

                        {location && (
                          <span>
                            {
                              location
                            }
                          </span>
                        )}

                        {location &&
                          score && (
                            <span>
                              •
                            </span>
                          )}

                        {score && (
                          <span>
                            {
                              score
                            }
                          </span>
                        )}
                      </div>

                      {source.customer_name && (
                        <span className="assistant-source-customer">
                          {source.customer_name}
                        </span>
                      )}
                    </div>

                    <ChevronDown
                      size={14}
                      className={
                        isSourceExpanded
                          ? "rotate"
                          : ""
                      }
                    />
                  </button>

                  {isSourceExpanded && (
                    <div className="assistant-source-preview">
                      {source.section_title && (
                        <div className="assistant-source-heading">
                          {source.section_title}
                        </div>
                      )}

                      {source.heading && (
                        <div className="assistant-source-subheading">
                          {source.heading}
                        </div>
                      )}

                      <blockquote>
                        {source.preview ??
                          "No preview available."}
                      </blockquote>

                      {source.document_id != null && workspaceId && (
                        <button
                          type="button"
                          className="assistant-source-open"
                          onClick={() => {
                            setOpenError(null);
                            void openDocument(
                              workspaceId,
                              source.document_id as number,
                              source.document_name
                            ).catch((error) => {
                              setOpenError(
                                error instanceof Error
                                  ? error.message
                                  : "Couldn't open that document."
                              );
                            });
                          }}
                        >
                          Open original
                        </button>
                      )}
                    </div>
                  )}
                </div>
              );
            }
          )}
          {openError && (
            <p className="assistant-source-error">{openError}</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function AssistantPage() {
  const {
    activeWorkspace,
    settings,
  } = useWorkspace();

  const assistantName = "Atlas Assistant";

  const welcomeMessage =
    settings?.welcome_message ||
    "Ask Atlas about customer profiles, contracts, invoices and consumption.";

  const workspaceId =
    activeWorkspace?.id;

  const [messages, setMessages] =
    useState<ChatMessage[]>([]);

  const [
    conversationId,
    setConversationId,
  ] = useState<string | null>(
    null
  );

  const [
    conversations,
    setConversations,
  ] = useState<Conversation[]>([]);

  const [
    isLoadingConversations,
    setIsLoadingConversations,
  ] = useState(false);

  const [
    isSwitchingConversation,
    setIsSwitchingConversation,
  ] = useState(false);

  const [
    isCreatingConversation,
    setIsCreatingConversation,
  ] = useState(false);

  const [
    loadingConversationId,
    setLoadingConversationId,
  ] = useState<string | null>(
    null
  );

  const [input, setInput] =
    useState("");

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState("");
  const [isLoadingCustomers, setIsLoadingCustomers] = useState(false);
  const [customerLoadError, setCustomerLoadError] = useState(false);

  const selectedCustomer = customers.find(
    (customer) => customer.id === selectedCustomerId
  );

  const [
    isSending,
    setIsSending,
  ] = useState(false);

  const [streamStatus, setStreamStatus] = useState("Preparing answer…");
  const activeRequestRef = useRef<AbortController | null>(null);

  const [
    isLoadingConversation,
    setIsLoadingConversation,
  ] = useState(false);

  const [
    conversationLoadError,
    setConversationLoadError,
  ] = useState<string | null>(
    null
  );

  const chatContainerRef =
    useRef<HTMLDivElement>(null);

  const textareaRef =
    useRef<HTMLTextAreaElement>(
      null
    );

  const conversationLoadRequestRef =
    useRef(0);

  const conversationSwitchRequestRef =
    useRef(0);

  const shouldAutoScrollRef = useRef(true);

  const scrollToBottom = (behavior: ScrollBehavior = "smooth") => {
    const container = chatContainerRef.current;
    if (!container) return;
    container.scrollTo({
      top: container.scrollHeight,
      behavior,
    });
  };

  const refreshConversationList =
    async (): Promise<Conversation[]> => {
      const currentWorkspaceId = workspaceId;

      if (!currentWorkspaceId) {
        setConversations([]);
        return [];
      }

      const loadedConversations =
        await listConversations(
          currentWorkspaceId,
          50
        );

      if (workspaceId !== currentWorkspaceId) {
        return [];
      }

      const sortedConversations = [
        ...loadedConversations,
      ].sort(
        (a, b) =>
          new Date(b.updated_at).getTime() -
          new Date(a.updated_at).getTime()
      );

      setConversations(
        sortedConversations
      );

      return sortedConversations;
    };

  const loadConversationById =
    async (
      selectedConversationId: string
    ) => {
      if (
        !workspaceId ||
        isSending ||
        isSwitchingConversation ||
        isCreatingConversation
      ) {
        return;
      }

      if (
        selectedConversationId ===
        conversationId
      ) {
        return;
      }

      const requestId =
        conversationSwitchRequestRef.current +
        1;
      conversationSwitchRequestRef.current =
        requestId;

      setIsSwitchingConversation(true);
      setLoadingConversationId(
        selectedConversationId
      );
      setConversationLoadError(null);
      setInput("");

      shouldAutoScrollRef.current = true;

      try {
        const conversation =
          await getConversation(
            workspaceId,
            selectedConversationId
          );

        if (
          conversationSwitchRequestRef.current !==
          requestId
        ) {
          return;
        }

        const restoredMessages =
          conversation.messages
            .map(
              (
                message,
                index
              ) =>
                normalizeStoredMessage(
                  message,
                  index
                )
            )
            .filter(
              (
                message
              ): message is ChatMessage =>
                message !== null
            );

        setConversationId(
          conversation.id
        );

        setMessages(
          restoredMessages
        );

        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            scrollToBottom("auto");
            textareaRef.current?.focus();
          });
        });
      } catch (error) {
        if (
          conversationSwitchRequestRef.current !==
          requestId
        ) {
          return;
        }

        setConversationLoadError(
          error instanceof Error
            ? error.message
            : "The conversation could not be loaded."
        );
      } finally {
        if (
          conversationSwitchRequestRef.current ===
          requestId
        ) {
          setIsSwitchingConversation(
            false
          );
          setLoadingConversationId(
            null
          );
        }
      }
    };

  const startNewConversation =
    async () => {
      if (
        isSending ||
        isLoadingConversation ||
        isSwitchingConversation ||
        isCreatingConversation ||
        !workspaceId
      ) {
        return;
      }

      setIsCreatingConversation(true);
      setConversationLoadError(null);

      try {
        const newConv = await createConversation({
          workspace_id: workspaceId,
          title: "New conversation",
        });

        setConversationId(
          newConv.id
        );

        setMessages([]);
        setInput("");
        shouldAutoScrollRef.current =
          true;

        setConversations((current) => [
          newConv,
          ...current.filter(
            (c) => c.id !== newConv.id
          ),
        ]);

        requestAnimationFrame(() => {
          resizeTextarea();
          textareaRef.current?.focus();
        });

        void refreshConversationList();
      } catch (error) {
        setConversationLoadError(
          error instanceof Error
            ? error.message
            : "Could not create a new conversation."
        );
      } finally {
        setIsCreatingConversation(
          false
        );
        setLoadingConversationId(null);
      }
    };

  useEffect(() => {
    const container = chatContainerRef.current;

    if (!container) return;

    const handleScroll = () => {
      const threshold = 100;

      shouldAutoScrollRef.current =
        container.scrollHeight -
          container.scrollTop -
          container.clientHeight <=
        threshold;
    };

    handleScroll();

    container.addEventListener(
      "scroll",
      handleScroll
    );

    return () => {
      container.removeEventListener(
        "scroll",
        handleScroll
      );
    };
  }, []);

  useEffect(() => {
    if (isLoadingConversation) {
      scrollToBottom("auto");
      return;
    }

    if (shouldAutoScrollRef.current) {
      scrollToBottom("smooth");
    }
  }, [
    messages,
    isSending,
    isLoadingConversation,
  ]);

  useEffect(() => {
    const requestId =
      conversationLoadRequestRef.current +
      1;

    conversationLoadRequestRef.current =
      requestId;

    setMessages([]);
    setConversations([]);
    setConversationId(null);
    setConversationLoadError(null);
    setInput("");

    shouldAutoScrollRef.current = true;

    if (!workspaceId) {
      setIsLoadingConversation(false);
      setIsLoadingConversations(false);
      return;
    }

    const loadWorkspaceConversations =
      async () => {
        setIsLoadingConversation(true);
        setIsLoadingConversations(true);

        try {
          const loadedConversations =
            await listConversations(
              workspaceId,
              50
            );

          const sortedConversations = [
            ...loadedConversations,
          ].sort(
            (a, b) =>
              new Date(
                b.updated_at
              ).getTime() -
              new Date(
                a.updated_at
              ).getTime()
          );

          if (
            conversationLoadRequestRef.current !==
            requestId
          ) {
            return;
          }

          setConversations(
            sortedConversations
          );

          const latestConversation =
            getLatestConversation(
              sortedConversations
            );

          if (!latestConversation) {
            setMessages([]);
            setConversationId(null);
            return;
          }

          const conversation =
            await getConversation(
              workspaceId,
              latestConversation.id
            );

          if (
            conversationLoadRequestRef.current !==
            requestId
          ) {
            return;
          }

          const restoredMessages =
            conversation.messages
              .map(
                (
                  message,
                  index
                ) =>
                  normalizeStoredMessage(
                    message,
                    index
                  )
              )
              .filter(
                (
                  message
                ): message is ChatMessage =>
                  message !== null
              );

          setConversationId(
            conversation.id
          );

          setMessages(
            restoredMessages
          );
        } catch (error) {
          if (
            conversationLoadRequestRef.current !==
            requestId
          ) {
            return;
          }

          setMessages([]);
          setConversations([]);
          setConversationId(null);

          setConversationLoadError(
            error instanceof Error
              ? error.message
              : "The previous conversation could not be restored."
          );
        } finally {
          if (
            conversationLoadRequestRef.current ===
            requestId
          ) {
            setIsLoadingConversation(
              false
            );

            setIsLoadingConversations(
              false
            );
          }
        }
      };

    void loadWorkspaceConversations();
  }, [workspaceId]);

  useEffect(() => {
    setCustomers([]);
    setSelectedCustomerId("");
    setCustomerLoadError(false);
    setIsLoadingCustomers(false);
    if (!workspaceId) return;
    let isCurrent = true;
    setIsLoadingCustomers(true);
    void listCustomers(workspaceId)
      .then((items) => {
        if (!isCurrent) return;
        setCustomers(items);
        const requestedCustomerId = new URLSearchParams(window.location.search).get("customer");
        const requestedCustomer = items.find((item) => item.id === requestedCustomerId);
        const demo = items.find((item) => item.company_name === "Demo Industrie SAS");
        if (requestedCustomer) {
          setSelectedCustomerId(requestedCustomer.id);
        } else if (demo) {
          setSelectedCustomerId(demo.id);
        }
      })
      .catch(() => {
        if (isCurrent) {
          setCustomers([]);
          setCustomerLoadError(true);
        }
      })
      .finally(() => {
        if (isCurrent) setIsLoadingCustomers(false);
      });
    return () => { isCurrent = false; };
  }, [workspaceId]);

  const resizeTextarea = () => {
    const element =
      textareaRef.current;

    if (!element) {
      return;
    }

    element.style.height =
      "auto";

    element.style.height = `${Math.min(
      element.scrollHeight,
      180
    )}px`;
  };

  const runAssistantStream = async ({
    question,
    assistantMessageId,
    regenerate = false,
    fallbackContent = "",
  }: {
    question: string;
    assistantMessageId: string;
    regenerate?: boolean;
    fallbackContent?: string;
  }) => {
    if (!workspaceId) return;
    const controller = new AbortController();
    activeRequestRef.current = controller;
    setIsSending(true);
    setStreamStatus("Searching customer information…");

    try {
      await streamAssistantMessage(
        {
          workspace_id: workspaceId,
          question,
          conversation_id: conversationId,
          customer_id: selectedCustomerId || null,
          regenerate,
        },
        (event) => {
          if (event.type === "start") {
            setConversationId(event.conversation_id);
          } else if (event.type === "status") {
            setStreamStatus(event.message);
          } else if (event.type === "metadata") {
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantMessageId
                  ? { ...message, sources: event.sources }
                  : message
              )
            );
          } else if (event.type === "delta") {
            setStreamStatus("Writing grounded answer…");
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantMessageId
                  ? {
                      ...message,
                      content: message.content + event.delta,
                      isStreaming: true,
                    }
                  : message
              )
            );
          } else if (event.type === "complete") {
            setConversationId(event.conversation_id);
            setMessages((current) =>
              current.map((message) =>
                message.id === assistantMessageId
                  ? {
                      ...message,
                      content: event.answer || message.content,
                      sources: event.sources,
                      isStreaming: false,
                    }
                  : message
              )
            );
          } else if (event.type === "error") {
            throw new Error(event.message);
          }
        },
        controller.signal
      );
      try {
        await refreshConversationList();
      } catch {
        // The answer remains usable if only the sidebar refresh fails.
      }
    } catch (error) {
      const wasStopped =
        error instanceof DOMException && error.name === "AbortError";
      setMessages((current) =>
        current.map((message) =>
          message.id === assistantMessageId
            ? {
                ...message,
                content:
                  message.content ||
                  fallbackContent ||
                  (wasStopped
                    ? "Generation stopped."
                    : error instanceof Error
                      ? error.message
                      : "Atlas could not complete this request."),
                isError: !wasStopped && !fallbackContent,
                isStreaming: false,
              }
            : message
        )
      );
    } finally {
      activeRequestRef.current = null;
      setIsSending(false);
      requestAnimationFrame(() => textareaRef.current?.focus());
    }
  };

  const sendMessage = async () => {
    const question = input.trim();
    if (
      !question ||
      isSending ||
      isLoadingConversation ||
      isSwitchingConversation ||
      isCreatingConversation ||
      !workspaceId
    ) {
      return;
    }

    const assistantMessageId = makeId();
    setInput("");
    setConversationLoadError(null);
    shouldAutoScrollRef.current = true;
    requestAnimationFrame(resizeTextarea);
    setMessages((current) => [
      ...current,
      { id: makeId(), role: "user", content: question },
      {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        isStreaming: true,
      },
    ]);
    await runAssistantStream({ question, assistantMessageId });
  };

  const regenerateLastAnswer = async () => {
    if (isSending || !conversationId) return;
    const assistantIndex = messages.findLastIndex(
      (message) => message.role === "assistant" && !message.isError
    );
    const userMessage = [...messages.slice(0, assistantIndex)]
      .reverse()
      .find((message) => message.role === "user");
    if (assistantIndex < 0 || !userMessage) return;
    const assistantMessage = messages[assistantIndex];
    setMessages((current) =>
      current.map((message) =>
        message.id === assistantMessage.id
          ? { ...message, content: "", sources: [], isStreaming: true }
          : message
      )
    );
    await runAssistantStream({
      question: userMessage.content,
      assistantMessageId: assistantMessage.id,
      regenerate: true,
      fallbackContent: assistantMessage.content,
    });
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      void sendMessage();
    }
  };

  const suggestedPrompts = selectedCustomerId
    ? [
        "Why was February more expensive than January?",
        "Summarize this customer's contract.",
        "Compare January and February consumption.",
      ]
    : [
        "What's covered in our onboarding docs?",
        "Summarize our latest policy updates.",
        "What does the knowledge base say about pricing?",
      ];

  const composerDisabled =
    isSending ||
    isLoadingConversation ||
    isSwitchingConversation ||
    isCreatingConversation ||
    !workspaceId;

  return (
    <PageTransition className="platform-page assistant-page">
      <section className="dashboard-intro">
        <div>
          <span className="platform-eyebrow">
            <Sparkles size={14} />
            {assistantName}
          </span>

          <h1>{assistantName}</h1>
        </div>

        <p>
          {selectedCustomer
            ? `Ask about ${selectedCustomer.company_name}'s profile, sites and documents.`
            : welcomeMessage}
        </p>
      </section>

      <div className="assistant-workspace">
        <aside className="assistant-conversations">
          <div className="assistant-conversations__header">
            <span>Conversations</span>

            <button
              type="button"
              className="assistant-new-conversation"
              onClick={() => {
                void startNewConversation();
              }}
              disabled={
                isSending ||
                isLoadingConversation ||
                isSwitchingConversation ||
                isCreatingConversation ||
                !workspaceId
              }
              aria-label="Start new conversation"
            >
              {isCreatingConversation ? (
                <Loader2
                  size={15}
                  className="assistant-spin"
                />
              ) : (
                <Plus size={15} />
              )}
              <span>New</span>
            </button>
          </div>

          <div className="assistant-conversations__list">
            {isLoadingConversations && (
              <div className="assistant-conversations__status">
                <Loader2
                  size={15}
                  className="assistant-spin"
                />

                <span>
                  Loading conversations...
                </span>
              </div>
            )}

            {!isLoadingConversations &&
              conversations.length ===
                0 && (
                <div className="assistant-conversations__empty">
                  <MessageSquare
                    size={17}
                  />

                  <span>
                    Start a new conversation to begin asking questions.
                  </span>
                </div>
              )}

            {!isLoadingConversations &&
              conversations.map(
                (conversation) => {
                  const isActive =
                    conversation.id ===
                    conversationId;

                  const isItemLoading =
                    loadingConversationId ===
                    conversation.id;

                  const titleText =
                    conversation.title ||
                    "New conversation";

                  return (
                    <button
                      key={
                        conversation.id
                      }
                      type="button"
                      className={[
                        "assistant-conversation-item",
                        isActive
                          ? "assistant-conversation-item--active"
                          : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                      onClick={() => {
                        void loadConversationById(
                          conversation.id
                        );
                      }}
                      disabled={
                        isSending ||
                        isSwitchingConversation ||
                        isCreatingConversation
                      }
                    >
                      <MessageSquare
                        size={14}
                      />

                      <span
                        className="assistant-conversation-item__content"
                        title={titleText}
                      >
                        <strong>
                          {titleText}
                        </strong>

                        <small>
                          {formatConversationDate(
                            conversation.updated_at
                          )}
                        </small>
                      </span>

                      {isItemLoading && (
                        <Loader2
                          size={13}
                          className="assistant-spin"
                        />
                      )}
                    </button>
                  );
                }
              )}
          </div>
        </aside>

        <section className="assistant-chat">
          <div ref={chatContainerRef} className="assistant-chat__messages">
            {isLoadingConversation && (
              <div className="assistant-loading-history">
                <Loader2
                  size={16}
                  className="assistant-spin"
                />

                <span>
                  Loading your conversation...
                </span>
              </div>
            )}

            {!isLoadingConversation &&
              conversationLoadError && (
                <div className="assistant-history-error">
                  <AlertCircle
                    size={15}
                  />

                  <span>
                    {
                      conversationLoadError
                    }
                  </span>
                </div>
              )}

            {!isLoadingConversation &&
              messages.length === 0 && (
                <div className="assistant-empty">
                  <AssistantAvatar />

                  <div className="assistant-empty__content">
                    <strong>
                      {selectedCustomer
                        ? "Choose a suggested question or ask anything about this customer's information."
                        : welcomeMessage}
                    </strong>

                    <div className="assistant-empty__prompts">
                      {suggestedPrompts.map(
                        (prompt) => (
                          <button
                            key={prompt}
                            type="button"
                            className="assistant-prompt-chip"
                            onClick={() => {
                              setInput(
                                prompt
                              );

                              requestAnimationFrame(
                                () => {
                                  resizeTextarea();
                                  textareaRef.current?.focus();
                                }
                              );
                            }}
                          >
                            {prompt}
                          </button>
                        )
                      )}
                    </div>
                  </div>
                </div>
              )}

            {!isLoadingConversation &&
              messages.map(
                (message, messageIndex) => (
                  <div
                    key={message.id}
                    className={[
                      "assistant-message",
                      `assistant-message--${message.role}`,
                    ].join(" ")}
                  >
                    {message.role ===
                    "assistant" ? (
                      <AssistantAvatar />
                    ) : (
                      <UserAvatar />
                    )}

                    <div className="assistant-message__body">
                      <div
                        className={[
                          "assistant-bubble",
                          message.isError
                            ? "assistant-bubble--error"
                            : "",
                        ]
                          .filter(
                            Boolean
                          )
                          .join(" ")}
                      >
                        {message.isError ? (
                          <div className="assistant-bubble__error-row">
                            <AlertCircle
                              size={14}
                            />

                            <span>
                              {
                                message.content
                              }
                            </span>
                          </div>
                        ) : message.isStreaming && !message.content ? (
                          <div className="assistant-bubble__status">
                            <Loader2 size={14} className="assistant-spin" />
                            <span>{streamStatus}</span>
                          </div>
                        ) : (
                          <div className="assistant-markdown">
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              rehypePlugins={[rehypeHighlight]}
                              components={{
                                table({ children }) {
                                  return (
                                    <div className="assistant-table-wrap">
                                      <table>{children}</table>
                                    </div>
                                  );
                                },
                              }}
                            >
                              {message.content}
                            </ReactMarkdown>
                          </div>
                        )}
                      </div>

                      {message.sources &&
                        message.sources
                          .length >
                          0 && (
                          <SourcesList
                            sources={
                              message.sources
                            }
                            workspaceId={workspaceId}
                          />
                        )}

                      {message.role === "assistant" &&
                        !message.isError &&
                        !message.isStreaming &&
                        message.content && (
                          <div className="assistant-message-actions">
                            <button
                              type="button"
                              onClick={() => void navigator.clipboard.writeText(message.content)}
                              aria-label="Copy answer"
                            >
                              <Copy size={13} /> Copy
                            </button>
                            {messageIndex === messages.length - 1 && (
                              <button
                                type="button"
                                onClick={() => void regenerateLastAnswer()}
                                disabled={isSending}
                                aria-label="Regenerate answer"
                              >
                                <RefreshCw size={13} /> Regenerate
                              </button>
                            )}
                          </div>
                        )}
                    </div>
                  </div>
                )
              )}

          </div>

          <div className="assistant-composer">
            <div className="assistant-customer-context">
              <Building2 size={15} />
              <label htmlFor="assistant-customer">Customer</label>
              <select
                id="assistant-customer"
                value={selectedCustomerId}
                onChange={(event) => setSelectedCustomerId(event.target.value)}
                disabled={isSending}
              >
                <option value="">
                  {isLoadingCustomers ? "Loading customers…" : "All company information"}
                </option>
                {customers.map((customer) => (
                  <option key={customer.id} value={customer.id}>{customer.company_name}</option>
                ))}
              </select>
              {selectedCustomerId && <span>Using profile details and documents</span>}
              {customerLoadError && <span className="assistant-customer-context__error">Customer list unavailable</span>}
            </div>
            <div className="assistant-composer__inner">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  resizeTextarea();
                }}
                onKeyDown={handleKeyDown}
                placeholder={selectedCustomer ? `Ask about ${selectedCustomer.company_name}...` : "Ask about company information..."}
                rows={1}
                disabled={composerDisabled}
              />

              <button
                type="button"
                className={isSending ? "assistant-send-button assistant-send-button--stop" : "assistant-send-button"}
                onClick={() => {
                  if (isSending) activeRequestRef.current?.abort();
                  else void sendMessage();
                }}
                disabled={!isSending && (composerDisabled || !input.trim())}
                aria-label={isSending ? "Stop generating" : "Send message"}
              >
                {isSending ? <Square size={14} /> : <ArrowUp size={16} />}
              </button>
            </div>
          </div>
        </section>
      </div>
    </PageTransition>
  );
}
