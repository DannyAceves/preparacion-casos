"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { canAccessRoute } from "@/lib/auth/permissions";
import { useAuth } from "@/providers/auth-provider";

const navigationItems = [
  { href: "/admin/users", label: "User Management" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/consultations", label: "Consultations" },
  { href: "/cases", label: "Cases" },
  { href: "/questionnaire-templates", label: "Questionnaires" },
  { href: "/reviews", label: "Reviews" },
  { href: "/submissions", label: "Submissions" },
];

export function Sidebar(): JSX.Element {
  const { user } = useAuth();
  const pathname = usePathname();
  const visibleItems = navigationItems.filter((item) => canAccessRoute(user.role, item.href));

  return (
    <aside className="app-sidebar">
      <div className="app-sidebar__brand">
        <span className="app-sidebar__eyebrow">{user.role === "reception" ? "Reception Workspace" : "Internal Staff"}</span>
        <strong>Case Prep</strong>
      </div>
      <nav className="app-sidebar__nav">
        {visibleItems.map((item) => (
          <Link
            key={`${item.href}-${item.label}`}
            href={item.href}
            className={`app-sidebar__link ${pathname.startsWith(item.href) ? "app-sidebar__link--active" : ""}`}
          >
            {item.label}
          </Link>
        ))}
        {!visibleItems.length ? <p className="entity-card__hint">No internal routes are available for this role.</p> : null}
      </nav>
    </aside>
  );
}
