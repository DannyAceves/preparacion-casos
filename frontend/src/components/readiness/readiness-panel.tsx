"use client";

import { useState } from "react";

import { CaseTransitionActions } from "@/components/readiness/case-transition-actions";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { validateCaseReadiness } from "@/services/readiness";
import { ApiErrorPayload } from "@/types/api";
import { CaseReadiness, CaseReadinessIssue, CaseTargetReadiness } from "@/types/case";

interface ReadinessPanelProps {
  caseId: string;
  caseStatus: string;
  readiness: CaseReadiness;
  loading: boolean;
  error: ApiErrorPayload | null;
  onValidated: (nextReadiness: CaseReadiness) => void;
}

function toneForStatus(isReady: boolean): "success" | "warning" {
  return isReady ? "success" : "warning";
}

function toneForIssue(severity: CaseReadinessIssue["severity"]): "info" | "warning" | "danger" {
  if (severity === "blocking") {
    return "danger";
  }
  if (severity === "warning") {
    return "warning";
  }
  return "info";
}

function getErrorMessage(error: unknown): string {
  const apiError = error as ApiErrorPayload;
  if (typeof apiError?.detail === "string") {
    return apiError.detail;
  }
  return apiError?.message ?? "Could not validate readiness.";
}

function ReadinessIssues({
  title,
  issues,
}: {
  title: string;
  issues: CaseReadinessIssue[];
}): JSX.Element {
  if (!issues.length) {
    return (
      <EmptyState
        title={`No ${title.toLowerCase()}`}
        description={`The backend did not return ${title.toLowerCase()} for this target.`}
      />
    );
  }

  return (
    <div className="page-stack">
      {issues.map((issue, index) => (
        <div key={`${issue.code}-${index}`} className="placeholder-note">
          <div className="case-hero__badges">
            <Badge tone={toneForIssue(issue.severity)}>{issue.severity}</Badge>
            <Badge tone="neutral">{issue.code}</Badge>
          </div>
          <strong>{issue.message}</strong>
        </div>
      ))}
    </div>
  );
}

function ReadinessTargetCard({ target }: { target: CaseTargetReadiness }): JSX.Element {
  const approvedChecks: string[] = [];
  if (target.is_ready) {
    approvedChecks.push("Target is clear to transition.");
  }
  if (!target.blockers.length) {
    approvedChecks.push("No blocking rules triggered.");
  }
  if (!target.warnings.length) {
    approvedChecks.push("No warnings returned.");
  }

  return (
    <div className="entity-card">
      <div className="entity-card__header entity-card__header--spread">
        <div>
          <strong>{target.target_status}</strong>
          <p>Transition gate evaluation from the backend.</p>
        </div>
        <div className="case-hero__badges">
          <Badge tone={toneForStatus(target.is_ready)}>{target.is_ready ? "ready" : "blocked"}</Badge>
          <Badge tone="neutral">{target.blockers.length} blockers</Badge>
          <Badge tone="neutral">{target.warnings.length} warnings</Badge>
        </div>
      </div>

      {approvedChecks.length ? (
        <div className="page-stack">
          {approvedChecks.map((item) => (
            <div key={item} className="placeholder-note">
              <strong>{item}</strong>
            </div>
          ))}
        </div>
      ) : null}

      <div className="detail-sections detail-sections--two-columns">
        <div className="entity-card">
          <div className="entity-card__header">
            <strong>Blockers</strong>
            <p>Rules preventing the transition.</p>
          </div>
          <ReadinessIssues title="Blockers" issues={target.blockers} />
        </div>

        <div className="entity-card">
          <div className="entity-card__header">
            <strong>Warnings</strong>
            <p>Advisory issues that do not fully block the transition.</p>
          </div>
          <ReadinessIssues title="Warnings" issues={target.warnings} />
        </div>
      </div>
    </div>
  );
}

export function ReadinessPanel({
  caseId,
  caseStatus,
  readiness,
  loading,
  error,
  onValidated,
}: ReadinessPanelProps): JSX.Element {
  const [actorReference, setActorReference] = useState("");
  const [busy, setBusy] = useState(false);
  const [panelError, setPanelError] = useState<string | null>(null);
  const [panelMessage, setPanelMessage] = useState<string | null>(null);

  async function handleValidate(): Promise<void> {
    setBusy(true);
    setPanelError(null);
    setPanelMessage(null);

    try {
      const nextReadiness = await validateCaseReadiness({
        caseId,
        actorReference: actorReference || undefined,
      });
      onValidated(nextReadiness);
      setPanelMessage("Readiness validated successfully.");
    } catch (validateError) {
      setPanelError(getErrorMessage(validateError));
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return <LoadingState label="Loading readiness..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Could not load readiness"
        description="The readiness data could not be retrieved from the backend."
      />
    );
  }

  return (
    <div className="detail-sections">
      <div className="entity-card">
        <div className="entity-card__header entity-card__header--spread">
          <div>
            <strong>Readiness Overview</strong>
            <p>System-level validation for attorney review, submission readiness and final submission.</p>
          </div>
          <div className="case-hero__badges">
            <Badge tone="info">{readiness.case_status}</Badge>
            <Badge tone={readiness.targets.some((item) => item.is_ready) ? "success" : "warning"}>
              {readiness.targets.filter((item) => item.is_ready).length} ready targets
            </Badge>
          </div>
        </div>

        <div className="entity-card__grid">
          <div className="placeholder-note">
            <strong>Missing Required Documents</strong>
            <p>{readiness.summary.missing_required_document_types.length}</p>
          </div>
          <div className="placeholder-note">
            <strong>High/Critical Inconsistencies</strong>
            <p>{readiness.summary.open_high_or_critical_inconsistency_count}</p>
          </div>
          <div className="placeholder-note">
            <strong>Critical Inconsistencies</strong>
            <p>{readiness.summary.open_critical_inconsistency_count}</p>
          </div>
          <div className="placeholder-note">
            <strong>Unapproved Forms</strong>
            <p>{readiness.summary.unapproved_generated_form_count}</p>
          </div>
          <div className="placeholder-note">
            <strong>Generated Forms</strong>
            <p>{readiness.summary.generated_form_count}</p>
          </div>
          <div className="placeholder-note">
            <strong>Attorney Review Present</strong>
            <p>{readiness.summary.attorney_approved_review_exists ? "Yes" : "No"}</p>
          </div>
        </div>

        <div className="detail-sections detail-sections--two-columns">
          <div className="entity-card">
            <div className="entity-card__header">
              <strong>Required Documents</strong>
              <p>Required and present document types.</p>
            </div>
            <div className="page-stack">
              <div className="placeholder-note">
                <strong>Required</strong>
                <p>{readiness.summary.required_document_types.join(", ") || "None defined"}</p>
              </div>
              <div className="placeholder-note">
                <strong>Present</strong>
                <p>{readiness.summary.present_required_document_types.join(", ") || "None present"}</p>
              </div>
              <div className="placeholder-note">
                <strong>Missing</strong>
                <p>{readiness.summary.missing_required_document_types.join(", ") || "None missing"}</p>
              </div>
            </div>
          </div>

          <div className="entity-card">
            <div className="entity-card__header">
              <strong>Manual Validation</strong>
              <p>Re-run readiness checks from the backend.</p>
            </div>

            <label className="ui-field">
              <span>Actor Reference</span>
              <input
                value={actorReference}
                onChange={(event) => setActorReference(event.target.value)}
                placeholder="staff.user"
              />
            </label>

            {panelError ? <p className="document-feedback document-feedback--error">{panelError}</p> : null}
            {panelMessage ? <p className="document-feedback document-feedback--success">{panelMessage}</p> : null}

            <button type="button" className="ui-button" disabled={busy} onClick={() => void handleValidate()}>
              {busy ? "Validating..." : "Validate readiness"}
            </button>
          </div>
        </div>
      </div>

      {readiness.targets.length ? (
        readiness.targets.map((target) => <ReadinessTargetCard key={target.target_status} target={target} />)
      ) : (
        <EmptyState
          title="No readiness targets"
          description="The backend did not return transition readiness targets for this case."
        />
      )}

      <CaseTransitionActions
        caseId={caseId}
        currentStatus={caseStatus}
        readiness={readiness}
        onValidated={onValidated}
      />
    </div>
  );
}
