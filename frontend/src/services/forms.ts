import { apiClient } from "@/lib/api/client";
import {
  AssistedFormWorkspaceRecord,
  GeneratedFormDetailRecord,
  GeneratedFormRecord,
} from "@/types/workspace";

interface GenerateFormsInput {
  caseId: string;
  generatedByReference?: string;
  exportBasePath?: string;
}

interface ReviewGeneratedFormInput {
  generatedFormId: string;
  reviewedByUserId: string;
  reviewNotes?: string;
}

interface UpdateAssistedFormFieldInput {
  generatedFormId: string;
  formFieldKey: string;
  actorReference?: string;
  value: Record<string, unknown> | unknown[] | string | number | boolean | null;
  manualOverride?: boolean;
  selectedSourceKey?: string | null;
  selectedSourceLabel?: string | null;
}

export async function generateForms(input: GenerateFormsInput): Promise<GeneratedFormRecord[]> {
  return apiClient.post<GeneratedFormRecord[]>(`/cases/${input.caseId}/forms/generate`, {
    body: JSON.stringify({
      generated_by_reference: input.generatedByReference || undefined,
      export_base_path: input.exportBasePath || undefined,
    }),
  });
}

export async function getGeneratedFormDetail(generatedFormId: string): Promise<GeneratedFormDetailRecord> {
  return apiClient.get<GeneratedFormDetailRecord>(`/generated-forms/${generatedFormId}`);
}

export async function getGeneratedFormWorkspace(generatedFormId: string): Promise<AssistedFormWorkspaceRecord> {
  return apiClient.get<AssistedFormWorkspaceRecord>(`/generated-forms/${generatedFormId}/workspace`);
}

export async function updateAssistedFormField(
  input: UpdateAssistedFormFieldInput,
): Promise<GeneratedFormDetailRecord> {
  return apiClient.patch<GeneratedFormDetailRecord>(
    `/generated-forms/${input.generatedFormId}/workspace/fields/${encodeURIComponent(input.formFieldKey)}`,
    {
      body: JSON.stringify({
        actor_reference: input.actorReference,
        value: input.value,
        manual_override: input.manualOverride ?? true,
        selected_source_key: input.selectedSourceKey ?? null,
        selected_source_label: input.selectedSourceLabel ?? null,
      }),
    },
  );
}

export async function approveGeneratedForm(input: ReviewGeneratedFormInput): Promise<GeneratedFormRecord> {
  return apiClient.post<GeneratedFormRecord>(`/generated-forms/${input.generatedFormId}/approve`, {
    body: JSON.stringify({
      reviewed_by_user_id: input.reviewedByUserId,
      review_notes: input.reviewNotes || undefined,
    }),
  });
}

export async function markGeneratedFormFixRequired(input: ReviewGeneratedFormInput): Promise<GeneratedFormRecord> {
  return apiClient.post<GeneratedFormRecord>(`/generated-forms/${input.generatedFormId}/fix`, {
    body: JSON.stringify({
      reviewed_by_user_id: input.reviewedByUserId,
      review_notes: input.reviewNotes || undefined,
    }),
  });
}
