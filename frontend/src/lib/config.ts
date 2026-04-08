const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const apiInternalBaseUrl = process.env.API_INTERNAL_BASE_URL ?? apiBaseUrl;
const authMode = (process.env.NEXT_PUBLIC_AUTH_MODE ?? "mock") as "mock" | "keycloak";

if (!apiBaseUrl.startsWith("http://") && !apiBaseUrl.startsWith("https://")) {
  throw new Error("NEXT_PUBLIC_API_BASE_URL must be an absolute http(s) URL.");
}

if (!apiInternalBaseUrl.startsWith("http://") && !apiInternalBaseUrl.startsWith("https://")) {
  throw new Error("API_INTERNAL_BASE_URL must be an absolute http(s) URL.");
}

if (authMode === "keycloak") {
  if (!process.env.NEXT_PUBLIC_KEYCLOAK_ISSUER || !process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID) {
    throw new Error("Keycloak mode requires NEXT_PUBLIC_KEYCLOAK_ISSUER and NEXT_PUBLIC_KEYCLOAK_CLIENT_ID.");
  }
}

export const appConfig = {
  appName: process.env.NEXT_PUBLIC_APP_NAME ?? "Case Prep Staff",
  apiBaseUrl,
  apiInternalBaseUrl,
  authMode,
  keycloakIssuer: process.env.NEXT_PUBLIC_KEYCLOAK_ISSUER ?? "",
  keycloakClientId: process.env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID ?? "",
  defaultProtectedRoute: "/dashboard",
  isProductionLike:
    process.env.NODE_ENV === "production" || process.env.NEXT_PUBLIC_APP_ENV === "staging",
};
