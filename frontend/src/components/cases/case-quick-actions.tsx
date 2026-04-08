"use client";

import Link from "next/link";

import { usePermissions } from "@/hooks/use-permissions";

interface CaseQuickActionsProps {
  caseId: string;
}

const quickActions = [
  { label: "Back To Cases", href: "/cases", tone: "ghost", section: null },
  { label: "Questionnaire", href: "?tab=questionnaire", tone: "ghost", section: "questionnaire" },
  { label: "Upload Document", href: "?tab=documents", tone: "ghost", section: "documents" },
  { label: "Validate Readiness", href: "?tab=readiness", tone: "ghost", section: "readiness" },
  { label: "Submission", href: "?tab=submission", tone: "primary", section: "submission" },
] as const;

export function CaseQuickActions({ caseId }: CaseQuickActionsProps): JSX.Element {
  const permissions = usePermissions();
  const visibleActions = quickActions.filter((action) =>
    action.section ? permissions.canAccessCaseSection(action.section) : true,
  );

  return (
    <div className="case-quick-actions">
      {visibleActions.map((action) => {
        const href = action.href.startsWith("?") ? `/cases/${caseId}${action.href}` : action.href;
        return (
          <Link
            key={action.label}
            href={href}
            className={`ui-button ${action.tone === "ghost" ? "ui-button--ghost" : ""}`}
          >
            {action.label}
          </Link>
        );
      })}
    </div>
  );
}
