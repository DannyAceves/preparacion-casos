export type QuestionnaireTemplateInputType =
  | "text"
  | "textarea"
  | "date"
  | "checkbox"
  | "radio"
  | "select"
  | "repeatable_group";

export interface QuestionnaireTemplateOption {
  label: string;
  value: string;
}

export interface QuestionnaireTemplateQuestion {
  id?: string;
  section_id?: string;
  key: string;
  prompt: string;
  help_text: string | null;
  input_type: QuestionnaireTemplateInputType;
  is_required: boolean;
  display_order: number;
  options: QuestionnaireTemplateOption[] | null;
  validation_rules: Record<string, unknown> | null;
  conditional_rules: Record<string, unknown> | null;
  field_config: Record<string, unknown> | null;
  created_at?: string;
  updated_at?: string;
}

export interface QuestionnaireTemplateSection {
  id?: string;
  template_id?: string;
  title: string;
  description: string | null;
  display_order: number;
  questions: QuestionnaireTemplateQuestion[];
  created_at?: string;
  updated_at?: string;
}

export interface QuestionnaireTemplate {
  id: string;
  case_type: string;
  title: string;
  description: string | null;
  status: "draft" | "active" | "archived";
  version: number;
  sections: QuestionnaireTemplateSection[];
  created_at: string;
  updated_at: string;
}

export interface CreateQuestionnaireTemplateInput {
  case_type: string;
  title: string;
  description?: string | null;
  status?: "draft" | "active" | "archived";
  sections: QuestionnaireTemplateSection[];
}

export interface UpdateQuestionnaireTemplateInput {
  title?: string;
  description?: string | null;
  status?: "draft" | "active" | "archived";
  sections?: QuestionnaireTemplateSection[];
}

export interface CreateQuestionnaireTemplateVersionInput {
  title?: string;
  description?: string | null;
  status?: "draft" | "active" | "archived";
}

export interface QuestionnaireInstance {
  id: string;
  case_id: string;
  template_id: string | null;
  title: string;
  status: string;
  version: number;
  template_version: number | null;
  created_at: string;
  updated_at: string;
}
