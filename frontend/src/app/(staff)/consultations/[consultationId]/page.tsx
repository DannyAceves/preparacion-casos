import { notFound } from "next/navigation";

import { ConsultationDetailPanel } from "@/components/consultations/consultation-detail-panel";
import { getServerPrincipalHeaders } from "@/lib/auth/server-principal-headers";
import { requireAllowedStaffRoute } from "@/lib/auth/session";
import { getConsultation } from "@/services/consultations";
import { ApiErrorPayload } from "@/types/api";

interface ConsultationDetailPageProps {
  params: {
    consultationId: string;
  };
}

export default async function ConsultationDetailPage({
  params,
}: ConsultationDetailPageProps): Promise<JSX.Element> {
  await requireAllowedStaffRoute("/consultations");

  try {
    const consultation = await getConsultation(params.consultationId, {
      headers: await getServerPrincipalHeaders(),
    });

    return (
      <div className="page-stack">
        <section className="page-heading">
          <div>
            <h2>{`${consultation.first_name} ${consultation.last_name}`.trim()}</h2>
            <p>{consultation.email}</p>
          </div>
        </section>

        <ConsultationDetailPanel initialConsultation={consultation} />
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
