import { apiClient } from "@/lib/api/client";
import { InconsistencyRecord } from "@/types/workspace";

interface InconsistencyActionInput {
  caseId: string;
  inconsistencyId: string;
  actorReference?: string;
  notes?: string;
}

function buildPayload(input: InconsistencyActionInput): string {
  return JSON.stringify({
    actor_reference: input.actorReference || undefined,
    notes: input.notes || undefined,
  });
}

export async function resolveInconsistency(input: InconsistencyActionInput): Promise<InconsistencyRecord> {
  return apiClient.post<InconsistencyRecord>(
    `/cases/${input.caseId}/inconsistencies/${input.inconsistencyId}/resolve`,
    {
      body: buildPayload(input),
    },
  );
}

export async function dismissInconsistency(input: InconsistencyActionInput): Promise<InconsistencyRecord> {
  return apiClient.post<InconsistencyRecord>(
    `/cases/${input.caseId}/inconsistencies/${input.inconsistencyId}/dismiss`,
    {
      body: buildPayload(input),
    },
  );
}
