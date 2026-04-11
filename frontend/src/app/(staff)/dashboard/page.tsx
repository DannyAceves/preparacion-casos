import Link from "next/link";

import { MetricCard } from "@/components/dashboard/metric-card";
import { CasesTable } from "@/components/ui/data-table";
import { Card } from "@/components/ui/card";
import { getServerPrincipalHeaders } from "@/lib/auth/server-principal-headers";
import { requireAllowedStaffRoute } from "@/lib/auth/session";
import { getDashboardMetrics, getRecentCasesPage } from "@/services/dashboard";
import { Case } from "@/types/case";

const RECENT_CASES_PAGE_SIZE = 5;

interface DashboardPageProps {
  searchParams?: Promise<{
    page?: string;
  }>;
}

export default async function DashboardPage({ searchParams }: DashboardPageProps): Promise<JSX.Element> {
  await requireAllowedStaffRoute("/dashboard");
  const params = searchParams ? await searchParams : undefined;
  const requestedPage = Number(params?.page ?? "1");
  const currentPage = Number.isFinite(requestedPage) && requestedPage > 0 ? Math.floor(requestedPage) : 1;
  const headers = await getServerPrincipalHeaders();
  let metrics = {
    totalCases: 0,
    draftCases: 0,
    activeReviewCases: 0,
    submissionReadyCases: 0,
  };
  let recentCases: Case[] = [];
  let safeCurrentPage = 1;
  let totalPages = 1;
  let rangeStart = 0;
  let rangeEnd = 0;
  let previousPageHref: string | null = null;
  let nextPageHref: string | null = null;
  let dashboardLoadError: string | null = null;

  try {
    metrics = await getDashboardMetrics({ headers });
    totalPages = Math.max(1, Math.ceil(metrics.totalCases / RECENT_CASES_PAGE_SIZE));
    safeCurrentPage = Math.min(currentPage, totalPages);
    recentCases = await getRecentCasesPage(safeCurrentPage, RECENT_CASES_PAGE_SIZE, { headers });
    rangeStart = metrics.totalCases === 0 ? 0 : (safeCurrentPage - 1) * RECENT_CASES_PAGE_SIZE + 1;
    rangeEnd = metrics.totalCases === 0 ? 0 : rangeStart + recentCases.length - 1;
    previousPageHref = safeCurrentPage > 1 ? `/dashboard?page=${safeCurrentPage - 1}` : null;
    nextPageHref = safeCurrentPage < totalPages ? `/dashboard?page=${safeCurrentPage + 1}` : null;
  } catch (error) {
    dashboardLoadError = error instanceof Error ? error.message : "Dashboard data is temporarily unavailable.";
  }

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
        {dashboardLoadError ? (
          <div className="placeholder-note">
            <strong>Dashboard data is temporarily unavailable</strong>
            <p>{dashboardLoadError}</p>
          </div>
        ) : (
          <div className="page-stack page-stack--compact">
            <CasesTable cases={recentCases} />
            <div className="pagination-bar">
              <p className="pagination-bar__summary">
                Showing {rangeStart}-{rangeEnd} of {metrics.totalCases} cases
              </p>
              <div className="pagination-bar__actions">
                {previousPageHref ? (
                  <Link href={previousPageHref} className="ui-button ui-button--ghost">
                    Previous
                  </Link>
                ) : (
                  <span className="ui-button ui-button--ghost ui-button--disabled">Previous</span>
                )}
                <span className="pagination-bar__page">
                  Page {safeCurrentPage} of {totalPages}
                </span>
                {nextPageHref ? (
                  <Link href={nextPageHref} className="ui-button ui-button--ghost">
                    Next
                  </Link>
                ) : (
                  <span className="ui-button ui-button--ghost ui-button--disabled">Next</span>
                )}
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
