import { apiClient } from "@/lib/api/client";
import {
  CreateSystemUserInput,
  ListSystemUsersFilters,
  SystemUser,
  UpdateSystemUserInput,
} from "@/types/system-user";

function buildQuery(filters: ListSystemUsersFilters): Record<string, string | undefined> {
  return {
    search: filters.search?.trim() || undefined,
    role: filters.role && filters.role !== "all" ? filters.role : undefined,
    is_active: filters.is_active && filters.is_active !== "all" ? filters.is_active : undefined,
  };
}

export async function listSystemUsers(filters: ListSystemUsersFilters = {}): Promise<SystemUser[]> {
  return apiClient.get<SystemUser[]>("/admin/users", {
    query: buildQuery(filters),
  });
}

export async function createSystemUser(input: CreateSystemUserInput): Promise<SystemUser> {
  return apiClient.post<SystemUser>("/admin/users", {
    body: JSON.stringify({
      ...input,
      is_active: input.is_active ?? true,
    }),
  });
}

export async function updateSystemUser(userId: string, input: UpdateSystemUserInput): Promise<SystemUser> {
  return apiClient.patch<SystemUser>(`/admin/users/${userId}`, {
    body: JSON.stringify(input),
  });
}
