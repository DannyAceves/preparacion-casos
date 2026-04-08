import { AuthSession } from "@/types/auth";

export function buildPrincipalHeaders(session: AuthSession | null | undefined): HeadersInit {
  if (!session?.user) {
    return {};
  }

  return {
    "X-Principal-Subject": session.user.id,
    "X-Principal-Roles": session.user.role,
    "X-Principal-Email": session.user.email,
  };
}
