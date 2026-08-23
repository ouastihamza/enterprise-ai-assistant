"use client";

import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { useAuth } from "../hooks/use-auth";

import {
  createWorkspaceRequest,
  getWorkspaceSettings,
  listWorkspaces,
} from "../services/workspace.service";

import type {
  CreateWorkspaceRequest,
  Workspace,
  WorkspaceContextValue,
  WorkspaceSettings,
} from "../types/workspace.types";

const ACTIVE_WORKSPACE_KEY =
  "ai-agency:active-workspace-id";

// Mirrors web_app.py's DEFAULT_WORKSPACE: a brand-new user has no
// workspace yet, and there is no workspace-creation UI (create_workspace
// exists on this context but nothing calls it), so a first-time user
// landing here would otherwise be stuck on PlatformShell's permanent
// "workspace onboarding" placeholder with no way to proceed.
const DEFAULT_WORKSPACE_REQUEST: CreateWorkspaceRequest = {
  name: "company-x-workspace",
  company_name: "Company X",
  industry: "General Business",
  description: "Internal AI assistant for company documents.",
  enabled_modules: ["ai_knowledge_assistant"],
};

export const WorkspaceContext =
  createContext<WorkspaceContextValue | null>(
    null
  );

interface WorkspaceProviderProps {
  children: ReactNode;
}

export function WorkspaceProvider({
  children,
}: WorkspaceProviderProps) {
  const {
    isAuthenticated,
    isLoading: isAuthLoading,
  } = useAuth();

  const [workspaces, setWorkspaces] = useState<
    Workspace[]
  >([]);

  const [activeWorkspace, setActiveWorkspace] =
    useState<Workspace | null>(null);

  const [settings, setSettings] =
    useState<WorkspaceSettings | null>(null);

  const [isLoading, setIsLoading] =
    useState(true);

  const [
    isSettingsLoading,
    setIsSettingsLoading,
  ] = useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const chooseWorkspace = useCallback(
    (
      availableWorkspaces: Workspace[],
      currentWorkspaceId?: string
    ): Workspace | null => {
      if (availableWorkspaces.length === 0) {
        return null;
      }

      const storedWorkspaceId =
        typeof window !== "undefined"
          ? localStorage.getItem(
              ACTIVE_WORKSPACE_KEY
            )
          : null;

      return (
        availableWorkspaces.find(
          (workspace) =>
            workspace.id === currentWorkspaceId
        ) ??
        availableWorkspaces.find(
          (workspace) =>
            workspace.id === storedWorkspaceId
        ) ??
        availableWorkspaces[0]
      );
    },
    []
  );

  const refreshWorkspaces =
    useCallback(async () => {
      if (!isAuthenticated) {
        setWorkspaces([]);
        setActiveWorkspace(null);
        setSettings(null);
        setError(null);
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        let availableWorkspaces =
          await listWorkspaces();

        if (availableWorkspaces.length === 0) {
          const createdWorkspace =
            await createWorkspaceRequest(
              DEFAULT_WORKSPACE_REQUEST
            );

          availableWorkspaces = [createdWorkspace];
        }

        setWorkspaces(availableWorkspaces);

        setActiveWorkspace(
          (currentWorkspace) => {
            const selectedWorkspace =
              chooseWorkspace(
                availableWorkspaces,
                currentWorkspace?.id
              );

            if (
              selectedWorkspace &&
              typeof window !== "undefined"
            ) {
              localStorage.setItem(
                ACTIVE_WORKSPACE_KEY,
                selectedWorkspace.id
              );
            }

            return selectedWorkspace;
          }
        );
      } catch (requestError) {
        console.error(
          "Unable to load workspaces.",
          requestError
        );

        setWorkspaces([]);
        setActiveWorkspace(null);
        setSettings(null);

        setError(
          "AI Agency could not load your company workspaces."
        );
      } finally {
        setIsLoading(false);
      }
    }, [chooseWorkspace, isAuthenticated]);

  const refreshSettings =
    useCallback(async () => {
      if (!activeWorkspace) {
        setSettings(null);
        return;
      }

      setIsSettingsLoading(true);

      try {
        const workspaceSettings =
          await getWorkspaceSettings();

        setSettings(workspaceSettings);
      } catch (requestError) {
        console.error(
          "Unable to load workspace settings.",
          requestError
        );

        setSettings(null);
      } finally {
        setIsSettingsLoading(false);
      }
    }, [activeWorkspace]);

  const selectWorkspace = useCallback(
    (workspaceId: string) => {
      const selectedWorkspace =
        workspaces.find(
          (workspace) =>
            workspace.id === workspaceId
        );

      if (!selectedWorkspace) {
        return;
      }

      setActiveWorkspace(selectedWorkspace);

      localStorage.setItem(
        ACTIVE_WORKSPACE_KEY,
        selectedWorkspace.id
      );
    },
    [workspaces]
  );

  const createWorkspace = useCallback(
    async (
      payload: CreateWorkspaceRequest
    ): Promise<Workspace> => {
      const createdWorkspace =
        await createWorkspaceRequest(payload);

      setWorkspaces((currentWorkspaces) => [
        ...currentWorkspaces,
        createdWorkspace,
      ]);

      setActiveWorkspace(createdWorkspace);

      localStorage.setItem(
        ACTIVE_WORKSPACE_KEY,
        createdWorkspace.id
      );

      return createdWorkspace;
    },
    []
  );

  useEffect(() => {
    if (isAuthLoading) {
      return;
    }

    void refreshWorkspaces();
  }, [isAuthLoading, refreshWorkspaces]);

  useEffect(() => {
    if (!activeWorkspace) {
      setSettings(null);
      return;
    }

    void refreshSettings();
  }, [activeWorkspace, refreshSettings]);

  const value =
    useMemo<WorkspaceContextValue>(
      () => ({
        workspaces,
        activeWorkspace,
        settings,
        isLoading,
        isSettingsLoading,
        error,
        selectWorkspace,
        createWorkspace,
        refreshWorkspaces,
        refreshSettings,
      }),
      [
        workspaces,
        activeWorkspace,
        settings,
        isLoading,
        isSettingsLoading,
        error,
        selectWorkspace,
        createWorkspace,
        refreshWorkspaces,
        refreshSettings,
      ]
    );

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
}
