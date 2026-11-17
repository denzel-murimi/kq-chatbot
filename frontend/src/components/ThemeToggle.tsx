"use client";

import { Monitor, Moon, Sun, type LucideIcon } from "lucide-react";
import { useTheme, type ThemePreference } from "@/hooks/useTheme";

const OPTIONS: { value: ThemePreference; label: string; icon: LucideIcon }[] = [
  { value: "system", label: "System theme", icon: Monitor },
  { value: "light", label: "Light theme", icon: Sun },
  { value: "dark", label: "Dark theme", icon: Moon },
];

type Props = {
  /** "night" for placement on the always-dark admin sidebar. */
  tone?: "default" | "night";
  className?: string;
};

// Three-way segmented control: system / light / dark. Exposed as a radiogroup so screen readers
// announce which option is selected.
export function ThemeToggle({ tone = "default", className = "" }: Props) {
  const { preference, setPreference } = useTheme();
  const isNight = tone === "night";

  return (
    <div
      role="radiogroup"
      aria-label="Colour theme"
      className={`inline-flex shrink-0 items-center gap-0.5 rounded-full p-0.5 ${
        isNight ? "bg-night-2" : "border border-line bg-surface-2"
      } ${className}`}
    >
      {OPTIONS.map(({ value, label, icon: Icon }) => {
        const checked = preference === value;
        return (
          <button
            key={value}
            type="button"
            role="radio"
            aria-checked={checked}
            aria-label={label}
            title={label}
            onClick={() => setPreference(value)}
            className={`flex h-8 w-8 items-center justify-center rounded-full transition-colors duration-150 ${
              checked
                ? isNight
                  ? "bg-on-night/15 text-on-night"
                  : "bg-surface text-ink shadow-xs ring-1 ring-line"
                : isNight
                  ? "text-on-night-2 hover:text-on-night"
                  : "text-ink-3 hover:text-ink"
            }`}
          >
            <Icon size={15} aria-hidden="true" />
          </button>
        );
      })}
    </div>
  );
}
