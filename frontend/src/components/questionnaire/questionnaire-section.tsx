"use client";

import { Card } from "@/components/ui/card";
import { buildQuestionMap, isQuestionVisible, QuestionnaireDraftValue } from "@/lib/questionnaire";
import { QuestionnaireQuestionField } from "@/components/questionnaire/questionnaire-question-field";
import { QuestionnaireQuestion, QuestionnaireSection as QuestionnaireSectionType } from "@/types/workspace";

interface QuestionnaireSectionProps {
  section: QuestionnaireSectionType;
  allSections: QuestionnaireSectionType[];
  actorReference: string;
  onSave: (question: QuestionnaireQuestion, value: QuestionnaireDraftValue) => Promise<void>;
}

export function QuestionnaireSection({
  section,
  allSections,
  actorReference,
  onSave,
}: QuestionnaireSectionProps): JSX.Element {
  const questionsByKey = buildQuestionMap(allSections);
  const visibleQuestions = section.questions.filter((question) => isQuestionVisible(question, questionsByKey));

  return (
    <Card title={section.title} subtitle={section.description ?? "Questionnaire section"}>
      <div className="page-stack">
        {visibleQuestions.map((question) => (
          <QuestionnaireQuestionField
            key={question.id}
            question={question}
            actorReference={actorReference}
            onSave={onSave}
          />
        ))}
      </div>
    </Card>
  );
}
