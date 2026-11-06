"use client";

import { useCallback, useState } from "react";
import { BarChart3, Database, KeyRound, LogOut, Ticket } from "lucide-react";
import { useAdminKey } from "@/hooks/useAdminKey";
import { adminApi, AdminAuthError } from "@/lib/admin-api";
import { KnowledgeBaseTab } from "@/components/admin/KnowledgeBaseTab";
import { MonitoringTab } from "@/components/admin/MonitoringTab";
import { BookingsTab } from "@/components/admin/BookingsTab";

type Tab = "kb" | "monitoring" | "bookings";

const TABS: { id: Tab; label: string; icon: typeof Database }[] = [
  { id: "kb", label: "Knowledge Base", icon: Database },
  { id: "monitoring", label: "Monitoring", icon: BarChart3 },
  { id: "bookings", label: "Bookings", icon: Ticket },
];

// Key gate: validates the entered key by making one authenticated call before
// unlocking, so a wrong key is caught immediately rather than on the first tab.
function Gate({ onUnlock }: { onUnlock: (key: string) => void }) {
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!value.trim()) return;
    setChecking(true);
    setError(null);
    try {
      await adminApi.metrics(value.trim()); // 401 -> AdminAuthError
      onUnlock(value.trim());
    } catch (err) {
      setError(err instanceof AdminAuthError ? "That key was not accepted." : "Could not reach the server.");
    } finally {
      setChecking(false);
    }
  }

  return (
    <div className="flex min-h-dvh items-center justify-center bg-gray-50 p-4">
      <form onSubmit={submit} className="w-full max-w-sm rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-full bg-brand/10 text-brand">
          <KeyRound size={20} aria-hidden="true" />
        </div>
        <h1 className="text-lg font-bold text-gray-900">Admin access</h1>
        <p className="mt-1 text-sm text-gray-500">Enter the administrator key to manage the knowledge base and view monitoring.</p>
        <input
          type="password"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Administrator key"
          autoFocus
          className="mt-4 w-full rounded-xl border border-gray-300 px-3 py-2.5 text-sm outline-none focus:border-brand focus:ring-2 focus:ring-brand/20"
        />
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={checking || !value.trim()}
          className="mt-4 w-full rounded-xl bg-brand px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand/90 disabled:opacity-50"
        >
          {checking ? "Checking…" : "Unlock"}
        </button>
      </form>
    </div>
  );
}

export default function AdminPage() {
  const { key, setKey, clearKey } = useAdminKey();
  const [tab, setTab] = useState<Tab>("kb");

  const onAuthError = useCallback(() => clearKey(), [clearKey]);

  if (!key) return <Gate onUnlock={setKey} />;

  return (
    <div className="min-h-dvh bg-gray-50 text-gray-900">
      <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-4 xl:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand/10 text-brand">
            <KeyRound size={18} aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight">Administration</h1>
            <p className="text-xs text-gray-500">Kenya Airways assistant — system admin</p>
          </div>
        </div>
        <button
          onClick={clearKey}
          className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-3 py-1.5 text-xs font-semibold text-gray-600 transition hover:bg-gray-50"
        >
          <LogOut size={14} aria-hidden="true" /> Lock
        </button>
      </header>

      <nav className="flex gap-1 border-b border-gray-200 bg-white px-4 xl:px-8">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-2 border-b-2 px-3 py-3 text-sm font-semibold transition ${
              tab === id ? "border-brand text-brand" : "border-transparent text-gray-500 hover:text-gray-800"
            }`}
          >
            <Icon size={16} aria-hidden="true" /> {label}
          </button>
        ))}
      </nav>

      <main className="mx-auto w-full max-w-6xl p-4 xl:p-8">
        {tab === "kb" && <KnowledgeBaseTab adminKey={key} onAuthError={onAuthError} />}
        {tab === "monitoring" && <MonitoringTab adminKey={key} onAuthError={onAuthError} />}
        {tab === "bookings" && <BookingsTab adminKey={key} onAuthError={onAuthError} />}
      </main>
    </div>
  );
}