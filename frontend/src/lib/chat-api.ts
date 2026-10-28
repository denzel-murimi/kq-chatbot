// The only file that knows where the backend lives and what a chat request looks like.
// NEXT_PUBLIC_ variables are baked into the browser bundle at build time, so they are public:
// never put a secret in one. Locally the fallback below is used; on Vercel, set NEXT_PUBLIC_API_URL.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type ChatResponse = {
  reply: string;
};

export async function sendChatMessage(message: string, sessionId: string): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    // The backend ignores session_id until the slot-filling sprint, but the contract can settle now.
    body: JSON.stringify({ message, session_id: sessionId }),
    signal: AbortSignal.timeout(30_000),
  });

  // fetch only rejects on network-level failures. A 404 or 500 still resolves, so check res.ok.
  if (!res.ok) {
    throw new Error(`Chat request failed with HTTP ${res.status}`);
  }

  return (await res.json()) as ChatResponse;
}
