"use client";

import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { FormFeedback } from "@/components/ui/form-feedback";
import { LoadingState } from "@/components/ui/loading-state";
import { getApiErrorMessage } from "@/lib/api/errors";
import {
  approveGeneratedForm,
  getGeneratedFormWorkspace,
  markGeneratedFormFixRequired,
  updateAssistedFormField,
} from "@/services/forms";
import {
  AssistedFormFieldRecord,
  AssistedFormWorkspaceRecord,
} from "@/types/workspace";

interface AssistedFormWorkspaceProps {
  caseId: string;
  generatedFormId: string;
}

function stringifyValue(value: AssistedFormFieldRecord["value"]): string {
  if (value === null || value === undefined) {
    return "";
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value, null, 2);
}

function parseFieldValue(field: AssistedFormFieldRecord, rawValue: string): AssistedFormFieldRecord["value"] {
  if (field.field_type === "checkbox") {
    return rawValue === "true";
  }
  if (field.field_type === "date") {
    return rawValue || null;
  }
  if (field.field_type === "repeatable_group") {
    return rawValue ? (JSON.parse(rawValue) as Record<string, unknown> | unknown[]) : [];
  }
  return rawValue;
}

function warningMessage(warning: Record<string, unknown>): string {
  return typeof warning.message === "string" ? warning.message : "Field warning";
}

function toneForStatus(status: AssistedFormWorkspaceRecord["status"]): "neutral" | "warning" | "danger" | "success" | "info" {
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

export function AssistedFormWorkspace({
  caseId,
  generatedFormId,
}: AssistedFormWorkspaceProps): JSX.Element {
  const [workspace, setWorkspace] = useState<AssistedFormWorkspaceRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [selectedFieldKey, setSelectedFieldKey] = useState<string | null>(null);
  const [fieldDraft, setFieldDraft] = useState("");
  const [reviewedByUserId, setReviewedByUserId] = useState("");
  const [reviewNotes, setReviewNotes] = useState("");
  const [busyAction, setBusyAction] = useState<"save" | "approve" | "fix" | null>(null);

  async function loadWorkspace(): Promise<void> {
    setLoading(true);
    setError(null);

    try {
      const nextWorkspace = await getGeneratedFormWorkspace(generatedFormId);
      setWorkspace(nextWorkspace);
      if (!selectedFieldKey) {
        setSelectedFieldKey(nextWorkspace.sections[0]?.fields[0]?.form_field_key ?? null);
      }
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Could not load assisted form workspace."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadWorkspace();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [generatedFormId]);

  const allFields = useMemo(
    () => workspace?.sections.flatMap((section) => section.fields) ?? [],
    [workspace],
  );
  const selectedField =
    allFields.find((field) => field.form_field_key === selectedFieldKey) ?? null;

  useEffect(() => {
    if (selectedField) {
      setFieldDraft(stringifyValue(selectedField.value));
    }
  }, [selectedField]);

  async function handleSaveField(): Promise<void> {
    if (!selectedField) {
      return;
    }
    setBusyAction("save");
    setError(null);
    setMessage(null);

    try {
      const detail = await updateAssistedFormField({
        generatedFormId,
        formFieldKey: selectedField.form_field_key,
        actorReference: reviewedByUserId.trim() || undefined,
        value: parseFieldValue(selectedField, fieldDraft),
        manualOverride: true,
        selectedSourceKey: selectedField.selected_source_key,
        selectedSourceLabel: selectedField.selected_source_label,
      });
      setWorkspace(detail.workspace);
      setMessage(`Field ${selectedField.field_label} updated.`);
    } catch (saveError) {
      setError(getApiErrorMessage(saveError, "Could not save field changes."));
    } finally {
      setBusyAction(null);
    }
  }

  async function handleAcceptSuggestion(index: number): Promise<void> {
    if (!selectedField) {
      return;
    }
    const suggestion = selectedField.suggestions[index];
    if (!suggestion) {
      return;
    }

    setBusyAction("save");
    setError(null);
    setMessage(null);

    try {
      const detail = await updateAssistedFormField({
        generatedFormId,
        formFieldKey: selectedField.form_field_key,
        actorReference: reviewedByUserId.trim() || undefined,
        value: suggestion.value,
        manualOverride: false,
        selectedSourceKey: suggestion.source_key,
        selectedSourceLabel: suggestion.source_label,
      });
      setWorkspace(detail.workspace);
      setMessage(`Suggestion applied to ${selectedField.field_label}.`);
    } catch (saveError) {
      setError(getApiErrorMessage(saveError, "Could not apply suggestion."));
    } finally {
      setBusyAction(null);
    }
  }

  async function handleApprove(): Promise<void> {
    setBusyAction("approve");
    setError(null);
    setMessage(null);

    try {
      await approveGeneratedForm({
        generatedFormId,
        reviewedByUserId: reviewedByUserId.trim() || "staff.user",
        reviewNotes: reviewNotes.trim() || undefined,
      });
      await loadWorkspace();
      setMessage("Form approved.");
    } catch (approveError) {
      setError(getApiErrorMessage(approveError, "Could not approve form."));
    } finally {
      setBusyAction(null);
    }
  }

  async function handleFix(): Promise<void> {
    setBusyAction("fix");
    setError(null);
    setMessage(null);

    try {
      await markGeneratedFormFixRequired({
        generatedFormId,
        reviewedByUserId: reviewedByUserId.trim() || "staff.user",
        reviewNotes: reviewNotes.trim() || undefined,
      });
      await loadWorkspace();
      setMessage("Form marked as fix required.");
    } catch (fixError) {
      setError(getApiErrorMessage(fixError, "Could not mark form as fix required."));
    } finally {
      setBusyAction(null);
    }
  }

  if (loading) {
    return <LoadingState label="Loading assisted form workspace..." />;
  }

  if (error && !workspace) {
    return <ErrorState title="Could not load assisted form workspace" description={error} />;
  }

  if (!workspace) {
    return (
      <EmptyState
        title="No assisted form workspace"
        description="Generate a form draft first so the field-by-field workspace can be prepared."
      />
    );
  }

  return (
    <div className="page-stack">
      <section className="page-heading">
        <div>
          <h2>{workspace.form.form_name}</h2>
          <p>
            {workspace.form.form_code} · Case {caseId}
          </p>
        </div>
        <div className="case-hero__badges">
          <Badge tone={toneForStatus(workspace.status)}>{workspace.status}</Badge>
          <Badge tone="warning">{workspace.warnings.length} warnings</Badge>
        </div>
      </section>

      {message ? <FormFeedback tone="success" message={message} /> : null}
      {error ? <FormFeedback tone="error" message={error} /> : null}

      <div className="assisted-form-workspace">
        <div className="assisted-form-workspace__main">
          {workspace.sections.map((section) => (
            <Card key={section.section_key} title={section.section_title} subtitle={`${section.fields.length} field(s)`}>
              <div className="page-stack">
                {section.fields.map((field) => (
                  <button
                    key={field.form_field_key}
                    type="button"
                    className={`entity-card entity-card--button ${selectedFieldKey === field.form_field_key ? "entity-card--selected" : ""}`}
                    onClick={() => setSelectedFieldKey(field.form_field_key)}
                  >
                    <div className="entity-card__header entity-card__header--spread">
                      <div>
                        <strong>{field.field_label}</strong>
                        <p>{field.form_field_key}</p>
                      </div>
                      <div className="case-hero__badges">
                        {field.required ? <Badge tone="warning">required</Badge> : null}
                        {field.manual_override ? <Badge tone="info">manual</Badge> : null}
                        {field.selected_source_label ? <Badge tone="neutral">{field.selected_source_label}</Badge> : null}
                      </div>
                    </div>
                    <div className="entity-card__meta">
                      <p>Current value: {stringifyValue(field.value) || "No value selected"}</p>
                      <p>{field.suggestions.length} suggestion(s) available</p>
                    </div>
                    {field.warnings.length ? (
                      <div className="case-hero__badges">
                        {field.warnings.map((warning, index) => (
                          <Badge key={`${field.form_field_key}-warning-${index}`} tone="danger">
                            {warningMessage(warning)}
                          </Badge>
                        ))}
                      </div>
                    ) : null}
                  </button>
                ))}
              </div>
            </Card>
          ))}
        </div>

        <aside className="assisted-form-workspace__sidebar">
          {!selectedField ? (
            <Card title="Field Suggestions" subtitle="Select a field to review suggested values and traceability.">
              <EmptyState
                title="No field selected"
                description="Choose a field from the form sections to inspect its value sources."
              />
            </Card>
          ) : (
            <div className="page-stack">
              <Card title={selectedField.field_label} subtitle={selectedField.form_field_key}>
                <div className="entity-form">
                  <div className="case-hero__badges">
                    {selectedField.required ? <Badge tone="warning">required</Badge> : null}
                    <Badge tone="neutral">{selectedField.field_type}</Badge>
                    <Badge tone="info">{selectedField.canonical_field_key}</Badge>
                  </div>
                  {selectedField.help_text ? <p className="entity-card__hint">{selectedField.help_text}</p> : null}

                  <label className="ui-field">
                    <span>Current Value</span>
                    {selectedField.field_type === "textarea" || selectedField.field_type === "repeatable_group" ? (
                      <textarea
                        className="ui-textarea"
                        value={fieldDraft}
                        onChange={(event) => setFieldDraft(event.target.value)}
                        rows={selectedField.field_type === "repeatable_group" ? 8 : 5}
                      />
                    ) : selectedField.field_type === "checkbox" ? (
                      <select value={fieldDraft} onChange={(event) => setFieldDraft(event.target.value)}>
                        <option value="">Select an option</option>
                        <option value="true">Yes</option>
                        <option value="false">No</option>
                      </select>
                    ) : (
                      <input
                        type={selectedField.field_type === "date" ? "date" : "text"}
                        value={fieldDraft}
                        onChange={(event) => setFieldDraft(event.target.value)}
                      />
                    )}
                  </label>

                  {selectedField.warnings.length ? (
                    <div className="page-stack">
                      {selectedField.warnings.map((warning, index) => (
                        <FormFeedback key={`${selectedField.form_field_key}-side-warning-${index}`} tone="error" message={warningMessage(warning)} />
                      ))}
                    </div>
                  ) : null}

                  <div className="entity-form__actions">
                    <button type="button" className="ui-button" disabled={busyAction === "save"} onClick={() => void handleSaveField()}>
                      {busyAction === "save" ? "Saving..." : "Save field"}
                    </button>
                  </div>
                </div>
              </Card>

              <Card title="Suggested Values" subtitle="Canonical fields, questionnaire answers and extracted document values.">
                {!selectedField.suggestions.length ? (
                  <EmptyState
                    title="No suggestions available"
                    description="This field does not have source values yet, so it must be completed manually."
                  />
                ) : (
                  <div className="page-stack">
                    {selectedField.suggestions.map((suggestion, index) => (
                      <div key={suggestion.source_key} className="entity-card">
                        <div className="entity-card__header entity-card__header--spread">
                          <div>
                            <strong>{suggestion.source_label}</strong>
                            <p>{suggestion.source_type}</p>
                          </div>
                          <button
                            type="button"
                            className="ui-button ui-button--ghost"
                            disabled={busyAction === "save"}
                            onClick={() => void handleAcceptSuggestion(index)}
                          >
                            Use this value
                          </button>
                        </div>
                        <pre className="entity-card__evidence">{JSON.stringify(suggestion.value, null, 2)}</pre>
                        {suggestion.source_document_name ? (
                          <p className="entity-card__hint">Source document: {suggestion.source_document_name}</p>
                        ) : null}
                      </div>
                    ))}
                  </div>
                )}
              </Card>

              <Card title="Review" subtitle="Finalize the draft after field-level review.">
                <div className="entity-form">
                  <label className="ui-field">
                    <span>Reviewed By User</span>
                    <input
                      value={reviewedByUserId}
                      onChange={(event) => setReviewedByUserId(event.target.value)}
                      placeholder="staff.user"
                    />
                  </label>
                  <label className="ui-field">
                    <span>Review Notes</span>
                    <textarea
                      className="ui-textarea"
                      value={reviewNotes}
                      onChange={(event) => setReviewNotes(event.target.value)}
                      rows={4}
                    />
                  </label>
                  <div className="entity-form__actions">
                    <button type="button" className="ui-button" disabled={busyAction !== null} onClick={() => void handleApprove()}>
                      {busyAction === "approve" ? "Approving..." : "Approve"}
                    </button>
                    <button type="button" className="ui-button ui-button--ghost" disabled={busyAction !== null} onClick={() => void handleFix()}>
                      {busyAction === "fix" ? "Saving..." : "Mark fix required"}
                    </button>
                  </div>
                </div>
              </Card>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
