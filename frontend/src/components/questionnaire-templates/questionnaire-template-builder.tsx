"use client";

import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { FormFeedback } from "@/components/ui/form-feedback";
import { FormField } from "@/components/ui/form-field";
import { LoadingState } from "@/components/ui/loading-state";
import { getApiErrorMessage } from "@/lib/api/errors";
import {
  activateQuestionnaireTemplate,
  createQuestionnaireTemplate,
  createQuestionnaireTemplateVersion,
  getQuestionnaireTemplate,
  listQuestionnaireTemplates,
  updateQuestionnaireTemplate,
} from "@/services/questionnaire-templates";
import {
  CreateQuestionnaireTemplateInput,
  QuestionnaireTemplate,
  QuestionnaireTemplateInputType,
  QuestionnaireTemplateQuestion,
  QuestionnaireTemplateSection,
} from "@/types/questionnaire-template";

interface EditableTemplateQuestion extends QuestionnaireTemplateQuestion {
  localId: string;
  optionsText: string;
  validationRulesText: string;
  conditionalRulesText: string;
  fieldConfigText: string;
}

interface EditableTemplateSection extends QuestionnaireTemplateSection {
  localId: string;
  questions: EditableTemplateQuestion[];
}

interface EditableTemplateState {
  caseType: string;
  title: string;
  description: string;
  status: "draft" | "active" | "archived";
  sections: EditableTemplateSection[];
}

const questionTypeOptions: QuestionnaireTemplateInputType[] = [
  "text",
  "textarea",
  "date",
  "checkbox",
  "radio",
  "select",
  "repeatable_group",
];

function makeId(prefix: string): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return `${prefix}-${crypto.randomUUID()}`;
  }
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}`;
}

function parseJsonObject(value: string): Record<string, unknown> | null {
  if (!value.trim()) {
    return null;
  }
  return JSON.parse(value) as Record<string, unknown>;
}

function serializeJson(value: Record<string, unknown> | null | undefined): string {
  return value ? JSON.stringify(value, null, 2) : "";
}

function serializeOptions(options: QuestionnaireTemplateQuestion["options"]): string {
  if (!options?.length) {
    return "";
  }
  return options.map((option) => `${option.label}|${option.value}`).join("\n");
}

function parseOptions(value: string): { label: string; value: string }[] | null {
  const options = value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [label, rawValue] = line.split("|");
      return {
        label: (label ?? "").trim(),
        value: (rawValue ?? label ?? "").trim(),
      };
    })
    .filter((option) => option.label && option.value);
  return options.length ? options : null;
}

function createBlankQuestion(displayOrder = 0): EditableTemplateQuestion {
  return {
    localId: makeId("question"),
    key: "",
    prompt: "",
    help_text: null,
    input_type: "text",
    is_required: false,
    display_order: displayOrder,
    options: null,
    validation_rules: null,
    conditional_rules: null,
    field_config: null,
    optionsText: "",
    validationRulesText: "",
    conditionalRulesText: "",
    fieldConfigText: "",
  };
}

function createBlankSection(displayOrder = 0): EditableTemplateSection {
  return {
    localId: makeId("section"),
    title: "",
    description: null,
    display_order: displayOrder,
    questions: [createBlankQuestion(0)],
  };
}

function createBlankTemplate(): EditableTemplateState {
  return {
    caseType: "",
    title: "",
    description: "",
    status: "draft",
    sections: [createBlankSection(0)],
  };
}

function mapTemplateToEditableState(template: QuestionnaireTemplate): EditableTemplateState {
  return {
    caseType: template.case_type,
    title: template.title,
    description: template.description ?? "",
    status: template.status,
    sections: template.sections.map((section, sectionIndex) => ({
      ...section,
      localId: makeId(`section-${sectionIndex}`),
      questions: section.questions.map((question, questionIndex) => ({
        ...question,
        localId: makeId(`question-${questionIndex}`),
        optionsText: serializeOptions(question.options),
        validationRulesText: serializeJson(question.validation_rules),
        conditionalRulesText: serializeJson(question.conditional_rules),
        fieldConfigText: serializeJson(question.field_config),
      })),
    })),
  };
}

function buildPayload(state: EditableTemplateState): CreateQuestionnaireTemplateInput {
  return {
    case_type: state.caseType.trim(),
    title: state.title.trim(),
    description: state.description.trim() || null,
    status: state.status,
    sections: state.sections.map((section, sectionIndex) => ({
      title: section.title.trim(),
      description: section.description?.trim() || null,
      display_order: sectionIndex,
      questions: section.questions.map((question, questionIndex) => ({
        key: question.key.trim(),
        prompt: question.prompt.trim(),
        help_text: question.help_text?.trim() || null,
        input_type: question.input_type,
        is_required: question.is_required,
        display_order: questionIndex,
        options: parseOptions(question.optionsText),
        validation_rules: parseJsonObject(question.validationRulesText),
        conditional_rules: parseJsonObject(question.conditionalRulesText),
        field_config: parseJsonObject(question.fieldConfigText),
      })),
    })),
  };
}

export function QuestionnaireTemplateBuilder(): JSX.Element {
  const [templates, setTemplates] = useState<QuestionnaireTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [filterCaseType, setFilterCaseType] = useState("");
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
  const [formState, setFormState] = useState<EditableTemplateState>(createBlankTemplate());
  const [submitting, setSubmitting] = useState(false);

  async function loadTemplates(preferredTemplateId?: string | null): Promise<void> {
    setLoading(true);
    setError(null);

    try {
      const nextTemplates = await listQuestionnaireTemplates(filterCaseType.trim() || undefined);
      setTemplates(nextTemplates);

      const nextSelectedId =
        preferredTemplateId ??
        selectedTemplateId ??
        nextTemplates[0]?.id ??
        null;

      if (nextSelectedId) {
        const detail = await getQuestionnaireTemplate(nextSelectedId);
        setSelectedTemplateId(detail.id);
        setFormState(mapTemplateToEditableState(detail));
      } else {
        setSelectedTemplateId(null);
        setFormState(createBlankTemplate());
      }
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Could not load questionnaire templates."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadTemplates();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterCaseType]);

  const groupedCaseTypes = useMemo(
    () => Array.from(new Set(templates.map((template) => template.case_type))).sort(),
    [templates],
  );

  function selectTemplate(template: QuestionnaireTemplate): void {
    setSelectedTemplateId(template.id);
    setFormState(mapTemplateToEditableState(template));
    setMessage(null);
    setError(null);
  }

  function updateSection(
    sectionLocalId: string,
    updater: (section: EditableTemplateSection) => EditableTemplateSection,
  ): void {
    setFormState((current) => ({
      ...current,
      sections: current.sections.map((section) =>
        section.localId === sectionLocalId ? updater(section) : section,
      ),
    }));
  }

  async function handleSaveTemplate(): Promise<void> {
    setSubmitting(true);
    setMessage(null);
    setError(null);

    try {
      const payload = buildPayload(formState);
      const saved = selectedTemplateId
        ? await updateQuestionnaireTemplate(selectedTemplateId, payload)
        : await createQuestionnaireTemplate(payload);
      await loadTemplates(saved.id);
      setMessage(selectedTemplateId ? "Template updated successfully." : "Template created successfully.");
    } catch (saveError) {
      setError(getApiErrorMessage(saveError, "Could not save questionnaire template."));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleActivateTemplate(): Promise<void> {
    if (!selectedTemplateId) {
      return;
    }
    setSubmitting(true);
    setMessage(null);
    setError(null);

    try {
      const saved = await activateQuestionnaireTemplate(selectedTemplateId);
      await loadTemplates(saved.id);
      setMessage("Template activated successfully.");
    } catch (activateError) {
      setError(getApiErrorMessage(activateError, "Could not activate template."));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCreateVersion(): Promise<void> {
    if (!selectedTemplateId) {
      return;
    }
    setSubmitting(true);
    setMessage(null);
    setError(null);

    try {
      const nextVersion = await createQuestionnaireTemplateVersion(selectedTemplateId, {
        title: formState.title,
        description: formState.description,
        status: "draft",
      });
      await loadTemplates(nextVersion.id);
      setMessage("New draft version created from the current template.");
    } catch (versionError) {
      setError(getApiErrorMessage(versionError, "Could not create new template version."));
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return <LoadingState label="Loading questionnaire templates..." />;
  }

  return (
    <div className="page-stack">
      <section className="page-heading">
        <div>
          <h2>Questionnaire Templates</h2>
          <p>Build reusable, versioned questionnaire templates per case type.</p>
        </div>
        <button
          type="button"
          className="ui-button"
          onClick={() => {
            setSelectedTemplateId(null);
            setFormState(createBlankTemplate());
            setMessage(null);
            setError(null);
          }}
        >
          New Template
        </button>
      </section>

      <section className="cases-toolbar">
        <div>
          <strong>Template library</strong>
          <p>Filter by case type, then activate a version when it is ready for production use.</p>
        </div>
        <div className="cases-toolbar__actions">
          <label className="ui-field">
            <span>Case Type Filter</span>
            <input
              value={filterCaseType}
              onChange={(event) => setFilterCaseType(event.target.value)}
              placeholder="family-based, i-751, humanitarian"
            />
          </label>
        </div>
      </section>

      {error ? <ErrorState title="Questionnaire templates failed to load" description={error} /> : null}
      {message ? <FormFeedback tone="success" message={message} /> : null}

      <div className="detail-sections detail-sections--two-columns">
        <Card title="Versions" subtitle="All templates returned from the backend">
          {!templates.length ? (
            <EmptyState
              title="No templates yet"
              description="Create the first questionnaire template for a case type to get started."
            />
          ) : (
            <div className="page-stack">
              {groupedCaseTypes.map((caseType) => (
                <div key={caseType} className="page-stack">
                  <div className="placeholder-note">
                    <strong>{caseType}</strong>
                    <p>{templates.filter((template) => template.case_type === caseType).length} version(s)</p>
                  </div>
                  {templates
                    .filter((template) => template.case_type === caseType)
                    .map((template) => (
                      <button
                        key={template.id}
                        type="button"
                        className={`entity-card entity-card--button ${selectedTemplateId === template.id ? "entity-card--selected" : ""}`}
                        onClick={() => selectTemplate(template)}
                      >
                        <div className="entity-card__header entity-card__header--spread">
                          <div>
                            <strong>{template.title}</strong>
                            <p>Version {template.version}</p>
                          </div>
                          <div className="case-hero__badges">
                            <Badge tone={template.status === "active" ? "success" : template.status === "draft" ? "warning" : "neutral"}>
                              {template.status}
                            </Badge>
                          </div>
                        </div>
                      </button>
                    ))}
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card
          title={selectedTemplateId ? "Edit Template" : "Create Template"}
          subtitle="Define sections, structured questions, conditions and reusable field configuration."
        >
          <div className="entity-form">
            <div className="entity-form__grid">
              <FormField label="Case Type" htmlFor="template-case-type">
                <input
                  id="template-case-type"
                  value={formState.caseType}
                  onChange={(event) => setFormState((current) => ({ ...current, caseType: event.target.value }))}
                  placeholder="i-751"
                />
              </FormField>
              <FormField label="Title" htmlFor="template-title">
                <input
                  id="template-title"
                  value={formState.title}
                  onChange={(event) => setFormState((current) => ({ ...current, title: event.target.value }))}
                  placeholder="Removal of Conditions / I-751"
                />
              </FormField>
              <FormField label="Status" htmlFor="template-status">
                <select
                  id="template-status"
                  value={formState.status}
                  onChange={(event) =>
                    setFormState((current) => ({
                      ...current,
                      status: event.target.value as EditableTemplateState["status"],
                    }))
                  }
                >
                  <option value="draft">draft</option>
                  <option value="active">active</option>
                  <option value="archived">archived</option>
                </select>
              </FormField>
              <FormField label="Description" htmlFor="template-description">
                <textarea
                  id="template-description"
                  className="ui-textarea"
                  value={formState.description}
                  onChange={(event) => setFormState((current) => ({ ...current, description: event.target.value }))}
                  placeholder="Reusable digital questionnaire for a specific case type."
                />
              </FormField>
            </div>

            <div className="page-stack">
              {formState.sections.map((section, sectionIndex) => (
                <div key={section.localId} className="entity-card">
                  <div className="entity-card__header entity-card__header--spread">
                    <div>
                      <strong>Section {sectionIndex + 1}</strong>
                      <p>Define the section and its structured questions.</p>
                    </div>
                    <button
                      type="button"
                      className="ui-button ui-button--ghost"
                      onClick={() =>
                        setFormState((current) => ({
                          ...current,
                          sections: current.sections.filter((item) => item.localId !== section.localId),
                        }))
                      }
                      disabled={formState.sections.length === 1}
                    >
                      Remove Section
                    </button>
                  </div>

                  <div className="entity-form__grid">
                    <FormField label="Section Title" htmlFor={`section-title-${section.localId}`}>
                      <input
                        id={`section-title-${section.localId}`}
                        value={section.title}
                        onChange={(event) =>
                          updateSection(section.localId, (current) => ({
                            ...current,
                            title: event.target.value,
                          }))
                        }
                      />
                    </FormField>
                    <FormField label="Description" htmlFor={`section-description-${section.localId}`}>
                      <textarea
                        id={`section-description-${section.localId}`}
                        className="ui-textarea"
                        value={section.description ?? ""}
                        onChange={(event) =>
                          updateSection(section.localId, (current) => ({
                            ...current,
                            description: event.target.value,
                          }))
                        }
                      />
                    </FormField>
                  </div>

                  <div className="page-stack">
                    {section.questions.map((question, questionIndex) => (
                      <div key={question.localId} className="questionnaire-field">
                        <div className="entity-card__header entity-card__header--spread">
                          <div>
                            <strong>Question {questionIndex + 1}</strong>
                            <p>Structured field definition used in the digital questionnaire.</p>
                          </div>
                          <button
                            type="button"
                            className="ui-button ui-button--ghost"
                            onClick={() =>
                              updateSection(section.localId, (current) => ({
                                ...current,
                                questions: current.questions.filter((item) => item.localId !== question.localId),
                              }))
                            }
                            disabled={section.questions.length === 1}
                          >
                            Remove Question
                          </button>
                        </div>

                        <div className="entity-form__grid">
                          <FormField label="Question Key" htmlFor={`question-key-${question.localId}`}>
                            <input
                              id={`question-key-${question.localId}`}
                              value={question.key}
                              onChange={(event) =>
                                updateSection(section.localId, (current) => ({
                                  ...current,
                                  questions: current.questions.map((item) =>
                                    item.localId === question.localId ? { ...item, key: event.target.value } : item,
                                  ),
                                }))
                              }
                              placeholder="marriage_date"
                            />
                          </FormField>
                          <FormField label="Input Type" htmlFor={`question-type-${question.localId}`}>
                            <select
                              id={`question-type-${question.localId}`}
                              value={question.input_type}
                              onChange={(event) =>
                                updateSection(section.localId, (current) => ({
                                  ...current,
                                  questions: current.questions.map((item) =>
                                    item.localId === question.localId
                                      ? { ...item, input_type: event.target.value as QuestionnaireTemplateInputType }
                                      : item,
                                  ),
                                }))
                              }
                            >
                              {questionTypeOptions.map((option) => (
                                <option key={option} value={option}>
                                  {option}
                                </option>
                              ))}
                            </select>
                          </FormField>
                          <FormField label="Prompt" htmlFor={`question-prompt-${question.localId}`}>
                            <textarea
                              id={`question-prompt-${question.localId}`}
                              className="ui-textarea"
                              value={question.prompt}
                              onChange={(event) =>
                                updateSection(section.localId, (current) => ({
                                  ...current,
                                  questions: current.questions.map((item) =>
                                    item.localId === question.localId ? { ...item, prompt: event.target.value } : item,
                                  ),
                                }))
                              }
                            />
                          </FormField>
                          <FormField label="Help Text" htmlFor={`question-help-${question.localId}`}>
                            <textarea
                              id={`question-help-${question.localId}`}
                              className="ui-textarea"
                              value={question.help_text ?? ""}
                              onChange={(event) =>
                                updateSection(section.localId, (current) => ({
                                  ...current,
                                  questions: current.questions.map((item) =>
                                    item.localId === question.localId ? { ...item, help_text: event.target.value } : item,
                                  ),
                                }))
                              }
                            />
                          </FormField>
                          <FormField
                            label="Options"
                            htmlFor={`question-options-${question.localId}`}
                            hint="Use one option per line in the format label|value. Required for radio and select."
                          >
                            <textarea
                              id={`question-options-${question.localId}`}
                              className="ui-textarea"
                              value={question.optionsText}
                              onChange={(event) =>
                                updateSection(section.localId, (current) => ({
                                  ...current,
                                  questions: current.questions.map((item) =>
                                    item.localId === question.localId ? { ...item, optionsText: event.target.value } : item,
                                  ),
                                }))
                              }
                            />
                          </FormField>
                          <FormField
                            label="Conditional Rules"
                            htmlFor={`question-conditions-${question.localId}`}
                            hint='Example: {"depends_on_key":"has_children","operator":"equals","value":true}'
                          >
                            <textarea
                              id={`question-conditions-${question.localId}`}
                              className="ui-textarea"
                              value={question.conditionalRulesText}
                              onChange={(event) =>
                                updateSection(section.localId, (current) => ({
                                  ...current,
                                  questions: current.questions.map((item) =>
                                    item.localId === question.localId
                                      ? { ...item, conditionalRulesText: event.target.value }
                                      : item,
                                  ),
                                }))
                              }
                            />
                          </FormField>
                          <FormField
                            label="Validation Rules"
                            htmlFor={`question-validation-${question.localId}`}
                            hint='Optional JSON. Example: {"min_length":2}'
                          >
                            <textarea
                              id={`question-validation-${question.localId}`}
                              className="ui-textarea"
                              value={question.validationRulesText}
                              onChange={(event) =>
                                updateSection(section.localId, (current) => ({
                                  ...current,
                                  questions: current.questions.map((item) =>
                                    item.localId === question.localId
                                      ? { ...item, validationRulesText: event.target.value }
                                      : item,
                                  ),
                                }))
                              }
                            />
                          </FormField>
                          <FormField
                            label="Field Config"
                            htmlFor={`question-config-${question.localId}`}
                            hint='Use this for repeatable groups. Example: {"columns":[{"key":"child_name","label":"Child name","type":"text"}]}'
                          >
                            <textarea
                              id={`question-config-${question.localId}`}
                              className="ui-textarea"
                              value={question.fieldConfigText}
                              onChange={(event) =>
                                updateSection(section.localId, (current) => ({
                                  ...current,
                                  questions: current.questions.map((item) =>
                                    item.localId === question.localId
                                      ? { ...item, fieldConfigText: event.target.value }
                                      : item,
                                  ),
                                }))
                              }
                            />
                          </FormField>
                        </div>

                        <label className="checklist-toggle">
                          <input
                            type="checkbox"
                            checked={question.is_required}
                            onChange={(event) =>
                              updateSection(section.localId, (current) => ({
                                ...current,
                                questions: current.questions.map((item) =>
                                  item.localId === question.localId
                                    ? { ...item, is_required: event.target.checked }
                                    : item,
                                ),
                              }))
                            }
                          />
                          <span>Required question</span>
                        </label>
                      </div>
                    ))}
                  </div>

                  <div className="entity-form__actions">
                    <button
                      type="button"
                      className="ui-button ui-button--ghost"
                      onClick={() =>
                        updateSection(section.localId, (current) => ({
                          ...current,
                          questions: [
                            ...current.questions,
                            createBlankQuestion(current.questions.length),
                          ],
                        }))
                      }
                    >
                      Add Question
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="entity-form__actions">
              <button
                type="button"
                className="ui-button ui-button--ghost"
                onClick={() =>
                  setFormState((current) => ({
                    ...current,
                    sections: [...current.sections, createBlankSection(current.sections.length)],
                  }))
                }
              >
                Add Section
              </button>
              <button type="button" className="ui-button" disabled={submitting} onClick={() => void handleSaveTemplate()}>
                {submitting ? "Saving..." : selectedTemplateId ? "Save Draft" : "Create Template"}
              </button>
              {selectedTemplateId ? (
                <>
                  <button type="button" className="ui-button ui-button--ghost" disabled={submitting} onClick={() => void handleActivateTemplate()}>
                    Activate Version
                  </button>
                  <button type="button" className="ui-button ui-button--ghost" disabled={submitting} onClick={() => void handleCreateVersion()}>
                    New Version
                  </button>
                </>
              ) : null}
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
