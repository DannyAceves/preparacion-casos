import { ApiErrorPayload } from "@/types/api";

function getValidationMessage(detail: unknown): string | null {
  if (!Array.isArray(detail)) {
    return null;
  }

  const messages = detail
    .map((item) => {
      if (typeof item !== "object" || item === null) {
        return null;
      }
      const issue = item as { loc?: unknown; msg?: unknown };
      const path = Array.isArray(issue.loc) ? issue.loc.slice(1).join(".") : "";
      if (typeof issue.msg !== "string" || issue.msg.length === 0) {
        return null;
      }
      return path ? `${path}: ${issue.msg}` : issue.msg;
    })
    .filter((message): message is string => Boolean(message));

  return messages.length > 0 ? messages.join(" ") : null;
}

export function getApiErrorMessage(error: unknown, fallbackMessage: string): string {
  if (typeof error === "object" && error !== null) {
    const apiError = error as Partial<ApiErrorPayload> & { detail?: unknown };
    if (typeof apiError.message === "string" && apiError.message.length > 0) {
      return apiError.message;
    }
    if (typeof apiError.detail === "string" && apiError.detail.length > 0) {
      return apiError.detail;
    }
    if (typeof apiError.detail === "object" && apiError.detail !== null) {
      const detail = apiError.detail as { error?: { detail?: unknown; message?: unknown } };
      if (typeof detail.error?.message === "string" && detail.error.message.length > 0) {
        return detail.error.message;
      }
      if (typeof detail.error?.detail === "string" && detail.error.detail.length > 0) {
        return detail.error.detail;
      }
      const validationMessage = getValidationMessage(apiError.detail);
      if (validationMessage) {
        return validationMessage;
      }
    }
  }
  return fallbackMessage;
}
