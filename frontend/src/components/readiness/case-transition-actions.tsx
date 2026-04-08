"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { PermissionGate } from "@/components/auth/permission-gate";
import { transitionCase, validateCaseReadiness } from "@/services/readiness";
import { ApiErrorPayload } from "@/types/api";
import { CaseReadiness } from "@/types/case";

type TransitionTarget = "attorney_review" | "ready_for_submission" | "submitted";

interface CaseTransitionActionsProps {
  caseId: string;
  currentStatus: string;
  readiness: CaseReadiness;
  onValidated: (nextReadiness: CaseReadiness) => void;
}

interface TransitionOption {
  target: TransitionTarget;
  label: string;
  description: string;
  critical: boolean;
}

function getErrorMessage(error: unknown): string {
  const apiError = error as ApiErrorPayload;
  if (typeof apiError?.detail === "string") {
    return apiError.detail;
  }
  return apiError?.message ?? "Could not transition case.";
}

function getTransitionOptions(currentStatus: string): TransitionOption[] {
  if (currentStatus === "attorney_review") {
    return [
      {
        target: "ready_for_submission",
        label: "Move to ready_for_submission",
        description: "Marks the case as ready to submit once readiness rules pass.",
        critical: true,
      },
    ];
  }

  if (currentStatus === "ready_for_submission") {
    return [
      {
        target: "submitted",
        label: "Move to submitted",
        description: "Marks the case as submitted. Use when filing is complete.",
        critical: true,
      },
    ];
  }

  if (currentStatus === "submitted" || currentStatus === "closed") {
    return [];
  }

  return [
    {
      target: "attorney_review",
      label: "Move to attorney_review",
      description: "Advances the case to attorney review once readiness rules pass.",
      critical: false,
    },
  ];
}

export function CaseTransitionActions({
  caseId,
  currentStatus,
  readiness,
  onValidated,
}: CaseTransitionActionsProps): JSX.Element {
  const router = useRouter();
  const [actorReference, setActorReference] = useState("");
  const [notes, setNotes] = useState("");
  const [busyTarget, setBusyTarget] = useState<TransitionTarget | null>(null);
  const [error, setError] = useState<string | null>(null);
  const options = getTransitionOptions(currentStatus);

  async function handleTransition(option: TransitionOption): Promise<void> {
    const confirmationMessage = option.critical
      ? `Confirm transition to ${option.target}. This is a critical state change.`
      : `Confirm transition to ${option.target}?`;

    if (!window.confirm(confirmationMessage)) {
      return;
    }

    setBusyTarget(option.target);
    setError(null);

    try {
      await transitionCase({
        caseId,
        targetStatus: option.target,
        actorReference: actorReference || undefined,
        notes: notes || undefined,
      });
      const nextReadiness = await validateCaseReadiness({
        caseId,
        actorReference: actorReference || undefined,
      });
      onValidated(nextReadiness);
      router.refresh();
    } catch (transitionError) {
      setError(getErrorMessage(transitionError));
    } finally {
      setBusyTarget(null);
    }
  }

  return (
    <div className="entity-card">
      <div className="entity-card__header">
        <strong>State Transitions</strong>
        <p>Controlled state changes based on the current case status and readiness rules.</p>
      </div>

      <div className="entity-card__meta">
        <p>Current status: {currentStatus}</p>
      </div>

      <div className="entity-card__grid">
        <label className="ui-field">
          <span>Actor Reference</span>
          <input
            value={actorReference}
            onChange={(event) => setActorReference(event.target.value)}
            placeholder="staff.user"
          />
        </label>

        <label className="ui-field entity-card__field-span">
          <span>Notes</span>
          <input
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Why this transition is being executed"
          />
        </label>
      </div>

      {error ? <p className="document-feedback document-feedback--error">{error}</p> : null}

      <PermissionGate
        action="transition_case_status"
        fallback={<p className="entity-card__hint">Your role can view readiness but cannot transition case status.</p>}
      >
        {options.length ? (
          <div className="page-stack">
            {options.map((option) => {
              const targetReadiness = readiness.targets.find((item) => item.target_status === option.target);
              const isDisabled = busyTarget !== null || !targetReadiness;

              return (
                <div key={option.target} className="placeholder-note">
                  <strong>{option.label}</strong>
                  <p>{option.description}</p>
                  <p>
                    {targetReadiness
                      ? targetReadiness.is_ready
                        ? "Readiness says this target is currently allowed."
                        : "Readiness currently blocks this target."
                      : "No readiness data available for this target."}
                  </p>
                  <button
                    type="button"
                    className="ui-button"
                    disabled={isDisabled}
                    onClick={() => void handleTransition(option)}
                  >
                    {busyTarget === option.target ? "Transitioning..." : option.label}
                  </button>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="placeholder-note">
            <strong>No UI transitions available</strong>
            <p>This case is already in a terminal or non-advanceable state from this panel.</p>
          </div>
        )}
      </PermissionGate>
    </div>
  );
}
