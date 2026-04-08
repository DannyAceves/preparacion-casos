"use client";

import { useState } from "react";

import { PermissionGate } from "@/components/auth/permission-gate";
import { GeneratedFormCard } from "@/components/forms/generated-form-card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { usePermissions } from "@/hooks/use-permissions";
import {
  approveGeneratedForm,
  generateForms,
  getGeneratedFormDetail,
  markGeneratedFormFixRequired,
} from "@/services/forms";
import { ApiErrorPayload } from "@/types/api";
import { GeneratedFormDetailRecord, GeneratedFormRecord } from "@/types/workspace";

interface FormsPanelProps {
  caseId: string;
  forms: GeneratedFormRecord[];
  loading: boolean;
  error: ApiErrorPayload | null;
  onRefresh: () => Promise<void>;
}

function getErrorMessage(error: unknown): string {
  const apiError = error as ApiErrorPayload;
  if (typeof apiError?.detail === "string") {
    return apiError.detail;
  }
  return apiError?.message ?? "Could not complete form action.";
}

export function FormsPanel({ caseId, forms, loading, error, onRefresh }: FormsPanelProps): JSX.Element {
  const permissions = usePermissions();
  const [generatedByReference, setGeneratedByReference] = useState("");
  const [exportBasePath, setExportBasePath] = useState("");
  const [panelError, setPanelError] = useState<string | null>(null);
  const [panelMessage, setPanelMessage] = useState<string | null>(null);
  const [busyFormId, setBusyFormId] = useState<string | null>(null);
  const [busyAction, setBusyAction] = useState<"approve" | "fix" | "loading" | "generate" | null>(null);
  const [details, setDetails] = useState<Record<string, GeneratedFormDetailRecord>>({});

  async function handleGenerate(): Promise<void> {
    setPanelError(null);
    setPanelMessage(null);
    setBusyAction("generate");

    try {
      await generateForms({
        caseId,
        generatedByReference: generatedByReference || undefined,
        exportBasePath: exportBasePath || undefined,
      });
      await onRefresh();
      setPanelMessage("Forms generated successfully.");
    } catch (generateError) {
      setPanelError(getErrorMessage(generateError));
    } finally {
      setBusyAction(null);
    }
  }

  async function handleLoadDetail(generatedFormId: string): Promise<void> {
    if (details[generatedFormId]) {
      return;
    }

    setBusyFormId(generatedFormId);
    setBusyAction("loading");
    setPanelError(null);

    try {
      const detail = await getGeneratedFormDetail(generatedFormId);
      setDetails((current) => ({ ...current, [generatedFormId]: detail }));
    } catch (detailError) {
      const message = getErrorMessage(detailError);
      setPanelError(message);
      throw new Error(message);
    } finally {
      setBusyFormId(null);
      setBusyAction(null);
    }
  }

  async function handleApprove(
    generatedFormId: string,
    input: { reviewedByUserId: string; reviewNotes?: string },
  ): Promise<void> {
    setBusyFormId(generatedFormId);
    setBusyAction("approve");
    setPanelError(null);
    setPanelMessage(null);

    try {
      await approveGeneratedForm({
        generatedFormId,
        reviewedByUserId: input.reviewedByUserId,
        reviewNotes: input.reviewNotes,
      });
      await onRefresh();
      setPanelMessage("Form approved.");
    } catch (approveError) {
      const message = getErrorMessage(approveError);
      setPanelError(message);
      throw new Error(message);
    } finally {
      setBusyFormId(null);
      setBusyAction(null);
    }
  }

  async function handleFix(
    generatedFormId: string,
    input: { reviewedByUserId: string; reviewNotes?: string },
  ): Promise<void> {
    setBusyFormId(generatedFormId);
    setBusyAction("fix");
    setPanelError(null);
    setPanelMessage(null);

    try {
      await markGeneratedFormFixRequired({
        generatedFormId,
        reviewedByUserId: input.reviewedByUserId,
        reviewNotes: input.reviewNotes,
      });
      await onRefresh();
      setPanelMessage("Form marked as fix required.");
    } catch (fixError) {
      const message = getErrorMessage(fixError);
      setPanelError(message);
      throw new Error(message);
    } finally {
      setBusyFormId(null);
      setBusyAction(null);
    }
  }

  if (loading) {
    return <LoadingState label="Loading generated forms..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Could not load forms"
        description="The generated forms for this case could not be retrieved from the backend."
      />
    );
  }

  return (
    <div className="detail-sections">
      <div className="entity-card">
        <div className="entity-card__header">
          <strong>Generate Forms</strong>
          <p>Create assisted form drafts from canonical fields, questionnaire answers and extracted document data.</p>
        </div>

        <div className="entity-card__grid">
          <label className="ui-field">
            <span>Generated By Reference</span>
            <input
              value={generatedByReference}
              onChange={(event) => setGeneratedByReference(event.target.value)}
              placeholder="staff.user"
              disabled={!permissions.can("generate_forms")}
            />
          </label>

          <label className="ui-field entity-card__field-span">
            <span>Export Base Path</span>
            <input
              value={exportBasePath}
              onChange={(event) => setExportBasePath(event.target.value)}
              placeholder="/exports/forms"
              disabled={!permissions.can("generate_forms")}
            />
          </label>
        </div>

        {panelError ? <p className="document-feedback document-feedback--error">{panelError}</p> : null}
        {panelMessage ? <p className="document-feedback document-feedback--success">{panelMessage}</p> : null}

        <PermissionGate
          action="generate_forms"
          fallback={<p className="entity-card__hint">Your role cannot generate form drafts.</p>}
        >
          <button type="button" className="ui-button" disabled={busyAction === "generate"} onClick={() => void handleGenerate()}>
            {busyAction === "generate" ? "Generating..." : "Generate forms"}
          </button>
        </PermissionGate>
      </div>

      {!forms.length ? (
        <EmptyState
          title="No generated forms"
          description="Generate forms to open the assisted field-by-field workspace and review export references here."
        />
      ) : (
        forms.map((form) => (
          <GeneratedFormCard
            key={form.id}
            form={form}
            detail={details[form.id] ?? null}
            actorReference={generatedByReference}
            caseId={caseId}
            busyAction={busyFormId === form.id ? busyAction === "generate" ? null : busyAction : null}
            onLoadDetail={() => handleLoadDetail(form.id)}
            onApprove={(input) => handleApprove(form.id, input)}
            onFix={(input) => handleFix(form.id, input)}
          />
        ))
      )}
    </div>
  );
}
