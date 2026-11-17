import type { ButtonHTMLAttributes, ReactNode } from "react";
import { AlertCircle, CheckCircle2, Loader2, RefreshCw } from "lucide-react";

// Small shared primitives for the admin console, so the three tabs stay visually consistent.

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger" | "ghost";
  loading?: boolean;
};

const VARIANTS: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary: "bg-brand text-on-brand hover:bg-brand-hover",
  secondary: "border border-line-strong bg-surface text-ink-2 hover:bg-surface-2 hover:text-ink",
  danger: "border border-danger/30 bg-surface text-danger hover:bg-danger-soft",
  ghost: "text-ink-2 hover:bg-surface-2 hover:text-ink",
};

export function Button({ variant = "secondary", loading, children, className = "", disabled, ...rest }: ButtonProps) {
  return (
    <button
      type="button"
      {...rest}
      disabled={disabled || loading}
      className={`inline-flex h-9 items-center justify-center gap-1.5 rounded-lg px-3 text-sm font-semibold transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-50 ${VARIANTS[variant]} ${className}`}
    >
      {loading && <Loader2 size={14} className="animate-spin" aria-hidden="true" />}
      {children}
    </button>
  );
}

export function RefreshButton({ onClick, loading }: { onClick: () => void; loading: boolean }) {
  return (
    <Button onClick={onClick} disabled={loading} aria-label="Refresh">
      <RefreshCw size={14} className={loading ? "animate-spin" : ""} aria-hidden="true" />
      <span className="hidden sm:inline">Refresh</span>
    </Button>
  );
}

export function Panel({ title, actions, children, className = "" }: { title?: ReactNode; actions?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`overflow-hidden rounded-xl border border-line bg-surface ${className}`}>
      {(title || actions) && (
        <header className="flex min-h-11 items-center justify-between gap-3 border-b border-line px-4 py-2">
          {title && <h3 className="text-xs font-semibold uppercase tracking-wider text-ink-3">{title}</h3>}
          {actions}
        </header>
      )}
      {children}
    </section>
  );
}

/** Banner for success/error feedback. role=status/alert so screen readers announce it. */
export function Notice({ tone, children }: { tone: "ok" | "error"; children: ReactNode }) {
  const isOk = tone === "ok";
  const Icon = isOk ? CheckCircle2 : AlertCircle;
  return (
    <p
      role={isOk ? "status" : "alert"}
      className={`flex items-start gap-2 rounded-lg px-3 py-2 text-sm motion-safe:animate-fade-in ${
        isOk ? "bg-ok-soft text-ok" : "bg-danger-soft text-danger"
      }`}
    >
      <Icon size={16} className="mt-0.5 shrink-0" aria-hidden="true" />
      <span>{children}</span>
    </p>
  );
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <span aria-hidden="true" className={`block animate-pulse rounded bg-surface-2 ${className}`} />;
}

/** "Updated 14:02" — admin views say how fresh their data is. */
export function UpdatedAt({ at }: { at: Date | null }) {
  if (!at) return null;
  return (
    <span className="text-xs text-ink-3">
      Updated {at.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
    </span>
  );
}

export const tableHead = "bg-surface-2 text-[11px] font-semibold uppercase tracking-wider text-ink-3";
export const th = "px-4 py-2.5 font-semibold";
export const td = "px-4 py-2.5";
