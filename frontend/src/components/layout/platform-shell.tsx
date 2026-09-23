"use client";

import type { ReactNode } from "react";

import { ProtectedRoute } from "../auth/protected-route";
import { AppLoader } from "../ui/app-loader";
import { useWorkspace } from "../../hooks/use-workspace";
import { PlatformHeader } from "./platform-header";
import { PlatformSidebar } from "./platform-sidebar";

interface PlatformShellProps {
  children: ReactNode;
}

export function PlatformShell({
  children,
}: PlatformShellProps) {
  const {
    activeWorkspace,
    isLoading,
    error,
  } = useWorkspace();

  return (
    <ProtectedRoute>
      {isLoading ? (
        <AppLoader />
      ) : error ? (
        <main className="platform-state">
          <span>Workspace unavailable</span>
          <h1>Atlas could not load your workspace.</h1>
          <p>{error}</p>
        </main>
      ) : !activeWorkspace ? (
        <main className="platform-state">
          <span>Workspace unavailable</span>
          <h1>No company workspace is available.</h1>
          <p>
            Sign out and try again, or ask your workspace
            administrator for access.
          </p>
        </main>
      ) : (
        <div className="platform-shell">
          <PlatformSidebar />

          <div className="platform-shell__main">
            <PlatformHeader />

            <div className="platform-shell__content">
              {children}
            </div>
          </div>
        </div>
      )}
    </ProtectedRoute>
  );
}
