import { ClipboardCheck, Clock, Plane, Sparkles, type LucideIcon } from "lucide-react";
import { DEMO_PASSENGER } from "@/lib/demo-data";
import { Logo } from "./Logo";

export type TabId = "dashboard" | "checkin" | "status";

type NavItem = {
  id: TabId;
  label: string;
  icon: LucideIcon;
  /** Heading and subheading shown in the page header while this view is active. */
  title: string;
  subtitle: string;
};

// One list drives the sidebar, the mobile bottom bar and the page header.
export const NAV_ITEMS: NavItem[] = [
  {
    id: "dashboard",
    label: "My trip",
    icon: Plane,
    title: `Welcome back, ${DEMO_PASSENGER.firstName}`,
    subtitle: "Here is your upcoming journey.",
  },
  {
    id: "checkin",
    label: "Check-in",
    icon: ClipboardCheck,
    title: "Online check-in",
    subtitle: "Enter your booking details and the assistant takes it from there.",
  },
  {
    id: "status",
    label: "Flight status",
    icon: Clock,
    title: "Flight status",
    subtitle: "Ask about departures, arrivals and delays.",
  },
];

type NavProps = {
  active: TabId;
  onChange: (tab: TabId) => void;
};

// Desktop (xl and up): left sidebar.
export function Sidebar({ active, onChange }: NavProps) {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-line bg-surface xl:flex">
      <div className="px-6 pb-5 pt-7">
        <Logo className="h-auto w-full dark:brightness-0 dark:invert" priority />
      </div>
      <p className="px-6 pb-2 text-xs font-bold uppercase tracking-[0.14em] text-ink-3">Passenger self-service</p>
      <nav aria-label="Main" className="flex-1 space-y-1 px-3">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => {
          const isActive = active === id;
          return (
            <button
              key={id}
              type="button"
              onClick={() => onChange(id)}
              aria-current={isActive ? "page" : undefined}
              className={`relative flex min-h-11 w-full items-center gap-3 rounded-lg px-3 text-[15px] font-semibold transition-colors duration-200 ${
                isActive ? "bg-brand-soft text-brand-ink" : "text-ink-2 hover:bg-surface-2 hover:text-ink"
              }`}
            >
              {isActive && <span aria-hidden="true" className="absolute inset-y-2 left-0 w-1 rounded-r bg-brand" />}
              <Icon size={18} aria-hidden="true" />
              {label}
            </button>
          );
        })}
      </nav>
      <div className="m-4 rounded-xl border border-line bg-surface-2 p-4">
        <p className="flex items-center gap-2 text-sm font-bold">
          <Sparkles size={16} className="text-brand-ink" aria-hidden="true" /> AI Assistant
        </p>
        <p className="mt-1 text-sm leading-snug text-ink-3">
          Answers come from Kenya Airways policy documents.
        </p>
      </div>
    </aside>
  );
}

// Below xl: a bottom tab bar, since the sidebar is hidden.
export function BottomNav({ active, onChange }: NavProps) {
  return (
    <nav
      aria-label="Main"
      className="fixed inset-x-0 bottom-0 z-30 flex border-t border-line bg-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur xl:hidden"
    >
      {NAV_ITEMS.map(({ id, label, icon: Icon }) => {
        const isActive = active === id;
        return (
          <button
            key={id}
            type="button"
            onClick={() => onChange(id)}
            aria-current={isActive ? "page" : undefined}
            className={`flex h-16 flex-1 flex-col items-center justify-center gap-1 text-xs font-semibold transition-colors ${
              isActive ? "text-brand-ink" : "text-ink-3 hover:text-ink"
            }`}
          >
            <span
              className={`flex h-7 w-12 items-center justify-center rounded-full transition-colors ${
                isActive ? "bg-brand-soft" : ""
              }`}
            >
              <Icon size={20} aria-hidden="true" />
            </span>
            {label}
          </button>
        );
      })}
    </nav>
  );
}
