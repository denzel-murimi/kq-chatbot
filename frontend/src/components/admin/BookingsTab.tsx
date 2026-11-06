"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { adminApi, AdminAuthError, type Booking } from "@/lib/admin-api";

type Props = { adminKey: string; onAuthError: () => void };

export function BookingsTab({ adminKey, onAuthError }: Props) {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setBookings(await adminApi.bookings(adminKey));
    } catch (e) {
      if (e instanceof AdminAuthError) onAuthError();
      else setError(e instanceof Error ? e.message : "Failed to load bookings.");
    }
  }, [adminKey, onAuthError]);

  useEffect(() => { void load(); }, [load]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-gray-700">Bookings ({bookings.length})</h3>
        <button
          onClick={() => void load()}
          className="flex items-center gap-1.5 rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs font-semibold text-gray-600 transition hover:bg-gray-50"
        >
          <RefreshCw size={14} aria-hidden="true" /> Refresh
        </button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-[11px] uppercase tracking-wider text-gray-500">
              <tr>
                <th className="px-4 py-2 font-semibold">PNR</th>
                <th className="px-4 py-2 font-semibold">Passenger</th>
                <th className="px-4 py-2 font-semibold">Flight</th>
                <th className="px-4 py-2 font-semibold">Route</th>
                <th className="px-4 py-2 font-semibold">Departure</th>
                <th className="px-4 py-2 font-semibold">Seat</th>
                <th className="px-4 py-2 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {bookings.map((b) => (
                <tr key={b.pnr} className="border-t border-gray-100">
                  <td className="whitespace-nowrap px-4 py-2 font-mono font-semibold text-gray-800">{b.pnr}</td>
                  <td className="whitespace-nowrap px-4 py-2 text-gray-700">{b.first_name} {b.last_name}</td>
                  <td className="whitespace-nowrap px-4 py-2 text-gray-700">{b.flight_number}</td>
                  <td className="whitespace-nowrap px-4 py-2 text-gray-600">{b.origin} → {b.destination}</td>
                  <td className="whitespace-nowrap px-4 py-2 text-gray-600">
                    {new Date(b.departure_time).toLocaleString([], {
                      day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
                    })}
                  </td>
                  <td className="px-4 py-2 font-semibold text-gray-800">{b.seat}</td>
                  <td className="px-4 py-2 text-gray-600">{b.status}</td>
                </tr>
              ))}
              {bookings.length === 0 && (
                <tr><td colSpan={7} className="px-4 py-6 text-center text-gray-500">No bookings found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}