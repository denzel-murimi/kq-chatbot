"use client";

import { useCallback, useEffect, useState } from "react";

// Holds the admin key for the session only. sessionStorage keeps it across page
// navigations within the tab but clears when the tab closes, and it is never
// part of the build. All reads/writes are guarded for private-window and
// storage-disabled cases.
const STORAGE_KEY = "kq-admin-key";

export function useAdminKey() {
  const [key, setKeyState] = useState("");

  // Read once on mount (client only), so the server and first client render match.
  useEffect(() => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY);
      if (stored) setKeyState(stored);
    } catch {
      /* storage unavailable — stay locked */
    }
  }, []);

  const setKey = useCallback((value: string) => {
    try {
      sessionStorage.setItem(STORAGE_KEY, value);
    } catch {
      /* ignore */
    }
    setKeyState(value);
  }, []);

  const clearKey = useCallback(() => {
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      /* ignore */
    }
    setKeyState("");
  }, []);

  return { key, setKey, clearKey };
}