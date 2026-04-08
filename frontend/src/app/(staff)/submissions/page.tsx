import { RouteAccessGuard } from "@/components/auth/route-access-guard";
import { RoutePlaceholder } from "@/components/ui/route-placeholder";

export default function SubmissionsPage(): JSX.Element {
  return (
    <RouteAccessGuard href="/submissions">
      <div className="page-stack">
        <section className="page-heading">
          <div>
            <h2>Submissions</h2>
            <p>Submission operations will become a dedicated queue once packet and filing workflows are consolidated.</p>
          </div>
        </section>

        <RoutePlaceholder
          title="Submissions Queue In Progress"
          description="This route is reserved for filing-ready cases, packet approval and final submission actions."
          currentFocus="Submission work still happens inside the selected case, alongside readiness, packet and final filing controls."
          nextStep="Open the relevant case from Cases and continue from the readiness, packet and submission sections until this queue is implemented."
          primaryActionHref="/cases"
          primaryActionLabel="Go To Cases"
        />
      </div>
    </RouteAccessGuard>
  );
}
