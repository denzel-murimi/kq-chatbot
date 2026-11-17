import {
  ArrowUpRight,
  BatteryCharging,
  CircleCheck,
  Clock,
  FileText,
  Luggage,
  Plane,
  type LucideIcon,
} from "lucide-react";
import { DEMO_FLIGHT, DEMO_PASSENGER, type FlightPoint } from "@/lib/demo-data";

type Props = {
  onAsk: (question: string) => void;
};

// Each card hands a ready-made question to the assistant, so they double as demo entry points.
// Every question maps to a document in the policy corpus.
const QUICK_QUESTIONS: { icon: LucideIcon; title: string; hint: string; question: string }[] = [
  {
    icon: Luggage,
    title: "Baggage allowance",
    hint: "What fits in Economy",
    question: "What is the baggage allowance for Economy class?",
  },
  {
    icon: Clock,
    title: "Check-in times",
    hint: "When it opens and closes",
    question: "When does check-in close for an international flight?",
  },
  {
    icon: FileText,
    title: "Travel documents",
    hint: "Passport and visa for the UK",
    question: "What travel documents do I need to fly from Nairobi to London?",
  },
  {
    icon: BatteryCharging,
    title: "Batteries & electronics",
    hint: "Power banks and laptops",
    question: "Can I bring a power bank in my cabin bag?",
  },
];

function Endpoint({ label, point, align }: { label: string; point: FlightPoint; align: "left" | "right" }) {
  return (
    <div className={align === "right" ? "text-right" : ""}>
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-on-night-2">{label}</p>
      <p className="mt-1 font-mono text-5xl font-bold tracking-tight text-on-night sm:text-6xl">{point.code}</p>
      <p className="mt-1 text-sm font-semibold text-on-night">{point.city}</p>
      <p className="text-sm text-on-night-2">{point.airport}</p>
    </div>
  );
}

function PassField({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <dt className="text-xs font-bold uppercase tracking-[0.12em] text-ink-3">{label}</dt>
      <dd className={`mt-0.5 whitespace-nowrap text-lg font-bold text-ink ${mono ? "font-mono" : ""}`}>{value}</dd>
    </div>
  );
}

export function DashboardView({ onAsk }: Props) {
  const flight = DEMO_FLIGHT;
  const [departDate, departTime] = flight.from.when.split(" • ");
  const [, arriveTime] = flight.to.when.split(" • ");

  return (
    <div className="space-y-8 motion-safe:animate-fade-up">
      {/* Boarding-pass card. The notches and dashed rule mark the tear-off stub. */}
      <section aria-label="Your upcoming flight" className="overflow-hidden rounded-3xl shadow-sm ring-1 ring-line">
        <div className="relative bg-night px-6 pb-7 pt-6 sm:px-8">
          {/* Faint flight-path arc behind the route, purely decorative. */}
          <svg
            aria-hidden="true"
            viewBox="0 0 400 120"
            preserveAspectRatio="none"
            className="pointer-events-none absolute inset-x-0 top-10 hidden h-28 w-full opacity-30 sm:block"
          >
            <path d="M40 110 Q200 -20 360 110" fill="none" stroke="var(--on-night-2)" strokeWidth="1.5" strokeDasharray="4 6" />
          </svg>

          <div className="relative flex items-center justify-between gap-3">
            <p className="font-mono text-sm font-bold tracking-wide text-on-night">{flight.number}</p>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-ok/15 px-3 py-1 text-sm font-bold text-on-night-ok">
              <CircleCheck size={15} aria-hidden="true" />
              {flight.status}
            </span>
          </div>

          <div className="relative mt-6 grid grid-cols-[1fr_auto_1fr] items-end gap-3">
            <Endpoint label="From" point={flight.from} align="left" />
            <div className="flex flex-col items-center pb-10 text-on-night-2">
              <Plane size={22} className="rotate-45 text-on-night" aria-hidden="true" />
              <p className="mt-2 whitespace-nowrap text-xs font-semibold">{flight.duration}</p>
            </div>
            <Endpoint label="To" point={flight.to} align="right" />
          </div>
        </div>

        {/* Perforation */}
        <div aria-hidden="true" className="relative h-0 bg-surface">
          <span className="absolute -left-3 -top-3 h-6 w-6 rounded-full bg-canvas ring-1 ring-line" />
          <span className="absolute -right-3 -top-3 h-6 w-6 rounded-full bg-canvas ring-1 ring-line" />
        </div>

        <div className="bg-surface px-6 pb-6 pt-6 sm:px-8">
          <dl className="grid grid-cols-2 gap-x-6 gap-y-5 sm:flex sm:flex-wrap sm:justify-between">
            <PassField label="Date" value={departDate} />
            <PassField label="Departs" value={departTime} />
            <PassField label="Arrives" value={arriveTime} />
            <PassField label="Seat" value={`${flight.seat} · ${flight.cabin}`} />
            <PassField label="Booking ref" value={flight.pnr} mono />
          </dl>

          <div className="mt-6 flex flex-col gap-2 border-t border-dashed border-line-strong pt-5 sm:flex-row">
            <button
              type="button"
              onClick={() => onAsk(`I want to check in for ${flight.number}. My booking reference is ${flight.pnr} and my last name is ${DEMO_PASSENGER.lastName}.`)}
              className="flex min-h-11 items-center justify-center gap-2 rounded-xl bg-brand px-5 font-bold text-on-brand transition hover:bg-brand-hover active:scale-[0.98]"
            >
              Check in with assistant
            </button>
            <button
              type="button"
              onClick={() => onAsk(`I want to change my seat for ${flight.number}.`)}
              className="flex min-h-11 items-center justify-center gap-2 rounded-xl border border-line-strong px-5 font-bold text-ink transition hover:bg-surface-2"
            >
              Change seat
            </button>
            <button
              type="button"
              onClick={() => onAsk(`Can you show me my full itinerary for ${flight.number}?`)}
              className="flex min-h-11 items-center justify-center gap-1 rounded-xl px-4 font-bold text-brand-ink transition hover:bg-brand-soft sm:ml-auto"
            >
              Full itinerary <ArrowUpRight size={16} aria-hidden="true" />
            </button>
          </div>
        </div>
      </section>

      <section aria-labelledby="plan-heading">
        <div className="mb-4 flex items-end justify-between gap-4">
          <div>
            <h2 id="plan-heading" className="text-xl font-bold tracking-tight">
              Before you fly
            </h2>
            <p className="text-sm text-ink-3">Tap a topic and the assistant answers from airline policy.</p>
          </div>
        </div>
        <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {QUICK_QUESTIONS.map(({ icon: Icon, title, hint, question }, i) => (
            <li key={title} className="motion-safe:animate-fade-up" style={{ animationDelay: `${80 + i * 50}ms` }}>
              <button
                type="button"
                onClick={() => onAsk(question)}
                className="group flex h-full w-full items-center gap-4 rounded-2xl border border-line bg-surface p-4 text-left transition duration-200 hover:-translate-y-0.5 hover:border-brand/35 hover:shadow-md"
              >
                <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-surface-2 text-ink-2 transition-colors group-hover:bg-brand-soft group-hover:text-brand-ink">
                  <Icon size={22} aria-hidden="true" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block font-bold">{title}</span>
                  <span className="block text-sm text-ink-3">{hint}</span>
                </span>
                <ArrowUpRight
                  size={18}
                  aria-hidden="true"
                  className="shrink-0 text-ink-3 transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:text-brand-ink"
                />
              </button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
