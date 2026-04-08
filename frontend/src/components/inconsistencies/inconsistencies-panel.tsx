"use client";

import { useState } from "react";

import { InconsistencyCard } from "@/components/inconsistencies/inconsistency-card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { dismissInconsistency, resolveInconsistency } from "@/services/inconsistencies";
import { ApiErrorPayload } from "@/types/api";
import { InconsistencyRecord } from "@/types/workspace";

interface InconsistenciesPanelProps {
  caseId: string;
  inconsistencies: InconsistencyRecord[];
  loading: boolean;
  error: ApiErrorPayload | null;
  onRefresh: () => Promise<void>;
}

function getErrorMessage(error: unknown): string {
  const apiError = error as ApiErrorPayload;
  if (typeof apiError?.detail === "string") {
    return apiError.detail;
  }
  return apiError?.message ?? "Could not update inconsistency.";
}

export function InconsistenciesPanel({
  caseId,
  inconsistencies,
  loading,
  error,
  onRefresh,
}: InconsistenciesPanelProps): JSX.Element {
  const [actorReference, setActorReference] = useState("");
  const [panelError, setPanelError] = useState<string | null>(null);

  async function handleResolve(input: { inconsistencyId: string; actorReference?: string; notes?: string }): Promise<void> {
    setPanelError(null);
    try {
      await resolveInconsistency({
        caseId,
        inconsistencyId: input.inconsistencyId,
        actorReference: input.actorReference,
        notes: input.notes,
      });
      await onRefresh();
    } catch (resolveError) {
      const message = getErrorMessage(resolveError);
      setPanelError(message);
      throw new Error(message);
    }
  }

  async function handleDismiss(input: { inconsistencyId: string; actorReference?: string; notes?: string }): Promise<void> {
    setPanelError(null);
    try {
      await dismissInconsistency({
        caseId,
        inconsistencyId: input.inconsistencyId,
        actorReference: input.actorReference,
        notes: input.notes,
      });
      await onRefresh();
    } catch (dismissError) {
      const message = getErrorMessage(dismissError);
      setPanelError(message);
      throw new Error(message);
    }
  }

  if (loading) {
    return <LoadingState label="Loading inconsistencies..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Could not load inconsistencies"
        description="The inconsistency data could not be retrieved from the backend."
      />
    );
  }

  if (!inconsistencies.length) {
    return (
      <EmptyState
        title="No inconsistencies"
        description="Detected mismatches between questionnaire, documents and canonical fields will appear here."
      />
    );
  }

  return (
    <div className="detail-sections">
      <div className="questionnaire-toolbar">
        <label className="ui-field">
          <span>Actor Reference</span>
          <input
            value={actorReference}
            onChange={(event) => setActorReference(event.target.value)}
            placeholder="staff.user"
          />
        </label>
        <p>Resolve or dismiss open inconsistencies and refresh the workspace after each action.</p>
      </div>

      {panelError ? <p className="document-feedback document-feedback--error">{panelError}</p> : null}

      {inconsistencies.map((item) => (
        <InconsistencyCard
          key={item.id}
          item={item}
          actorReference={actorReference}
          onResolve={handleResolve}
          onDismiss={handleDismiss}
        />
      ))}
    </div>
  );
}
