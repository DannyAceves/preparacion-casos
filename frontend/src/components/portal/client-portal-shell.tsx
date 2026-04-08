"use client";

import { FormEvent, useEffect, useState } from "react";

import { ClientPortalChecklistPanel } from "@/components/portal/client-portal-checklist-panel";
import { ClientPortalDocumentsPanel } from "@/components/portal/client-portal-documents-panel";
import { ClientPortalQuestionnairePanel } from "@/components/portal/client-portal-questionnaire-panel";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { ErrorState } from "@/components/ui/error-state";
import { FormFeedback } from "@/components/ui/form-feedback";
import { FormField } from "@/components/ui/form-field";
import { LoadingState } from "@/components/ui/loading-state";
import { getApiErrorMessage } from "@/lib/api/errors";
import {
  authenticateClientPortal,
  getClientPortalContext,
  getClientPortalContextWithSession,
} from "@/services/client-portal";
import { ClientPortalContext } from "@/types/client-portal";

interface ClientPortalShellProps {
  token: string;
}

const passcodeStorageKey = (token: string): string => `client-portal-passcode:${token}`;
const sessionStorageTokenKey = (token: string): string => `client-portal-session:${token}`;

function formatDateTime(value: string | null): string {
  if (!value) {
    return "Not available";
  }

  return new Date(value).toLocaleString();
}

export function ClientPortalShell({ token }: ClientPortalShellProps): JSX.Element {
  const [passcode, setPasscode] = useState("");
  const [portalSessionToken, setPortalSessionToken] = useState("");
  const [context, setContext] = useState<ClientPortalContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function loadPortalContext(nextPasscode: string, options?: { silent?: boolean }): Promise<void> {
    if (!options?.silent) {
      setLoading(true);
    }
    setError(null);

    try {
      const nextContext = await getClientPortalContext(token, nextPasscode);
      setContext(nextContext);
      setPasscode(nextPasscode);
      setPortalSessionToken(nextContext.session_token);
      setMessage(null);
      sessionStorage.setItem(passcodeStorageKey(token), nextPasscode);
      sessionStorage.setItem(sessionStorageTokenKey(token), nextContext.session_token);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Could not open the client portal."));
      if (!options?.silent) {
        setContext(null);
        sessionStorage.removeItem(passcodeStorageKey(token));
        sessionStorage.removeItem(sessionStorageTokenKey(token));
      }
    } finally {
      setLoading(false);
    }
  }

  async function loadPortalContextWithSession(nextSessionToken: string, options?: { silent?: boolean }): Promise<void> {
    if (!options?.silent) {
      setLoading(true);
    }
    setError(null);

    try {
      const nextContext = await getClientPortalContextWithSession(nextSessionToken);
      setContext(nextContext);
      setPortalSessionToken(nextContext.session_token);
      sessionStorage.setItem(sessionStorageTokenKey(token), nextContext.session_token);
    } catch (loadError) {
      sessionStorage.removeItem(sessionStorageTokenKey(token));
      const storedPasscode = passcode || sessionStorage.getItem(passcodeStorageKey(token)) || "";
      if (!storedPasscode) {
        setContext(null);
        setPortalSessionToken("");
        setError(getApiErrorMessage(loadError, "Your secure portal session expired. Enter the passcode again."));
        return;
      }
      await loadPortalContext(storedPasscode, options);
      return;
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const storedSessionToken = sessionStorage.getItem(sessionStorageTokenKey(token));
    const storedPasscode = sessionStorage.getItem(passcodeStorageKey(token));
    if (storedSessionToken) {
      void loadPortalContextWithSession(storedSessionToken);
      return;
    }
    if (storedPasscode) {
      void loadPortalContext(storedPasscode);
      return;
    }
    setLoading(false);
  }, [token]);

  async function handleUnlock(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (!passcode.trim()) {
      setError("Enter the access passcode to continue.");
      return;
    }

    setSubmitting(true);
    setMessage(null);
    try {
      const session = await authenticateClientPortal(token, passcode.trim());
      setPortalSessionToken(session.session_token);
      sessionStorage.setItem(sessionStorageTokenKey(token), session.session_token);
    } catch (authError) {
      setError(getApiErrorMessage(authError, "Could not unlock the client portal."));
      setSubmitting(false);
      return;
    }
    await loadPortalContext(passcode.trim());
    setSubmitting(false);
  }

  async function handleRefresh(): Promise<void> {
    if (portalSessionToken) {
      await loadPortalContextWithSession(portalSessionToken, { silent: true });
      return;
    }
    if (!passcode) {
      return;
    }
    await loadPortalContext(passcode, { silent: true });
  }

  return (
    <main className="client-portal">
      <section className="client-portal__hero">
        <div>
          <span className="app-sidebar__eyebrow">Client Portal</span>
          <h1>Case questionnaire and document upload</h1>
          <p>Use the secure passcode provided by your legal team to continue your intake and upload documents.</p>
        </div>
      </section>

      {loading ? <LoadingState label="Opening client portal..." /> : null}

      {!loading && !context ? (
        <section className="client-portal__content">
          <Card title="Secure Access" subtitle="This portal is unique to your case and requires a valid passcode.">
            <form className="entity-form" onSubmit={(event) => void handleUnlock(event)}>
              <FormField label="Passcode" htmlFor="client-portal-passcode-access">
                <input
                  id="client-portal-passcode-access"
                  type="password"
                  value={passcode}
                  onChange={(event) => setPasscode(event.target.value)}
                  placeholder="Enter your access code"
                />
              </FormField>
              {error ? <FormFeedback tone="error" message={error} /> : null}
              <div className="entity-form__actions">
                <button type="submit" className="ui-button" disabled={submitting}>
                  {submitting ? "Opening..." : "Open portal"}
                </button>
              </div>
            </form>
          </Card>
        </section>
      ) : null}

      {!loading && context ? (
        <section className="client-portal__content">
          <div className="page-stack">
            <Card title={context.case_title} subtitle={`${context.case_number} · ${context.case_type}`}>
              <div className="page-stack">
                <div className="case-hero__badges">
                  <Badge tone="info">{context.progress.overall_percent_complete}% complete</Badge>
                  <Badge tone="neutral">
                    Questionnaire {context.progress.questionnaire_answered_questions}/{context.progress.questionnaire_total_questions}
                  </Badge>
                  <Badge tone="warning">
                    Documents {context.progress.checklist_received_items}/{context.progress.checklist_applicable_items}
                  </Badge>
                  <Badge tone="neutral">Session until {formatDateTime(context.session_expires_at)}</Badge>
                </div>
                <p className="client-portal__summary">
                  {context.case_summary ?? "Your legal team has prepared this portal so you can complete your intake and submit files securely."}
                </p>
                <div className="client-portal__progress">
                  <div className="checklist-progress__bar">
                    <div
                      className="checklist-progress__fill"
                      style={{ width: `${context.progress.overall_percent_complete}%` }}
                    />
                  </div>
                  <p>Access expires: {formatDateTime(context.access_expires_at)}</p>
                </div>
              </div>
            </Card>

            {context.instructions ? (
              <Card title="Instructions" subtitle="Please review these notes before continuing.">
                <div className="placeholder-note">
                  <strong>Next steps</strong>
                  <p>{context.instructions}</p>
                </div>
              </Card>
            ) : null}

            {message ? <FormFeedback tone="success" message={message} /> : null}
            {error ? <ErrorState title="Portal refresh failed" description={error} /> : null}

            <div className="client-portal__grid">
              <ClientPortalChecklistPanel checklist={context.checklist} />
              <ClientPortalDocumentsPanel
                portalSessionToken={portalSessionToken}
                checklist={context.checklist}
                documents={context.documents}
                onRefresh={handleRefresh}
              />
            </div>

            <ClientPortalQuestionnairePanel
              portalSessionToken={portalSessionToken}
              questionnaire={context.questionnaire}
              onRefresh={handleRefresh}
            />
          </div>
        </section>
      ) : null}
    </main>
  );
}
