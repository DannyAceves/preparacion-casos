import { apiClient } from "@/lib/api/client";
import { CanonicalFieldRecord } from "@/types/workspace";

interface UpdateCanonicalFieldInput {
  caseId: string;
  fieldKey: string;
  actorReference?: string;
  fieldValue?: Record<string, unknown> | unknown[] | string | number | boolean | null;
  confidenceScore?: string | null;
  sourcePriority?: number | null;
  status?: "suggested" | "confirmed" | "approved" | "rejected" | null;
}

export async function updateCanonicalField(input: UpdateCanonicalFieldInput): Promise<CanonicalFieldRecord> {
  const payload: Record<string, unknown> = {};

  if (input.actorReference) {
    payload.actor_reference = input.actorReference;
  }
  if (input.fieldValue !== undefined) {
    payload.field_value = input.fieldValue;
  }
  if (input.confidenceScore !== undefined) {
    payload.confidence_score = input.confidenceScore === "" ? null : input.confidenceScore;
  }
  if (input.sourcePriority !== undefined && input.sourcePriority !== null) {
    payload.source_priority = input.sourcePriority;
  }
  if (input.status !== undefined) {
    payload.status = input.status;
  }

  return apiClient.patch<CanonicalFieldRecord>(
    `/cases/${input.caseId}/canonical-fields/${encodeURIComponent(input.fieldKey)}`,
    {
      body: JSON.stringify(payload),
    },
  );
}
