import { RouteAccessGuard } from "@/components/auth/route-access-guard";
import { AssistedFormWorkspace } from "@/components/forms/assisted-form-workspace";

interface AssistedFormWorkspacePageProps {
  params: {
    caseId: string;
    generatedFormId: string;
  };
}

export default function AssistedFormWorkspacePage({
  params,
}: AssistedFormWorkspacePageProps): JSX.Element {
  return (
    <RouteAccessGuard href="/cases">
      <AssistedFormWorkspace
        caseId={params.caseId}
        generatedFormId={params.generatedFormId}
      />
    </RouteAccessGuard>
  );
}
