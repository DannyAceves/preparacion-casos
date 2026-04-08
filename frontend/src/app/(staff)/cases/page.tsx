import { RouteAccessGuard } from "@/components/auth/route-access-guard";
import { CasesWorkspace } from "@/components/cases/cases-workspace";
import { Card } from "@/components/ui/card";

export default function CasesPage(): JSX.Element {
  return (
    <RouteAccessGuard href="/cases">
      <div className="page-stack">
        <section className="page-heading">
          <div>
            <h2>Cases</h2>
            <p>Internal work queue for intake, case creation and navigation into each case workspace.</p>
          </div>
        </section>

        <Card title="Case Registry" subtitle="Search, filter and navigate live case records">
          <CasesWorkspace />
        </Card>
      </div>
    </RouteAccessGuard>
  );
}
