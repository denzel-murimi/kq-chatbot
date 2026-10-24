import { useState, type FormEvent } from "react";
import { Search } from "lucide-react";
import { Field } from "@/components/Field";

type Props = {
  onAsk: (question: string) => void;
};

export function FlightStatusView({ onAsk }: Props) {
  const [flightNumber, setFlightNumber] = useState("");
  const [date, setDate] = useState("");

  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!flightNumber) return;
    onAsk(`What is the current flight status for KQ ${flightNumber}${date ? ` on ${date}` : " today"}?`);
  }

  return (
    <div className="mx-auto mt-4 max-w-2xl motion-safe:animate-fade-up">
      <form onSubmit={submit} className="space-y-5 rounded-2xl border border-gray-200 bg-white p-8 shadow-xs">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <Field
            id="flight-number"
            label="Flight number"
            leading="KQ"
            value={flightNumber}
            onChange={(e) => setFlightNumber(e.target.value.replace(/\D/g, ""))}
            placeholder="100"
            inputMode="numeric"
            maxLength={4}
            autoComplete="off"
          />
          <Field id="flight-date" label="Date" type="date" value={date} onChange={(e) => setDate(e.target.value)} />
        </div>
        <button
          type="submit"
          disabled={!flightNumber}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-ink py-3.5 font-bold text-white shadow-md transition hover:bg-black disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Search size={18} aria-hidden="true" /> Check status
        </button>
      </form>
    </div>
  );
}
