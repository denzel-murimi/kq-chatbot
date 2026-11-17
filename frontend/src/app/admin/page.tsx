"use client";

import { useCallback, useState } from "react";
import Link from "next/link";
import { BarChart3, Database, ExternalLink, KeyRound, Lock, Ticket, type LucideIcon } from "lucide-react";
import { useAdminKey } from "@/hooks/useAdminKey";
import { adminApi, AdminAuthError } from "@/lib/admin-api";
import { KnowledgeBaseTab } from "@/components/admin/KnowledgeBaseTab";
import { MonitoringTab } from "@/components/admin/MonitoringTab";
import { BookingsTab } from "@/components/admin/BookingsTab";
import { Notice } from "@/components/admin/ui";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";

type Tab = "kb" | "monitoring" | "bookings";

const TABS: { id: Tab; label: string; icon: LucideIcon; blurb: string }[] = [
  { id: "monitoring", label: "Monitoring", icon: BarChart3, blurb: "Request volume, routing and latency." },
  { id: "kb", label: "Knowledge base", icon: Database, blurb: "Policy documents the assistant answers from." },
  { id: "bookings", label: "Bookings", icon: Ticket, blurb: "Simulated passenger bookings." },
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
    <div className="grid min-h-dvh bg-canvas font-admin lg:grid-cols-[1fr_minmax(420px,40%)]">
      <div className="relative hidden flex-col justify-between overflow-hidden bg-night p-12 text-on-night lg:flex">
        <Logo className="h-9 w-auto self-start brightness-0 invert" priority />
        <div className="relative max-w-md">
          <p className="font-admin-mono text-xs uppercase tracking-[0.2em] text-on-night-2">Operations console</p>
          <p className="mt-3 text-3xl font-semibold leading-tight">
            Keep the assistant&apos;s answers accurate, and see how it is performing.
          </p>
        </div>
        <p className="text-sm text-on-night-2">Academic prototype. Not an official Kenya Airways system.</p>
        <div aria-hidden="true" className="absolute -right-24 top-1/3 h-96 w-96 rounded-full bg-brand/20 blur-3xl" />
      </div>

      <div className="relative flex items-center justify-center p-6">
        <ThemeToggle className="absolute right-4 top-4" />
        <form onSubmit={submit} className="w-full max-w-sm">
          <div className="mb-6 flex h-11 w-11 items-center justify-center rounded-xl bg-brand-soft text-brand-ink">
            <KeyRound size={20} aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-semibold text-ink">Admin access</h1>
          <p className="mt-1 text-sm text-ink-3">Enter the administrator key to continue.</p>
          <label htmlFor="admin-key" className="mt-6 block text-sm font-medium text-ink-2">
            Administrator key
          </label>
          <input
            id="admin-key"
            type="password"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            autoFocus
            autoComplete="current-password"
            aria-invalid={error ? true : undefined}
            aria-describedby={error ? "admin-key-error" : undefined}
            className="mt-1.5 h-11 w-full rounded-lg border border-line-strong bg-surface px-3 font-admin-mono text-sm text-ink outline-none focus:border-brand focus:ring-4 focus:ring-brand/15 focus-visible:outline-none"
          />
          {error && (
            <div id="admin-key-error" className="mt-3">
              <Notice tone="error">{error}</Notice>
            </div>
          )}
          <button
            type="submit"
            disabled={checking || !value.trim()}
            className="mt-5 h-11 w-full rounded-lg bg-brand text-sm font-semibold text-on-brand transition hover:bg-brand-hover disabled:cursor-not-allowed disabled:opacity-50"
          >
            {checking ? "Checking…" : "Unlock console"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function AdminPage() {
  const { key, setKey, clearKey } = useAdminKey();
  const [tab, setTab] = useState<Tab>("monitoring");

  const onAuthError = useCallback(() => clearKey(), [clearKey]);

  if (!key) return <Gate onUnlock={setKey} />;

  const current = TABS.find((t) => t.id === tab) ?? TABS[0];

  return (
    <div className="flex min-h-dvh flex-col bg-canvas font-admin text-ink lg:flex-row">
      <aside className="flex shrink-0 flex-col bg-night text-on-night lg:sticky lg:top-0 lg:h-dvh lg:w-60">
        <div className="flex items-center justify-between gap-3 px-4 py-4 lg:block lg:px-5 lg:py-6">
          <div>
            <Logo className="h-7 w-auto brightness-0 invert" priority />
            <p className="mt-2 hidden font-admin-mono text-[11px] uppercase tracking-[0.18em] text-on-night-2 lg:block">
              Admin console
            </p>
          </div>
          <div className="flex items-center gap-1 lg:hidden">
          <ThemeToggle tone="night" />
          <button
            type="button"
            onClick={clearKey}
            className="flex h-9 items-center gap-1.5 rounded-lg px-3 text-sm font-medium text-on-night-2 hover:bg-night-2 hover:text-on-night lg:hidden"
          >
            <Lock size={14} aria-hidden="true" /> Lock
          </button>
          </div>
        </div>

        <nav aria-label="Admin sections" className="flex gap-1 overflow-x-auto px-3 pb-3 lg:flex-1 lg:flex-col lg:pb-0">
          {TABS.map(({ id, label, icon: Icon }) => {
            const isActive = tab === id;
            return (
              <button
                key={id}
                type="button"
                onClick={() => setTab(id)}
                aria-current={isActive ? "page" : undefined}
                className={`flex h-10 shrink-0 items-center gap-2.5 rounded-lg px-3 text-sm font-medium transition-colors ${
                  isActive ? "bg-night-2 text-on-night shadow-[inset_2px_0_0_var(--brand)]" : "text-on-night-2 hover:bg-night-2/60 hover:text-on-night"
                }`}
              >
                <Icon size={16} aria-hidden="true" />
                {label}
              </button>
            );
          })}
        </nav>

        <div className="hidden space-y-1 border-t border-white/10 p-3 lg:block">
          <div className="flex items-center justify-between px-3 pb-2 pt-1">
            <span className="text-sm text-on-night-2">Theme</span>
            <ThemeToggle tone="night" />
          </div>
          <Link
            href="/"
            className="flex h-10 items-center gap-2.5 rounded-lg px-3 text-sm font-medium text-on-night-2 hover:bg-night-2/60 hover:text-on-night"
          >
            <ExternalLink size={16} aria-hidden="true" /> Passenger app
          </Link>
          <button
            type="button"
            onClick={clearKey}
            className="flex h-10 w-full items-center gap-2.5 rounded-lg px-3 text-sm font-medium text-on-night-2 hover:bg-night-2/60 hover:text-on-night"
          >
            <Lock size={16} aria-hidden="true" /> Lock console
          </button>
        </div>
      </aside>

      <main className="min-w-0 flex-1">
        <header className="border-b border-line bg-surface px-4 py-4 lg:px-8 lg:py-5">
          <h1 className="text-xl font-semibold tracking-tight">{current.label}</h1>
          <p className="text-sm text-ink-3">{current.blurb}</p>
        </header>
        <div key={tab} className="mx-auto w-full max-w-7xl p-4 motion-safe:animate-fade-in lg:p-8">
          {tab === "kb" && <KnowledgeBaseTab adminKey={key} onAuthError={onAuthError} />}
          {tab === "monitoring" && <MonitoringTab adminKey={key} onAuthError={onAuthError} />}
          {tab === "bookings" && <BookingsTab adminKey={key} onAuthError={onAuthError} />}
        </div>
      </main>
    </div>
  );
}
