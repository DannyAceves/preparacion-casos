import { CaseSubmissionRead } from "@/types/workspace-submission";

export interface QuestionnaireAnswer {
  id: string;
  case_id: string;
  question_id: string;
  answer_text: string | null;
  answer_date: string | null;
  answer_boolean: boolean | null;
  answer_choice: string | null;
  answer_choices: string[] | null;
  answer_json: Record<string, unknown> | unknown[] | null;
  created_at: string;
  updated_at: string;
}

export interface QuestionnaireQuestionOption {
  label: string;
  value: string;
}

export interface QuestionnaireQuestion {
  id: string;
  key: string;
  prompt: string;
  help_text: string | null;
  input_type:
    | "text"
    | "textarea"
    | "date"
    | "checkbox"
    | "radio"
    | "select"
    | "repeatable_group"
    | "boolean"
    | "single_select"
    | "multi_select"
    | "json";
  is_required: boolean;
  display_order: number;
  options: QuestionnaireQuestionOption[] | null;
  validation_rules: Record<string, unknown> | null;
  conditional_rules: Record<string, unknown> | null;
  field_config: Record<string, unknown> | null;
  answer: QuestionnaireAnswer | null;
}

export interface QuestionnaireSection {
  id: string;
  title: string;
  description: string | null;
  display_order: number;
  questions: QuestionnaireQuestion[];
}

export interface QuestionnaireTemplateSummary {
  id: string;
  case_type: string;
  title: string;
  description: string | null;
  status: string;
  version: number;
}

export interface CaseQuestionnaire {
  case_id: string;
  case_type: string;
  questionnaire: QuestionnaireTemplateSummary;
  questionnaire_instance_id: string | null;
  questionnaire_instance_status: string | null;
  questionnaire_instance_version: number | null;
  sections: QuestionnaireSection[];
}

export interface DocumentRecord {
  id: string;
  case_id: string;
  uploaded_by_user_id: string;
  document_type: string;
  original_filename: string;
  stored_filename: string;
  storage_backend: string;
  storage_key: string;
  mime_type: string;
  size_bytes: number;
  sha256_hash: string;
  document_status: string;
  processing_status: string;
  classification_label: string | null;
  classification_source: string | null;
  classification_confidence_score: number | null;
  file_metadata: Record<string, unknown> | null;
  extracted_text: string | null;
  extracted_fields: Record<string, unknown> | unknown[] | null;
  extracted_metadata: Record<string, unknown> | null;
  version_number: number;
  is_current: boolean;
  previous_version_id: string | null;
  root_document_id: string | null;
  replacement_notes: string | null;
  uploaded_at: string;
  created_at: string;
  updated_at: string;
}

export interface CaseDocumentChecklistItem {
  id: string;
  case_id: string;
  template_item_id: string | null;
  label: string;
  document_type: string | null;
  display_order: number;
  applies: boolean;
  requested: boolean;
  received: boolean;
  validated: boolean;
  observations: string | null;
  color_required: boolean;
  english_translation_required: boolean;
  signed_copy_required: boolean;
  original_required: boolean;
  copy_only: boolean;
  is_manual: boolean;
  linked_document_ids: string[];
  linked_document_count: number;
  created_at: string;
  updated_at: string;
}

export interface CaseDocumentChecklistProgress {
  total_items: number;
  applicable_items: number;
  requested_items: number;
  received_items: number;
  validated_items: number;
  percent_complete: number;
}

export interface CaseDocumentChecklist {
  case_id: string;
  template_case_type: string | null;
  items: CaseDocumentChecklistItem[];
  progress: CaseDocumentChecklistProgress;
}

export interface CanonicalFieldRecord {
  id: string;
  case_id: string;
  source_document_id: string | null;
  field_key: string;
  field_value: Record<string, unknown> | unknown[] | string | number | boolean | null;
  confidence_score: string | null;
  source_priority: number;
  status: "suggested" | "confirmed" | "approved" | "rejected";
  created_at: string;
  updated_at: string;
}

export interface InconsistencyRecord {
  id: string;
  case_id: string;
  field_key: string;
  severity: "low" | "medium" | "high" | "critical";
  status: "open" | "under_review" | "resolved" | "dismissed";
  description: string;
  evidence_payload: Record<string, unknown> | unknown[] | null;
  resolution_notes: string | null;
  resolved_by_user_id: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReviewRecord {
  id: string;
  case_id: string;
  review_type: "paralegal" | "attorney" | "qa";
  reviewer_reference: string;
  decision: "fix_required" | "changes_requested" | "approved" | "rejected";
  notes: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface GeneratedFormTemplate {
  form_id: string;
  form_code: string;
  form_name: string;
  version: number;
  case_type_id: string;
}

export interface GeneratedFormSuggestion {
  source_type: string;
  source_key: string;
  source_label: string;
  value: Record<string, unknown> | unknown[] | string | number | boolean | null;
  confidence_score: number | null;
  source_document_id: string | null;
  source_document_name: string | null;
}

export interface AssistedFormFieldRecord {
  form_field_key: string;
  canonical_field_key: string;
  section_key: string;
  section_title: string;
  field_label: string;
  field_type: string;
  help_text: string | null;
  required: boolean;
  display_order: number;
  value: Record<string, unknown> | unknown[] | string | number | boolean | null;
  manual_override: boolean;
  selected_source_key: string | null;
  selected_source_label: string | null;
  warnings: Array<Record<string, unknown>>;
  suggestions: GeneratedFormSuggestion[];
}

export interface AssistedFormSectionRecord {
  section_key: string;
  section_title: string;
  display_order: number;
  fields: AssistedFormFieldRecord[];
}

export interface AssistedFormWorkspaceRecord {
  generated_form_id: string;
  case_id: string;
  status: "draft" | "review_pending" | "approved" | "fix_required";
  form: GeneratedFormTemplate;
  sections: AssistedFormSectionRecord[];
  warnings: Array<Record<string, unknown>>;
}

export interface GeneratedFormRecord {
  id: string;
  case_id: string;
  form_id: string;
  draft_version: number;
  status: "draft" | "review_pending" | "approved" | "fix_required";
  generated_payload: Record<string, unknown> | unknown[];
  warnings_payload: Array<Record<string, unknown>> | Record<string, unknown> | null;
  export_path: string | null;
  review_notes: string | null;
  generated_at: string;
  reviewed_by_user_id: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface GeneratedFormDetailRecord extends GeneratedFormRecord {
  form: GeneratedFormTemplate;
  workspace: AssistedFormWorkspaceRecord | null;
}

export interface PacketDocumentItem {
  document_id: string;
  document_type: string;
  title: string;
  original_filename: string;
  classification_label: string | null;
  classification_confidence_score: number | null;
  document_status: string;
  processing_status: string;
  priority: number;
  section: string;
  uploaded_at: string;
}

export interface PacketSummary {
  case_id: string;
  case_number: string;
  case_type: string;
  case_status: string;
  title: string;
  client: Record<string, unknown>;
  participants: Array<Record<string, unknown>>;
  canonical_fields: Array<Record<string, unknown>>;
  open_inconsistency_count: number;
  latest_review: Record<string, unknown> | null;
}

export interface PacketChecklistItem {
  item_key: string;
  label: string;
  status: "ready" | "missing" | "warning";
  required: boolean;
  related_document_type: string | null;
  notes: string | null;
}

export interface PacketExportArtifact {
  artifact_type: "case_review_packet";
  format: "json";
  generated_at: string;
  packet_version: number;
  sections: Array<Record<string, unknown>>;
  prefilled_forms_placeholder: Record<string, unknown>;
}

export interface CasePacketRecord {
  id: string;
  case_id: string;
  packet_version: number;
  packet_status: "generated" | "stale" | "approved";
  generated_by_reference: string | null;
  summary_payload: PacketSummary | Record<string, unknown> | unknown[];
  document_index: PacketDocumentItem[] | Record<string, unknown> | unknown[];
  checklist_payload: PacketChecklistItem[] | Record<string, unknown> | unknown[];
  export_artifact: PacketExportArtifact | Record<string, unknown> | unknown[];
  generation_notes: string | null;
  generated_at: string;
  created_at: string;
  updated_at: string;
}

export interface TimelineEventRecord {
  id: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  action: string;
  actor_reference: string | null;
  occurred_at: string;
  payload: Record<string, unknown> | unknown[] | null;
}

export interface CaseWorkspaceData {
  questionnaire: CaseQuestionnaire | null;
  documents: DocumentRecord[];
  documentChecklist: CaseDocumentChecklist;
  canonicalFields: CanonicalFieldRecord[];
  inconsistencies: InconsistencyRecord[];
  reviews: ReviewRecord[];
  forms: GeneratedFormRecord[];
  packet: CasePacketRecord | null;
  submission: CaseSubmissionRead | null;
  timeline: TimelineEventRecord[];
}
