export interface Workspace {
  id: string;
  name: string;
  company_name: string;
  industry: string;
  description: string;
  enabled_modules: string[];
  status?: string;
}

export interface CreateWorkspaceRequest {
  name: string;
  company_name: string;
  industry: string;
  description: string;
  enabled_modules: string[];
}

export interface WorkspaceSettings {
  assistant_name: string;
  company_logo: string;
  primary_color: string;
  theme: string;
  llm_model: string;
  temperature: number;
  chunk_size: number;
  chunk_overlap: number;
  top_k: number;
  max_upload_size_mb: number;
  allowed_file_types: string[];
  welcome_message: string;
  system_prompt: string;
}

export interface WorkspaceContextValue {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  settings: WorkspaceSettings | null;

  isLoading: boolean;
  isSettingsLoading: boolean;
  error: string | null;

  selectWorkspace: (workspaceId: string) => void;

  createWorkspace: (
    payload: CreateWorkspaceRequest
  ) => Promise<Workspace>;

  refreshWorkspaces: () => Promise<void>;
  refreshSettings: () => Promise<void>;
}