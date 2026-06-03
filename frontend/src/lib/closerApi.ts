// Cliente HTTP para el portal del closer. Usa un token separado del de usuarios
// ("closer_token") para que ambas sesiones puedan coexistir.
const BASE_URL = import.meta.env.VITE_API_URL ?? "";

export function getCloserToken(): string | null {
  return localStorage.getItem("closer_token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getCloserToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  const isJson = (res.headers.get("content-type") || "").includes("application/json");

  if (!res.ok) {
    if (isJson) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail ?? "Request failed");
    }
    throw new Error(`HTTP ${res.status} en ${path}`);
  }
  return res.json() as Promise<T>;
}

export const closerApi = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
};
