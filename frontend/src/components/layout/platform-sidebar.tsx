"use client";

import {
  BookOpen,
  Bot,
  Building2,
  LayoutDashboard,
  Settings,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Customers",
    href: "/customers",
    icon: Building2,
  },
  {
    label: "Documents",
    href: "/knowledge",
    icon: BookOpen,
  },
  {
    label: "Ask Atlas",
    href: "/assistant",
    icon: Bot,
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
        <span>A</span>
        <div><strong>ATLAS</strong><small>Enterprise Intelligence</small></div>
      </div>

      <nav className="platform-sidebar__navigation">
        <span className="platform-sidebar__section-label">
          Workspace
        </span>

        {navigation.map((item) => {
          const Icon = item.icon;
          const isActive =
            pathname === item.href || pathname.startsWith(`${item.href}/`);

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
        <span>Private workspace</span>
        <small>Grounded in your customer information</small>
      </div>
    </aside>
  );
}
