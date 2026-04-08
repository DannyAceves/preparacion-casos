"use client";

import { useEffect, useMemo, useState } from "react";

import { SystemUserForm } from "@/components/admin/system-user-form";
import { Card } from "@/components/ui/card";
import { FormFeedback } from "@/components/ui/form-feedback";
import { FormField } from "@/components/ui/form-field";
import { LoadingState } from "@/components/ui/loading-state";
import { getApiErrorMessage } from "@/lib/api/errors";
import { listSystemUsers, updateSystemUser } from "@/services/system-users";
import { InternalRole } from "@/types/auth";
import { ListSystemUsersFilters, SystemUser } from "@/types/system-user";

const roleOptions: Array<InternalRole | "all"> = ["all", "admin", "reception", "attorney", "paralegal", "client"];

export function UserManagementWorkspace(): JSX.Element {
  const [users, setUsers] = useState<SystemUser[]>([]);
  const [filters, setFilters] = useState<ListSystemUsersFilters>({
    search: "",
    role: "all",
    is_active: "all",
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [editingUser, setEditingUser] = useState<SystemUser | null>(null);

  async function loadUsers(nextFilters: ListSystemUsersFilters = filters): Promise<void> {
    setLoading(true);
    setError(null);
    try {
      const result = await listSystemUsers(nextFilters);
      setUsers(result);
    } catch (loadError) {
      setError(getApiErrorMessage(loadError, "Could not load users."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadUsers();
  }, []);

  const activeCount = useMemo(() => users.filter((user) => user.is_active).length, [users]);

  function updateFilter<Key extends keyof ListSystemUsersFilters>(
    field: Key,
    value: ListSystemUsersFilters[Key],
  ): void {
    setFilters((current) => ({ ...current, [field]: value }));
  }

  async function handleRefreshWithSuccess(message: string): Promise<void> {
    setSuccess(message);
    setIsCreating(false);
    setEditingUser(null);
    await loadUsers();
  }

  async function handleToggleActive(user: SystemUser): Promise<void> {
    setError(null);
    setSuccess(null);
    try {
      const updated = await updateSystemUser(user.id, { is_active: !user.is_active });
      await handleRefreshWithSuccess(
        `${updated.first_name} ${updated.last_name} is now ${updated.is_active ? "active" : "inactive"}.`,
      );
    } catch (toggleError) {
      setError(getApiErrorMessage(toggleError, "Could not update the user status."));
    }
  }

  return (
    <div className="page-stack">
      <section className="page-heading">
        <div>
          <h2>User Management</h2>
          <p>Admin-only workspace for creating, editing and controlling accounts.</p>
        </div>
        <button
          type="button"
          className="ui-button"
          onClick={() => {
            setIsCreating(true);
            setEditingUser(null);
          }}
        >
          New User
        </button>
      </section>

      <section className="metrics-grid">
        <Card title="Total Users" subtitle="Accounts currently registered in the system">
          <strong>{users.length}</strong>
        </Card>
        <Card title="Active Users" subtitle="Enabled accounts">
          <strong>{activeCount}</strong>
        </Card>
      </section>

      <Card title="Filters" subtitle="Search by name or email, then narrow by role and status.">
        <div className="entity-form__grid admin-filters">
          <FormField label="Search" htmlFor="user-search">
            <input
              id="user-search"
              value={filters.search ?? ""}
              onChange={(event) => updateFilter("search", event.target.value)}
              placeholder="Name or email"
            />
          </FormField>

          <FormField label="Role" htmlFor="user-role-filter">
            <select
              id="user-role-filter"
              value={filters.role ?? "all"}
              onChange={(event) => updateFilter("role", event.target.value as ListSystemUsersFilters["role"])}
            >
              {roleOptions.map((role) => (
                <option key={role} value={role}>
                  {role === "all" ? "All roles" : role}
                </option>
              ))}
            </select>
          </FormField>

          <FormField label="Status" htmlFor="user-status-filter">
            <select
              id="user-status-filter"
              value={filters.is_active ?? "all"}
              onChange={(event) => updateFilter("is_active", event.target.value as ListSystemUsersFilters["is_active"])}
            >
              <option value="all">All users</option>
              <option value="true">Active only</option>
              <option value="false">Inactive only</option>
            </select>
          </FormField>
        </div>

        <div className="entity-form__actions">
          <button type="button" className="ui-button" onClick={() => void loadUsers(filters)} disabled={loading}>
            Apply Filters
          </button>
          <button
            type="button"
            className="ui-button ui-button--ghost"
            onClick={() => {
              const resetFilters: ListSystemUsersFilters = { search: "", role: "all", is_active: "all" };
              setFilters(resetFilters);
              void loadUsers(resetFilters);
            }}
            disabled={loading}
          >
            Reset
          </button>
        </div>
      </Card>

      {isCreating ? (
        <Card title="Create User" subtitle="Create an internal or client account.">
          <SystemUserForm
            mode="create"
            onSaved={async (user) => {
              await handleRefreshWithSuccess(`${user.first_name} ${user.last_name} was created.`);
            }}
            onCancel={() => setIsCreating(false)}
          />
        </Card>
      ) : null}

      {editingUser ? (
        <Card title="Edit User" subtitle={`Update ${editingUser.first_name} ${editingUser.last_name}.`}>
          <SystemUserForm
            mode="edit"
            initialUser={editingUser}
            onSaved={async (user) => {
              await handleRefreshWithSuccess(`${user.first_name} ${user.last_name} was updated.`);
            }}
            onCancel={() => setEditingUser(null)}
          />
        </Card>
      ) : null}

      {success ? <FormFeedback tone="success" message={success} /> : null}
      {error ? <FormFeedback tone="error" message={error} /> : null}

      <Card title="Users" subtitle="Admin-only list of accounts and role assignments.">
        {loading ? <LoadingState label="Loading users..." /> : null}
        {!loading ? (
          <div className="ui-table-wrap">
            <table className="ui-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Last login</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.length ? (
                  users.map((user) => (
                    <tr key={user.id}>
                      <td>{`${user.first_name} ${user.last_name}`}</td>
                      <td>{user.email}</td>
                      <td>
                        <span className="ui-badge ui-badge--info">{user.role}</span>
                      </td>
                      <td>
                        <span className={`ui-badge ${user.is_active ? "ui-badge--success" : "ui-badge--warning"}`}>
                          {user.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td>{user.last_login_at ? new Date(user.last_login_at).toLocaleString() : "Never"}</td>
                      <td>
                        <div className="table-actions">
                          <button
                            type="button"
                            className="ui-button ui-button--ghost"
                            onClick={() => {
                              setEditingUser(user);
                              setIsCreating(false);
                            }}
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            className="ui-button ui-button--ghost"
                            onClick={() => void handleToggleActive(user)}
                          >
                            {user.is_active ? "Deactivate" : "Activate"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6}>
                      <p className="entity-card__hint">No users match the current filters.</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        ) : null}
      </Card>
    </div>
  );
}
