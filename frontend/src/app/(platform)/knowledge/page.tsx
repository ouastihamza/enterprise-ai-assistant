"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  AlertCircle,
  CheckCircle2,
  File,
  FileSpreadsheet,
  FileText,
  Loader2,
  Sparkles,
  Trash2,
  UploadCloud,
  X,
} from "lucide-react";

import {
  PageTransition,
} from "../../../components/layout/page-transition";

import {
  useWorkspace,
} from "../../../hooks/use-workspace";

import {
  deleteDocument,
  listDocuments,
  uploadDocument,
} from "../../../services/documents.service";

import type {
  KnowledgeDocument,
} from "../../../types/document.types";

type PendingUpload = {
  id: string;
  file: File;
  error: string | null;
};

const ALLOWED_FILE_TYPES_FALLBACK = [
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
];

function extensionOf(name: string): string {
  const parts = name.split(".");
  return parts.length > 1
    ? parts[parts.length - 1].toLowerCase()
    : "";
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 KB";
  const units = ["B", "KB", "MB", "GB"];
  const exponent = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1
  );
  const value = bytes / Math.pow(1024, exponent);
  return `${
    exponent === 0 ? value : value.toFixed(1)
  } ${units[exponent]}`;
}

function formatDate(
  isoString: string | null
): string {
  if (!isoString) return "—";

  try {
    return new Date(isoString).toLocaleDateString(
      undefined,
      {
        month: "short",
        day: "numeric",
        year: "numeric",
      }
    );
  } catch {
    return isoString;
  }
}

function FileTypeIcon({ type }: { type: string }) {
  const normalized = type.toLowerCase();

  if (["csv", "xlsx", "xls"].includes(normalized)) {
    return <FileSpreadsheet size={17} />;
  }

  if (
    ["json", "xml", "html", "htm"].includes(
      normalized
    )
  ) {
    return <File size={17} />;
  }

  return <FileText size={17} />;
}

function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();

  if (normalized === "processing") {
    return (
      <span className="knowledge-status knowledge-status--processing">
        <Loader2
          size={13}
          className="knowledge-status__spin"
        />
        Processing
      </span>
    );
  }

  if (normalized === "failed") {
    return (
      <span className="knowledge-status knowledge-status--failed">
        <AlertCircle size={13} />
        Failed
      </span>
    );
  }

  return (
    <span className="knowledge-status knowledge-status--ready">
      <CheckCircle2 size={13} />
      Ready
    </span>
  );
}

export default function KnowledgePage() {
  const { activeWorkspace, settings } = useWorkspace();

  const allowedFileTypes: string[] =
    settings?.allowed_file_types?.length
      ? settings.allowed_file_types
      : ALLOWED_FILE_TYPES_FALLBACK;

  const [documents, setDocuments] = useState<
    KnowledgeDocument[]
  >([]);
  const [isLoadingDocuments, setIsLoadingDocuments] =
    useState(true);
  const [loadError, setLoadError] = useState<
    string | null
  >(null);
  const [pendingUploads, setPendingUploads] = useState<
    PendingUpload[]
  >([]);
  const [isDragActive, setIsDragActive] =
    useState(false);
  const [deletingId, setDeletingId] = useState<
    number | null
  >(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCounter = useRef(0);

  const workspaceId = activeWorkspace?.id;

  const loadDocuments = useCallback(async () => {
    if (!workspaceId) return;

    setIsLoadingDocuments(true);
    setLoadError(null);

    try {
      const data = await listDocuments(workspaceId);
      setDocuments(data);
    } catch (error) {
      setLoadError(
        error instanceof Error
          ? error.message
          : "Couldn't load your documents."
      );
    } finally {
      setIsLoadingDocuments(false);
    }
  }, [workspaceId]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const uploadOne = useCallback(
    async (file: File) => {
      if (!workspaceId) return;

      const uploadId = `${file.name}-${file.lastModified}-${Math.random()
        .toString(36)
        .slice(2)}`;

      setPendingUploads((current) => [
        ...current,
        { id: uploadId, file, error: null },
      ]);

      try {
        await uploadDocument(workspaceId, file);

        setPendingUploads((current) =>
          current.filter(
            (item) => item.id !== uploadId
          )
        );

        await loadDocuments();
      } catch (error) {
        setPendingUploads((current) =>
          current.map((item) =>
            item.id === uploadId
              ? {
                  ...item,
                  error:
                    error instanceof Error
                      ? error.message
                      : "Upload failed. Please try again.",
                }
              : item
          )
        );
      }
    },
    [workspaceId, loadDocuments]
  );

  const handleFiles = useCallback(
    (fileList: FileList | null) => {
      if (!fileList) return;

      Array.from(fileList).forEach((file) => {
        const ext = extensionOf(file.name);

        if (!allowedFileTypes.includes(ext)) {
          setPendingUploads((current) => [
            ...current,
            {
              id: `${file.name}-${Math.random()
                .toString(36)
                .slice(2)}`,
              file,
              error: `.${ext || "unknown"} isn't a supported file type.`,
            },
          ]);
          return;
        }

        uploadOne(file);
      });
    },
    [allowedFileTypes, uploadOne]
  );

  const handleDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      dragCounter.current = 0;
      setIsDragActive(false);
      handleFiles(event.dataTransfer.files);
    },
    [handleFiles]
  );

  const handleDragEnter = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      dragCounter.current += 1;
      setIsDragActive(true);
    },
    []
  );

  const handleDragLeave = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      dragCounter.current -= 1;
      if (dragCounter.current <= 0) {
        setIsDragActive(false);
      }
    },
    []
  );

  const dismissPendingError = (id: string) => {
    setPendingUploads((current) =>
      current.filter((item) => item.id !== id)
    );
  };

  const handleDelete = async (
    documentId: number
  ) => {
    if (!workspaceId) return;

    setDeletingId(documentId);

    try {
      await deleteDocument(workspaceId, documentId);

      setDocuments((current) =>
        current.filter(
          (doc) => doc.id !== documentId
        )
      );
    } catch (error) {
      setLoadError(
        error instanceof Error
          ? error.message
          : "Couldn't remove that file."
      );
    } finally {
      setDeletingId(null);
    }
  };

  const activeUploadCount = pendingUploads.filter(
    (item) => !item.error
  ).length;

  return (
    <PageTransition className="platform-page knowledge-page">
      <section className="dashboard-intro">
        <div>
          <span className="platform-eyebrow">
            <Sparkles size={14} />
            Company knowledge
          </span>

          <h1>
            Company documents
            <span>
              {" "}
              for{" "}
              {activeWorkspace?.company_name ||
                "your workspace"}
              .
            </span>
          </h1>
        </div>

        <p>
          Upload contracts, invoices, consumption records
          and procedures so the assistant can use them in
          clear, sourced answers.
        </p>
      </section>

      <section
        className={[
          "knowledge-dropzone",
          isDragActive
            ? "knowledge-dropzone--active"
            : "",
        ]
          .filter(Boolean)
          .join(" ")}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={(event) => event.preventDefault()}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(event) => {
          if (
            event.key === "Enter" ||
            event.key === " "
          ) {
            fileInputRef.current?.click();
          }
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="knowledge-dropzone__input"
          onChange={(event) => {
            handleFiles(event.target.files);
            event.target.value = "";
          }}
        />

        <div className="knowledge-dropzone__icon">
          <UploadCloud size={26} />
        </div>

        <strong>
          Drop files here or click to upload
        </strong>

        <span className="knowledge-dropzone__hint">
          Supports {allowedFileTypes
            .join(", ")
            .toUpperCase()}
        </span>
      </section>

      {pendingUploads.length > 0 && (
        <section className="knowledge-pending">
          {pendingUploads.map((item) => (
            <div
              key={item.id}
              className={[
                "knowledge-pending__row",
                item.error
                  ? "knowledge-pending__row--error"
                  : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              <FileTypeIcon
                type={extensionOf(item.file.name)}
              />

              <div className="knowledge-pending__meta">
                <strong>{item.file.name}</strong>
                <span>
                  {item.error ||
                    `Uploading ${formatBytes(
                      item.file.size
                    )}...`}
                </span>
              </div>

              {item.error ? (
                <button
                  type="button"
                  className="knowledge-pending__dismiss"
                  onClick={() =>
                    dismissPendingError(item.id)
                  }
                  aria-label={`Dismiss ${item.file.name}`}
                >
                  <X size={15} />
                </button>
              ) : (
                <Loader2
                  size={16}
                  className="knowledge-status__spin"
                />
              )}
            </div>
          ))}
        </section>
      )}

      <section className="knowledge-list">
        <div className="knowledge-list__header">
          <h2>Uploaded documents</h2>
          <span>
            {documents.length}{" "}
            {documents.length === 1 ? "file" : "files"}
            {activeUploadCount > 0 &&
              ` · ${activeUploadCount} uploading`}
          </span>
        </div>

        {loadError && (
          <div className="knowledge-list__error">
            <AlertCircle size={16} />
            {loadError}
          </div>
        )}

        {isLoadingDocuments ? (
          <div className="knowledge-list__empty">
            <Loader2
              size={20}
              className="knowledge-status__spin"
            />
            Loading your documents...
          </div>
        ) : documents.length === 0 ? (
          <div className="knowledge-list__empty">
            <strong>No documents yet.</strong>
            <span>
              Upload your first file above to start
              building this workspace's knowledge.
            </span>
          </div>
        ) : (
          <div className="knowledge-table">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="knowledge-table__row"
              >
                <div className="knowledge-table__name">
                  <FileTypeIcon
                    type={extensionOf(doc.name)}
                  />
                  <span title={doc.error_message || undefined}>
                    {doc.name}
                  </span>
                </div>

                <span className="knowledge-table__size">
                  {formatBytes(doc.file_size)}
                </span>

                <span className="knowledge-table__category">
                  {doc.category}
                </span>

                <span className="knowledge-table__date">
                  {formatDate(doc.uploaded_at)}
                </span>

                <StatusBadge status={doc.status} />

                <button
                  type="button"
                  className="knowledge-table__delete"
                  onClick={() =>
                    handleDelete(doc.id)
                  }
                  disabled={deletingId === doc.id}
                  aria-label={`Remove ${doc.name}`}
                >
                  {deletingId === doc.id ? (
                    <Loader2
                      size={15}
                      className="knowledge-status__spin"
                    />
                  ) : (
                    <Trash2 size={15} />
                  )}
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      <style jsx>{`
        .knowledge-dropzone {
          margin-top: 2rem;
          border: 1.5px dashed rgba(148, 163, 184, 0.35);
          border-radius: 16px;
          padding: 2.75rem 2rem;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
          text-align: center;
          cursor: pointer;
          background: rgba(148, 163, 184, 0.04);
          transition: border-color 0.2s ease,
            background 0.2s ease, transform 0.15s ease;
        }

        .knowledge-dropzone:hover {
          border-color: rgba(148, 163, 184, 0.55);
          background: rgba(148, 163, 184, 0.07);
        }

        .knowledge-dropzone--active {
          border-color: rgba(129, 140, 248, 0.7);
          background: rgba(129, 140, 248, 0.08);
          transform: scale(1.005);
        }

        .knowledge-dropzone__input {
          display: none;
        }

        .knowledge-dropzone__icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(129, 140, 248, 0.12);
          color: rgb(129, 140, 248);
          margin-bottom: 0.5rem;
        }

        .knowledge-dropzone__hint {
          font-size: 0.8rem;
          opacity: 0.6;
          letter-spacing: 0.02em;
        }

        .knowledge-pending {
          margin-top: 1rem;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .knowledge-pending__row {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem 1rem;
          border-radius: 10px;
          background: rgba(148, 163, 184, 0.06);
        }

        .knowledge-pending__row--error {
          background: rgba(239, 68, 68, 0.08);
          color: rgb(248, 113, 113);
        }

        .knowledge-pending__meta {
          display: flex;
          flex-direction: column;
          gap: 0.1rem;
          flex: 1;
          min-width: 0;
        }

        .knowledge-pending__meta strong {
          font-size: 0.875rem;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .knowledge-pending__meta span {
          font-size: 0.75rem;
          opacity: 0.65;
        }

        .knowledge-pending__dismiss {
          background: none;
          border: none;
          cursor: pointer;
          color: inherit;
          opacity: 0.6;
          display: flex;
        }

        .knowledge-pending__dismiss:hover {
          opacity: 1;
        }

        .knowledge-list {
          margin-top: 2.5rem;
        }

        .knowledge-list__header {
          display: flex;
          align-items: baseline;
          justify-content: space-between;
          margin-bottom: 1rem;
        }

        .knowledge-list__header h2 {
          font-size: 1.05rem;
          font-weight: 600;
        }

        .knowledge-list__header span {
          font-size: 0.8rem;
          opacity: 0.6;
        }

        .knowledge-list__error {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem 1rem;
          border-radius: 10px;
          background: rgba(239, 68, 68, 0.08);
          color: rgb(248, 113, 113);
          font-size: 0.85rem;
          margin-bottom: 1rem;
        }

        .knowledge-list__empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.35rem;
          padding: 3rem 1rem;
          border-radius: 14px;
          background: rgba(148, 163, 184, 0.04);
          text-align: center;
          opacity: 0.85;
        }

        .knowledge-list__empty span {
          font-size: 0.85rem;
          opacity: 0.65;
          max-width: 32ch;
        }

        .knowledge-table {
          display: flex;
          flex-direction: column;
          border-radius: 14px;
          overflow: hidden;
          border: 1px solid rgba(148, 163, 184, 0.12);
        }

        .knowledge-table__row {
          display: grid;
          grid-template-columns: minmax(180px, 1fr) 100px 80px 110px 120px 40px;
          align-items: center;
          gap: 1rem;
          padding: 0.85rem 1.1rem;
          border-bottom: 1px solid
            rgba(148, 163, 184, 0.1);
          font-size: 0.85rem;
        }

        .knowledge-table__row:last-child {
          border-bottom: none;
        }

        .knowledge-table__name {
          display: flex;
          align-items: center;
          gap: 0.6rem;
          min-width: 0;
        }

        .knowledge-table__name span {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .knowledge-table__size,
        .knowledge-table__date {
          opacity: 0.65;
        }

        .knowledge-table__category {
          width: fit-content;
          padding: 0.25rem 0.55rem;
          border-radius: 999px;
          color: #067e91;
          background: rgba(13, 184, 189, 0.1);
          font-size: 0.72rem;
          font-weight: 650;
        }

        .knowledge-table__delete {
          background: none;
          border: none;
          cursor: pointer;
          color: inherit;
          opacity: 0.5;
          display: flex;
          justify-self: end;
        }

        .knowledge-table__delete:hover {
          opacity: 1;
          color: rgb(248, 113, 113);
        }

        .knowledge-table__delete:disabled {
          cursor: default;
        }

        .knowledge-status {
          display: inline-flex;
          align-items: center;
          gap: 0.35rem;
          font-size: 0.75rem;
          font-weight: 500;
          padding: 0.2rem 0.55rem;
          border-radius: 999px;
          width: fit-content;
        }

        .knowledge-status--ready {
          background: rgba(34, 197, 94, 0.12);
          color: rgb(74, 222, 128);
        }

        .knowledge-status--processing {
          background: rgba(129, 140, 248, 0.12);
          color: rgb(129, 140, 248);
        }

        .knowledge-status--failed {
          background: rgba(239, 68, 68, 0.12);
          color: rgb(248, 113, 113);
        }

        .knowledge-status__spin {
          animation: knowledge-spin 0.8s linear infinite;
        }

        @keyframes knowledge-spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .knowledge-status__spin {
            animation: none;
          }
        }

        @media (max-width: 640px) {
          .knowledge-table__row {
            grid-template-columns: 1fr 40px;
            grid-template-areas:
              "name delete"
              "category category"
              "size size"
              "date date"
              "status status";
            row-gap: 0.35rem;
          }

          .knowledge-table__name {
            grid-area: name;
          }

          .knowledge-table__delete {
            grid-area: delete;
          }

          .knowledge-table__size {
            grid-area: size;
          }

          .knowledge-table__category {
            grid-area: category;
          }

          .knowledge-table__date {
            grid-area: date;
          }

          .knowledge-status {
            grid-area: status;
          }
        }
      `}</style>
    </PageTransition>
  );
}
