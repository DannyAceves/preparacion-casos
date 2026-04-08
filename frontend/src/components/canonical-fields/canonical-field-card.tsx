"use client";

import { useEffect, useState } from "react";

import { usePermissions } from "@/hooks/use-permissions";
import { CanonicalFieldRecord } from "@/types/workspace";

type CanonicalStatus = "suggested" | "confirmed" | "approved" | "rejected";

interface CanonicalFieldCardProps {
  field: CanonicalFieldRecord;
  actorReference: string;
  onSave: (input: {
    fieldKey: string;
    actorReference?: string;
    fieldValue: Record<string, unknown> | unknown[] | string | number | boolean | null;
    confidenceScore?: string | null;
    sourcePriority?: number | null;
    status?: CanonicalStatus | null;
  }) => Promise<void>;
}

function formatFieldValue(value: CanonicalFieldRecord["field_value"]): string {
  if (value === null || value === undefined) {
    return "";
  }

  if (typeof value === "string") {
    return value;
  }

  return JSON.stringify(value, null, 2);
}

function parseFieldValue(rawValue: string): Record<string, unknown> | unknown[] | string | number | boolean | null {
  const trimmed = rawValue.trim();
  if (!trimmed) {
    return null;
  }

  if (trimmed === "true") {
    return true;
  }
  if (trimmed === "false") {
    return false;
  }
  if (!Number.isNaN(Number(trimmed)) && trimmed !== "") {
    return Number(trimmed);
  }
  if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
    return JSON.parse(trimmed) as Record<string, unknown> | unknown[];
  }

  return rawValue;
}

export function CanonicalFieldCard({ field, actorReference, onSave }: CanonicalFieldCardProps): JSX.Element {
  const permissions = usePermissions();
  const [fieldValue, setFieldValue] = useState(formatFieldValue(field.field_value));
  const [confidenceScore, setConfidenceScore] = useState(field.confidence_score ?? "");
  const [sourcePriority, setSourcePriority] = useState(String(field.source_priority));
  const [status, setStatus] = useState<CanonicalStatus>(field.status);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  useEffect(() => {
    setFieldValue(formatFieldValue(field.field_value));
    setConfidenceScore(field.confidence_score ?? "");
    setSourcePriority(String(field.source_priority));
    setStatus(field.status);
    setError(null);
    setFeedback(null);
  }, [field]);

  async function handleSave(): Promise<void> {
    setSaving(true);
    setError(null);
    setFeedback(null);

    try {
      await onSave({
        fieldKey: field.field_key,
        actorReference: actorReference || undefined,
        fieldValue: parseFieldValue(fieldValue),
        confidenceScore,
        sourcePriority: Number(sourcePriority),
        status,
      });
      setFeedback("Canonical field updated.");
    } catch (saveError) {
      const message = saveError instanceof Error ? saveError.message : "Could not update field.";
      setError(message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="entity-card">
      <div className="entity-card__header">
        <div>
          <strong>{field.field_key}</strong>
          <p>Source document: {field.source_document_id ?? "Not linked"}</p>
        </div>
      </div>

      <label className="ui-field">
        <span>Field Value</span>
        <textarea
          className="questionnaire-field__textarea"
          rows={5}
          value={fieldValue}
          onChange={(event) => setFieldValue(event.target.value)}
          disabled={!permissions.can("edit_canonical_fields")}
        />
      </label>

      <div className="entity-card__grid">
        <label className="ui-field">
          <span>Status</span>
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value as CanonicalStatus)}
            disabled={!permissions.can("edit_canonical_fields")}
          >
            <option value="suggested">suggested</option>
            <option value="confirmed">confirmed</option>
            <option value="approved">approved</option>
            <option value="rejected">rejected</option>
          </select>
        </label>

        <label className="ui-field">
          <span>Confidence Score</span>
          <input
            value={confidenceScore}
            onChange={(event) => setConfidenceScore(event.target.value)}
            placeholder="0.95"
            disabled={!permissions.can("edit_canonical_fields")}
          />
        </label>

        <label className="ui-field">
          <span>Source Priority</span>
          <input
            value={sourcePriority}
            onChange={(event) => setSourcePriority(event.target.value)}
            placeholder="0"
            disabled={!permissions.can("edit_canonical_fields")}
          />
        </label>
      </div>

      {error ? <p className="document-feedback document-feedback--error">{error}</p> : null}
      {feedback ? <p className="document-feedback document-feedback--success">{feedback}</p> : null}

      <button
        type="button"
        className="ui-button"
        disabled={saving || !permissions.can("edit_canonical_fields")}
        onClick={() => void handleSave()}
      >
        {permissions.can("edit_canonical_fields") ? (saving ? "Saving..." : "Save field") : "Editing Restricted"}
      </button>
    </div>
  );
}
