import { QuestionnaireAnswer, QuestionnaireQuestion, QuestionnaireSection } from "@/types/workspace";

export type QuestionnaireDraftValue = {
  answer_text?: string | null;
  answer_date?: string | null;
  answer_boolean?: boolean | null;
  answer_choice?: string | null;
  answer_choices?: string[] | null;
  answer_json?: Record<string, unknown> | unknown[] | null;
};

function getComparableAnswerValue(answer: QuestionnaireAnswer | null): unknown {
  if (!answer) {
    return null;
  }
  if (answer.answer_boolean !== null) {
    return answer.answer_boolean;
  }
  if (answer.answer_choice !== null) {
    return answer.answer_choice;
  }
  if (answer.answer_choices !== null) {
    return answer.answer_choices;
  }
  if (answer.answer_date !== null) {
    return answer.answer_date;
  }
  if (answer.answer_json !== null) {
    return answer.answer_json;
  }
  return answer.answer_text;
}

function evaluateCondition(
  condition: Record<string, unknown>,
  questionsByKey: Map<string, QuestionnaireQuestion>,
): boolean {
  const dependsOnKey = typeof condition.depends_on_key === "string" ? condition.depends_on_key : null;
  if (!dependsOnKey) {
    return true;
  }

  const dependentQuestion = questionsByKey.get(dependsOnKey);
  const actualValue = getComparableAnswerValue(dependentQuestion?.answer ?? null);
  const operator = typeof condition.operator === "string" ? condition.operator : "equals";
  const expectedValue = condition.value;

  if (operator === "equals") {
    return JSON.stringify(actualValue) === JSON.stringify(expectedValue);
  }
  if (operator === "not_equals") {
    return JSON.stringify(actualValue) !== JSON.stringify(expectedValue);
  }
  if (operator === "contains") {
    return Array.isArray(actualValue) ? actualValue.includes(expectedValue) : false;
  }
  if (operator === "exists") {
    return actualValue !== null && actualValue !== undefined && actualValue !== "";
  }

  return true;
}

export function isQuestionVisible(
  question: QuestionnaireQuestion,
  questionsByKey: Map<string, QuestionnaireQuestion>,
): boolean {
  const rules = question.conditional_rules;
  if (!rules) {
    return true;
  }

  if (Array.isArray(rules.all)) {
    return (rules.all as Record<string, unknown>[]).every((condition) =>
      evaluateCondition(condition, questionsByKey),
    );
  }

  if (Array.isArray(rules.any)) {
    return (rules.any as Record<string, unknown>[]).some((condition) =>
      evaluateCondition(condition, questionsByKey),
    );
  }

  return evaluateCondition(rules, questionsByKey);
}

export function buildQuestionMap(sections: QuestionnaireSection[]): Map<string, QuestionnaireQuestion> {
  return new Map(
    sections.flatMap((section) =>
      section.questions.map((question) => [question.key, question] as const),
    ),
  );
}

export function getInitialQuestionValue(question: QuestionnaireQuestion): string {
  const answer = question.answer;
  if (!answer) {
    return "";
  }

  if (question.input_type === "text" || question.input_type === "textarea") {
    return answer.answer_text ?? "";
  }

  if (question.input_type === "date") {
    return answer.answer_date ?? "";
  }

  if (question.input_type === "boolean" || question.input_type === "checkbox") {
    if (answer.answer_boolean === null) {
      return "";
    }
    return answer.answer_boolean ? "true" : "false";
  }

  if (question.input_type === "single_select" || question.input_type === "radio" || question.input_type === "select") {
    return answer.answer_choice ?? "";
  }

  if (question.input_type === "multi_select") {
    return answer.answer_choices?.join(", ") ?? "";
  }

  return answer.answer_json ? JSON.stringify(answer.answer_json, null, 2) : "";
}

export function parseQuestionDraftValue(
  question: QuestionnaireQuestion,
  draftValue: string,
): QuestionnaireDraftValue {
  if (question.input_type === "text" || question.input_type === "textarea") {
    return { answer_text: draftValue };
  }

  if (question.input_type === "date") {
    return { answer_date: draftValue || null };
  }

  if (question.input_type === "boolean" || question.input_type === "checkbox") {
    if (!draftValue) {
      return { answer_boolean: null };
    }
    return { answer_boolean: draftValue === "true" };
  }

  if (question.input_type === "single_select" || question.input_type === "radio" || question.input_type === "select") {
    return { answer_choice: draftValue || null };
  }

  if (question.input_type === "multi_select") {
    return {
      answer_choices: draftValue
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
    };
  }

  return {
    answer_json: draftValue ? (JSON.parse(draftValue) as Record<string, unknown> | unknown[]) : null,
  };
}
