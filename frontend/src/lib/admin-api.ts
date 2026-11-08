// Client for the administrative API. Every request carries the admin key in the
// X-Admin-Key header; the key is entered at runtime and held in sessionStorage
// (see useAdminKey), never baked into the bundle. A 401 throws AdminAuthError so
// the UI can drop back to the key gate.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class AdminAuthError extends Error {
  constructor() {
    super("Invalid or missing admin key");
    this.name = "AdminAuthError";
  }
}

async function request<T>(path: string, key: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}/admin${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", "X-Admin-Key": key, ...(init.headers ?? {}) },
    signal: AbortSignal.timeout(30_000),
  });
  if (res.status === 401) throw new AdminAuthError();
  if (!res.ok) throw new Error(`Request failed with HTTP ${res.status}`);
  if (res.status === 204) return null as T;
  return (await res.json()) as T;
}

export type AdminDoc = { title: string; chunks: number; updated_at: string };
export type DocumentDetail = { title: string; content: string; updated_at: string };
export type Metrics = {
  total_queries: number;
  by_route: Record<string, number>;
  avg_latency_ms: number;
  p95_latency_ms: number;
  informational_queries: number;
  grounded_queries: number;
  grounded_rate: number | null;
};
export type LogRow = {
  created_at: string;
  route: string;
  message: string;
  grounded: boolean | null;
  outcome: string | null;
  latency_ms: number;
};
export type Booking = {
  pnr: string; last_name: string; first_name: string; flight_number: string;
  origin: string; destination: string; departure_time: string; seat: string; status: string;
};

export const adminApi = {
  listDocuments: (key: string) => request<AdminDoc[]>("/documents", key),
  getDocument: (key: string, title: string) =>
    request<DocumentDetail>(`/documents/${encodeURIComponent(title)}`, key),
  saveDocument: (key: string, title: string, content: string) =>
    request<{ title: string; chunks: number }>(`/documents/${encodeURIComponent(title)}`, key, {
      method: "PUT", body: JSON.stringify({ content }),
    }),
  deleteDocument: (key: string, title: string) =>
    request<{ title: string; deleted: boolean }>(`/documents/${encodeURIComponent(title)}`, key, {
      method: "DELETE",
    }),
  reindex: (key: string) => request<{ documents: number; chunks: number }>("/reindex", key, { method: "POST" }),
  metrics: (key: string) => request<Metrics>("/metrics", key),
  logs: (key: string, limit = 50) => request<LogRow[]>(`/logs?limit=${limit}`, key),
  bookings: (key: string) => request<Booking[]>("/bookings", key),
};