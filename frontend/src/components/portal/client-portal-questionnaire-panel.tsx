"use client";

import { ChangeEvent, useEffect, useState } from "react";

import {
  buildQuestionMap,
  getInitialQuestionValue,
  getInitialRepeatableGroupValue,
  getRepeatableGroupFieldNames,
  getRepeatableGroupItemLabel,
  isQuestionVisible,
  parseQuestionDraftValue,
} from "@/lib/questionnaire";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { FormFeedback } from "@/components/ui/form-feedback";
import { RepeatableGroupField } from "@/components/questionnaire/repeatable-group-field";
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
      await saveClientPortalAnswer({
        portalSessionToken,
        question,
        value:
          question.input_type === "repeatable_group"
            ? { answer_json: groupDraftValue }
            : parseQuestionDraftValue(question, draftValue),
      });
      await onRefresh();
      setFeedback("Progreso guardado.");
    } catch (saveError) {
      setError(getApiErrorMessage(saveError, "No se pudo guardar la respuesta."));
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

      {error ? <FormFeedback tone="error" message={error} /> : null}
      {feedback ? <FormFeedback tone="success" message={feedback} /> : null}

      <button type="button" className="ui-button" disabled={saving} onClick={() => void handleSave()}>
        {saving ? "Guardando..." : question.answer?.id ? "Actualizar respuesta" : "Guardar respuesta"}
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
      <Card title="Cuestionario" subtitle="Formulario digital del cliente">
        <EmptyState
          title="No hay cuestionario asignado"
          description="Tu equipo legal aun no ha publicado un cuestionario para este tipo de caso."
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
          subtitle={section.description ?? "Completa cada pregunta y guarda tu avance conforme avances."}
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
