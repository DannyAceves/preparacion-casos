import { RouteAccessGuard } from "@/components/auth/route-access-guard";
import { UserManagementWorkspace } from "@/components/admin/user-management-workspace";

export default function AdminUsersPage(): JSX.Element {
  return (
    <RouteAccessGuard href="/admin/users">
      <UserManagementWorkspace />
    </RouteAccessGuard>
  );
}
