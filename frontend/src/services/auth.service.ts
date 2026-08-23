import {
  api,
  getApiErrorMessage,
} from "../lib/api";

import type {
  AuthUser,
  LoginCredentials,
  LoginResponse,
  RegisterPayload,
} from "../types/auth.types";

const ACCESS_TOKEN_KEY = "access_token";

export async function registerRequest(
  payload: RegisterPayload
): Promise<AuthUser> {
  try {
    const response = await api.post<AuthUser>(
      "/auth/register",
      payload
    );

    return response.data;
  } catch (error) {
    throw new Error(
      getApiErrorMessage(
        error,
        "Unable to create your account."
      )
    );
  }
}

export async function loginRequest(
  credentials: LoginCredentials
): Promise<LoginResponse> {
  try {
    const response =
      await api.post<LoginResponse>(
        "/auth/login",
        credentials
      );

    return response.data;
  } catch (error) {
    throw new Error(
      getApiErrorMessage(
        error,
        "Unable to sign in."
      )
    );
  }
}

export async function getCurrentUser():
  Promise<AuthUser> {
  try {
    const response =
      await api.get<AuthUser>("/auth/me");

    return response.data;
  } catch (error) {
    throw new Error(
      getApiErrorMessage(
        error,
        "Unable to load the current user."
      )
    );
  }
}

export function saveAccessToken(
  accessToken: string
): void {
  if (typeof window === "undefined") {
    return;
  }

  localStorage.setItem(
    ACCESS_TOKEN_KEY,
    accessToken
  );
}

export function getAccessToken():
  | string
  | null {
  if (typeof window === "undefined") {
    return null;
  }

  return localStorage.getItem(
    ACCESS_TOKEN_KEY
  );
}

export function clearAccessToken(): void {
  if (typeof window === "undefined") {
    return;
  }

  localStorage.removeItem(
    ACCESS_TOKEN_KEY
  );
}