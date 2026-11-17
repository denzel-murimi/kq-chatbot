"use client";

import { useSyncExternalStore } from "react";

export type ThemePreference = "system" | "light" | "dark";

export const THEME_STORAGE_KEY = "kq-theme";

/**
 * Runs inline in <head> before first paint, so a saved dark preference never flashes light.
 * Keep the logic in sync with applyTheme below.
 */
export const THEME_INIT_SCRIPT = `(function(){try{var p=localStorage.getItem("${THEME_STORAGE_KEY}");var d=p==="dark"||(p!=="light"&&matchMedia("(prefers-color-scheme: dark)").matches);document.documentElement.dataset.theme=d?"dark":"light";}catch(e){}})();`;

// One module-level store, so every toggle on the page (e.g. admin's sidebar and mobile bar) shares
// the same preference and only one OS-change listener exists.
let preference: ThemePreference | null = null;
const listeners = new Set<() => void>();
let mediaQuery: MediaQueryList | null = null;

function readStored(): ThemePreference {
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    return stored === "light" || stored === "dark" ? stored : "system";
  } catch {
    return "system";
  }
}

function applyTheme() {
  const dark = preference === "dark" || (preference === "system" && !!mediaQuery?.matches);
  document.documentElement.dataset.theme = dark ? "dark" : "light";
}

function subscribe(listener: () => void) {
  if (preference === null) {
    preference = readStored();
    mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    // Only matters while following the system; applyTheme ignores it otherwise.
    mediaQuery.addEventListener("change", applyTheme);
  }
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function setThemePreference(next: ThemePreference) {
  preference = next;
  try {
    if (next === "system") localStorage.removeItem(THEME_STORAGE_KEY);
    else localStorage.setItem(THEME_STORAGE_KEY, next);
  } catch {
    /* storage unavailable: the choice still applies for this page view */
  }
  applyTheme();
  listeners.forEach((l) => l());
}

export function useTheme() {
  // Server and hydration render "system"; the stored value is read once subscribed on the client.
  const current = useSyncExternalStore(
    subscribe,
    () => preference ?? "system",
    () => "system" as ThemePreference,
  );
  return { preference: current, setPreference: setThemePreference };
}
