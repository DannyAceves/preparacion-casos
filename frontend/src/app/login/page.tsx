import { redirect } from "next/navigation";

import { LoginForm } from "@/components/auth/login-form";
import { resolveAuthorizedPathForRole } from "@/lib/auth/permissions";
import { getCurrentSession } from "@/lib/auth/session";

interface LoginPageProps {
  searchParams?: {
    next?: string;
  };
}

export default async function LoginPage({ searchParams }: LoginPageProps): Promise<JSX.Element> {
  const session = await getCurrentSession();
  if (session) {
    redirect(resolveAuthorizedPathForRole(session.user.role, searchParams?.next));
  }

  return (
    <main className="login-page">
      <div className="login-page__hero">
        <p className="app-header__label">Case Prep Staff</p>
        <h1 className="app-header__title">Internal Access</h1>
        <p>
          Sign in with the email registered for your account. The system will load your active role automatically and
          send you to the right workspace.
        </p>
      </div>
      <LoginForm nextPath={searchParams?.next} />
    </main>
  );
}
