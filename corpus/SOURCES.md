# Corpus Sources and Provenance

This knowledge base was compiled from Kenya Airways' official public website for
the Intelligent Passenger Self-Service System. It contains published passenger
policy information only; it holds no personal, confidential, or proprietary data.
The documents were retrieved and lightly edited into clean prose for the
retrieval-augmented generation pipeline. Policies change, so figures should be
re-verified against the live pages before any real-world use.


| File | Topic | Source page |
|---|---|---|
| baggage_checked_allowance.md | Checked baggage limits by route and class | kenya-airways.com /plan/baggage-information/baggage-allowance/ |
| baggage_cabin_handbaggage.md | Cabin and hand baggage limits | kenya-airways.com /plan/baggage-information/hand-baggage/ |
| check_in_times.md | Online and airport check-in deadlines | kenya-airways.com /book-manage/post-booking/check-in/ |
| prohibited_restricted_items.md | Forbidden and restricted items | kenya-airways.com /plan/baggage-information/baggage-security-guidelines/ |
| pets_and_service_animals.md | Pet carriage and service dogs | kenya-airways.com /en-ZA/plan/baggage-information/pet-carriage/ |

## Notes on accuracy and gaps

- Content reflects the official pages as retrieved on the date above. Where a page
  did not state a figure (for example, international airport counter deadlines, or
  baggage drop-off times), the documents do not invent one.
- The checked-baggage per-piece maximum dimension (158 cm total) appeared on the
  source page under a note whose exact scope was ambiguous; it is stated here as a
  general guide and should be confirmed.
- Flight delays, cancellations, and refunds are not yet included: the Conditions
  of Carriage page is largely rendered dynamically and did not return clean text.
  This topic can be added later from the live page or the linked Delay &
  Cancellations and Refunds pages.
- This is a starter corpus intended to build and demonstrate the pipeline. It can
  be expanded with further official pages as the project grows.
# Corpus Expansion — Sources and Provenance

All documents below were drafted from the official Kenya Airways website
(kenya-airways.com). Figures and rules are quoted
as stated on those pages at that date; airline policies and fees change, so
re-verify against the live pages before relying on a specific figure. Where a
page rendered its figures only in JavaScript (fee tables), the document states
the policy qualitatively and directs the reader to confirm current amounts,
rather than stating an unverified number.

| Document (title) | Source page | Accessed |
|---|---|---|
| Unaccompanied Minors | https://www.kenya-airways.com/en/plan/special-care/unaccompanied-minors/ | 2026-11-07 |
| Special Assistance and Reduced Mobility | https://www.kenya-airways.com/en/plan/special-care/reduced-mobility/ | 2026-11-07 |
| Travelling with Infants and Children | https://www.kenya-airways.com/en/plan/special-care/infant-toddlers/ | 2026-11-07 |
| Medical Clearance and Travelling with Medical Needs | https://www.kenya-airways.com/en/plan/special-care/medical-special-support/ | 2026-11-07 |
| Travelling While Pregnant | https://www.kenya-airways.com/en/plan/special-care/expectant-mothers/ | 2026-11-07 |
| Travel Documents and Visa Requirements | https://www.kenya-airways.com/en/plan/travel-information/travel-requirements/ | 2026-11-07 |
| Changing Your Booking | https://www.kenya-airways.com/en/book-manage/manage-booking/change-booking/ | 2026-11-07 |
| Cancellations and Refunds | https://www.kenya-airways.com/en/policies/24-hours-refund-policy/ ; https://www.kenya-airways.com/en/book-manage/manage-booking/request-for-your-refund/ | 2026-11-07 |
| Seat Selection | https://www.kenya-airways.com/en/experience/seat-selection/seat-terms/ | 2026-11-07 |
| Excess, Overweight and Oversized Baggage | https://www.kenya-airways.com/en/policies/optional-fees/ ; https://www.kenya-airways.com/en/plan/baggage-information/special-baggage/ | 2026-11-07 |
| Delayed, Lost or Damaged Baggage | https://www.kenya-airways.com/en/plan/baggage-information/conditions-of-carriage-baggage/ | 2026-11-07 |
| Batteries, Power Banks and Electronic Devices | https://www.kenya-airways.com/en-us/plan/baggage-information/baggage-restrictions/ | 2026-11-07 |

## Notes on overlap and figures
- "Batteries, Power Banks and Electronic Devices" overlaps your existing prohibited/restricted-items document. Keep each fact in one place: either merge the battery guidance into the existing document or keep this as the dedicated battery document and trim duplicates from the other, so the two never state different rules.
- Excess/overweight/oversize baggage fees, booking-change fees and exact lithium/power-bank watt-hour limits were not exposed as plain text on the site; those documents describe the policy and point the passenger to confirm current figures. Add the exact numbers if you obtain them from the live site.
- Several rules are specific to flights to or from the United States (the 24-hour refund, the 10-day pregnancy letter, the lighter ban); these are stated as US-route-specific in the documents.
