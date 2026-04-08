import { apiClient } from "@/lib/api/client";
import { appConfig } from "@/lib/config";
import { ApiErrorPayload } from "@/types/api";
import {
  ClientPortalAccess,
  ClientPortalContext,
  ClientPortalIssuedAccess,
  ClientPortalSession,
  ClientPortalQuestionnaireValue,
  IssueClientPortalAccessInput,
  SaveClientPortalAnswerInput,
  UploadClientPortalDocumentInput,
} from "@/types/client-portal";
import { CaseDocumentChecklist, DocumentRecord, QuestionnaireAnswer, QuestionnaireQuestion } from "@/types/workspace";

interface ClientPortalDocumentUploadResponse {
  document: DocumentRecord;
  checklist: CaseDocumentChecklist;
}

function buildAbsoluteUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const baseUrl = typeof window === "undefined" ? appConfig.apiInternalBaseUrl : appConfig.apiBaseUrl;
  return new URL(`${baseUrl}${normalizedPath}`).toString();
}

async function parseJsonSafe<T>(response: Response): Promise<T | null> {
  const text = await response.text();
  if (!text) {
    return null;
  }
  return JSON.parse(text) as T;
}

async function getNullable<T>(path: string): Promise<T | null> {
  const response = await fetch(buildAbsoluteUrl(path), {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await parseJsonSafe<unknown>(response);
    throw {
      message: `API request failed for ${path} (${response.status})`,
      status: response.status,
      detail,
    } satisfies ApiErrorPayload;
  }

  return parseJsonSafe<T | null>(response);
}

function buildPortalAuthFormData(token: string, passcode: string): FormData {
  const formData = new FormData();
  formData.set("token", token);
  formData.set("passcode", passcode);
  return formData;
}

function buildPortalSessionFormData(portalSessionToken: string): FormData {
  const formData = new FormData();
  formData.set("portal_session_token", portalSessionToken);
  return formData;
}

function appendQuestionnaireValue(
  formData: FormData,
  question: QuestionnaireQuestion,
  value: ClientPortalQuestionnaireValue,
): void {
  if (question.input_type === "text" && value.answer_text !== undefined && value.answer_text !== null) {
    formData.set("answer_text", value.answer_text);
  }

  if (question.input_type === "date" && value.answer_date) {
    formData.set("answer_date", value.answer_date);
  }

  if (question.input_type === "boolean" && value.answer_boolean !== undefined && value.answer_boolean !== null) {
    formData.set("answer_boolean", String(value.answer_boolean));
  }

  if (question.input_type === "single_select" && value.answer_choice) {
    formData.set("answer_choice", value.answer_choice);
  }

  if (question.input_type === "multi_select" && value.answer_choices) {
    formData.set("answer_choices", value.answer_choices.join(","));
  }

  if (question.input_type === "json" && value.answer_json !== undefined && value.answer_json !== null) {
    formData.set("answer_json", JSON.stringify(value.answer_json));
  }
}

function buildQuestionnaireValuePayload(input: SaveClientPortalAnswerInput): ClientPortalQuestionnaireValue {
  const { question, value } = input;

  if (question.input_type === "text") {
    return { answer_text: value.answer_text ?? "" };
  }

  if (question.input_type === "date") {
    return { answer_date: value.answer_date ?? null };
  }

  if (question.input_type === "boolean") {
    return { answer_boolean: value.answer_boolean ?? null };
  }

  if (question.input_type === "single_select") {
    return { answer_choice: value.answer_choice ?? null };
  }

  if (question.input_type === "multi_select") {
    return { answer_choices: value.answer_choices ?? [] };
  }

  return { answer_json: value.answer_json ?? null };
}

export async function getCaseClientPortalAccess(caseId: string): Promise<ClientPortalAccess | null> {
  return getNullable<ClientPortalAccess>(`/cases/${caseId}/client-portal/access`);
}

export async function issueCaseClientPortalAccess(
  caseId: string,
  input: IssueClientPortalAccessInput,
): Promise<ClientPortalIssuedAccess> {
  return apiClient.post<ClientPortalIssuedAccess>(`/cases/${caseId}/client-portal/access/issue`, {
    body: JSON.stringify({
      instructions: input.instructions ?? null,
      expires_in_days: input.expires_in_days ?? 7,
    }),
  });
}

export async function getClientPortalContext(token: string, passcode: string): Promise<ClientPortalContext> {
  return apiClient.post<ClientPortalContext>("/client-portal/access/context", {
    body: buildPortalAuthFormData(token, passcode),
  });
}

export async function authenticateClientPortal(token: string, passcode: string): Promise<ClientPortalSession> {
  return apiClient.post<ClientPortalSession>("/client-portal/access/authenticate", {
    body: buildPortalAuthFormData(token, passcode),
  });
}

export async function getClientPortalContextWithSession(portalSessionToken: string): Promise<ClientPortalContext> {
  return apiClient.post<ClientPortalContext>("/client-portal/access/context", {
    body: buildPortalSessionFormData(portalSessionToken),
  });
}

export async function saveClientPortalAnswer(input: SaveClientPortalAnswerInput): Promise<QuestionnaireAnswer> {
  const payload = buildQuestionnaireValuePayload(input);
  const formData = input.portalSessionToken
    ? buildPortalSessionFormData(input.portalSessionToken)
    : buildPortalAuthFormData(input.token ?? "", input.passcode ?? "");
  appendQuestionnaireValue(formData, input.question, payload);

  if (input.question.answer?.id) {
    return apiClient.patch<QuestionnaireAnswer>(
      `/client-portal/access/questionnaire/answers/${input.question.answer.id}`,
      { body: formData },
    );
  }

  formData.set("question_id", input.question.id);
  return apiClient.post<QuestionnaireAnswer>("/client-portal/access/questionnaire/answers", {
    body: formData,
  });
}

export async function uploadClientPortalDocument(
  input: UploadClientPortalDocumentInput,
): Promise<ClientPortalDocumentUploadResponse> {
  const formData = input.portalSessionToken
    ? buildPortalSessionFormData(input.portalSessionToken)
    : buildPortalAuthFormData(input.token ?? "", input.passcode ?? "");
  formData.set("file", input.file);

  if (input.checklistItemId) {
    formData.set("checklist_item_id", input.checklistItemId);
  }

  if (input.documentType) {
    formData.set("document_type", input.documentType);
  }

  return apiClient.post<ClientPortalDocumentUploadResponse>("/client-portal/access/documents/upload", {
    body: formData,
  });
}
