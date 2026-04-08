import { apiClient } from "@/lib/api/client";
import { CaseDocumentChecklist } from "@/types/workspace";

interface AddChecklistItemInput {
  caseId: string;
  label: string;
  documentType?: string | null;
  observations?: string | null;
  colorRequired?: boolean;
  englishTranslationRequired?: boolean;
  signedCopyRequired?: boolean;
  originalRequired?: boolean;
  copyOnly?: boolean;
}

interface UpdateChecklistItemInput {
  caseId: string;
  itemId: string;
  label?: string;
  documentType?: string | null;
  applies?: boolean;
  requested?: boolean;
  received?: boolean;
  validated?: boolean;
  observations?: string | null;
  colorRequired?: boolean;
  englishTranslationRequired?: boolean;
  signedCopyRequired?: boolean;
  originalRequired?: boolean;
  copyOnly?: boolean;
}

export async function getCaseDocumentChecklist(caseId: string): Promise<CaseDocumentChecklist> {
  return apiClient.get<CaseDocumentChecklist>(`/cases/${caseId}/document-checklist`);
}

export async function syncCaseDocumentChecklist(caseId: string): Promise<CaseDocumentChecklist> {
  return apiClient.post<CaseDocumentChecklist>(`/cases/${caseId}/document-checklist/generate`);
}

export async function addCaseDocumentChecklistItem(
  input: AddChecklistItemInput,
): Promise<CaseDocumentChecklist> {
  return apiClient.post<CaseDocumentChecklist>(`/cases/${input.caseId}/document-checklist/items`, {
    body: JSON.stringify({
      label: input.label,
      document_type: input.documentType || null,
      observations: input.observations || null,
      color_required: input.colorRequired ?? false,
      english_translation_required: input.englishTranslationRequired ?? false,
      signed_copy_required: input.signedCopyRequired ?? false,
      original_required: input.originalRequired ?? false,
      copy_only: input.copyOnly ?? false,
    }),
  });
}

export async function updateCaseDocumentChecklistItem(
  input: UpdateChecklistItemInput,
): Promise<CaseDocumentChecklist> {
  return apiClient.patch<CaseDocumentChecklist>(
    `/cases/${input.caseId}/document-checklist/items/${input.itemId}`,
    {
      body: JSON.stringify({
        ...(input.label !== undefined ? { label: input.label } : {}),
        ...(input.documentType !== undefined ? { document_type: input.documentType } : {}),
        ...(input.applies !== undefined ? { applies: input.applies } : {}),
        ...(input.requested !== undefined ? { requested: input.requested } : {}),
        ...(input.received !== undefined ? { received: input.received } : {}),
        ...(input.validated !== undefined ? { validated: input.validated } : {}),
        ...(input.observations !== undefined ? { observations: input.observations } : {}),
        ...(input.colorRequired !== undefined ? { color_required: input.colorRequired } : {}),
        ...(input.englishTranslationRequired !== undefined
          ? { english_translation_required: input.englishTranslationRequired }
          : {}),
        ...(input.signedCopyRequired !== undefined ? { signed_copy_required: input.signedCopyRequired } : {}),
        ...(input.originalRequired !== undefined ? { original_required: input.originalRequired } : {}),
        ...(input.copyOnly !== undefined ? { copy_only: input.copyOnly } : {}),
      }),
    },
  );
}

export async function reorderCaseDocumentChecklistItems(
  caseId: string,
  itemIds: string[],
): Promise<CaseDocumentChecklist> {
  return apiClient.post<CaseDocumentChecklist>(`/cases/${caseId}/document-checklist/reorder`, {
    body: JSON.stringify({ item_ids: itemIds }),
  });
}
