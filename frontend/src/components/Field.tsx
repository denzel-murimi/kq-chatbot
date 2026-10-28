import type { InputHTMLAttributes } from "react";

type Props = InputHTMLAttributes<HTMLInputElement> & {
  id: string;
  label: string;
  /** Fixed text shown inside the left edge of the input, e.g. "KQ". */
  leading?: string;
};

// A label and input that are actually linked (htmlFor/id), so clicking the label focuses the
// input and screen readers announce it.
export function Field({ id, label, leading, className = "", ...inputProps }: Props) {
  return (
    <div>
      <label htmlFor={id} className="mb-2 block text-xs font-bold uppercase tracking-widest text-gray-600">
        {label}
      </label>
      <div className="relative">
        {leading && (
          <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 font-bold text-gray-500">
            {leading}
          </span>
        )}
        <input
          id={id}
          {...inputProps}
          className={`w-full rounded-xl border border-gray-200 bg-gray-50 py-3.5 font-medium text-gray-900 outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/20 ${
            leading ? "pl-12 pr-4" : "px-4"
          } ${className}`}
        />
      </div>
    </div>
  );
}
