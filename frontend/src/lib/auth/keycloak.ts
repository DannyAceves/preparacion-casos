import { appConfig } from "@/lib/config";

export interface KeycloakAuthAdapter {
  provider: "keycloak";
  issuer: string;
  clientId: string;
  loginUrl: string;
  logoutUrl: string;
}

export function getKeycloakAuthAdapter(): KeycloakAuthAdapter {
  return {
    provider: "keycloak",
    issuer: appConfig.keycloakIssuer,
    clientId: appConfig.keycloakClientId,
    loginUrl: "#keycloak-login-placeholder",
    logoutUrl: "#keycloak-logout-placeholder",
  };
}
