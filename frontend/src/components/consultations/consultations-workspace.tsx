"use client";

import { useState } from "react";

import { ConsultationsTable } from "@/components/consultations/consultations-table";
import { CreateConsultationForm } from "@/components/consultations/create-consultation-form";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { usePermissions } from "@/hooks/use-permissions";
import { useConsultationsList } from "@/hooks/use-consultations-list";
import { Consultation } from "@/types/consultation";

export function ConsultationsWorkspace(): JSX.Element {
  const permissions = usePermissions();
  const { items, loading, error, refresh } = useConsultationsList();
  const [isCreating, setIsCreating] = useState(false);

  async function handleCreated(_: Consultation): Promise<void> {
    await refresh();
    setIsCreating(false);
  }

  return (
    <div className="page-stack">
      <section className="cases-toolbar">
        <div>
          <strong>Consultation Intake</strong>
          <p>
            {permissions.role === "admin" || permissions.role === "reception"
              ? "Register the first appointment, intake notes and preliminary case classification."
              : "Review intake records, assignment and conversion status for your legal workflow."}
          </p>
        </div>
        <div className="cases-toolbar__actions">
          {permissions.role === "admin" || permissions.role === "reception" ? (
            <button type="button" className="ui-button" onClick={() => setIsCreating(true)}>
              New Consultation
            </button>
          ) : null}
        </div>
      </section>

      {isCreating && (permissions.role === "admin" || permissions.role === "reception") ? (
        <Card title="Create Consultation" subtitle="Capture intake information before opening the formal case.">
          <CreateConsultationForm onCreated={handleCreated} onCancel={() => setIsCreating(false)} />
        </Card>
      ) : null}

      <Card title="Consultation Queue" subtitle="Active intake records and preliminary evaluations">
        {loading ? <LoadingState label="Loading consultations..." /> : null}
        {!loading && error ? <ErrorState title="Could not load consultations" description={error} /> : null}
        {!loading && !error && items.length === 0 ? (
          <EmptyState
            title="No consultations yet"
            description="Create the first consultation to start the intake workflow."
          />
        ) : null}
        {!loading && !error && items.length > 0 ? <ConsultationsTable items={items} /> : null}
      </Card>
    </div>
  );
}
