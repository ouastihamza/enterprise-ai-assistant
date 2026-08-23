export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  full_name: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  workspace_id?: string | null;
  is_active?: boolean;
  is_superuser?: boolean;
}

export interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;

  login: (
    credentials: LoginCredentials
  ) => Promise<void>;

  logout: () => void;

  restoreSession: () => Promise<void>;

  clearError: () => void;
}