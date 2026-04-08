import { ReactNode } from "react";
import { redirect } from "next/navigation";

import { AppShell } from "@/components/layout/app-shell";
import { requireSession } from "@/lib/auth/session";
import { AuthProvider } from "@/providers/auth-provider";

interface StaffLayoutProps {
  children: ReactNode;
}

export default async function StaffLayout({ children }: StaffLayoutProps): Promise<JSX.Element> {
  const session = await requireSession();
  if (session.user.role === "client") {
    redirect("/portal?notice=internal-workspace-unavailable");
  }

  return (
    <AuthProvider initialSession={session}>
      <AppShell>{children}</AppShell>
    </AuthProvider>
  );
}
