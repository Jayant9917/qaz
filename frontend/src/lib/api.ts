export function getApiBase() {
  const configured = process.env.NEXT_PUBLIC_NOVO_API_URL?.trim();
  if (configured) {
    return configured.replace(/\/$/, "");
  }

  if (typeof window !== "undefined") {
    return `http://${window.location.hostname}:8000/api/v1`;
  }

  return "http://localhost:8000/api/v1";
}
