import {
  Armchair,
  ChevronRight,
  Clock,
  Info,
  Luggage,
  Plane,
  Sparkles,
  Ticket,
  type LucideIcon,
} from "lucide-react";
import { DEMO_FLIGHT, type FlightPoint } from "@/lib/demo-data";

type Props = {
  onAsk: (question: string) => void;
};

// Each card hands a ready-made question to the assistant, so they double as demo entry points.
const QUICK_QUESTIONS: { icon: LucideIcon; title: string; hint: string; question: string }[] = [
  {
    icon: Luggage,
    title: "Baggage guidelines",
    hint: "Allowance and restrictions",
    question: "What is the baggage allowance for Economy class?",
  },
  {
    icon: Clock,
    title: "Check-in timelines",
    hint: "Opening and closing times",
    question: "When does check-in close for an international flight?",
  },
];

function Endpoint({ label, point }: { label: string; point: FlightPoint }) {
  return (
    <div className="w-full text-center @lg:w-36">
      <p className="mb-1 text-[11px] font-bold uppercase tracking-widest text-gray-500">{label}</p>
      <p className="text-4xl font-light tracking-tight">{point.code}</p>
      <p className="mt-1 text-xs font-medium text-gray-500">{point.airport}</p>
      <p className="mt-1 text-xs font-bold text-gray-800">{point.when}</p>
    </div>
  );
}

export function DashboardView({ onAsk }: Props) {
  const flight = DEMO_FLIGHT;

  return (
    <div className="space-y-6 motion-safe:animate-fade-up">
      {/* @container: the layout inside reacts to this card's width, not the window's. */}
      <section
        aria-label="Active flight"
        className="@container rounded-2xl border border-gray-200 bg-white p-6 shadow-xs xl:p-8"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="rounded-lg bg-brand/10 p-1.5 text-brand">
              <Plane size={20} aria-hidden="true" />
            </span>
            <h2 className="text-xs font-bold uppercase tracking-widest text-gray-500">Active flight</h2>
          </div>
          <button
            type="button"
            onClick={() => onAsk(`Can you show me my full itinerary for ${flight.number}?`)}
            className="flex items-center gap-1 rounded-lg px-3 py-1.5 text-sm font-semibold text-brand transition-colors hover:bg-brand/10"
          >
            View itinerary <ChevronRight size={16} aria-hidden="true" />
          </button>
        </div>

        <div className="mt-6">
          <p className="text-4xl font-bold tracking-tight">{flight.number}</p>
          <p className="mt-2 flex flex-wrap items-center gap-2 text-sm font-medium text-gray-500">
            {flight.from.city} ({flight.from.code}) to {flight.to.city} ({flight.to.code})
            <span className="inline-flex items-center gap-1.5 rounded-full border border-green-200 bg-green-100 px-2.5 py-0.5 text-xs font-bold text-green-800">
              <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
              {flight.status}
            </span>
          </p>
        </div>

        <div className="mt-6 flex flex-col items-center gap-6 rounded-xl border border-gray-100 bg-gray-50/60 p-6 @lg:flex-row @lg:justify-between">
          <Endpoint label="Departure" point={flight.from} />
          <div className="flex w-full flex-1 flex-col items-center gap-2 px-4">
            <div className="flex w-full items-center text-gray-400">
              <span className="h-0.5 flex-1 rounded-full bg-gray-300" />
              <Plane size={24} className="mx-3 rotate-90" aria-hidden="true" />
              <span className="flex-1 border-t-2 border-dashed border-gray-300" />
            </div>
            <p className="rounded-full border border-gray-200 bg-white px-3 py-1 text-xs font-medium text-gray-500">
              Duration: {flight.duration}
            </p>
          </div>
          <Endpoint label="Arrival" point={flight.to} />
        </div>

        <div className="mt-6 grid grid-cols-1 gap-4 border-t border-gray-100 pt-6 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => onAsk(`I want to change my seat for ${flight.number}.`)}
            className="group flex items-start gap-3 rounded-lg p-2 text-left transition-colors hover:bg-gray-50"
          >
            <span className="mt-0.5 rounded border border-gray-100 bg-white p-1.5 text-gray-500 shadow-xs">
              <Armchair size={18} aria-hidden="true" />
            </span>
            <span>
              <span className="block text-[11px] font-bold uppercase tracking-wide text-gray-500">Seat</span>
              <span className="block text-sm font-bold group-hover:text-brand">
                {flight.seat} <span className="ml-1 text-xs font-medium text-gray-500">{flight.cabin}</span>
              </span>
              <span className="block text-xs font-semibold text-brand">Change seat</span>
            </span>
          </button>
          <div className="flex items-start gap-3 p-2">
            <span className="mt-0.5 rounded border border-gray-100 bg-white p-1.5 text-gray-500 shadow-xs">
              <Ticket size={18} aria-hidden="true" />
            </span>
            <span>
              <span className="block text-[11px] font-bold uppercase tracking-wide text-gray-500">
                Booking reference
              </span>
              <span className="block text-sm font-bold">{flight.pnr}</span>
            </span>
          </div>
        </div>
      </section>

      <section aria-labelledby="plan-heading">
        <h2
          id="plan-heading"
          className="mb-4 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-gray-800"
        >
          Plan your journey <Info size={14} className="text-gray-400" aria-hidden="true" />
        </h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {QUICK_QUESTIONS.map(({ icon: Icon, title, hint, question }) => (
            <button
              key={title}
              type="button"
              onClick={() => onAsk(question)}
              className="group rounded-2xl border border-gray-200 bg-white p-5 text-left transition hover:border-brand/30 hover:shadow-lg"
            >
              <span className="mb-4 flex items-center gap-4">
                <span className="flex h-12 w-12 items-center justify-center rounded-xl border border-gray-100 bg-gray-50 text-gray-600 transition-colors group-hover:bg-brand/10 group-hover:text-brand">
                  <Icon size={24} aria-hidden="true" />
                </span>
                <span>
                  <span className="block font-bold">{title}</span>
                  <span className="mt-0.5 block text-xs font-medium text-gray-500">{hint}</span>
                </span>
              </span>
              <span className="flex items-center justify-center gap-2 rounded-xl border border-gray-200 bg-gray-50 py-2.5 text-sm font-semibold text-gray-700 transition-all group-hover:border-brand group-hover:bg-brand group-hover:text-white">
                Ask assistant <Sparkles size={14} aria-hidden="true" />
              </span>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
