"use client";

import { useState } from "react";

import { CanonicalFieldCard } from "@/components/canonical-fields/canonical-field-card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { updateCanonicalField } from "@/services/canonical-fields";
import { ApiErrorPayload } from "@/types/api";
import { CanonicalFieldRecord } from "@/types/workspace";

interface CanonicalFieldsPanelProps {
  caseId: string;
  fields: CanonicalFieldRecord[];
  loading: boolean;
  error: ApiErrorPayload | null;
  onRefresh: () => Promise<void>;
}

function getErrorMessage(error: unknown): string {
  const apiError = error as ApiErrorPayload;
  if (typeof apiError?.detail === "string") {
    return apiError.detail;
  }
  return apiError?.message ?? "Could not update field.";
}

export function CanonicalFieldsPanel({
  caseId,
  fields,
  loading,
  error,
  onRefresh,
}: CanonicalFieldsPanelProps): JSX.Element {
  const [actorReference, setActorReference] = useState("");
  const [panelError, setPanelError] = useState<string | null>(null);

  async function handleSave(input: {
    fieldKey: string;
    actorReference?: string;
    fieldValue: Record<string, unknown> | unknown[] | string | number | boolean | null;
    confidenceScore?: string | null;
    sourcePriority?: number | null;
    status?: "suggested" | "confirmed" | "approved" | "rejected" | null;
  }): Promise<void> {
    setPanelError(null);

    try {
      await updateCanonicalField({
        caseId,
        fieldKey: input.fieldKey,
        actorReference: input.actorReference,
        fieldValue: input.fieldValue,
        confidenceScore: input.confidenceScore,
        sourcePriority: input.sourcePriority,
        status: input.status,
      });
      await onRefresh();
    } catch (saveError) {
      const message = getErrorMessage(saveError);
      setPanelError(message);
      throw new Error(message);
    }
  }

  if (loading) {
    return <LoadingState label="Loading canonical fields..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Could not load canonical fields"
        description="The canonical field data could not be retrieved from the backend."
      />
    );
  }

  if (!fields.length) {
    return (
      <EmptyState
        title="No canonical fields"
        description="Canonical case fields will appear here once extraction and consolidation run."
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
        <p>Updates write back to the canonical field table and refresh the case workspace.</p>
      </div>

      {panelError ? <p className="document-feedback document-feedback--error">{panelError}</p> : null}

      {fields.map((field) => (
        <CanonicalFieldCard
          key={field.id}
          field={field}
          actorReference={actorReference}
          onSave={handleSave}
        />
      ))}
    </div>
  );
}
