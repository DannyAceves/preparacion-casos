import { CaseWorkspaceSection, InternalRole, PermissionAction, StaffRouteKey } from "@/types/auth";

const permissionMatrix: Record<PermissionAction, InternalRole[]> = {
  manage_users: ["admin"],
  view_dashboard: ["admin", "attorney", "paralegal"],
  view_consultations: ["admin", "reception", "attorney", "paralegal"],
  view_cases: ["admin", "attorney", "paralegal"],
  create_clients: ["admin", "reception", "attorney", "paralegal"],
  create_cases: ["admin", "attorney", "paralegal"],
  manage_documents: ["admin", "attorney", "paralegal"],
  issue_client_portal_access: ["admin", "attorney", "paralegal"],
  edit_questionnaire: ["admin", "attorney", "paralegal"],
  edit_canonical_fields: ["admin", "attorney", "paralegal"],
  view_canonical_fields: ["admin", "attorney", "paralegal"],
  view_inconsistencies: ["admin", "attorney", "paralegal"],
  resolve_inconsistencies: ["admin", "attorney"],
  generate_forms: ["admin", "attorney", "paralegal"],
  review_forms: ["admin", "attorney"],
  generate_packet: ["admin", "attorney", "paralegal"],
  view_submission: ["admin", "attorney", "paralegal"],
  manage_submission: ["admin", "attorney"],
  execute_submission: ["admin", "attorney", "paralegal"],
  transition_case_status: ["admin", "attorney"],
  view_timeline: ["admin", "attorney", "paralegal"],
  manage_questionnaire_templates: ["admin"],
};

const routeTitles: Record<StaffRouteKey, string> = {
  "/admin/users": "User Management",
  "/dashboard": "Dashboard",
  "/consultations": "Consultations",
  "/cases": "Cases",
  "/questionnaire-templates": "Questionnaires",
  "/reviews": "Reviews",
  "/submissions": "Submissions",
};

const routeAccessMatrix: Record<StaffRouteKey, PermissionAction> = {
  "/admin/users": "manage_users",
  "/dashboard": "view_dashboard",
  "/consultations": "view_consultations",
  "/cases": "view_cases",
  "/questionnaire-templates": "manage_questionnaire_templates",
  "/reviews": "review_forms",
  "/submissions": "view_submission",
};

const caseSectionMatrix: Record<CaseWorkspaceSection, PermissionAction | null> = {
  overview: "view_cases",
  questionnaire: "edit_questionnaire",
  documents: "manage_documents",
  "canonical-fields": "view_canonical_fields",
  inconsistencies: "view_inconsistencies",
  reviews: "view_timeline",
  forms: "generate_forms",
  packet: "generate_packet",
  readiness: "view_timeline",
  submission: "view_submission",
  timeline: "view_timeline",
};

export interface RouteAccessDecision {
  allowed: boolean;
  title: string;
  message: string;
  fallbackHref: string;
  fallbackLabel: string;
}

const CLIENT_PORTAL_HOME = "/portal";
const CLIENT_PORTAL_BLOCKED_NOTICE = "internal-workspace-unavailable";

function isSafeInternalPath(path: string): boolean {
  return path.startsWith("/") && !path.startsWith("//");
}

function getLandingLabel(path: string): string {
  if (path.startsWith(CLIENT_PORTAL_HOME)) {
    return "Client Portal";
  }
  const route = resolveStaffRoute(path);
  return route ? routeTitles[route] : "Home";
}

export function canPerformAction(role: InternalRole, action: PermissionAction): boolean {
  return permissionMatrix[action].includes(role);
}

export function canAccessRoute(role: InternalRole, href: string): boolean {
  const route = resolveStaffRoute(href);
  if (!route) {
    return true;
  }
  return canPerformAction(role, routeAccessMatrix[route]);
}

export function canAccessCaseSection(role: InternalRole, section: CaseWorkspaceSection): boolean {
  const requiredAction = caseSectionMatrix[section];
  return requiredAction ? canPerformAction(role, requiredAction) : true;
}

export function resolveStaffRoute(href: string): StaffRouteKey | null {
  const knownRoutes = Object.keys(routeAccessMatrix) as StaffRouteKey[];
  return knownRoutes.find((route) => href.startsWith(route)) ?? null;
}

export function getDefaultRouteForRole(role: InternalRole): StaffRouteKey {
  if (role === "admin") {
    return "/dashboard";
  }
  if (role === "reception") {
    return "/consultations";
  }
  return "/cases";
}

export function getRoleLandingPath(role: InternalRole): string {
  if (role === "client") {
    return CLIENT_PORTAL_HOME;
  }
  return getDefaultRouteForRole(role);
}

export function resolveAuthorizedPathForRole(role: InternalRole, requestedPath?: string | null): string {
  const fallbackPath = getRoleLandingPath(role);

  if (!requestedPath || !isSafeInternalPath(requestedPath) || requestedPath === "/login") {
    return fallbackPath;
  }

  if (requestedPath.startsWith("/portal")) {
    return role === "client" ? requestedPath : fallbackPath;
  }

  if (role === "client") {
    return `${CLIENT_PORTAL_HOME}?notice=${CLIENT_PORTAL_BLOCKED_NOTICE}`;
  }

  const route = resolveStaffRoute(requestedPath);
  if (!route) {
    return fallbackPath;
  }

  return canAccessRoute(role, route) ? requestedPath : fallbackPath;
}

export function getRouteAccessDecision(role: InternalRole, href: string): RouteAccessDecision {
  const route = resolveStaffRoute(href) ?? getDefaultRouteForRole(role);
  if (role === "client") {
    return {
      allowed: false,
      title: routeTitles[route],
      message: "The client role is limited to the client portal and cannot enter the internal staff workspace.",
      fallbackHref: `${CLIENT_PORTAL_HOME}?notice=${CLIENT_PORTAL_BLOCKED_NOTICE}`,
      fallbackLabel: "Open client portal",
    };
  }
  const title = routeTitles[route];
  if (canAccessRoute(role, route)) {
    return {
      allowed: true,
      title,
      message: "",
      fallbackHref: getDefaultRouteForRole(role),
      fallbackLabel: routeTitles[getDefaultRouteForRole(role)],
    };
  }

  return {
    allowed: false,
    title,
    message: `Your ${role} role does not have access to ${title.toLowerCase()} in the internal workspace.`,
    fallbackHref: getRoleLandingPath(role),
    fallbackLabel: getLandingLabel(getRoleLandingPath(role)),
  };
}
