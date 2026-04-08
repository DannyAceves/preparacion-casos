import "server-only";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { appConfig } from "@/lib/config";
import { getRoleLandingPath, getRouteAccessDecision, resolveAuthorizedPathForRole } from "@/lib/auth/permissions";
import { AuthSession, InternalRole, InternalUser } from "@/types/auth";

const SESSION_COOKIE_NAME = "caseprep_staff_session";

export function getSessionCookieOptions() {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: appConfig.isProductionLike,
    path: "/",
    maxAge: 60 * 60 * 8,
  };
}

function getDefaultMockUser(): InternalUser {
  return {
    id: "staff-placeholder",
    name: process.env.NEXT_PUBLIC_DEFAULT_USER_NAME ?? "Internal Staff",
    email: process.env.NEXT_PUBLIC_DEFAULT_USER_EMAIL ?? "staff@example.com",
    role: (process.env.NEXT_PUBLIC_DEFAULT_ROLE ?? "paralegal") as InternalRole,
  };
}

function parseSessionCookie(rawValue: string | undefined): AuthSession | null {
  if (!rawValue) {
    return null;
  }

  try {
    return JSON.parse(rawValue) as AuthSession;
  } catch {
    return null;
  }
}

export function getMockSessionTemplate(): AuthSession {
  return {
    user: getDefaultMockUser(),
    accessToken: null,
    provider: "mock",
    expiresAt: null,
  };
}

export async function getCurrentSession(): Promise<AuthSession | null> {
  const cookieStore = cookies();
  const sessionCookie = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  return parseSessionCookie(sessionCookie);
}

export async function requireSession(): Promise<AuthSession> {
  const session = await getCurrentSession();
  if (!session) {
    redirect(`/login?next=${encodeURIComponent(appConfig.defaultProtectedRoute)}`);
  }

  return session;
}

export async function getCurrentUser(): Promise<InternalUser | null> {
  const session = await getCurrentSession();
  return session?.user ?? null;
}

export async function getStaffRouteAccess(href: string): Promise<{
  session: AuthSession;
  allowed: boolean;
  title: string;
  message: string;
  fallbackHref: string;
  fallbackLabel: string;
}> {
  const session = await requireSession();
  const decision = getRouteAccessDecision(session.user.role, href);

  return {
    session,
    ...decision,
  };
}

export async function requireAllowedStaffRoute(href: string): Promise<AuthSession> {
  const session = await requireSession();
  const decision = getRouteAccessDecision(session.user.role, href);
  if (!decision.allowed) {
    redirect(decision.fallbackHref);
  }
  return session;
}

export async function redirectToRoleLandingPath(nextPath?: string | null): Promise<never> {
  const session = await requireSession();
  redirect(resolveAuthorizedPathForRole(session.user.role, nextPath));
}

export function getRoleHomePath(role: InternalRole): string {
  return getRoleLandingPath(role);
}

export function getSessionCookieName(): string {
  return SESSION_COOKIE_NAME;
}
