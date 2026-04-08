export interface Case {
  id: string;
  client_id: string;
  case_number: string;
  case_type: string;
  status: string;
  title: string;
  summary: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateCaseInput {
  client_id: string;
  case_number: string;
  case_type: string;
  status?: string;
  title: string;
  summary?: string | null;
}

export type CasePriority = "high" | "medium" | "low" | "unknown";

export interface CaseListItem extends Case {
  client_name: string;
  priority: CasePriority;
  assigned_attorney: string | null;
  due_date: string | null;
}

export interface CaseReadinessIssue {
  code: string;
  message: string;
  severity: "info" | "warning" | "blocking";
}

export interface CaseTargetReadiness {
  target_status: "attorney_review" | "ready_for_submission" | "submitted";
  is_ready: boolean;
  blockers: CaseReadinessIssue[];
  warnings: CaseReadinessIssue[];
}

export interface CaseReadinessSummary {
  required_document_types: string[];
  present_required_document_types: string[];
  missing_required_document_types: string[];
  open_high_or_critical_inconsistency_count: number;
  open_critical_inconsistency_count: number;
  unapproved_generated_form_count: number;
  generated_form_count: number;
  attorney_approved_review_exists: boolean;
}

export interface CaseReadiness {
  case_id: string;
  case_status: string;
  summary: CaseReadinessSummary;
  targets: CaseTargetReadiness[];
}
