import { apiClient } from "@/lib/api/client";
import { QuestionnaireAnswer, QuestionnaireQuestion } from "@/types/workspace";

type QuestionnaireAnswerInputValue = {
  answer_text?: string | null;
  answer_date?: string | null;
  answer_boolean?: boolean | null;
  answer_choice?: string | null;
  answer_choices?: string[] | null;
  answer_json?: Record<string, unknown> | unknown[] | null;
};

interface SaveQuestionnaireAnswerInput {
  caseId: string;
  question: QuestionnaireQuestion;
  value: QuestionnaireAnswerInputValue;
  actorReference?: string;
}

function buildValuePayload(input: SaveQuestionnaireAnswerInput): QuestionnaireAnswerInputValue {
  const { question, value } = input;

  if (question.input_type === "text" || question.input_type === "textarea") {
    return { answer_text: value.answer_text ?? null };
  }

  if (question.input_type === "date") {
    return { answer_date: value.answer_date ?? null };
  }

  if (question.input_type === "boolean" || question.input_type === "checkbox") {
    return { answer_boolean: value.answer_boolean ?? null };
  }

  if (question.input_type === "single_select" || question.input_type === "radio" || question.input_type === "select") {
    return { answer_choice: value.answer_choice ?? null };
  }

  if (question.input_type === "multi_select") {
    return { answer_choices: value.answer_choices ?? [] };
  }

  if (question.input_type === "repeatable_group" || question.input_type === "json") {
    return { answer_json: value.answer_json ?? null };
  }

  return { answer_text: value.answer_text ?? null };
}

export async function saveQuestionnaireAnswer(input: SaveQuestionnaireAnswerInput): Promise<QuestionnaireAnswer> {
  const payloadValue = buildValuePayload(input);

  if (input.question.answer?.id) {
    return apiClient.patch<QuestionnaireAnswer>(
      `/cases/${input.caseId}/questionnaire/answers/${input.question.answer.id}`,
      {
        body: JSON.stringify({
          actor_reference: input.actorReference,
          value: payloadValue,
        }),
      },
    );
  }

  const response = await apiClient.post<QuestionnaireAnswer[]>(
    `/cases/${input.caseId}/questionnaire/answers`,
    {
      body: JSON.stringify({
        actor_reference: input.actorReference,
        answers: [
          {
            question_id: input.question.id,
            value: payloadValue,
          },
        ],
      }),
    },
  );

  return response[0];
}
