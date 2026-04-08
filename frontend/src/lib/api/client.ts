import { appConfig } from "@/lib/config";
import { buildPrincipalHeaders } from "@/lib/auth/principal-headers";
import { getBrowserSessionSnapshot } from "@/lib/auth/session-store";
import { ApiErrorPayload } from "@/types/api";

export type ApiRequestOptions = Omit<RequestInit, "body"> & {
  body?: BodyInit | null;
  query?: Record<string, string | number | boolean | undefined>;
};

function buildHeaders(options: ApiRequestOptions): HeadersInit {
  const isFormData = options.body instanceof FormData;

  return {
    Accept: "application/json",
    ...(!isFormData && options.body ? { "Content-Type": "application/json" } : {}),
    ...(options.headers ?? {}),
  };
}

async function getSessionHeaders(): Promise<HeadersInit> {
  return typeof window !== "undefined" ? buildPrincipalHeaders(getBrowserSessionSnapshot()) : {};
}

function buildUrl(path: string, query?: ApiRequestOptions["query"]): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const baseUrl = typeof window === "undefined" ? appConfig.apiInternalBaseUrl : appConfig.apiBaseUrl;
  const url = new URL(`${baseUrl}${normalizedPath}`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

async function parseJsonSafe<T>(response: Response): Promise<T | null> {
  const text = await response.text();
  if (!text) {
    return null;
  }
  return JSON.parse(text) as T;
}

function getErrorMessage(path: string, status: number, detail: unknown): string {
  if (typeof detail === "object" && detail !== null) {
    const errorObject = detail as { error?: { message?: string; detail?: unknown }; detail?: unknown };
    if (errorObject.error?.message) {
      return errorObject.error.message;
    }
    if (typeof errorObject.detail === "string") {
      return errorObject.detail;
    }
  }
  return `API request failed for ${path} (${status})`;
}

export class ApiClient {
  async get<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
    return this.request<T>(path, { ...options, method: "GET" });
  }

  async post<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
    return this.request<T>(path, { ...options, method: "POST" });
  }

  async patch<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
    return this.request<T>(path, { ...options, method: "PATCH" });
  }

  private async request<T>(path: string, options: ApiRequestOptions): Promise<T> {
    const sessionHeaders = await getSessionHeaders();
    const response = await fetch(buildUrl(path, options.query), {
      ...options,
      headers: {
        ...buildHeaders(options),
        ...sessionHeaders,
      },
      cache: "no-store",
    });

    if (!response.ok) {
      const detail = await parseJsonSafe<unknown>(response);
      const error: ApiErrorPayload = {
        message: getErrorMessage(path, response.status, detail),
        status: response.status,
        detail,
      };
      throw error;
    }

    const payload = await parseJsonSafe<T>(response);
    if (payload === null) {
      throw {
        message: `Empty response for ${path}`,
        status: response.status,
      } satisfies ApiErrorPayload;
    }
    return payload;
  }
}

export const apiClient = new ApiClient();
