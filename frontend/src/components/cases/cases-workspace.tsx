"use client";

import { useState } from "react";

import { CasesFilters } from "@/components/cases/cases-filters";
import { CasesTable } from "@/components/cases/cases-table";
import { CreateCaseForm } from "@/components/cases/create-case-form";
import { CreateClientForm } from "@/components/clients/create-client-form";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";
import { usePermissions } from "@/hooks/use-permissions";
import { useCasesList } from "@/hooks/use-cases-list";
import { Case } from "@/types/case";
import { Client } from "@/types/client";

export function CasesWorkspace(): JSX.Element {
  const permissions = usePermissions();
  const {
    items,
    clients,
    loading,
    error,
    query,
    setQuery,
    statusFilter,
    setStatusFilter,
    priorityFilter,
    setPriorityFilter,
    availableStatuses,
    refresh,
  } = useCasesList();
  const [activePanel, setActivePanel] = useState<"client" | "case" | null>(null);
  const [preferredClientId, setPreferredClientId] = useState<string | null>(null);

  async function handleClientCreated(client: Client): Promise<void> {
    await refresh();
    setPreferredClientId(client.id);
    setActivePanel("case");
  }

  async function handleCaseCreated(_: Case): Promise<void> {
    await refresh();
  }

  return (
    <div className="page-stack">
      <section className="cases-toolbar">
        <div>
          <strong>Operational actions</strong>
          <p>
            {permissions.can("create_cases")
              ? "Create a client first, then open a case tied to that record."
              : "Your role can review the case registry but cannot create new client or case records."}
          </p>
        </div>
        <div className="cases-toolbar__actions">
          {permissions.can("create_clients") ? (
            <button type="button" className="ui-button ui-button--ghost" onClick={() => setActivePanel("client")}>
              New Client
            </button>
          ) : null}
          {permissions.can("create_cases") ? (
            <button type="button" className="ui-button" onClick={() => setActivePanel("case")}>
              New Case
            </button>
          ) : null}
        </div>
      </section>

      {activePanel === "client" && permissions.can("create_clients") ? (
        <Card title="Create Client" subtitle="Add a new client record for intake and case assignment.">
          <CreateClientForm onCreated={handleClientCreated} onCancel={() => setActivePanel(null)} />
        </Card>
      ) : null}

      {activePanel === "case" && permissions.can("create_cases") ? (
        <Card title="Create Case" subtitle="Open a new case and route the team straight to its workspace.">
          <CreateCaseForm
            clients={clients}
            initialClientId={preferredClientId}
            onCreated={handleCaseCreated}
            onCancel={() => setActivePanel(null)}
          />
        </Card>
      ) : null}

      <CasesFilters
        query={query}
        onQueryChange={setQuery}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        priorityFilter={priorityFilter}
        onPriorityFilterChange={setPriorityFilter}
        availableStatuses={availableStatuses}
      />

      {loading ? <LoadingState label="Loading cases from the backend..." /> : null}
      {!loading && error ? (
        <ErrorState title="Could not load cases" description={error} />
      ) : null}
      {!loading && !error && items.length === 0 ? (
        <EmptyState
          title="No cases match the current view"
          description="Adjust search terms or filters to broaden the result set."
        />
      ) : null}
      {!loading && !error && items.length > 0 ? <CasesTable cases={items} /> : null}
    </div>
  );
}
