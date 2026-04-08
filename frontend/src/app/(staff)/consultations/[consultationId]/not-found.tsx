import Link from "next/link";

import { EmptyState } from "@/components/ui/empty-state";

export default function ConsultationDetailNotFound(): JSX.Element {
  return (
    <div className="page-stack">
      <EmptyState
        title="Consultation not found"
        description="The requested consultation does not exist or is no longer available."
      />
      <div className="case-quick-actions">
        <Link href="/consultations" className="ui-button">
          Return To Consultations
        </Link>
      </div>
    </div>
  );
}
