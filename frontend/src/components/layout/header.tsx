"use client";

import { useRouter } from "next/navigation";

import { appConfig } from "@/lib/config";
import { useAuth } from "@/providers/auth-provider";

export function Header(): JSX.Element {
  const router = useRouter();
  const { user } = useAuth();

  async function handleLogout(): Promise<void> {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }

  return (
    <header className="app-header">
      <div>
        <p className="app-header__label">{appConfig.appName}</p>
        <h1 className="app-header__title">
          {user.role === "reception"
            ? "Intake Workspace"
            : user.role === "client"
              ? "Restricted Internal Workspace"
              : "Staff Workspace"}
        </h1>
      </div>
      <div className="app-header__user">
        <div>
          <strong>{user.name}</strong>
          <p>
            {user.role} | {user.email}
          </p>
        </div>
        <button type="button" className="ui-button ui-button--ghost" onClick={() => void handleLogout()}>
          Sign out
        </button>
      </div>
    </header>
  );
}
