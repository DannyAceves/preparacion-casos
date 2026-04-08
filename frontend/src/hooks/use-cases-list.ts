"use client";

import { useDeferredValue, useEffect, useState } from "react";

import { listCases } from "@/services/cases";
import { listClients } from "@/services/clients";
import { Client } from "@/types/client";
import { Case, CaseListItem, CasePriority } from "@/types/case";

interface UseCasesListResult {
  items: CaseListItem[];
  clients: Client[];
  loading: boolean;
  error: string | null;
  query: string;
  setQuery: (value: string) => void;
  statusFilter: string;
  setStatusFilter: (value: string) => void;
  priorityFilter: string;
  setPriorityFilter: (value: string) => void;
  availableStatuses: string[];
  refresh: () => Promise<void>;
}

function buildClientMap(clients: Client[]): Record<string, Client> {
  return Object.fromEntries(clients.map((client) => [client.id, client]));
}

function formatClientName(client: Client | undefined): string {
  if (!client) {
    return "No client linked";
  }
  return `${client.first_name} ${client.last_name}`.trim();
}

function derivePriority(caseItem: Case): CasePriority {
  if (caseItem.status === "attorney_review" || caseItem.status === "fix_required") {
    return "high";
  }
  if (caseItem.status === "ready_for_submission") {
    return "high";
  }
  if (caseItem.status === "draft") {
    return "medium";
  }
  if (caseItem.status === "submitted" || caseItem.status === "closed") {
    return "low";
  }
  return "unknown";
}

function mapCases(cases: Case[], clients: Client[]): CaseListItem[] {
  const clientMap = buildClientMap(clients);

  return cases.map((caseItem) => ({
    ...caseItem,
    client_name: formatClientName(clientMap[caseItem.client_id]),
    priority: derivePriority(caseItem),
    assigned_attorney: null,
    due_date: null,
  }));
}

export function useCasesList(): UseCasesListResult {
  const [sourceItems, setSourceItems] = useState<CaseListItem[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const deferredQuery = useDeferredValue(query);

  async function load(activeCheck?: () => boolean): Promise<void> {
    setLoading(true);
    setError(null);
    try {
      const [cases, clientRecords] = await Promise.all([listCases(), listClients()]);
      if (activeCheck && !activeCheck()) {
        return;
      }
      setClients(clientRecords);
      setSourceItems(mapCases(cases, clientRecords));
    } catch (loadError) {
      if (activeCheck && !activeCheck()) {
        return;
      }
      const message = loadError instanceof Error ? loadError.message : "Failed to load cases.";
      setError(message);
    } finally {
      if (!activeCheck || activeCheck()) {
        setLoading(false);
      }
    }
  }

  useEffect(() => {
    let active = true;

    void load(() => active);
    return () => {
      active = false;
    };
  }, []);

  const normalizedQuery = deferredQuery.trim().toLowerCase();
  const items = sourceItems.filter((item) => {
    const matchesQuery =
      normalizedQuery.length === 0 ||
      item.case_number.toLowerCase().includes(normalizedQuery) ||
      item.title.toLowerCase().includes(normalizedQuery) ||
      item.case_type.toLowerCase().includes(normalizedQuery) ||
      item.client_name.toLowerCase().includes(normalizedQuery);

    const matchesStatus = statusFilter === "all" || item.status === statusFilter;
    const matchesPriority = priorityFilter === "all" || item.priority === priorityFilter;
    return matchesQuery && matchesStatus && matchesPriority;
  });

  const availableStatuses = [...new Set(sourceItems.map((item) => item.status))].sort((left, right) =>
    left.localeCompare(right),
  );

  return {
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
    refresh: () => load(),
  };
}
