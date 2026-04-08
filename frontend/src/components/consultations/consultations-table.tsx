import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Consultation } from "@/types/consultation";

interface ConsultationsTableProps {
  items: Consultation[];
}

function formatDateTime(value: string | null): string {
  return value ? new Date(value).toLocaleString() : "Not scheduled";
}

function toneForStatus(status: string): "neutral" | "success" | "warning" | "danger" | "info" {
  if (status === "converted") {
    return "success";
  }
  if (status === "approved") {
    return "info";
  }
  if (status === "scheduled" || status === "intake_in_progress") {
    return "warning";
  }
  if (status === "closed") {
    return "neutral";
  }
  return "neutral";
}

export function ConsultationsTable({ items }: ConsultationsTableProps): JSX.Element {
  return (
    <div className="ui-table-wrap">
      <table className="ui-table">
        <thead>
          <tr>
            <th>Prospect</th>
            <th>Appointment</th>
            <th>Attorney</th>
            <th>Suggested Type</th>
            <th>Status</th>
            <th>Updated</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>
                <div className="ui-table__primary">{`${item.first_name} ${item.last_name}`.trim()}</div>
                <div className="ui-table__secondary">{item.email}</div>
              </td>
              <td>{formatDateTime(item.appointment_at)}</td>
              <td>{item.assigned_attorney ?? "Unassigned"}</td>
              <td>{item.suggested_case_type ?? "Not classified"}</td>
              <td>
                <Badge tone={toneForStatus(item.status)}>{item.status}</Badge>
              </td>
              <td>{new Date(item.updated_at).toLocaleString()}</td>
              <td>
                <Link href={`/consultations/${item.id}`} className="ui-table__action">
                  Open consultation
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
