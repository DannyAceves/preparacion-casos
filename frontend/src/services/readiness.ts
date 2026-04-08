import { apiClient } from "@/lib/api/client";
import { Case, CaseReadiness } from "@/types/case";

interface ValidateReadinessInput {
  caseId: string;
  actorReference?: string;
}

export async function validateCaseReadiness(input: ValidateReadinessInput): Promise<CaseReadiness> {
  return apiClient.post<CaseReadiness>(`/cases/${input.caseId}/validate-readiness`, {
    body: JSON.stringify({
      actor_reference: input.actorReference || undefined,
    }),
  });
}

interface TransitionCaseInput {
  caseId: string;
  targetStatus: "attorney_review" | "ready_for_submission" | "submitted";
  actorReference?: string;
  notes?: string;
}

export async function transitionCase(input: TransitionCaseInput): Promise<Case> {
  return apiClient.post<Case>(`/cases/${input.caseId}/transition`, {
    body: JSON.stringify({
      target_status: input.targetStatus,
      actor_reference: input.actorReference || undefined,
      notes: input.notes || undefined,
    }),
  });
}
