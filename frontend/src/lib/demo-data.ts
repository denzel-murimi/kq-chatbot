// Simulated passenger and booking for the dashboard. The proposal commits to simulated data only.
// When the bookings table is seeded, insert this exact record so the PNR on screen works in the chat.
// Keep the date in the future of your demo. The times are consistent: 09:30 EAT (UTC+3) plus 8h 45m
// lands at 15:15 GMT in December.

export type FlightPoint = {
  code: string;
  city: string;
  airport: string;
  when: string;
};

export type Flight = {
  number: string;
  pnr: string;
  status: string;
  duration: string;
  seat: string;
  cabin: string;
  from: FlightPoint;
  to: FlightPoint;
};

export const DEMO_PASSENGER = { firstName: "John", lastName: "Doe" };

export const DEMO_FLIGHT: Flight = {
  number: "KQ 100",
  pnr: "ABC123",
  status: "On time",
  duration: "8h 45m",
  seat: "12A",
  cabin: "Economy",
  from: { code: "NBO", city: "Nairobi", airport: "Jomo Kenyatta Intl.", when: "18 Dec 2026 • 09:30 EAT" },
  to: { code: "LHR", city: "London", airport: "Heathrow Airport", when: "18 Dec 2026 • 15:15 GMT" },
};
