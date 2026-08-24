import { api, getApiErrorMessage } from "../lib/api";

import type {
  CreateWorkspaceRequest,
  Workspace,
  WorkspaceSettings,
} from "../types/workspace.types";

const DEFAULT_WORKSPACE_SETTINGS: WorkspaceSettings = {
  assistant_name: "Atlas Assistant",
  company_logo: "",
  primary_color: "#8d74d8",
  theme: "default",
  llm_model: "",
  temperature: 0.2,
  chunk_size: 1000,
  chunk_overlap: 200,
  top_k: 3,
  max_upload_size_mb: 25,
  allowed_file_types: [
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
  ],
  welcome_message:
    "Ask questions about your company’s knowledge.",
  system_prompt: "",
};

export async function listWorkspaces(): Promise<
  Workspace[]
> {
  const response = await api.get<Workspace[]>(
    "/workspaces/"
  );

  return response.data;
}

export async function createWorkspaceRequest(
  payload: CreateWorkspaceRequest
): Promise<Workspace> {
  const response = await api.post<Workspace>(
    "/workspaces/",
    payload
  );

  return response.data;
}

export async function getWorkspaceSettings(): Promise<
  WorkspaceSettings
> {
  const response =
    await api.get<Partial<WorkspaceSettings>>(
      "/workspace/settings"
    );

  return {
    ...DEFAULT_WORKSPACE_SETTINGS,
    ...response.data,
  };
}

export async function updateWorkspaceSettings(
  payload: Partial<WorkspaceSettings>
): Promise<WorkspaceSettings> {
  try {
    const response =
      await api.put<WorkspaceSettings>(
        "/workspace/settings",
        payload
      );

    return response.data;
  } catch (error) {
    throw new Error(
      getApiErrorMessage(
        error,
        "Couldn't save your settings."
      )
    );
  }
}
