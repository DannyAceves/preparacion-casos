"use client";

import { useState } from "react";

import { PermissionGate } from "@/components/auth/permission-gate";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { usePermissions } from "@/hooks/use-permissions";
import { approveForSubmission, closeCase, failSubmission, submitCase } from "@/services/submission";
import { ApiErrorPayload } from "@/types/api";
import { CaseSubmissionRead } from "@/types/workspace-submission";

interface SubmissionPanelProps {
  caseId: string;
  submission: CaseSubmissionRead | null;
  loading: boolean;
  error: ApiErrorPayload | null;
  onRefresh: () => Promise<void>;
}

function getErrorMessage(error: unknown): string {
  const apiError = error as ApiErrorPayload;
  if (typeof apiError?.detail === "string") {
    return apiError.detail;
  }
  return apiError?.message ?? "Could not complete submission action.";
}

export function SubmissionPanel({
  caseId,
  submission,
  loading,
  error,
  onRefresh,
}: SubmissionPanelProps): JSX.Element {
  const permissions = usePermissions();
  const [approvedByUserId, setApprovedByUserId] = useState("");
  const [submittedByUserId, setSubmittedByUserId] = useState("");
  const [submissionReference, setSubmissionReference] = useState("");
  const [failedByUserId, setFailedByUserId] = useState("");
  const [failureReason, setFailureReason] = useState("");
  const [closedByUserId, setClosedByUserId] = useState("");
  const [notes, setNotes] = useState("");
  const [busyAction, setBusyAction] = useState<"approve" | "submit" | "fail" | "close" | null>(null);
  const [panelError, setPanelError] = useState<string | null>(null);
  const [panelMessage, setPanelMessage] = useState<string | null>(null);

  async function runAction(action: "approve" | "submit" | "fail" | "close", runner: () => Promise<void>): Promise<void> {
    setBusyAction(action);
    setPanelError(null);
    setPanelMessage(null);

    try {
      await runner();
      await onRefresh();
      setPanelMessage("Submission state updated.");
    } catch (actionError) {
      setPanelError(getErrorMessage(actionError));
    } finally {
      setBusyAction(null);
    }
  }

  if (loading) {
    return <LoadingState label="Loading submission..." />;
  }

  if (error && !submission) {
    return (
      <ErrorState
        title="Could not load submission"
        description="The submission state could not be retrieved from the backend."
      />
    );
  }

  return (
    <div className="detail-sections">
      {submission ? (
        <div className="entity-card">
          <div className="entity-card__header">
            <strong>Submission Status</strong>
            <p>Current final-state status for this case.</p>
          </div>

          <dl className="ui-key-values">
            <div>
              <dt>Status</dt>
              <dd>{submission.status}</dd>
            </div>
            <div>
              <dt>Approved At</dt>
              <dd>{submission.approved_for_submission_at ? new Date(submission.approved_for_submission_at).toLocaleString() : "Not approved"}</dd>
            </div>
            <div>
              <dt>Submitted At</dt>
              <dd>{submission.submitted_at ? new Date(submission.submitted_at).toLocaleString() : "Not submitted"}</dd>
            </div>
            <div>
              <dt>Submission Reference</dt>
              <dd>{submission.submission_reference ?? "Not available"}</dd>
            </div>
            <div>
              <dt>Approved By</dt>
              <dd>{submission.approved_by_user_id ?? "Not available"}</dd>
            </div>
            <div>
              <dt>Submitted By</dt>
              <dd>{submission.submitted_by_user_id ?? "Not available"}</dd>
            </div>
            <div>
              <dt>Failed At</dt>
              <dd>{submission.failed_at ? new Date(submission.failed_at).toLocaleString() : "No failure"}</dd>
            </div>
            <div>
              <dt>Failure Reason</dt>
              <dd>{submission.failure_reason ?? "No failure reason recorded"}</dd>
            </div>
          </dl>
        </div>
      ) : (
        <EmptyState
          title="No submission record"
          description="Approve, submit or fail the case to create and update the submission state."
        />
      )}

      <div className="entity-card">
        <div className="entity-card__header">
          <strong>Submission Actions</strong>
          <p>Approve for submission, mark submitted, fail the submission or close the case.</p>
        </div>

        {panelError ? <p className="document-feedback document-feedback--error">{panelError}</p> : null}
        {panelMessage ? <p className="document-feedback document-feedback--success">{panelMessage}</p> : null}

        {!permissions.can("manage_submission") && !permissions.can("execute_submission") ? (
          <p className="entity-card__hint">Your role can view submission state but cannot change it.</p>
        ) : null}

        <div className="detail-sections detail-sections--two-columns">
          <PermissionGate action="manage_submission">
            <div className="entity-card">
              <strong>Approve For Submission</strong>
              <label className="ui-field">
                <span>Approved By User</span>
                <input
                  value={approvedByUserId}
                  onChange={(event) => setApprovedByUserId(event.target.value)}
                  placeholder="staff.user"
                />
              </label>
              <label className="ui-field">
                <span>Notes</span>
                <input value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Approval notes" />
              </label>
              <button
                type="button"
                className="ui-button"
                disabled={busyAction !== null || !approvedByUserId.trim()}
                onClick={() =>
                  void runAction("approve", () =>
                    approveForSubmission({
                      caseId,
                      approvedByUserId: approvedByUserId.trim(),
                      notes: notes || undefined,
                    }).then(() => undefined),
                  )
                }
              >
                {busyAction === "approve" ? "Approving..." : "Approve for submission"}
              </button>
            </div>
          </PermissionGate>

          <PermissionGate
            anyOf={["execute_submission", "manage_submission"]}
            fallback={<p className="entity-card__hint">Your role cannot mark filings as submitted or failed.</p>}
          >
            <div className="entity-card">
              <strong>Mark Submitted</strong>
              <label className="ui-field">
                <span>Submitted By User</span>
                <input
                  value={submittedByUserId}
                  onChange={(event) => setSubmittedByUserId(event.target.value)}
                  placeholder="staff.user"
                />
              </label>
              <label className="ui-field">
                <span>Submission Reference</span>
                <input
                  value={submissionReference}
                  onChange={(event) => setSubmissionReference(event.target.value)}
                  placeholder="USCIS-12345"
                />
              </label>
              <label className="ui-field">
                <span>Notes</span>
                <input value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Submission notes" />
              </label>
              <button
                type="button"
                className="ui-button"
                disabled={busyAction !== null || !submittedByUserId.trim() || !submissionReference.trim()}
                onClick={() =>
                  void runAction("submit", () =>
                    submitCase({
                      caseId,
                      submittedByUserId: submittedByUserId.trim(),
                      submissionReference: submissionReference.trim(),
                      notes: notes || undefined,
                    }).then(() => undefined),
                  )
                }
              >
                {busyAction === "submit" ? "Submitting..." : "Mark submitted"}
              </button>
            </div>

            <div className="entity-card">
              <strong>Mark Failed</strong>
              <label className="ui-field">
                <span>Failed By User</span>
                <input
                  value={failedByUserId}
                  onChange={(event) => setFailedByUserId(event.target.value)}
                  placeholder="staff.user"
                />
              </label>
              <label className="ui-field">
                <span>Failure Reason</span>
                <input
                  value={failureReason}
                  onChange={(event) => setFailureReason(event.target.value)}
                  placeholder="Validation error from filing system"
                />
              </label>
              <button
                type="button"
                className="ui-button ui-button--ghost"
                disabled={busyAction !== null || !failedByUserId.trim() || !failureReason.trim()}
                onClick={() =>
                  void runAction("fail", () =>
                    failSubmission({
                      caseId,
                      failedByUserId: failedByUserId.trim(),
                      failureReason: failureReason.trim(),
                    }).then(() => undefined),
                  )
                }
              >
                {busyAction === "fail" ? "Saving..." : "Mark failed"}
              </button>
            </div>
          </PermissionGate>

          <PermissionGate action="manage_submission">
            <div className="entity-card">
              <strong>Close Case</strong>
              <label className="ui-field">
                <span>Closed By User</span>
                <input
                  value={closedByUserId}
                  onChange={(event) => setClosedByUserId(event.target.value)}
                  placeholder="staff.user"
                />
              </label>
              <label className="ui-field">
                <span>Notes</span>
                <input value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Closure notes" />
              </label>
              <button
                type="button"
                className="ui-button ui-button--ghost"
                disabled={busyAction !== null || !closedByUserId.trim()}
                onClick={() =>
                  void runAction("close", () =>
                    closeCase({
                      caseId,
                      closedByUserId: closedByUserId.trim(),
                      notes: notes || undefined,
                    }).then(() => undefined),
                  )
                }
              >
                {busyAction === "close" ? "Closing..." : "Close case"}
              </button>
            </div>
          </PermissionGate>
        </div>
      </div>
    </div>
  );
}
