"use client";

import Link from "next/link";
import { useState } from "react";

import { PermissionGate } from "@/components/auth/permission-gate";
import { Badge } from "@/components/ui/badge";
import { usePermissions } from "@/hooks/use-permissions";
import { GeneratedFormDetailRecord, GeneratedFormRecord } from "@/types/workspace";

interface GeneratedFormCardProps {
  form: GeneratedFormRecord;
  detail: GeneratedFormDetailRecord | null;
  actorReference: string;
  caseId: string;
  busyAction: "approve" | "fix" | "loading" | null;
  onLoadDetail: () => Promise<void>;
  onApprove: (input: { reviewedByUserId: string; reviewNotes?: string }) => Promise<void>;
  onFix: (input: { reviewedByUserId: string; reviewNotes?: string }) => Promise<void>;
}

function toneForStatus(status: string): "neutral" | "warning" | "danger" | "success" | "info" {
  if (status === "approved") {
    return "success";
  }
  if (status === "fix_required") {
    return "danger";
  }
  if (status === "review_pending") {
    return "warning";
  }
  return "info";
}

export function GeneratedFormCard({
  form,
  detail,
  actorReference,
  caseId,
  busyAction,
  onLoadDetail,
  onApprove,
  onFix,
}: GeneratedFormCardProps): JSX.Element {
  const permissions = usePermissions();
  const [expanded, setExpanded] = useState(false);
  const [reviewedByUserId, setReviewedByUserId] = useState(actorReference);
  const [reviewNotes, setReviewNotes] = useState(form.review_notes ?? "");
  const [localError, setLocalError] = useState<string | null>(null);

  async function handleExpand(): Promise<void> {
    setExpanded((current) => !current);
    if (!detail) {
      setLocalError(null);
      try {
        await onLoadDetail();
      } catch (error) {
        setLocalError(error instanceof Error ? error.message : "Could not load form detail.");
      }
    }
  }

  async function handleApprove(): Promise<void> {
    setLocalError(null);
    try {
      await onApprove({
        reviewedByUserId: reviewedByUserId.trim(),
        reviewNotes: reviewNotes || undefined,
      });
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "Could not approve form.");
    }
  }

  async function handleFix(): Promise<void> {
    setLocalError(null);
    try {
      await onFix({
        reviewedByUserId: reviewedByUserId.trim(),
        reviewNotes: reviewNotes || undefined,
      });
    } catch (error) {
      setLocalError(error instanceof Error ? error.message : "Could not mark form as fix required.");
    }
  }

  return (
    <div className="entity-card">
      <div className="entity-card__header entity-card__header--spread">
        <div>
          <strong>{detail?.form.form_name ?? "Generated form"}</strong>
          <p>{detail?.form.form_code ?? form.form_id}</p>
        </div>
        <div className="case-hero__badges">
          <Badge tone={toneForStatus(form.status)}>{form.status}</Badge>
          <Badge tone="neutral">v{form.draft_version}</Badge>
        </div>
      </div>

      <div className="entity-card__meta">
        <p>Generated at: {new Date(form.generated_at).toLocaleString()}</p>
        <p>Reviewed at: {form.reviewed_at ? new Date(form.reviewed_at).toLocaleString() : "Not reviewed"}</p>
        <p>Export path: {form.export_path ?? "Not available"}</p>
      </div>

      <div className="document-actions">
        {permissions.can("generate_forms") ? (
          <Link className="ui-button" href={`/cases/${caseId}/forms/${form.id}`}>
            Open workspace
          </Link>
        ) : null}
        <button type="button" className="ui-button ui-button--ghost" disabled={busyAction === "loading"} onClick={() => void handleExpand()}>
          {expanded ? "Hide detail" : busyAction === "loading" ? "Loading detail..." : "View detail"}
        </button>
      </div>

      {expanded && detail ? (
        <div className="page-stack">
          <div className="entity-card__meta">
            <p>Template version: {detail.form.version}</p>
            <p>Case type: {detail.form.case_type_id}</p>
          </div>

          <pre className="entity-card__evidence">{JSON.stringify(detail.generated_payload, null, 2)}</pre>

          {detail.warnings_payload ? (
            <pre className="entity-card__evidence">{JSON.stringify(detail.warnings_payload, null, 2)}</pre>
          ) : null}
        </div>
      ) : null}

      <PermissionGate action="review_forms" fallback={<p className="entity-card__hint">Your role can prepare and inspect forms here, but approval is restricted.</p>}>
        <div className="entity-card__grid">
          <label className="ui-field">
            <span>Reviewed By User</span>
            <input
              value={reviewedByUserId}
              onChange={(event) => setReviewedByUserId(event.target.value)}
              placeholder="staff.user"
            />
          </label>

          <label className="ui-field entity-card__field-span">
            <span>Review Notes</span>
            <input
              value={reviewNotes}
              onChange={(event) => setReviewNotes(event.target.value)}
              placeholder="Review notes or fix instructions"
            />
          </label>
        </div>

        {localError ? <p className="document-feedback document-feedback--error">{localError}</p> : null}

        <div className="document-actions">
          <button
            type="button"
            className="ui-button"
            disabled={busyAction !== null || !reviewedByUserId.trim()}
            onClick={() => void handleApprove()}
          >
            {busyAction === "approve" ? "Approving..." : "Approve"}
          </button>
          <button
            type="button"
            className="ui-button ui-button--ghost"
            disabled={busyAction !== null || !reviewedByUserId.trim()}
            onClick={() => void handleFix()}
          >
            {busyAction === "fix" ? "Saving..." : "Mark fix required"}
          </button>
        </div>
      </PermissionGate>
    </div>
  );
}
