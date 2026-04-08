import { ApiRequestOptions } from "@/lib/api/client";
import { listCases } from "@/services/cases";
import { Case } from "@/types/case";

export interface DashboardMetrics {
  totalCases: number;
  draftCases: number;
  activeReviewCases: number;
  submissionReadyCases: number;
  recentCases: Case[];
}

export async function getDashboardMetrics(options: ApiRequestOptions = {}): Promise<DashboardMetrics> {
  const cases = await listCases(options);

  return {
    totalCases: cases.length,
    draftCases: cases.filter((item) => item.status === "draft").length,
    activeReviewCases: cases.filter((item) => item.status === "attorney_review").length,
    submissionReadyCases: cases.filter((item) => item.status === "ready_for_submission").length,
    recentCases: [...cases]
      .sort((left, right) => right.updated_at.localeCompare(left.updated_at))
      .slice(0, 5),
  };
}
