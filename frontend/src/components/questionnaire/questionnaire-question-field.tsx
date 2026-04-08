"use client";

import { ChangeEvent, useEffect, useState } from "react";

import {
  getInitialQuestionValue,
  parseQuestionDraftValue,
  QuestionnaireDraftValue,
} from "@/lib/questionnaire";
import { QuestionnaireQuestion } from "@/types/workspace";

interface QuestionnaireQuestionFieldProps {
  question: QuestionnaireQuestion;
  actorReference: string;
  onSave: (question: QuestionnaireQuestion, value: QuestionnaireDraftValue) => Promise<void>;
}

export function QuestionnaireQuestionField({
  question,
  actorReference,
  onSave,
}: QuestionnaireQuestionFieldProps): JSX.Element {
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
      const value = parseQuestionDraftValue(question, draftValue);
      await onSave(question, value);
      setFeedback(actorReference ? "Saved." : "Saved without actor reference.");
    } catch (saveError) {
      const message = saveError instanceof Error ? saveError.message : "Could not save answer.";
      setError(message);
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
                name={`question-${question.id}`}
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
          <p>
            {question.key} | {question.input_type} {question.is_required ? "| required" : "| optional"}
          </p>
        </div>
      </div>

      {question.help_text ? <p className="questionnaire-field__help">{question.help_text}</p> : null}

      <label className="ui-field">
        <span>Answer</span>
        {renderInput()}
      </label>

      {error ? <p className="document-feedback document-feedback--error">{error}</p> : null}
      {feedback ? <p className="document-feedback document-feedback--success">{feedback}</p> : null}

      <button type="button" className="ui-button" disabled={saving} onClick={() => void handleSave()}>
        {saving ? "Saving..." : question.answer?.id ? "Update answer" : "Save answer"}
      </button>
    </div>
  );
}
