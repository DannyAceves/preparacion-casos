export interface CaseSubmissionRead {
  id: string;
  case_id: string;
  status: "draft" | "approved_for_submission" | "submitted" | "failed";
  approved_for_submission_at: string | null;
  approved_by_user_id: string | null;
  submitted_at: string | null;
  submitted_by_user_id: string | null;
  submission_reference: string | null;
  failed_at: string | null;
  failed_by_user_id: string | null;
  failure_reason: string | null;
  created_at: string;
  updated_at: string;
}
