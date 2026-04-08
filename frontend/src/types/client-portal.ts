import { CaseDocumentChecklist, CaseQuestionnaire, DocumentRecord, QuestionnaireQuestion } from "@/types/workspace";

export interface ClientPortalAccess {
  case_id: string;
  token_last4: string;
  instructions: string | null;
  expires_at: string | null;
  is_active: boolean;
  last_accessed_at: string | null;
  failed_access_attempt_count: number;
  last_failed_access_at: string | null;
  locked_until: string | null;
  access_session_expires_at: string | null;
}

export interface ClientPortalIssuedAccess extends ClientPortalAccess {
  token: string;
  passcode: string;
  portal_path: string;
}

export interface ClientPortalProgress {
  questionnaire_total_questions: number;
  questionnaire_answered_questions: number;
  questionnaire_percent_complete: number;
  checklist_applicable_items: number;
  checklist_received_items: number;
  checklist_validated_items: number;
  checklist_percent_complete: number;
  overall_percent_complete: number;
}

export interface ClientPortalContext {
  case_id: string;
  case_number: string;
  case_type: string;
  case_title: string;
  case_summary: string | null;
  instructions: string | null;
  access_expires_at: string | null;
  session_token: string;
  session_expires_at: string | null;
  questionnaire: CaseQuestionnaire | null;
  checklist: CaseDocumentChecklist;
  documents: DocumentRecord[];
  progress: ClientPortalProgress;
}

export interface ClientPortalSession {
  session_token: string;
  session_expires_at: string | null;
}

export interface IssueClientPortalAccessInput {
  instructions?: string | null;
  expires_in_days?: number;
}

export interface ClientPortalQuestionnaireValue {
  answer_text?: string | null;
  answer_date?: string | null;
  answer_boolean?: boolean | null;
  answer_choice?: string | null;
  answer_choices?: string[] | null;
  answer_json?: Record<string, unknown> | unknown[] | null;
}

export interface SaveClientPortalAnswerInput {
  token?: string;
  passcode?: string;
  portalSessionToken?: string;
  question: QuestionnaireQuestion;
  value: ClientPortalQuestionnaireValue;
}

export interface UploadClientPortalDocumentInput {
  token?: string;
  passcode?: string;
  portalSessionToken?: string;
  file: File;
  checklistItemId?: string | null;
  documentType?: string | null;
}
