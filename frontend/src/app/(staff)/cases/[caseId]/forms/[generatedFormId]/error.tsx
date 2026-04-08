"use client";

import { ErrorState } from "@/components/ui/error-state";

export default function AssistedFormWorkspaceError(): JSX.Element {
  return (
    <ErrorState
      title="Could not load assisted form workspace"
      description="The form workspace failed to load from the backend."
    />
  );
}
