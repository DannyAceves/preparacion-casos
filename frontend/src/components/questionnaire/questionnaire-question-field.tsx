"use client";

import { ChangeEvent, useEffect, useState } from "react";

import {
  getInitialQuestionValue,
  getInitialRepeatableGroupValue,
  getRepeatableGroupFieldNames,
  getRepeatableGroupItemLabel,
  parseQuestionDraftValue,
  QuestionnaireDraftValue,
} from "@/lib/questionnaire";
import { RepeatableGroupField } from "@/components/questionnaire/repeatable-group-field";
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
  const [groupDraftValue, setGroupDraftValue] = useState(getInitialRepeatableGroupValue(question));
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDraftValue(getInitialQuestionValue(question));
    setGroupDraftValue(getInitialRepeatableGroupValue(question));
    setFeedback(null);
    setError(null);
  }, [question]);

  async function handleSave(): Promise<void> {
    setSaving(true);
    setFeedback(null);
    setError(null);

    try {
      const value =
        question.input_type === "repeatable_group"
          ? { answer_json: groupDraftValue }
          : parseQuestionDraftValue(question, draftValue);
      await onSave(question, value);
      setFeedback(actorReference ? "Guardado." : "Guardado sin referencia de usuario.");
    } catch (saveError) {
      const message = saveError instanceof Error ? saveError.message : "No se pudo guardar la respuesta.";
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
          <option value="">Seleccione una opcion</option>
          <option value="true">Si</option>
          <option value="false">No</option>
        </select>
      );
    }

    if (question.input_type === "single_select" || question.input_type === "select") {
      return (
        <select value={draftValue} onChange={(event) => setDraftValue(event.target.value)}>
          <option value="">Seleccione una opcion</option>
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
          placeholder="Valores separados por coma"
        />
      );
    }

    if (question.input_type === "repeatable_group") {
      return (
        <RepeatableGroupField
          itemLabel={getRepeatableGroupItemLabel(question)}
          fieldNames={getRepeatableGroupFieldNames(question)}
          value={groupDraftValue}
          onChange={setGroupDraftValue}
        />
      );
    }

    return (
      <textarea
        className="questionnaire-field__textarea"
        value={draftValue}
        onChange={(event: ChangeEvent<HTMLTextAreaElement>) => setDraftValue(event.target.value)}
        rows={6}
        placeholder='{"clave":"valor"}'
      />
    );
  }

  return (
    <div className="questionnaire-field">
      <div className="questionnaire-field__header">
        <div>
          <strong>{question.prompt}</strong>
          <p>{question.is_required ? "Obligatoria" : "Opcional"}</p>
        </div>
      </div>

      {question.help_text ? <p className="questionnaire-field__help">{question.help_text}</p> : null}

      <label className="ui-field">
        <span>Respuesta</span>
        {renderInput()}
      </label>

      {error ? <p className="document-feedback document-feedback--error">{error}</p> : null}
      {feedback ? <p className="document-feedback document-feedback--success">{feedback}</p> : null}

      <button type="button" className="ui-button" disabled={saving} onClick={() => void handleSave()}>
        {saving ? "Guardando..." : question.answer?.id ? "Actualizar respuesta" : "Guardar respuesta"}
      </button>
    </div>
  );
}
