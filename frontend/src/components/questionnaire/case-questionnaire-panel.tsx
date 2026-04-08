"use client";

import { useState } from "react";

import { QuestionnaireSection } from "@/components/questionnaire/questionnaire-section";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { FormFeedback } from "@/components/ui/form-feedback";
import { getApiErrorMessage } from "@/lib/api/errors";
import { instantiateCaseQuestionnaire } from "@/services/questionnaire-templates";
import { saveQuestionnaireAnswer } from "@/services/questionnaire";
import { ApiErrorPayload } from "@/types/api";
import { CaseQuestionnaire, QuestionnaireQuestion } from "@/types/workspace";
import { QuestionnaireDraftValue } from "@/lib/questionnaire";

interface CaseQuestionnairePanelProps {
  caseId: string;
  questionnaire: CaseQuestionnaire | null;
  loading: boolean;
  error: ApiErrorPayload | null;
  onRefresh: () => Promise<void>;
}

function getErrorMessage(error: unknown): string {
  const apiError = error as ApiErrorPayload;
  if (typeof apiError?.detail === "string") {
    return apiError.detail;
  }
  return apiError?.message ?? "Could not save answer.";
}

export function CaseQuestionnairePanel({
  caseId,
  questionnaire,
  loading,
  error,
  onRefresh,
}: CaseQuestionnairePanelProps): JSX.Element {
  const [actorReference, setActorReference] = useState("");
  const [saveError, setSaveError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [instantiating, setInstantiating] = useState(false);

  async function handleSave(question: QuestionnaireQuestion, value: QuestionnaireDraftValue): Promise<void> {
    setSaveError(null);
    setActionMessage(null);

    try {
      await saveQuestionnaireAnswer({
        caseId,
        question,
        value,
        actorReference: actorReference.trim() || undefined,
      });
      await onRefresh();
    } catch (saveAnswerError) {
      const message = getErrorMessage(saveAnswerError);
      setSaveError(message);
      throw new Error(message);
    }
  }

  async function handleInstantiate(): Promise<void> {
    setInstantiating(true);
    setSaveError(null);
    setActionMessage(null);

    try {
      await instantiateCaseQuestionnaire(caseId);
      await onRefresh();
      setActionMessage("Questionnaire instance generated for this case.");
    } catch (error) {
      setSaveError(getApiErrorMessage(error, "Could not generate questionnaire for this case."));
    } finally {
      setInstantiating(false);
    }
  }

  if (loading) {
    return <LoadingState label="Loading questionnaire..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Could not load questionnaire"
        description="The questionnaire data could not be retrieved from the backend."
      />
    );
  }

  if (!questionnaire || !questionnaire.sections.length) {
    return (
      <EmptyState
        title="No questionnaire available"
        description="This case type does not have a questionnaire template assigned yet."
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
        <div className="questionnaire-toolbar__meta">
          <p>Responses are saved per question and refresh the workspace after each successful write.</p>
          <div className="entity-form__actions">
            <button type="button" className="ui-button ui-button--ghost" disabled={instantiating} onClick={() => void handleInstantiate()}>
              {instantiating
                ? "Generating..."
                : questionnaire.questionnaire_instance_id
                  ? "Ensure questionnaire instance"
                  : "Generate questionnaire for case"}
            </button>
          </div>
        </div>
      </div>

      {actionMessage ? <FormFeedback tone="success" message={actionMessage} /> : null}
      {saveError ? <p className="document-feedback document-feedback--error">{saveError}</p> : null}

      {questionnaire.sections.map((section) => (
        <QuestionnaireSection
          key={section.id}
          section={section}
          allSections={questionnaire.sections}
          actorReference={actorReference}
          onSave={handleSave}
        />
      ))}
    </div>
  );
}
