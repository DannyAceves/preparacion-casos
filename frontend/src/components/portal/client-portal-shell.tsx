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
import { openClientPortalPrintablePdf } from "@/lib/client-portal-print";
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
    return "No disponible";
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
      setError(getApiErrorMessage(loadError, "No se pudo abrir el portal del cliente."));
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
        setError(getApiErrorMessage(loadError, "Tu sesion segura expiro. Ingresa el codigo nuevamente."));
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
      setError("Ingresa el codigo de acceso para continuar.");
      return;
    }

    setSubmitting(true);
    setMessage(null);
    try {
      const session = await authenticateClientPortal(token, passcode.trim());
      setPortalSessionToken(session.session_token);
      sessionStorage.setItem(sessionStorageTokenKey(token), session.session_token);
    } catch (authError) {
      setError(getApiErrorMessage(authError, "No se pudo desbloquear el portal del cliente."));
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

  function handlePrint(): void {
    if (!context) {
      return;
    }
    try {
      openClientPortalPrintablePdf(context);
    } catch (printError) {
      setError(getApiErrorMessage(printError, "No se pudo preparar la version para PDF."));
    }
  }

  return (
    <main className="client-portal">
      <section className="client-portal__hero">
        <div>
          <span className="app-sidebar__eyebrow">Portal del Cliente</span>
          <h1>Cuestionario del caso y carga de documentos</h1>
          <p>Usa el codigo seguro que te compartio tu equipo legal para continuar tu proceso y cargar documentos con claridad.</p>
        </div>
      </section>

      {loading ? <LoadingState label="Abriendo portal del cliente..." /> : null}

      {!loading && !context ? (
        <section className="client-portal__content">
          <Card title="Acceso Seguro" subtitle="Este portal es unico para tu caso y requiere un codigo valido.">
            <form className="entity-form" onSubmit={(event) => void handleUnlock(event)}>
              <FormField label="Codigo de acceso" htmlFor="client-portal-passcode-access">
                <input
                  id="client-portal-passcode-access"
                  type="password"
                  value={passcode}
                  onChange={(event) => setPasscode(event.target.value)}
                  placeholder="Ingresa tu codigo de acceso"
                />
              </FormField>
              {error ? <FormFeedback tone="error" message={error} /> : null}
              <div className="entity-form__actions">
                <button type="submit" className="ui-button" disabled={submitting}>
                  {submitting ? "Abriendo..." : "Abrir portal"}
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
                  <Badge tone="info">{context.progress.overall_percent_complete}% completado</Badge>
                  <Badge tone="neutral">
                    Cuestionario {context.progress.questionnaire_answered_questions}/{context.progress.questionnaire_total_questions}
                  </Badge>
                  <Badge tone="warning">
                    Documentos {context.progress.checklist_received_items}/{context.progress.checklist_applicable_items}
                  </Badge>
                  <Badge tone="neutral">Sesion hasta {formatDateTime(context.session_expires_at)}</Badge>
                </div>
                <p className="client-portal__summary">
                  {context.case_summary ?? "Tu equipo legal preparo este portal para que completes tu informacion y subas archivos de forma segura."}
                </p>
                <div className="client-portal__actions">
                  <button type="button" className="ui-button ui-button--ghost" onClick={() => void handleRefresh()}>
                    Actualizar portal
                  </button>
                  <button type="button" className="ui-button" onClick={handlePrint}>
                    Imprimir o guardar PDF
                  </button>
                </div>
                <div className="client-portal__progress">
                  <div className="checklist-progress__bar">
                    <div
                      className="checklist-progress__fill"
                      style={{ width: `${context.progress.overall_percent_complete}%` }}
                    />
                  </div>
                  <p>El acceso vence: {formatDateTime(context.access_expires_at)}</p>
                </div>
              </div>
            </Card>

            {context.instructions ? (
              <Card title="Instrucciones" subtitle="Revisa estas notas antes de continuar.">
                <div className="placeholder-note">
                  <strong>Siguientes pasos</strong>
                  <p>{context.instructions}</p>
                </div>
              </Card>
            ) : null}

            {message ? <FormFeedback tone="success" message={message} /> : null}
            {error ? <ErrorState title="No se pudo actualizar el portal" description={error} /> : null}

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
