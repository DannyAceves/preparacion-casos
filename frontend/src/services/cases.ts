import { apiClient, ApiRequestOptions } from "@/lib/api/client";
import { Case, CaseReadiness, CreateCaseInput } from "@/types/case";

export interface ListCasesQuery {
  limit?: number;
  offset?: number;
  sort_by?: "created_at" | "updated_at" | "case_number" | "title" | "status" | "case_type";
  sort_order?: "asc" | "desc";
}

export async function listCases(options: ApiRequestOptions = {}, query: ListCasesQuery = {}): Promise<Case[]> {
  return apiClient.get<Case[]>("/cases", {
    ...options,
    query: {
      ...(options.query ?? {}),
      ...query,
    },
  });
}

export async function createCase(input: CreateCaseInput): Promise<Case> {
  return apiClient.post<Case>("/cases", {
    body: JSON.stringify({
      ...input,
      status: input.status ?? "draft",
      summary: input.summary || null,
    }),
  });
}

export async function getCase(caseId: string, options: ApiRequestOptions = {}): Promise<Case> {
  return apiClient.get<Case>(`/cases/${caseId}`, options);
}

export async function getCaseReadiness(
  caseId: string,
  options: ApiRequestOptions = {},
): Promise<CaseReadiness> {
  return apiClient.get<CaseReadiness>(`/cases/${caseId}/readiness`, options);
}
