import { apiClient } from "@/lib/api/client";
import { DocumentRecord } from "@/types/workspace";

interface UploadCaseDocumentInput {
  caseId: string;
  uploadedByUserId: string;
  file: File;
  documentStatus?: string;
  classificationLabel?: string;
  classificationSource?: string;
}

interface ReplaceDocumentInput {
  documentId: string;
  uploadedByUserId: string;
  file: File;
  documentStatus?: string;
  replacementNotes?: string;
}

interface ReprocessDocumentInput {
  documentId: string;
  actorReference: string;
}

function buildUploadFormData(input: UploadCaseDocumentInput): FormData {
  const formData = new FormData();
  formData.set("uploaded_by_user_id", input.uploadedByUserId);
  formData.set("file", input.file);
  formData.set("document_status", input.documentStatus ?? "uploaded");

  if (input.classificationLabel) {
    formData.set("classification_label", input.classificationLabel);
  }

  if (input.classificationSource) {
    formData.set("classification_source", input.classificationSource);
  }

  return formData;
}

function buildReplaceFormData(input: ReplaceDocumentInput): FormData {
  const formData = new FormData();
  formData.set("uploaded_by_user_id", input.uploadedByUserId);
  formData.set("file", input.file);

  if (input.documentStatus) {
    formData.set("document_status", input.documentStatus);
  }

  if (input.replacementNotes) {
    formData.set("replacement_notes", input.replacementNotes);
  }

  return formData;
}

export async function uploadCaseDocument(input: UploadCaseDocumentInput): Promise<DocumentRecord> {
  return apiClient.post<DocumentRecord>(`/cases/${input.caseId}/documents/upload`, {
    body: buildUploadFormData(input),
  });
}

export async function replaceDocument(input: ReplaceDocumentInput): Promise<DocumentRecord> {
  return apiClient.post<DocumentRecord>(`/documents/${input.documentId}/replace`, {
    body: buildReplaceFormData(input),
  });
}

export async function reprocessDocument(input: ReprocessDocumentInput): Promise<{ status: string }> {
  return apiClient.post<{ status: string }>(`/documents/${input.documentId}/reprocess`, {
    body: JSON.stringify({ actor_reference: input.actorReference }),
  });
}
