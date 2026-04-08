export type InternalRole = "admin" | "reception" | "attorney" | "paralegal" | "client";

export type AuthProviderMode = "database" | "mock" | "keycloak";

export interface InternalUser {
  id: string;
  name: string;
  email: string;
  role: InternalRole;
}

export interface AuthSession {
  user: InternalUser;
  accessToken: string | null;
  provider: AuthProviderMode;
  expiresAt: string | null;
}

export type PermissionAction =
  | "manage_users"
  | "view_dashboard"
  | "view_consultations"
  | "view_cases"
  | "create_clients"
  | "create_cases"
  | "manage_documents"
  | "issue_client_portal_access"
  | "edit_questionnaire"
  | "edit_canonical_fields"
  | "view_canonical_fields"
  | "view_inconsistencies"
  | "resolve_inconsistencies"
  | "generate_forms"
  | "review_forms"
  | "generate_packet"
  | "view_submission"
  | "manage_submission"
  | "execute_submission"
  | "transition_case_status"
  | "view_timeline"
  | "manage_questionnaire_templates";

export type StaffRouteKey =
  | "/admin/users"
  | "/dashboard"
  | "/consultations"
  | "/cases"
  | "/questionnaire-templates"
  | "/reviews"
  | "/submissions";

export type CaseWorkspaceSection =
  | "overview"
  | "questionnaire"
  | "documents"
  | "canonical-fields"
  | "inconsistencies"
  | "reviews"
  | "forms"
  | "packet"
  | "readiness"
  | "submission"
  | "timeline";
