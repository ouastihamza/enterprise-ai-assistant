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
  file: File
): Promise<KnowledgeDocument> {
  try {
    const formData = new FormData();
    formData.append("file", file);

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