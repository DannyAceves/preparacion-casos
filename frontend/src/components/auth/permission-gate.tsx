"use client";

import { ReactNode } from "react";

import { canPerformAction } from "@/lib/auth/permissions";
import { useAuth } from "@/providers/auth-provider";
import { PermissionAction } from "@/types/auth";

interface PermissionGateProps {
  action?: PermissionAction;
  anyOf?: PermissionAction[];
  children: ReactNode;
  fallback?: ReactNode;
}

export function PermissionGate({
  action,
  anyOf,
  children,
  fallback = null,
}: PermissionGateProps): JSX.Element | null {
  const { user } = useAuth();
  const allowed =
    (action ? canPerformAction(user.role, action) : false) ||
    Boolean(anyOf?.some((permission) => canPerformAction(user.role, permission)));
  return allowed ? <>{children}</> : <>{fallback}</>;
}
