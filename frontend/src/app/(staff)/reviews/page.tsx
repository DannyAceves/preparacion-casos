import { RouteAccessGuard } from "@/components/auth/route-access-guard";
import { RoutePlaceholder } from "@/components/ui/route-placeholder";

export default function ReviewsPage(): JSX.Element {
  return (
    <RouteAccessGuard href="/reviews">
      <div className="page-stack">
        <section className="page-heading">
          <div>
            <h2>Reviews</h2>
            <p>Central review queue for attorney decisions is being separated from the case registry.</p>
          </div>
        </section>

        <RoutePlaceholder
          title="Reviews Queue In Progress"
          description="This section will become the focused workspace for approvals, fixes and review notes."
          currentFocus="Review work is currently handled inside each case detail under the case workspace tabs."
          nextStep="Use the case registry to open a specific case, then continue from its Reviews or Forms tabs until the dedicated queue is ready."
          primaryActionHref="/cases"
          primaryActionLabel="Open Cases"
        />
      </div>
    </RouteAccessGuard>
  );
}
