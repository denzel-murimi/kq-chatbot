// The only file that knows where the backend lives and what a chat request looks like.
// NEXT_PUBLIC_ variables are baked into the browser bundle at build time, so they are public:
// never put a secret in one. Locally the fallback below is used; on Vercel, set NEXT_PUBLIC_API_URL.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type ChatResponse = {
  reply: string;
  /** True only when the reply was generated from retrieved Kenya Airways documents. */
  grounded?: boolean;
  /** Deduplicated document titles behind a grounded reply. Empty otherwise. */
  sources?: string[];
};

/** A prior turn, sent so the backend can resolve follow-ups like "that form". */
export type HistoryTurn = { role: "user" | "bot"; text: string };

export async function sendChatMessage(
  message: string,
  sessionId: string,
  history: HistoryTurn[] = [],
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    // session_id ties follow-up messages to the same slot-filling conversation on the backend.
    body: JSON.stringify({ message, session_id: sessionId, history }),
    signal: AbortSignal.timeout(30_000),
  });

  // fetch only rejects on network-level failures. A 404 or 500 still resolves, so check res.ok.
  if (!res.ok) {
    throw new Error(`Chat request failed with HTTP ${res.status}`);
  }

  return (await res.json()) as ChatResponse;
}
