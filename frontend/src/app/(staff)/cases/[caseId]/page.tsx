import { notFound } from "next/navigation";

import { Case360Tabs } from "@/components/cases/case-360-tabs";
import { CaseSummary } from "@/components/cases/case-summary";
import { Badge } from "@/components/ui/badge";
import { getServerPrincipalHeaders } from "@/lib/auth/server-principal-headers";
import { requireAllowedStaffRoute } from "@/lib/auth/session";
import { getCase, getCaseReadiness } from "@/services/cases";
import { ApiErrorPayload } from "@/types/api";

interface CaseDetailPageProps {
  params: {
    caseId: string;
  };
}

export default async function CaseDetailPage({ params }: CaseDetailPageProps): Promise<JSX.Element> {
  await requireAllowedStaffRoute("/cases");

  try {
    const serverHeaders = await getServerPrincipalHeaders();
    const [caseItem, readiness] = await Promise.all([
      getCase(params.caseId, { headers: serverHeaders }),
      getCaseReadiness(params.caseId, { headers: serverHeaders }),
    ]);

    return (
      <div className="page-stack">
        <section className="page-heading">
          <div>
            <h2>{caseItem.title}</h2>
            <p>
              {caseItem.case_number} | {caseItem.case_type}
            </p>
          </div>
          <Badge tone="info">{caseItem.status}</Badge>
        </section>

        <CaseSummary caseItem={caseItem} readiness={readiness} />
        <Case360Tabs caseItem={caseItem} readiness={readiness} />
      </div>
    );
  } catch (error) {
    const apiError = error as ApiErrorPayload;
    if (apiError.status === 404) {
      notFound();
    }
    throw error;
  }
}
