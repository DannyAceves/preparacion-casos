"use client";

import { ChangeEvent, useEffect, useState } from "react";

import {
  buildQuestionMap,
  getInitialQuestionValue,
  isQuestionVisible,
  parseQuestionDraftValue,
} from "@/lib/questionnaire";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { FormFeedback } from "@/components/ui/form-feedback";
import { getApiErrorMessage } from "@/lib/api/errors";
import { saveClientPortalAnswer } from "@/services/client-portal";
import { CaseQuestionnaire, QuestionnaireQuestion } from "@/types/workspace";

interface ClientPortalQuestionnairePanelProps {
  portalSessionToken: string;
  questionnaire: CaseQuestionnaire | null;
  onRefresh: () => Promise<void>;
}

function ClientPortalQuestionField({
  portalSessionToken,
  question,
  onRefresh,
}: {
  portalSessionToken: string;
  question: QuestionnaireQuestion;
  onRefresh: () => Promise<void>;
}): JSX.Element {
  const [draftValue, setDraftValue] = useState(getInitialQuestionValue(question));
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDraftValue(getInitialQuestionValue(question));
    setFeedback(null);
    setError(null);
  }, [question]);

  async function handleSave(): Promise<void> {
    setSaving(true);
    setFeedback(null);
    setError(null);

    try {
      await saveClientPortalAnswer({
        portalSessionToken,
        question,
        value: parseQuestionDraftValue(question, draftValue),
      });
      await onRefresh();
      setFeedback("Progress saved.");
    } catch (saveError) {
      setError(getApiErrorMessage(saveError, "Could not save answer."));
    } finally {
      setSaving(false);
    }
  }

  function renderInput(): JSX.Element {
    if (question.input_type === "text" || question.input_type === "textarea") {
      return (
        <textarea
          className="questionnaire-field__textarea"
          value={draftValue}
          onChange={(event) => setDraftValue(event.target.value)}
          rows={4}
        />
      );
    }

    if (question.input_type === "date") {
      return <input type="date" value={draftValue} onChange={(event) => setDraftValue(event.target.value)} />;
    }

    if (question.input_type === "boolean" || question.input_type === "checkbox") {
      return (
        <select value={draftValue} onChange={(event) => setDraftValue(event.target.value)}>
          <option value="">Select an option</option>
          <option value="true">Yes</option>
          <option value="false">No</option>
        </select>
      );
    }

    if (question.input_type === "single_select" || question.input_type === "select") {
      return (
        <select value={draftValue} onChange={(event) => setDraftValue(event.target.value)}>
          <option value="">Select an option</option>
          {(question.options ?? []).map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      );
    }

    if (question.input_type === "radio") {
      return (
        <div className="questionnaire-choice-list">
          {(question.options ?? []).map((option) => (
            <label key={option.value} className="checklist-toggle">
              <input
                type="radio"
                name={`portal-question-${question.id}`}
                value={option.value}
                checked={draftValue === option.value}
                onChange={(event) => setDraftValue(event.target.value)}
              />
              <span>{option.label}</span>
            </label>
          ))}
        </div>
      );
    }

    if (question.input_type === "multi_select") {
      return (
        <input
          value={draftValue}
          onChange={(event) => setDraftValue(event.target.value)}
          placeholder="Comma-separated values"
        />
      );
    }

    return (
      <textarea
        className="questionnaire-field__textarea"
        value={draftValue}
        onChange={(event: ChangeEvent<HTMLTextAreaElement>) => setDraftValue(event.target.value)}
        rows={6}
        placeholder={
          question.input_type === "repeatable_group"
            ? '[{"field":"value"}]'
            : '{"key":"value"}'
        }
      />
    );
  }

  return (
    <div className="questionnaire-field">
      <div className="questionnaire-field__header">
        <div>
          <strong>{question.prompt}</strong>
          <p>{question.is_required ? "Required" : "Optional"}</p>
        </div>
      </div>

      {question.help_text ? <p className="questionnaire-field__help">{question.help_text}</p> : null}

      <label className="ui-field">
        <span>Answer</span>
        {renderInput()}
      </label>

      {error ? <FormFeedback tone="error" message={error} /> : null}
      {feedback ? <FormFeedback tone="success" message={feedback} /> : null}

      <button type="button" className="ui-button" disabled={saving} onClick={() => void handleSave()}>
        {saving ? "Saving..." : question.answer?.id ? "Update response" : "Save response"}
      </button>
    </div>
  );
}

export function ClientPortalQuestionnairePanel({
  portalSessionToken,
  questionnaire,
  onRefresh,
}: ClientPortalQuestionnairePanelProps): JSX.Element {
  if (!questionnaire || !questionnaire.sections.length) {
    return (
      <Card title="Questionnaire" subtitle="Digital intake form">
        <EmptyState
          title="No questionnaire assigned"
          description="Your legal team has not published a questionnaire for this case type yet."
        />
      </Card>
    );
  }

  const questionsByKey = buildQuestionMap(questionnaire.sections);

  return (
    <div className="page-stack">
      {questionnaire.sections.map((section) => (
        <Card
          key={section.id}
          title={section.title}
          subtitle={section.description ?? "Complete each question and save progress as you go."}
        >
          <div className="page-stack">
            {section.questions
              .filter((question) => isQuestionVisible(question, questionsByKey))
              .map((question) => (
                <ClientPortalQuestionField
                  key={question.id}
                  portalSessionToken={portalSessionToken}
                  question={question}
                  onRefresh={onRefresh}
                />
              ))}
          </div>
        </Card>
      ))}
    </div>
  );
}
