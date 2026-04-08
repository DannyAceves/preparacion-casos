import Link from "next/link";
import { redirect } from "next/navigation";
import { ReactNode } from "react";

import { Card } from "@/components/ui/card";
import { getStaffRouteAccess } from "@/lib/auth/session";

interface RestrictedRouteStateProps {
  title: string;
  message: string;
  fallbackHref: string;
  fallbackLabel: string;
}

export function RestrictedRouteState({
  title,
  message,
  fallbackHref,
  fallbackLabel,
}: RestrictedRouteStateProps): JSX.Element {
  return (
    <div className="page-stack">
      <section className="page-heading">
        <div>
          <h2>{title}</h2>
          <p>Access restricted for the current role.</p>
        </div>
      </section>

      <Card title="Restricted Access" subtitle="This area is not available in your current internal role.">
        <div className="placeholder-note">
          <strong>Why this is hidden</strong>
          <p>{message}</p>
          <p>Ask an administrator if your assignment changed and this section should now be available.</p>
        </div>
        <div className="case-quick-actions">
          <Link href={fallbackHref} className="ui-button">
            {fallbackLabel}
          </Link>
        </div>
      </Card>
    </div>
  );
}

interface RouteAccessGuardProps {
  href: string;
  children: ReactNode;
}

export async function RouteAccessGuard({
  href,
  children,
}: RouteAccessGuardProps): Promise<JSX.Element> {
  const access = await getStaffRouteAccess(href);

  if (access.allowed) {
    return <>{children}</>;
  }

  redirect(access.fallbackHref);
}
