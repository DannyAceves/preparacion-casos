"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { FormFeedback } from "@/components/ui/form-feedback";
import { FormField } from "@/components/ui/form-field";
import { getApiErrorMessage } from "@/lib/api/errors";
import { resolveAuthorizedPathForRole } from "@/lib/auth/permissions";
import { InternalUser } from "@/types/auth";

interface LoginFormProps {
  nextPath?: string | null;
}

export function LoginForm({ nextPath }: LoginFormProps): JSX.Element {
  const router = useRouter();
  const [email, setEmail] = useState(process.env.NEXT_PUBLIC_DEFAULT_USER_EMAIL ?? "staff@example.com");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        const detail = (await response.json().catch(() => null)) as unknown;
        throw {
          message: getApiErrorMessage(detail, "Could not sign in."),
          detail,
        };
      }

      const payload = (await response.json()) as { user: InternalUser };
      setSuccess(`Welcome back, ${payload.user.name}. Redirecting...`);
      router.push(resolveAuthorizedPathForRole(payload.user.role, nextPath));
      router.refresh();
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Login failed."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="login-card" onSubmit={(event) => void handleSubmit(event)}>
      <div className="login-card__header">
        <strong>Staff Sign In</strong>
        <p>Enter your registered email address to open your account with the role assigned in the system.</p>
      </div>

      <FormField label="Email" htmlFor="login-email" hint="The system will load your active account and role automatically.">
        <input
          id="login-email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          autoComplete="email"
          disabled={submitting}
        />
      </FormField>

      {success ? <FormFeedback tone="success" message={success} /> : null}
      {error ? <FormFeedback tone="error" message={error} /> : null}

      <button type="submit" className="ui-button" disabled={submitting}>
        {submitting ? "Signing in..." : "Continue"}
      </button>
    </form>
  );
}
