import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { CaseListItem } from "@/types/case";

interface CasesTableProps {
  cases: CaseListItem[];
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

function toneForPriority(priority: CaseListItem["priority"]): "neutral" | "success" | "warning" | "danger" | "info" {
  if (priority === "high") {
    return "danger";
  }
  if (priority === "medium") {
    return "warning";
  }
  if (priority === "low") {
    return "success";
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
            <th>Client</th>
            <th>Case Type</th>
            <th>Status</th>
            <th>Priority</th>
            <th>Attorney</th>
            <th>Due Date</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((item) => (
            <tr key={item.id}>
              <td>
                <Link href={`/cases/${item.id}`}>{item.case_number}</Link>
              </td>
              <td>
                <div className="ui-table__primary">{item.client_name}</div>
                <div className="ui-table__secondary">{item.title}</div>
              </td>
              <td>{item.case_type}</td>
              <td>
                <Badge tone={toneForStatus(item.status)}>{item.status}</Badge>
              </td>
              <td>
                <Badge tone={toneForPriority(item.priority)}>{item.priority}</Badge>
              </td>
              <td>{item.assigned_attorney ?? "Unassigned"}</td>
              <td>{item.due_date ? new Date(item.due_date).toLocaleDateString() : "No due date"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
