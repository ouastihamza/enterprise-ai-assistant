import type {
  ReactNode,
} from "react";

import {
  ProtectedRoute,
} from "../../components/auth/protected-route";

import {
  PlatformShell,
} from "../../components/layout/platform-shell";

import {
  WorkspaceProvider,
} from "../../context/workspace-context";

interface PlatformLayoutProps {
  children: ReactNode;
}

export default function PlatformLayout({
  children,
}: PlatformLayoutProps) {
  return (
    <ProtectedRoute>
      <WorkspaceProvider>
        <PlatformShell>
          {children}
        </PlatformShell>
      </WorkspaceProvider>
    </ProtectedRoute>
  );
}