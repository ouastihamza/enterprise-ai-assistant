"use client";

import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  clearAccessToken,
  getAccessToken,
  getCurrentUser,
  loginRequest,
  saveAccessToken,
} from "../services/auth.service";

import type {
  AuthContextValue,
  AuthUser,
  LoginCredentials,
} from "../types/auth.types";

export const AuthContext =
  createContext<AuthContextValue | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({
  children,
}: AuthProviderProps) {
  const [user, setUser] =
    useState<AuthUser | null>(null);

  const [isLoading, setIsLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const restoreSession =
    useCallback(async (): Promise<void> => {
      const accessToken = getAccessToken();

      if (!accessToken) {
        setUser(null);
        setIsLoading(false);
        return;
      }

      setIsLoading(true);

      try {
        const currentUser =
          await getCurrentUser();

        setUser(currentUser);
        setError(null);
      } catch (requestError) {
        console.error(
          "Authentication session restoration failed:",
          requestError
        );

        clearAccessToken();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }, []);

  const login = useCallback(
    async (
      credentials: LoginCredentials
    ): Promise<void> => {
      setError(null);
      setIsLoading(true);

      try {
        const loginResponse =
          await loginRequest(credentials);

        saveAccessToken(
          loginResponse.access_token
        );

        const currentUser =
          await getCurrentUser();

        setUser(currentUser);
        setError(null);
      } catch (requestError) {
        clearAccessToken();
        setUser(null);

        const message =
          requestError instanceof Error
            ? requestError.message
            : "Unable to sign in.";

        setError(message);

        throw requestError;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const logout = useCallback((): void => {
    clearAccessToken();
    setUser(null);
    setError(null);
  }, []);

  const clearError =
    useCallback((): void => {
      setError(null);
    }, []);

  useEffect(() => {
    void restoreSession();
  }, [restoreSession]);

  useEffect(() => {
    function handleUnauthorized(): void {
      clearAccessToken();
      setUser(null);
      setError(
        "Your session expired. Please sign in again."
      );
    }

    window.addEventListener(
      "auth:unauthorized",
      handleUnauthorized
    );

    return () => {
      window.removeEventListener(
        "auth:unauthorized",
        handleUnauthorized
      );
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isAuthenticated: Boolean(user),
      error,
      login,
      logout,
      restoreSession,
      clearError,
    }),
    [
      user,
      isLoading,
      error,
      login,
      logout,
      restoreSession,
      clearError,
    ]
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}