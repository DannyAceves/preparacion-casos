import Link from "next/link";

import { MetricCard } from "@/components/dashboard/metric-card";
import { CasesTable } from "@/components/ui/data-table";
import { Card } from "@/components/ui/card";
import { getServerPrincipalHeaders } from "@/lib/auth/server-principal-headers";
import { requireAllowedStaffRoute } from "@/lib/auth/session";
import { getDashboardMetrics } from "@/services/dashboard";

export default async function DashboardPage(): Promise<JSX.Element> {
  await requireAllowedStaffRoute("/dashboard");

  const metrics = await getDashboardMetrics({
    headers: await getServerPrincipalHeaders(),
  });

  return (
    <div className="page-stack">
      <section className="page-heading">
        <div>
          <h2>Dashboard</h2>
          <p>Operational snapshot for legal and immigration case preparation.</p>
        </div>
        <Link href="/cases" className="ui-badge ui-badge--info">
          View all cases
        </Link>
      </section>

      <section className="metrics-grid">
        <MetricCard label="Total Cases" value={metrics.totalCases} />
        <MetricCard label="Draft Cases" value={metrics.draftCases} />
        <MetricCard label="Attorney Review" value={metrics.activeReviewCases} />
        <MetricCard label="Ready For Submission" value={metrics.submissionReadyCases} />
      </section>

      <Card title="Recently Updated Cases" subtitle="Direct feed from the backend cases endpoint">
        <CasesTable cases={metrics.recentCases} />
      </Card>
    </div>
  );
}
