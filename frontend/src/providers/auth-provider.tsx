"use client";

import { createContext, ReactNode, useContext, useLayoutEffect, useState } from "react";

import { setBrowserSessionSnapshot } from "@/lib/auth/session-store";
import { AuthSession, InternalUser } from "@/types/auth";

interface AuthContextValue {
  session: AuthSession;
  user: InternalUser;
  setSession: (session: AuthSession | null) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

interface AuthProviderProps {
  initialSession: AuthSession;
  children: ReactNode;
}

export function AuthProvider({ initialSession, children }: AuthProviderProps): JSX.Element {
  const [session, setSessionState] = useState<AuthSession>(initialSession);

  useLayoutEffect(() => {
    setBrowserSessionSnapshot(session);
  }, [session]);

  function setSession(nextSession: AuthSession | null): void {
    if (nextSession) {
      setSessionState(nextSession);
      setBrowserSessionSnapshot(nextSession);
    }
  }

  return (
    <AuthContext.Provider value={{ session, user: session.user, setSession }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
