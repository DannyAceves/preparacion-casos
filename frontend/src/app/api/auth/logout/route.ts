import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { getSessionCookieName, getSessionCookieOptions } from "@/lib/auth/session";

export async function POST(): Promise<NextResponse> {
  cookies().set(getSessionCookieName(), "", {
    ...getSessionCookieOptions(),
    maxAge: 0,
  });
  return NextResponse.json({ ok: true });
}
