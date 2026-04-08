import { InternalRole } from "@/types/auth";

export interface SystemUser {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: InternalRole;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateSystemUserInput {
  first_name: string;
  last_name: string;
  email: string;
  role: InternalRole;
  is_active?: boolean;
}

export interface UpdateSystemUserInput {
  first_name?: string;
  last_name?: string;
  email?: string;
  role?: InternalRole;
  is_active?: boolean;
}

export interface ListSystemUsersFilters {
  search?: string;
  role?: InternalRole | "all";
  is_active?: "all" | "true" | "false";
}
