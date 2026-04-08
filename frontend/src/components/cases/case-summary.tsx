import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Case, CaseReadiness } from "@/types/case";

interface CaseSummaryProps {
  caseItem: Case;
  readiness: CaseReadiness;
}

export function CaseSummary({ caseItem, readiness }: CaseSummaryProps): JSX.Element {
  const readyTarget = readiness.targets.find((item) => item.target_status === "ready_for_submission");

  return (
    <div className="case-detail-grid">
      <Card title="Case Overview" subtitle="Core case metadata from the backend">
        <dl className="ui-key-values">
          <div>
            <dt>Case Number</dt>
            <dd>{caseItem.case_number}</dd>
          </div>
          <div>
            <dt>Type</dt>
            <dd>{caseItem.case_type}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>
              <Badge tone="info">{caseItem.status}</Badge>
            </dd>
          </div>
          <div>
            <dt>Updated</dt>
            <dd>{new Date(caseItem.updated_at).toLocaleString()}</dd>
          </div>
        </dl>
      </Card>

      <Card title="Readiness Snapshot" subtitle="Automatic validation status">
        <dl className="ui-key-values">
          <div>
            <dt>Missing Required Documents</dt>
            <dd>{readiness.summary.missing_required_document_types.length}</dd>
          </div>
          <div>
            <dt>Critical Open Inconsistencies</dt>
            <dd>{readiness.summary.open_critical_inconsistency_count}</dd>
          </div>
          <div>
            <dt>Unapproved Forms</dt>
            <dd>{readiness.summary.unapproved_generated_form_count}</dd>
          </div>
          <div>
            <dt>Ready For Submission</dt>
            <dd>
              <Badge tone={readyTarget?.is_ready ? "success" : "warning"}>
                {readyTarget?.is_ready ? "Ready" : "Blocked"}
              </Badge>
            </dd>
          </div>
        </dl>
      </Card>
    </div>
  );
}
