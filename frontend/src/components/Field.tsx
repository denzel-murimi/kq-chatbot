import type { InputHTMLAttributes } from "react";

type Props = InputHTMLAttributes<HTMLInputElement> & {
  id: string;
  label: string;
  /** Fixed text shown inside the left edge of the input, e.g. "KQ". */
  leading?: string;
  /** Short helper line under the input. */
  hint?: string;
};

// A label and input that are actually linked (htmlFor/id), so clicking the label focuses the
// input and screen readers announce it. The hint is tied in with aria-describedby.
export function Field({ id, label, leading, hint, className = "", ...inputProps }: Props) {
  const hintId = hint ? `${id}-hint` : undefined;

  return (
    <div>
      <label htmlFor={id} className="mb-2 block text-sm font-bold text-ink-2">
        {label}
      </label>
      <div className="relative">
        {leading && (
          <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 font-mono font-bold text-ink-3">
            {leading}
          </span>
        )}
        <input
          id={id}
          aria-describedby={hintId}
          {...inputProps}
          className={`h-13 w-full rounded-xl border border-line-strong bg-surface text-base text-ink outline-none transition placeholder:text-ink-3/70 focus:border-brand focus:ring-4 focus:ring-brand/15 focus-visible:outline-none ${
            leading ? "pl-13 pr-4" : "px-4"
          } ${className}`}
        />
      </div>
      {hint && (
        <p id={hintId} className="mt-1.5 text-sm text-ink-3">
          {hint}
        </p>
      )}
    </div>
  );
}
