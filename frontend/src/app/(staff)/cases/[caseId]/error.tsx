"use client";

import Link from "next/link";

import { ErrorState } from "@/components/ui/error-state";

interface CaseDetailErrorProps {
  error: Error;
  reset: () => void;
}

export default function CaseDetailError({ error, reset }: CaseDetailErrorProps): JSX.Element {
  return (
    <div className="page-stack">
      <ErrorState
        title="Could not load this case"
        description={error.message || "The case detail view failed while loading its data."}
      />
      <div className="case-quick-actions">
        <button type="button" className="ui-button" onClick={() => reset()}>
          Retry
        </button>
        <Link href="/cases" className="ui-button ui-button--ghost">
          Back To Cases
        </Link>
      </div>
    </div>
  );
}
