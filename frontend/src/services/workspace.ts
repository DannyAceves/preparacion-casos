import { apiClient } from "@/lib/api/client";
import { getCaseDocumentChecklist } from "@/services/document-checklist";
import { ApiErrorPayload } from "@/types/api";
import { CaseWorkspaceData } from "@/types/workspace";

async function optionalGet<T>(path: string): Promise<T | null> {
  try {
    return await apiClient.get<T>(path);
  } catch (error) {
    const apiError = error as ApiErrorPayload;
    if (apiError.status === 404) {
      return null;
    }
    throw error;
  }
}

export async function getCaseWorkspace(caseId: string): Promise<CaseWorkspaceData> {
  const [
    questionnaire,
    documents,
    documentChecklist,
    canonicalFields,
    inconsistencies,
    reviews,
    forms,
    packet,
    submission,
    timeline,
  ] = await Promise.all([
    optionalGet<CaseWorkspaceData["questionnaire"]>(`/cases/${caseId}/questionnaire`),
    apiClient.get<CaseWorkspaceData["documents"]>(`/cases/${caseId}/documents`),
    getCaseDocumentChecklist(caseId),
    apiClient.get<CaseWorkspaceData["canonicalFields"]>(`/cases/${caseId}/canonical-fields`),
    apiClient.get<CaseWorkspaceData["inconsistencies"]>(`/cases/${caseId}/inconsistencies`),
    apiClient.get<CaseWorkspaceData["reviews"]>(`/cases/${caseId}/reviews`),
    apiClient.get<CaseWorkspaceData["forms"]>(`/cases/${caseId}/forms`),
    optionalGet<CaseWorkspaceData["packet"]>(`/cases/${caseId}/packet`),
    optionalGet<CaseWorkspaceData["submission"]>(`/cases/${caseId}/submission`),
    apiClient.get<CaseWorkspaceData["timeline"]>(`/cases/${caseId}/timeline`),
  ]);

  return {
    questionnaire,
    documents,
    documentChecklist,
    canonicalFields,
    inconsistencies,
    reviews,
    forms,
    packet,
    submission,
    timeline,
  };
}
