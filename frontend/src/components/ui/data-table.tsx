import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Case } from "@/types/case";

interface CasesTableProps {
  cases: Case[];
}

function toneForStatus(status: string): "neutral" | "success" | "warning" | "danger" | "info" {
  if (status === "submitted" || status === "closed") {
    return "success";
  }
  if (status === "ready_for_submission" || status === "attorney_review") {
    return "info";
  }
  if (status === "draft") {
    return "warning";
  }
  return "neutral";
}

export function CasesTable({ cases }: CasesTableProps): JSX.Element {
  return (
    <div className="ui-table-wrap">
      <table className="ui-table">
        <thead>
          <tr>
            <th>Case #</th>
            <th>Title</th>
            <th>Type</th>
            <th>Status</th>
            <th>Updated</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((item) => (
            <tr key={item.id}>
              <td>
                <Link href={`/cases/${item.id}`}>{item.case_number}</Link>
              </td>
              <td>{item.title}</td>
              <td>{item.case_type}</td>
              <td>
                <Badge tone={toneForStatus(item.status)}>{item.status}</Badge>
              </td>
              <td>{new Date(item.updated_at).toLocaleString()}</td>
              <td>
                <Link href={`/cases/${item.id}`} className="ui-table__action">
                  Open case
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
