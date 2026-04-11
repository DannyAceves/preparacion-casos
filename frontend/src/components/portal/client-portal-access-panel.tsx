"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { FormFeedback } from "@/components/ui/form-feedback";
import { FormField } from "@/components/ui/form-field";
import { LoadingState } from "@/components/ui/loading-state";
import { getApiErrorMessage } from "@/lib/api/errors";
import { buildPrincipalHeaders } from "@/lib/auth/principal-headers";
import { getCaseClientPortalAccess, issueCaseClientPortalAccess } from "@/services/client-portal";
import { useAuth } from "@/providers/auth-provider";
import { ClientPortalAccess, ClientPortalIssuedAccess } from "@/types/client-portal";

interface ClientPortalAccessPanelProps {
  caseId: string;
  caseTitle: string;
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return "Not available";
  }

  return new Date(value).toLocaleString();
}

export function ClientPortalAccessPanel({
  caseId,
  caseTitle,
}: ClientPortalAccessPanelProps): JSX.Element {
  const { session } = useAuth();
  const [access, setAccess] = useState<ClientPortalAccess | null>(null);
  const [issuedAccess, setIssuedAccess] = useState<ClientPortalIssuedAccess | null>(null);
  const [instructions, setInstructions] = useState("");
  const [expiresInDays, setExpiresInDays] = useState("7");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const principalHeaders = useMemo(() => buildPrincipalHeaders(session), [session]);

  useEffect(() => {
    let cancelled = false;

    async function loadAccess(): Promise<void> {
      setLoading(true);
      setError(null);

      try {
        const nextAccess = await getCaseClientPortalAccess(caseId, { headers: principalHeaders });
        if (!cancelled) {
          setAccess(nextAccess);
          if (nextAccess?.instructions) {
            setInstructions(nextAccess.instructions);
          }
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(getApiErrorMessage(loadError, "Could not load client portal access."));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadAccess();

    return () => {
      cancelled = true;
    };
  }, [caseId, principalHeaders]);

  const portalUrl = useMemo(() => {
    if (!issuedAccess) {
      return "";
    }
    if (typeof window === "undefined") {
      return issuedAccess.portal_path;
    }
    return `${window.location.origin}${issuedAccess.portal_path}`;
  }, [issuedAccess]);

  async function handleIssueAccess(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    setMessage(null);

    try {
      const issued = await issueCaseClientPortalAccess(caseId, {
        instructions: instructions.trim() || null,
        expires_in_days: Number(expiresInDays) || 7,
      }, { headers: principalHeaders });
      setAccess(issued);
      setIssuedAccess(issued);
      setMessage("Client portal access issued successfully.");
    } catch (issueError) {
      setError(getApiErrorMessage(issueError, "Could not issue client portal access."));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card title="Client Portal Access" subtitle="Issue a secure link so the client can complete the questionnaire, review instructions, and upload requested evidence.">
      <div className="page-stack">
        {loading ? <LoadingState label="Loading client portal access..." /> : null}

        {!loading && access ? (
          <div className="entity-card">
            <div className="entity-card__header entity-card__header--spread">
              <div>
                <strong>Current access on file</strong>
                <p>{caseTitle}</p>
              </div>
              <div className="case-hero__badges">
                <Badge tone={access.is_active ? "success" : "warning"}>
                  {access.is_active ? "active" : "inactive"}
                </Badge>
                <Badge tone="neutral">token ending {access.token_last4}</Badge>
              </div>
            </div>
            <div className="entity-card__grid">
              <div>
                <strong>Expires</strong>
                <p>{formatDateTime(access.expires_at)}</p>
              </div>
              <div>
                <strong>Last access</strong>
                <p>{formatDateTime(access.last_accessed_at)}</p>
              </div>
              <div>
                <strong>Failed attempts</strong>
                <p>{access.failed_access_attempt_count}</p>
              </div>
              <div>
                <strong>Locked until</strong>
                <p>{formatDateTime(access.locked_until)}</p>
              </div>
              <div className="entity-card__field-span">
                <strong>Instructions</strong>
                <p>{access.instructions ?? "No custom instructions yet."}</p>
              </div>
            </div>
            <p className="entity-card__hint">
              Regenerating access rotates the unique link, clears any active portal session and invalidates the previous credentials.
            </p>
          </div>
        ) : null}

        {message ? <FormFeedback tone="success" message={message} /> : null}
        {error ? <FormFeedback tone="error" message={error} /> : null}

        {issuedAccess ? (
          <div className="entity-card">
            <div className="entity-card__header">
              <strong>Share this with the client</strong>
              <p>The full token and passcode are shown only right after issuing or regenerating access.</p>
            </div>
            <div className="entity-form">
              <FormField label="Portal link" htmlFor="portal-link">
                <input id="portal-link" value={portalUrl} readOnly />
              </FormField>
              <FormField label="Passcode" htmlFor="portal-passcode">
                <input id="portal-passcode" value={issuedAccess.passcode} readOnly />
              </FormField>
              <p className="entity-card__hint">
                Share this passcode through a separate secure channel from the portal link whenever possible.
              </p>
              <div className="entity-form__actions">
                <a className="ui-button ui-button--ghost" href={portalUrl} target="_blank" rel="noreferrer">
                  Open portal
                </a>
              </div>
            </div>
          </div>
        ) : null}

        <form className="entity-form" onSubmit={(event) => void handleIssueAccess(event)}>
          <div className="entity-form__grid">
            <FormField
              label="Instructions"
              htmlFor="client-portal-instructions"
              hint="These instructions are visible inside the client portal."
            >
              <textarea
                id="client-portal-instructions"
                className="ui-textarea"
                value={instructions}
                onChange={(event) => setInstructions(event.target.value)}
                placeholder="Explain what the client should complete first, which ROC checklist items apply, and what documents should be uploaded."
              />
            </FormField>
            <FormField
              label="Expires in days"
              htmlFor="client-portal-expiry"
              hint="For beta access, keep links short-lived and regenerate when needed."
            >
              <input
                id="client-portal-expiry"
                type="number"
                min={1}
                max={30}
                value={expiresInDays}
                onChange={(event) => setExpiresInDays(event.target.value)}
              />
            </FormField>
          </div>
          <div className="entity-form__actions">
            <button type="submit" className="ui-button" disabled={submitting}>
              {submitting ? "Issuing access..." : access ? "Regenerate portal access" : "Issue portal access"}
            </button>
          </div>
        </form>
      </div>
    </Card>
  );
}
