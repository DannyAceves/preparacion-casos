import { apiClient, ApiRequestOptions } from "@/lib/api/client";
import {
  Consultation,
  ConsultationConversionResult,
  ConvertConsultationInput,
  CreateConsultationInput,
  UpdateConsultationInput,
} from "@/types/consultation";

function normalizeConsultationPayload(
  input: CreateConsultationInput | UpdateConsultationInput,
): Record<string, unknown> {
  return {
    ...input,
    phone: input.phone || null,
    date_of_birth: input.date_of_birth || null,
    appointment_at: input.appointment_at || null,
    assigned_attorney: input.assigned_attorney || null,
    reception_notes: input.reception_notes || null,
    intake_answers: input.intake_answers || null,
    suggested_case_type: input.suggested_case_type || null,
    ...(input.status ? { status: input.status } : {}),
  };
}

export async function listConsultations(): Promise<Consultation[]> {
  return apiClient.get<Consultation[]>("/consultations");
}

export async function getConsultation(
  consultationId: string,
  options: ApiRequestOptions = {},
): Promise<Consultation> {
  return apiClient.get<Consultation>(`/consultations/${consultationId}`, options);
}

export async function createConsultation(input: CreateConsultationInput): Promise<Consultation> {
  return apiClient.post<Consultation>("/consultations", {
    body: JSON.stringify({
      ...normalizeConsultationPayload(input),
      status: input.status || "scheduled",
    }),
  });
}

export async function updateConsultation(
  consultationId: string,
  input: UpdateConsultationInput,
): Promise<Consultation> {
  return apiClient.patch<Consultation>(`/consultations/${consultationId}`, {
    body: JSON.stringify(normalizeConsultationPayload(input)),
  });
}

export async function convertConsultationToCase(
  consultationId: string,
  input: ConvertConsultationInput,
): Promise<ConsultationConversionResult> {
  return apiClient.post<ConsultationConversionResult>(`/consultations/${consultationId}/convert`, {
    body: JSON.stringify({
      ...input,
      case_type: input.case_type || null,
      summary: input.summary || null,
    }),
  });
}
