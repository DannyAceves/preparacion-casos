import { apiClient, ApiRequestOptions } from "@/lib/api/client";
import { Case, CaseReadiness, CreateCaseInput } from "@/types/case";

export async function listCases(options: ApiRequestOptions = {}): Promise<Case[]> {
  return apiClient.get<Case[]>("/cases", options);
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
