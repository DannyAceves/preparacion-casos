import { RouteAccessGuard } from "@/components/auth/route-access-guard";
import { QuestionnaireTemplateBuilder } from "@/components/questionnaire-templates/questionnaire-template-builder";

export default function QuestionnaireTemplatesPage(): JSX.Element {
  return (
    <RouteAccessGuard href="/questionnaire-templates">
      <QuestionnaireTemplateBuilder />
    </RouteAccessGuard>
  );
}
