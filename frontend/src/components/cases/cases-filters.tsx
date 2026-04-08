"use client";

interface CasesFiltersProps {
  query: string;
  onQueryChange: (value: string) => void;
  statusFilter: string;
  onStatusFilterChange: (value: string) => void;
  priorityFilter: string;
  onPriorityFilterChange: (value: string) => void;
  availableStatuses: string[];
}

export function CasesFilters({
  query,
  onQueryChange,
  statusFilter,
  onStatusFilterChange,
  priorityFilter,
  onPriorityFilterChange,
  availableStatuses,
}: CasesFiltersProps): JSX.Element {
  return (
    <section className="cases-filters">
      <label className="ui-field">
        <span>Search</span>
        <input
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Case #, title, type or client"
        />
      </label>

      <label className="ui-field">
        <span>Status</span>
        <select value={statusFilter} onChange={(event) => onStatusFilterChange(event.target.value)}>
          <option value="all">All statuses</option>
          {availableStatuses.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </label>

      <label className="ui-field">
        <span>Priority</span>
        <select value={priorityFilter} onChange={(event) => onPriorityFilterChange(event.target.value)}>
          <option value="all">All priorities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="unknown">Unknown</option>
        </select>
      </label>
    </section>
  );
}
