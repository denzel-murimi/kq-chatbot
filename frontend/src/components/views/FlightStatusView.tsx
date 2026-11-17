import { useState, type FormEvent } from "react";
import { Search } from "lucide-react";
import { Field } from "@/components/Field";
import { DEMO_FLIGHT } from "@/lib/demo-data";

type Props = {
  onAsk: (question: string) => void;
};

export function FlightStatusView({ onAsk }: Props) {
  const [flightNumber, setFlightNumber] = useState("");
  const [date, setDate] = useState("");
  const demoNumber = DEMO_FLIGHT.number.replace(/\D/g, "");

  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!flightNumber) return;
    onAsk(`What is the current flight status for KQ ${flightNumber}${date ? ` on ${date}` : " today"}?`);
  }

  return (
    <div className="mx-auto max-w-2xl motion-safe:animate-fade-up">
      <form onSubmit={submit} className="space-y-5 rounded-2xl border border-line bg-surface p-6 shadow-xs sm:p-8">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <Field
            id="flight-number"
            label="Flight number"
            leading="KQ"
            value={flightNumber}
            onChange={(e) => setFlightNumber(e.target.value.replace(/\D/g, ""))}
            placeholder={demoNumber}
            inputMode="numeric"
            maxLength={4}
            autoComplete="off"
            className="font-mono tracking-wider"
          />
          <Field
            id="flight-date"
            label="Date"
            hint="Leave empty for today."
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </div>
        <button
          type="submit"
          disabled={!flightNumber}
          className="flex min-h-13 w-full items-center justify-center gap-2 rounded-xl bg-night font-bold text-on-night transition hover:bg-night-2 active:scale-[0.99] disabled:cursor-not-allowed disabled:bg-surface-2 disabled:text-ink-3"
        >
          <Search size={18} aria-hidden="true" /> Check status
        </button>
      </form>

      <p className="mt-4 text-center text-sm text-ink-3">
        Your booked flight:{" "}
        <button
          type="button"
          onClick={() => setFlightNumber(demoNumber)}
          className="font-mono font-bold text-brand-ink underline-offset-4 hover:underline"
        >
          {DEMO_FLIGHT.number}
        </button>
      </p>
    </div>
  );
}
