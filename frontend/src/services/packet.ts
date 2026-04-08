import { apiClient } from "@/lib/api/client";
import { CasePacketRecord } from "@/types/workspace";

interface GeneratePacketInput {
  caseId: string;
  generatedByReference?: string;
  generationNotes?: string;
}

export async function getCasePacket(caseId: string): Promise<CasePacketRecord> {
  return apiClient.get<CasePacketRecord>(`/cases/${caseId}/packet`);
}

export async function generateCasePacket(input: GeneratePacketInput): Promise<CasePacketRecord> {
  return apiClient.post<CasePacketRecord>(`/cases/${input.caseId}/packet/generate`, {
    body: JSON.stringify({
      generated_by_reference: input.generatedByReference || undefined,
      generation_notes: input.generationNotes || undefined,
    }),
  });
}
