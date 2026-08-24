"use client";

import {
  BookOpen,
  Bot,
  Building2,
  LayoutDashboard,
  Settings,
  Workflow,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  {
    label: "Customers",
    href: "/customers",
    icon: Building2,
  },
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Knowledge",
    href: "/knowledge",
    icon: BookOpen,
  },
  {
    label: "Assistant",
    href: "/assistant",
    icon: Bot,
  },
  {
    label: "Workflows",
    href: "/workflows",
    icon: Workflow,
    disabled: true,
  },
  {
    label: "Settings",
    href: "/settings",
    icon: Settings,
  },
];

export function PlatformSidebar() {
  const pathname = usePathname();

  return (
    <aside className="platform-sidebar">
      <div className="platform-sidebar__brand">
        <span>V</span>
        <strong>AI Agency</strong>
      </div>

      <nav className="platform-sidebar__navigation">
        <span className="platform-sidebar__section-label">
          Workspace
        </span>

        {navigation.map((item) => {
          const Icon = item.icon;
          const isActive =
            pathname === item.href || pathname.startsWith(`${item.href}/`);

          if (item.disabled) {
            return (
              <div
                key={item.label}
                className="platform-nav-item platform-nav-item--disabled"
              >
                <Icon size={18} />
                <span>{item.label}</span>
                <small>Soon</small>
              </div>
            );
          }

          return (
            <Link
              key={item.label}
              href={item.href}
              className={`platform-nav-item ${
                isActive
                  ? "platform-nav-item--active"
                  : ""
              }`}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="platform-sidebar__footer">
        <span>Private company workspace</span>
        <small>Customer information in one place</small>
      </div>
    </aside>
  );
}
