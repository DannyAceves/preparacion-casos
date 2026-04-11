import { ApiRequestOptions } from "@/lib/api/client";
import { listCases } from "@/services/cases";
import { Case } from "@/types/case";

export interface DashboardMetrics {
  totalCases: number;
  draftCases: number;
  activeReviewCases: number;
  submissionReadyCases: number;
}

export async function getDashboardMetrics(options: ApiRequestOptions = {}): Promise<DashboardMetrics> {
  const cases = await listCases(options);

  return {
    totalCases: cases.length,
    draftCases: cases.filter((item) => item.status === "draft").length,
    activeReviewCases: cases.filter((item) => item.status === "attorney_review").length,
    submissionReadyCases: cases.filter((item) => item.status === "ready_for_submission").length,
  };
}

export async function getRecentCasesPage(
  page: number,
  pageSize: number,
  options: ApiRequestOptions = {},
): Promise<Case[]> {
  const safePage = Math.max(1, page);
  const safePageSize = Math.max(1, pageSize);
  return listCases(options, {
    limit: safePageSize,
    offset: (safePage - 1) * safePageSize,
    sort_by: "updated_at",
    sort_order: "desc",
  });
}
