import {
  api,
  getApiErrorMessage,
} from "../lib/api";

import type {
  KnowledgeDocument,
} from "../types/document.types";

export async function listDocuments(
  workspaceId: string
): Promise<KnowledgeDocument[]> {
  try {
    const response = await api.get<
      KnowledgeDocument[]
    >(`/workspaces/${workspaceId}/documents`);

    return response.data;
  } catch (error) {
    throw new Error(
      getApiErrorMessage(
        error,
        "Couldn't load your documents."
      )
    );
  }
}

export async function uploadDocument(
  workspaceId: string,
  file: File,
  options?: {
    customerId?: string;
    category?: KnowledgeDocument["category"];
  }
): Promise<KnowledgeDocument> {
  try {
    const formData = new FormData();
    formData.append("file", file);
    if (options?.customerId) {
      formData.append("customer_id", options.customerId);
    }
    if (options?.category) {
      formData.append("category", options.category);
    }

    const response =
      await api.post<KnowledgeDocument>(
        `/workspaces/${workspaceId}/documents`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

    return response.data;
  } catch (error) {
    throw new Error(
      getApiErrorMessage(
        error,
        `${file.name} could not be uploaded.`
      )
    );
  }
}

export async function deleteDocument(
  workspaceId: string,
  documentId: number
): Promise<void> {
  try {
    await api.delete(
      `/workspaces/${workspaceId}/documents/${documentId}`
    );
  } catch (error) {
    throw new Error(
      getApiErrorMessage(
        error,
        "Couldn't remove that document."
      )
    );
  }
}

export async function openDocument(
  workspaceId: string,
  documentId: number,
  documentName: string
): Promise<void> {
  try {
    const response = await api.get(
      `/workspaces/${workspaceId}/documents/${documentId}/file`,
      { responseType: "blob" }
    );
    const url = URL.createObjectURL(response.data as Blob);
    const opened = window.open(url, "_blank", "noopener,noreferrer");
    if (!opened) {
      const link = document.createElement("a");
      link.href = url;
      link.download = documentName;
      link.click();
    }
    window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
  } catch (error) {
    throw new Error(
      getApiErrorMessage(error, "Couldn't open that document.")
    );
  }
}
