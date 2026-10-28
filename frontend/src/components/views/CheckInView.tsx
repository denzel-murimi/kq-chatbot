import { useState, type FormEvent } from "react";
import { ArrowRight, Info } from "lucide-react";
import { Field } from "@/components/Field";

type Props = {
  onAsk: (question: string) => void;
};

export function CheckInView({ onAsk }: Props) {
  const [pnr, setPnr] = useState("");
  const [lastName, setLastName] = useState("");
  const ready = pnr.trim() !== "" && lastName.trim() !== "";

  // The two values become the first answers in the assistant's slot-filling conversation.
  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!ready) return;
    onAsk(
      `I want to check in for my flight. My booking reference is ${pnr.trim().toUpperCase()} and my last name is ${lastName.trim()}.`,
    );
  }

  return (
    <div className="mx-auto mt-4 max-w-2xl motion-safe:animate-fade-up">
      <form onSubmit={submit} className="space-y-5 rounded-2xl border border-gray-200 bg-white p-8 shadow-xs">
        <Field
          id="pnr"
          label="Booking reference (PNR)"
          value={pnr}
          onChange={(e) => setPnr(e.target.value)}
          placeholder="e.g. ABC123"
          maxLength={6}
          autoComplete="off"
          className="uppercase"
        />
        <Field
          id="last-name"
          label="Last name"
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
          placeholder="e.g. Doe"
          autoComplete="family-name"
        />
        <button
          type="submit"
          disabled={!ready}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand py-3.5 font-bold text-white shadow-md transition hover:bg-brand/90 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Start check-in <ArrowRight size={18} aria-hidden="true" />
        </button>
      </form>

      <button
        type="button"
        onClick={() => onAsk("When does online check-in open and close?")}
        className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl border border-blue-100 bg-blue-50/60 p-4 text-sm text-gray-700 transition hover:bg-blue-50"
      >
        <Info size={18} className="text-blue-500" aria-hidden="true" />
        Not sure when check-in opens? Ask the assistant.
      </button>
    </div>
  );
}
