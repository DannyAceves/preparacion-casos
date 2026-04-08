import "server-only";

import { buildPrincipalHeaders } from "@/lib/auth/principal-headers";
import { getCurrentSession } from "@/lib/auth/session";

export async function getServerPrincipalHeaders(): Promise<HeadersInit> {
  const session = await getCurrentSession();
  return buildPrincipalHeaders(session);
}
