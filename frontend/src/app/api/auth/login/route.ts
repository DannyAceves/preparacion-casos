import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { appConfig } from "@/lib/config";
import { getSessionCookieName, getSessionCookieOptions } from "@/lib/auth/session";
import { AuthSession, InternalRole } from "@/types/auth";

interface BackendLoginResponse {
  id: string;
  email: string;
  full_name: string;
  role: InternalRole;
  is_active: boolean;
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  const payload = (await request.json()) as {
    email?: string;
  };

  const response = await fetch(`${appConfig.apiInternalBaseUrl}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      email: payload.email ?? "",
    }),
    cache: "no-store",
  });

  const detail = (await response.json().catch(() => null)) as { detail?: unknown } | null;
  if (!response.ok) {
    return NextResponse.json(
      {
        error: {
          message: typeof detail?.detail === "string" ? detail.detail : "Login failed.",
          detail: detail?.detail ?? "Login failed.",
        },
      },
      { status: response.status },
    );
  }

  const user = detail as BackendLoginResponse;
  const session: AuthSession = {
    user: {
      id: user.id,
      name: user.full_name,
      email: user.email,
      role: user.role,
    },
    accessToken: null,
    provider: "database",
    expiresAt: null,
  };

  cookies().set(getSessionCookieName(), JSON.stringify(session), getSessionCookieOptions());

  return NextResponse.json({
    ok: true,
    user: session.user,
  });
}
