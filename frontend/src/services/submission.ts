import { apiClient } from "@/lib/api/client";
import { Case } from "@/types/case";
import { CaseSubmissionRead } from "@/types/workspace-submission";

interface ApproveSubmissionInput {
  caseId: string;
  approvedByUserId: string;
  notes?: string;
}

interface SubmitCaseInput {
  caseId: string;
  submittedByUserId: string;
  submissionReference: string;
  notes?: string;
}

interface FailSubmissionInput {
  caseId: string;
  failedByUserId: string;
  failureReason: string;
}

interface CloseCaseInput {
  caseId: string;
  closedByUserId: string;
  notes?: string;
}

export async function approveForSubmission(input: ApproveSubmissionInput): Promise<CaseSubmissionRead> {
  return apiClient.post<CaseSubmissionRead>(`/cases/${input.caseId}/submission/approve`, {
    body: JSON.stringify({
      approved_by_user_id: input.approvedByUserId,
      notes: input.notes || undefined,
    }),
  });
}

export async function submitCase(input: SubmitCaseInput): Promise<CaseSubmissionRead> {
  return apiClient.post<CaseSubmissionRead>(`/cases/${input.caseId}/submission/submit`, {
    body: JSON.stringify({
      submitted_by_user_id: input.submittedByUserId,
      submission_reference: input.submissionReference,
      notes: input.notes || undefined,
    }),
  });
}

export async function failSubmission(input: FailSubmissionInput): Promise<CaseSubmissionRead> {
  return apiClient.post<CaseSubmissionRead>(`/cases/${input.caseId}/submission/fail`, {
    body: JSON.stringify({
      failed_by_user_id: input.failedByUserId,
      failure_reason: input.failureReason,
    }),
  });
}

export async function closeCase(input: CloseCaseInput): Promise<Case> {
  return apiClient.post<Case>(`/cases/${input.caseId}/close`, {
    body: JSON.stringify({
      closed_by_user_id: input.closedByUserId,
      notes: input.notes || undefined,
    }),
  });
}
