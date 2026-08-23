"use client";

import {
  Bell,
  LogOut,
  Search,
} from "lucide-react";

import { useAuth } from "../../hooks/use-auth";
import { WorkspaceSwitcher } from "../workspaces/workspace-switcher";

export function PlatformHeader() {
  const { user, logout } = useAuth();

  const initials =
    user?.full_name
      ?.split(" ")
      .map((part) => part.charAt(0))
      .join("")
      .slice(0, 2)
      .toUpperCase() || "V";

  return (
    <header className="platform-header">
      <WorkspaceSwitcher />

      <div className="platform-header__actions">
        <button
          type="button"
          className="platform-header__icon-button"
          aria-label="Search"
        >
          <Search size={18} />
        </button>

        <button
          type="button"
          className="platform-header__icon-button"
          aria-label="Notifications"
        >
          <Bell size={18} />
        </button>

        <div className="platform-user">
          <span className="platform-user__avatar">
            {initials}
          </span>

          <span className="platform-user__identity">
            <strong>{user?.full_name}</strong>
            <small>{user?.email}</small>
          </span>
        </div>

        <button
          type="button"
          className="platform-header__icon-button"
          aria-label="Sign out"
          onClick={logout}
        >
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}