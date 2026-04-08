import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

import { getMockSessionTemplate, getSessionCookieName, getSessionCookieOptions } from "@/lib/auth/session";
import { AuthSession, InternalRole } from "@/types/auth";

export async function POST(request: NextRequest): Promise<NextResponse> {
  const payload = (await request.json()) as {
    name?: string;
    email?: string;
    role?: InternalRole;
  };

  const baseSession = getMockSessionTemplate();
  const session: AuthSession = {
    ...baseSession,
    user: {
      ...baseSession.user,
      name: payload.name || baseSession.user.name,
      email: payload.email || baseSession.user.email,
      role: payload.role || baseSession.user.role,
    },
  };

  cookies().set(getSessionCookieName(), JSON.stringify(session), getSessionCookieOptions());

  return NextResponse.json({ ok: true });
}
