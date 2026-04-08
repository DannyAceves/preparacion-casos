import { AuthSession } from "@/types/auth";

let browserSessionSnapshot: AuthSession | null = null;

export function setBrowserSessionSnapshot(session: AuthSession | null): void {
  browserSessionSnapshot = session;
}

export function getBrowserSessionSnapshot(): AuthSession | null {
  return browserSessionSnapshot;
}
