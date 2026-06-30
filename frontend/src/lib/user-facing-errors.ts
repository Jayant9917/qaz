export function getUserFacingErrorMessage(status: number, bodyText: string, fallback: string): string {
  const trimmed = bodyText.trim();

  if (status === 409) {
    return "That chat name is already in use. Please choose a different title.";
  }

  if (status === 401) {
    return "Your session ended. Please sign in again.";
  }

  if (status === 403) {
    return "NOVO does not have permission to do that right now.";
  }

  if (status === 404) {
    return "We could not find what you requested. Please try again.";
  }

  if (status === 422) {
    const validationMessage = extractValidationMessage(trimmed);
    return validationMessage ?? "Please check the fields you entered and try again.";
  }

  if (status >= 500) {
    return "NOVO hit a server issue. Please try again in a moment.";
  }

  const parsedMessage = extractMessage(trimmed);
  return parsedMessage ?? fallback;
}

function extractMessage(text: string): string | null {
  if (!text) {
    return null;
  }

  try {
    const parsed = JSON.parse(text) as unknown;
    if (typeof parsed === "string") {
      return parsed;
    }

    if (parsed && typeof parsed === "object" && "detail" in parsed) {
      const detail = (parsed as { detail?: unknown }).detail;
      if (typeof detail === "string") {
        return detail;
      }

      if (Array.isArray(detail)) {
        const messages = detail
          .map((item) => {
            if (!item || typeof item !== "object") {
              return null;
            }

            const record = item as { msg?: unknown; message?: unknown };
            if (typeof record.msg === "string") {
              return record.msg;
            }
            if (typeof record.message === "string") {
              return record.message;
            }
            return null;
          })
          .filter((value): value is string => typeof value === "string" && value.length > 0);

        if (messages.length > 0) {
          return messages.join(" ");
        }
      }
    }
  } catch {
    return text;
  }

  return text || null;
}

function extractValidationMessage(text: string): string | null {
  const message = extractMessage(text);
  if (!message) {
    return null;
  }

  if (message.toLowerCase().includes("value is not a valid email address")) {
    return "Please enter a valid email address.";
  }

  if (message.toLowerCase().includes("string should have at least")) {
    return "One of the fields is too short. Please make it a little longer.";
  }

  return message;
}
