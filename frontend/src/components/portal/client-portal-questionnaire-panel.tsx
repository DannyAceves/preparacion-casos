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
import {
  isRocI751CaseType,
  localizeRocQuestion,
  localizeRocRepeatableField,
  localizeRocSection,
} from "@/lib/roc-i751-localization";
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
  isRocQuestionnaire,
}: {
  portalSessionToken: string;
  question: QuestionnaireQuestion;
  onRefresh: () => Promise<void>;
  isRocQuestionnaire: boolean;
}): JSX.Element {
  const [draftValue, setDraftValue] = useState(getInitialQuestionValue(question));
  const [groupDraftValue, setGroupDraftValue] = useState(getInitialRepeatableGroupValue(question));
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const displayQuestion = isRocQuestionnaire ? localizeRocQuestion(question) : question;

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
    if (displayQuestion.input_type === "text" || displayQuestion.input_type === "textarea") {
      return (
        <textarea
          className="questionnaire-field__textarea questionnaire-field__textarea--portal"
          value={draftValue}
          onChange={(event) => setDraftValue(event.target.value)}
          rows={4}
        />
      );
    }

    if (displayQuestion.input_type === "date") {
      return <input type="date" value={draftValue} onChange={(event) => setDraftValue(event.target.value)} />;
    }

    if (displayQuestion.input_type === "boolean" || displayQuestion.input_type === "checkbox") {
      return (
        <select value={draftValue} onChange={(event) => setDraftValue(event.target.value)}>
          <option value="">Seleccione una opcion</option>
          <option value="true">Si</option>
          <option value="false">No</option>
        </select>
      );
    }

    if (displayQuestion.input_type === "single_select" || displayQuestion.input_type === "select") {
      return (
        <select value={draftValue} onChange={(event) => setDraftValue(event.target.value)}>
          <option value="">Seleccione una opcion</option>
          {(displayQuestion.options ?? []).map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      );
    }

    if (displayQuestion.input_type === "radio") {
      return (
        <div className="questionnaire-choice-list questionnaire-choice-list--portal">
          {(displayQuestion.options ?? []).map((option) => (
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

    if (displayQuestion.input_type === "multi_select") {
      return (
        <input
          value={draftValue}
          onChange={(event) => setDraftValue(event.target.value)}
          placeholder="Valores separados por coma"
        />
      );
    }

    if (displayQuestion.input_type === "repeatable_group") {
      return (
        <RepeatableGroupField
          itemLabel={getRepeatableGroupItemLabel(displayQuestion)}
          fieldNames={getRepeatableGroupFieldNames(displayQuestion)}
          value={groupDraftValue}
          onChange={setGroupDraftValue}
          fieldLabelResolver={isRocQuestionnaire ? localizeRocRepeatableField : undefined}
          itemDescription="Completa cada bloque con la informacion correspondiente."
          addButtonLabel={`Agregar ${getRepeatableGroupItemLabel(displayQuestion).toLowerCase()}`}
        />
      );
    }

    return (
      <textarea
        className="questionnaire-field__textarea questionnaire-field__textarea--portal"
        value={draftValue}
        onChange={(event: ChangeEvent<HTMLTextAreaElement>) => setDraftValue(event.target.value)}
        rows={6}
        placeholder='{"clave":"valor"}'
      />
    );
  }

  return (
    <div className="questionnaire-field questionnaire-field--portal">
      <div className="questionnaire-field__header questionnaire-field__header--portal">
        <div>
          <strong>{displayQuestion.prompt}</strong>
          <p>{displayQuestion.is_required ? "Respuesta obligatoria" : "Respuesta opcional"}</p>
        </div>
      </div>

      {displayQuestion.help_text ? <p className="questionnaire-field__help">{displayQuestion.help_text}</p> : null}

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
  const isRocQuestionnaire = isRocI751CaseType(questionnaire.case_type);

  return (
    <div className="page-stack">
      {questionnaire.sections.map((section) => {
        const localizedSection = isRocQuestionnaire
          ? localizeRocSection(section.title, section.description)
          : { title: section.title, description: section.description ?? null };

        return (
          <Card
            key={section.id}
            title={localizedSection.title}
            subtitle={localizedSection.description ?? "Completa cada pregunta y guarda tu avance conforme avances."}
          >
            <div className="client-questionnaire-section">
              <div className="client-questionnaire-section__intro">
                <p>Guarda cada respuesta en cuanto la completes para no perder avance.</p>
              </div>
              <div className="client-questionnaire-grid">
                {section.questions
                  .filter((question) => isQuestionVisible(question, questionsByKey))
                  .map((question) => (
                    <ClientPortalQuestionField
                      key={question.id}
                      portalSessionToken={portalSessionToken}
                      question={question}
                      onRefresh={onRefresh}
                      isRocQuestionnaire={isRocQuestionnaire}
                    />
                  ))}
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
