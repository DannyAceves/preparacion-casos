import { RouteAccessGuard } from "@/components/auth/route-access-guard";
import { ConsultationsWorkspace } from "@/components/consultations/consultations-workspace";

export default function ConsultationsPage(): JSX.Element {
  return (
    <RouteAccessGuard href="/consultations">
      <div className="page-stack">
        <section className="page-heading">
          <div>
            <h2>Consultations</h2>
            <p>Initial intake queue for consultations, appointments and preliminary case classification.</p>
          </div>
        </section>

        <ConsultationsWorkspace />
      </div>
    </RouteAccessGuard>
  );
}
