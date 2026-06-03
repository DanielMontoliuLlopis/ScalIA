const BASE_URL = import.meta.env.VITE_API_URL ?? "";

function getToken(): string | null {
  return localStorage.getItem("token");
}

function getClientAccountId(): string | null {
  return localStorage.getItem("active_client_id");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const clientId = getClientAccountId();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (clientId) headers["X-Client-Account-Id"] = clientId;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  const contentType = res.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");

  if (!res.ok) {
    if (isJson) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail ?? "Request failed");
    }
    const body = await res.text().catch(() => "");
    throw new Error(
      `HTTP ${res.status} en ${path}. ${body.startsWith("<") ? "El backend no respondió (¿endpoint inexistente o backend caído?)" : body.slice(0, 200)}`
    );
  }

  if (!isJson) {
    throw new Error(`Respuesta no-JSON desde ${path}. ¿Backend reiniciado tras último cambio?`);
  }
  return res.json() as Promise<T>;
}

async function requestForm<T>(path: string, form: FormData): Promise<T> {
  const token = getToken();
  const clientId = getClientAccountId();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (clientId) headers["X-Client-Account-Id"] = clientId;

  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
  upload: <T>(path: string, form: FormData) => requestForm<T>(path, form),
};
