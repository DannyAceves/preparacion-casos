"use client";

import { useAuth } from "@/providers/auth-provider";
import { InternalUser } from "@/types/auth";

export function useCurrentUser(): InternalUser | null {
  const { user } = useAuth();
  return user;
}
