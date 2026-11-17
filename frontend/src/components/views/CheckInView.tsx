import { useState, type FormEvent } from "react";
import { ArrowRight, Info } from "lucide-react";
import { Field } from "@/components/Field";

type Props = {
  onAsk: (question: string) => void;
};

// The funnel the passenger is in. Step 1 happens on this page; the assistant runs 2 and 3.
const STEPS = ["Find booking", "Confirm details", "Boarding pass"];

function Stepper({ current }: { current: number }) {
  return (
    <ol aria-label="Check-in steps" className="mb-6 flex items-center gap-2">
      {STEPS.map((step, i) => {
        const isCurrent = i === current;
        return (
          <li key={step} aria-current={isCurrent ? "step" : undefined} className="flex flex-1 items-center gap-2">
            <span
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-sm font-bold ${
                isCurrent ? "bg-brand text-on-brand" : "border border-line-strong text-ink-3"
              }`}
            >
              {i + 1}
            </span>
            <span className={`hidden text-sm font-bold sm:inline ${isCurrent ? "text-ink" : "text-ink-3"}`}>{step}</span>
            {i < STEPS.length - 1 && <span aria-hidden="true" className="h-px flex-1 bg-line-strong" />}
          </li>
        );
      })}
    </ol>
  );
}

export function CheckInView({ onAsk }: Props) {
  const [pnr, setPnr] = useState("");
  const [lastName, setLastName] = useState("");
  const ready = pnr.trim().length === 6 && lastName.trim() !== "";

  // The two values become the first answers in the assistant's slot-filling conversation.
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!ready) return;
    onAsk(
      `I want to check in for my flight. My booking reference is ${pnr.trim().toUpperCase()} and my last name is ${lastName.trim()}.`,
    );
  }

  return (
    <div className="mx-auto max-w-2xl motion-safe:animate-fade-up">
      <Stepper current={0} />

      <form onSubmit={submit} className="space-y-5 rounded-2xl border border-line bg-surface p-6 shadow-xs sm:p-8">
        <Field
          id="pnr"
          label="Booking reference"
          hint="6 letters and numbers, on your e-ticket. Try ABC123."
          value={pnr}
          onChange={(e) => setPnr(e.target.value.replace(/[^a-z0-9]/gi, "").toUpperCase())}
          placeholder="ABC123"
          maxLength={6}
          autoComplete="off"
          spellCheck={false}
          className="font-mono uppercase tracking-[0.2em]"
        />
        <Field
          id="last-name"
          label="Last name"
          hint="As it appears on your passport."
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
          placeholder="Doe"
          autoComplete="family-name"
        />
        <button
          type="submit"
          disabled={!ready}
          className="flex min-h-13 w-full items-center justify-center gap-2 rounded-xl bg-brand font-bold text-on-brand transition hover:bg-brand-hover active:scale-[0.99] disabled:cursor-not-allowed disabled:bg-surface-2 disabled:text-ink-3"
        >
          Find my booking <ArrowRight size={18} aria-hidden="true" />
        </button>
      </form>

      <button
        type="button"
        onClick={() => onAsk("When does online check-in open and close?")}
        className="mt-4 flex min-h-12 w-full items-center gap-3 rounded-xl border border-line bg-surface-2 px-4 py-3 text-left text-sm text-ink-2 transition hover:border-line-strong"
      >
        <Info size={18} className="shrink-0 text-ink-3" aria-hidden="true" />
        <span>
          Not sure when check-in opens? <span className="font-bold text-brand-ink">Ask the assistant</span>
        </span>
      </button>
    </div>
  );
}
