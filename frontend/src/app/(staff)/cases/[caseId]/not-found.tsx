import Link from "next/link";

import { EmptyState } from "@/components/ui/empty-state";

export default function CaseDetailNotFound(): JSX.Element {
  return (
    <div className="page-stack">
      <EmptyState
        title="Case not found"
        description="The requested case does not exist or is no longer available from the backend."
      />
      <div className="case-quick-actions">
        <Link href="/cases" className="ui-button">
          Return To Cases
        </Link>
      </div>
    </div>
  );
}
