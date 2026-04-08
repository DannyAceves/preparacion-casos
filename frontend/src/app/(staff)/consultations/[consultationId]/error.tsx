"use client";

import Link from "next/link";

import { ErrorState } from "@/components/ui/error-state";

interface ConsultationDetailErrorProps {
  error: Error;
  reset: () => void;
}

export default function ConsultationDetailError({
  error,
  reset,
}: ConsultationDetailErrorProps): JSX.Element {
  return (
    <div className="page-stack">
      <ErrorState
        title="Could not load this consultation"
        description={error.message || "The consultation detail view failed while loading its data."}
      />
      <div className="case-quick-actions">
        <button type="button" className="ui-button" onClick={() => reset()}>
          Retry
        </button>
        <Link href="/consultations" className="ui-button ui-button--ghost">
          Back To Consultations
        </Link>
      </div>
    </div>
  );
}
