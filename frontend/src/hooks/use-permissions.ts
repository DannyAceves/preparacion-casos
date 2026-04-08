"use client";

import { canAccessCaseSection, canAccessRoute, canPerformAction } from "@/lib/auth/permissions";
import { useAuth } from "@/providers/auth-provider";
import { CaseWorkspaceSection, PermissionAction } from "@/types/auth";

export function usePermissions() {
  const { user } = useAuth();

  return {
    role: user.role,
    can: (action: PermissionAction): boolean => canPerformAction(user.role, action),
    canAccessRoute: (href: string): boolean => canAccessRoute(user.role, href),
    canAccessCaseSection: (section: CaseWorkspaceSection): boolean => canAccessCaseSection(user.role, section),
  };
}
