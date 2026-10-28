import { ClipboardCheck, Clock, Plane, type LucideIcon } from "lucide-react";
import { DEMO_PASSENGER } from "@/lib/demo-data";
import { BrandMark } from "./BrandMark";

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
    label: "Dashboard",
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
    <aside className="hidden w-64 shrink-0 flex-col border-r border-gray-200 bg-white xl:flex">
      <div className="flex items-center gap-3 border-b border-gray-100 p-6">
        <BrandMark />
        <div>
          <p className="text-lg font-bold leading-tight tracking-tight">Kenya Airways</p>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-500">Passenger self-service</p>
        </div>
      </div>
      <nav aria-label="Main" className="flex-1 space-y-1.5 p-4">
        {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => onChange(id)}
            aria-current={active === id ? "page" : undefined}
            className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
              active === id ? "bg-brand/10 text-brand" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
            }`}
          >
            <Icon size={18} aria-hidden="true" />
            {label}
          </button>
        ))}
      </nav>
    </aside>
  );
}

// Below xl: a bottom tab bar, since the sidebar is hidden.
export function BottomNav({ active, onChange }: NavProps) {
  return (
    <nav aria-label="Main" className="fixed inset-x-0 bottom-0 z-30 flex h-16 border-t border-gray-200 bg-white xl:hidden">
      {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          type="button"
          onClick={() => onChange(id)}
          aria-current={active === id ? "page" : undefined}
          className={`flex flex-1 flex-col items-center justify-center gap-1 text-xs font-medium ${
            active === id ? "text-brand" : "text-gray-500"
          }`}
        >
          <Icon size={20} aria-hidden="true" />
          {label}
        </button>
      ))}
    </nav>
  );
}
