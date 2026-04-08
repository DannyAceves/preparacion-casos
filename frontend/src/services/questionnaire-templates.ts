import { apiClient } from "@/lib/api/client";
import {
  CreateQuestionnaireTemplateInput,
  CreateQuestionnaireTemplateVersionInput,
  QuestionnaireInstance,
  QuestionnaireTemplate,
  QuestionnaireTemplateOption,
  QuestionnaireTemplateSection,
  UpdateQuestionnaireTemplateInput,
} from "@/types/questionnaire-template";

function normalizeOptions(options: QuestionnaireTemplateOption[] | null): QuestionnaireTemplateOption[] | null {
  if (!options?.length) {
    return null;
  }
  return options
    .map((option) => ({
      label: option.label.trim(),
      value: option.value.trim(),
    }))
    .filter((option) => option.label && option.value);
}

function serializeSections(sections: QuestionnaireTemplateSection[]): unknown[] {
  return sections.map((section, sectionIndex) => ({
    title: section.title.trim(),
    description: section.description?.trim() || null,
    display_order: section.display_order ?? sectionIndex,
    questions: section.questions.map((question, questionIndex) => ({
      key: question.key.trim(),
      prompt: question.prompt.trim(),
      help_text: question.help_text?.trim() || null,
      input_type: question.input_type,
      is_required: question.is_required,
      display_order: question.display_order ?? questionIndex,
      options: normalizeOptions(question.options),
      validation_rules: question.validation_rules,
      conditional_rules: question.conditional_rules,
      field_config: question.field_config,
    })),
  }));
}

export async function listQuestionnaireTemplates(caseType?: string): Promise<QuestionnaireTemplate[]> {
  return apiClient.get<QuestionnaireTemplate[]>("/questionnaire-templates", {
    query: caseType ? { case_type: caseType } : undefined,
  });
}

export async function getQuestionnaireTemplate(templateId: string): Promise<QuestionnaireTemplate> {
  return apiClient.get<QuestionnaireTemplate>(`/questionnaire-templates/${templateId}`);
}

export async function createQuestionnaireTemplate(
  input: CreateQuestionnaireTemplateInput,
): Promise<QuestionnaireTemplate> {
  return apiClient.post<QuestionnaireTemplate>("/questionnaire-templates", {
    body: JSON.stringify({
      case_type: input.case_type.trim(),
      title: input.title.trim(),
      description: input.description?.trim() || null,
      status: input.status ?? "draft",
      sections: serializeSections(input.sections),
    }),
  });
}

export async function updateQuestionnaireTemplate(
  templateId: string,
  input: UpdateQuestionnaireTemplateInput,
): Promise<QuestionnaireTemplate> {
  return apiClient.patch<QuestionnaireTemplate>(`/questionnaire-templates/${templateId}`, {
    body: JSON.stringify({
      ...(input.title !== undefined ? { title: input.title.trim() } : {}),
      ...(input.description !== undefined ? { description: input.description?.trim() || null } : {}),
      ...(input.status !== undefined ? { status: input.status } : {}),
      ...(input.sections !== undefined ? { sections: serializeSections(input.sections) } : {}),
    }),
  });
}

export async function activateQuestionnaireTemplate(templateId: string): Promise<QuestionnaireTemplate> {
  return apiClient.post<QuestionnaireTemplate>(`/questionnaire-templates/${templateId}/activate`, {
    body: JSON.stringify({}),
  });
}

export async function createQuestionnaireTemplateVersion(
  templateId: string,
  input: CreateQuestionnaireTemplateVersionInput = {},
): Promise<QuestionnaireTemplate> {
  return apiClient.post<QuestionnaireTemplate>(`/questionnaire-templates/${templateId}/versions`, {
    body: JSON.stringify({
      title: input.title?.trim() || null,
      description: input.description?.trim() || null,
      status: input.status ?? "draft",
    }),
  });
}

export async function instantiateCaseQuestionnaire(
  caseId: string,
  templateId?: string,
): Promise<QuestionnaireInstance> {
  return apiClient.post<QuestionnaireInstance>(`/cases/${caseId}/questionnaire/instantiate`, {
    body: JSON.stringify({
      template_id: templateId ?? null,
    }),
  });
}
