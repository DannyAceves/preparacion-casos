"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { usePermissions } from "@/hooks/use-permissions";
import { InconsistencyRecord } from "@/types/workspace";

interface InconsistencyCardProps {
  item: InconsistencyRecord;
  actorReference: string;
  onResolve: (input: { inconsistencyId: string; actorReference?: string; notes?: string }) => Promise<void>;
  onDismiss: (input: { inconsistencyId: string; actorReference?: string; notes?: string }) => Promise<void>;
}

function toneForSeverity(severity: string): "neutral" | "warning" | "danger" | "info" {
  if (severity === "critical" || severity === "high") {
    return "danger";
  }
  if (severity === "medium") {
    return "warning";
  }
  return "info";
}

function toneForStatus(status: string): "neutral" | "warning" | "danger" | "success" | "info" {
  if (status === "resolved") {
    return "success";
  }
  if (status === "dismissed") {
    return "neutral";
  }
  if (status === "under_review") {
    return "warning";
  }
  return "danger";
}

export function InconsistencyCard({
  item,
  actorReference,
  onResolve,
  onDismiss,
}: InconsistencyCardProps): JSX.Element {
  const permissions = usePermissions();
  const [notes, setNotes] = useState(item.resolution_notes ?? "");
  const [busyAction, setBusyAction] = useState<"resolve" | "dismiss" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canAct = item.status === "open" || item.status === "under_review";

  async function handleResolve(): Promise<void> {
    setBusyAction("resolve");
    setError(null);
    try {
      await onResolve({
        inconsistencyId: item.id,
        actorReference: actorReference || undefined,
        notes: notes || undefined,
      });
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Could not resolve inconsistency.");
    } finally {
      setBusyAction(null);
    }
  }

  async function handleDismiss(): Promise<void> {
    setBusyAction("dismiss");
    setError(null);
    try {
      await onDismiss({
        inconsistencyId: item.id,
        actorReference: actorReference || undefined,
        notes: notes || undefined,
      });
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Could not dismiss inconsistency.");
    } finally {
      setBusyAction(null);
    }
  }

  return (
    <div className="entity-card">
      <div className="entity-card__header entity-card__header--spread">
        <div>
          <strong>{item.field_key}</strong>
          <p>{item.description}</p>
        </div>
        <div className="case-hero__badges">
          <Badge tone={toneForSeverity(item.severity)}>{item.severity}</Badge>
          <Badge tone={toneForStatus(item.status)}>{item.status}</Badge>
        </div>
      </div>

      <div className="entity-card__meta">
        <p>Resolved by: {item.resolved_by_user_id ?? "Not resolved"}</p>
        <p>Resolved at: {item.resolved_at ? new Date(item.resolved_at).toLocaleString() : "Not resolved"}</p>
      </div>

      {item.evidence_payload ? (
        <pre className="entity-card__evidence">{JSON.stringify(item.evidence_payload, null, 2)}</pre>
      ) : (
        <p className="entity-card__hint">No evidence payload attached.</p>
      )}

      <label className="ui-field">
        <span>Resolution Notes</span>
        <textarea
          className="questionnaire-field__textarea"
          rows={4}
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="Explain why the inconsistency was resolved or dismissed"
          disabled={!permissions.can("resolve_inconsistencies")}
        />
      </label>

      {error ? <p className="document-feedback document-feedback--error">{error}</p> : null}

      {canAct && permissions.can("resolve_inconsistencies") ? (
        <div className="document-actions">
          <button type="button" className="ui-button" disabled={busyAction !== null} onClick={() => void handleResolve()}>
            {busyAction === "resolve" ? "Resolving..." : "Resolve"}
          </button>
          <button
            type="button"
            className="ui-button ui-button--ghost"
            disabled={busyAction !== null}
            onClick={() => void handleDismiss()}
          >
            {busyAction === "dismiss" ? "Dismissing..." : "Dismiss"}
          </button>
        </div>
      ) : canAct ? (
        <p className="entity-card__hint">Your role can inspect inconsistencies but only attorneys or admins can resolve them.</p>
      ) : null}
    </div>
  );
}
