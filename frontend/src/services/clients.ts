import { apiClient } from "@/lib/api/client";
import { Client, CreateClientInput } from "@/types/client";

export async function listClients(): Promise<Client[]> {
  return apiClient.get<Client[]>("/clients");
}

export async function createClient(input: CreateClientInput): Promise<Client> {
  return apiClient.post<Client>("/clients", {
    body: JSON.stringify({
      ...input,
      phone: input.phone || null,
      date_of_birth: input.date_of_birth || null,
      notes: input.notes || null,
    }),
  });
}
