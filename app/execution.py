"""
Database transaction execution for the transactional pipeline (Issue #10).

This module runs once the slot-filling state machine (Issue #9) has collected
every required slot. It is the only place that reads from or writes to the
bookings table. It is pure SQL and deterministic: no language model is involved
here at all. The state machine decided WHICH action to take and gathered the
inputs; this module carries it out and reports the result.

Two operations:
  check_flight_status -> read: look up the booking and report its flight status.
  change_seat         -> write: look up the booking, verify the requested seat
                         is free on that flight, then update it.

Note the slot/column mapping: the collected slot is called 'seat_number', but
the bookings column is 'seat'. The lookup matches the PNR exactly and the
surname case-insensitively, so "mwangi" and "Mwangi" both resolve.

Every path is guarded: a booking that does not match returns a friendly
"couldn't find it" message rather than an error, so a wrong PNR or surname is a
normal conversational outcome, not a failure.
"""
from __future__ import annotations


def _fmt_departure(dt) -> str:
    """Render a departure timestamp as e.g. '15 Nov 2026, 23:59'."""
    try:
        return dt.strftime("%d %b %Y, %H:%M")
    except Exception:
        return str(dt)


async def _find_booking(db, pnr: str, last_name: str):
    """Return the booking row for this PNR + surname, or None. PNR is matched
    case-insensitively on both sides; surname likewise."""
    return await db.fetchrow(
        "select id, pnr, last_name, first_name, flight_number, origin, "
        "destination, departure_time, seat, status "
        "from bookings "
        "where upper(pnr) = upper($1) and lower(last_name) = lower($2)",
        pnr, last_name,
    )


_NOT_FOUND = (
    "I couldn't find a booking with reference {pnr} under the name {last_name}. "
    "Please double-check the booking reference and surname and try again."
)


async def check_flight_status(db, slots: dict) -> dict:
    booking = await _find_booking(db, slots["pnr"], slots["last_name"])
    if booking is None:
        return {"outcome": "not_found",
                "reply": _NOT_FOUND.format(pnr=slots["pnr"], last_name=slots["last_name"])}

    reply = (
        f"Booking {booking['pnr']} for {booking['first_name']} {booking['last_name']}: "
        f"flight {booking['flight_number']} from {booking['origin']} to {booking['destination']}, "
        f"departing {_fmt_departure(booking['departure_time'])}, seat {booking['seat']}. "
        f"Current status: {booking['status']}."
    )
    return {"outcome": "found", "reply": reply,
            "data": {"flight_number": booking["flight_number"], "status": booking["status"],
                     "seat": booking["seat"]}}


async def change_seat(db, slots: dict) -> dict:
    requested = slots["seat_number"].upper()
    booking = await _find_booking(db, slots["pnr"], slots["last_name"])
    if booking is None:
        return {"outcome": "not_found",
                "reply": _NOT_FOUND.format(pnr=slots["pnr"], last_name=slots["last_name"])}

    current = booking["seat"]
    if current.upper() == requested:
        return {"outcome": "no_change",
                "reply": f"You're already in seat {current} on {booking['flight_number']}."}

    # Business rule: the seat must be free on the same flight. A flight is
    # identified by its number and departure time, so two different departures
    # that reuse a flight number don't collide.
    taken = await db.fetchrow(
        "select 1 from bookings "
        "where flight_number = $1 and departure_time = $2 "
        "and upper(seat) = $3 and id <> $4",
        booking["flight_number"], booking["departure_time"], requested, booking["id"],
    )
    if taken is not None:
        return {"outcome": "seat_taken",
                "reply": f"Seat {requested} is already taken on {booking['flight_number']}. "
                         f"Please choose a different seat."}

    await db.execute("update bookings set seat = $1 where id = $2", requested, booking["id"])
    return {"outcome": "changed",
            "reply": f"Done — I've moved you from seat {current} to {requested} on "
                     f"{booking['flight_number']}.",
            "data": {"from": current, "to": requested, "flight_number": booking["flight_number"]}}


# Dispatch table: intent -> the function that executes it. The state machine
# never chooses a DB action directly; it only names the intent, and this map is
# the single authority on what each intent does.
EXECUTORS = {
    "check_flight_status": check_flight_status,
    "change_seat": change_seat,
}


async def execute_transaction(db, intent: str, slots: dict) -> dict:
    """Run the collected transaction and return {outcome, reply, [data]}."""
    executor = EXECUTORS[intent]
    return await executor(db, slots)