"""
Intent-classification evaluation (answers Research Question iii, Chapter 1).

A labelled, held-out test set of passenger messages is run through the live
router (app.router.classify, margin safeguard on) and, for transactional
messages, through the transactional sub-intent classifier
(app.slot_filling.classify_transactional_intent). It reports:

  * routing accuracy over the three router classes
    (informational, transactional, out_of_scope)
  * per-class precision, recall and F1, macro-F1, and the confusion matrix
  * transactional sub-intent accuracy (check_flight_status vs change_seat)
  * end-to-end transactional intent accuracy: routed transactional AND the
    correct sub-intent chosen (the figure compared with the 90% target)

The test messages were written separately from the router's exemplar phrases.
Before anything runs, the script checks that none of them is an exemplar and
stops if one is, so the test stays held-out.

Usage (repo root, venv active, .env with GEMINI_API_KEY):
    python -m scripts.eval_intent_classification            # Set A
    python -m scripts.eval_intent_classification --set B    # Set B, final test

One Gemini embedding call per message, paced by --delay (default 0.7 s);
96 messages take about two minutes.
"""
from __future__ import annotations

import argparse
import collections
import csv
import sys
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.router import classify
import app.router as router_module
from app.slot_filling import classify_transactional_intent

INF, TX, OOS = "informational", "transactional", "out_of_scope"
STATUS, SEAT = "check_flight_status", "change_seat"

# (message, expected route, expected sub-intent for transactional or None)
TEST_SET = [
    # ---------------- informational: policy questions across the corpus -------
    ("How many kilos can I check in on an economy ticket?", INF, None),
    ("What size of carry-on bag is allowed?", INF, None),
    ("Is a laptop bag counted as part of my hand luggage?", INF, None),
    ("How long before departure does the check-in counter close?", INF, None),
    ("Can I check in online the day before I fly?", INF, None),
    ("Am I allowed to pack a lighter in my suitcase?", INF, None),
    ("Can I carry perfume in my hand luggage?", INF, None),
    ("Does Kenya Airways allow cats on board?", INF, None),
    ("Can a guide dog travel with a blind passenger?", INF, None),
    ("My daughter is 12, does she need an escort to fly alone?", INF, None),
    ("What does the unaccompanied minor service cost?", INF, None),
    ("My grandmother uses a wheelchair, what help is available?", INF, None),
    ("Can I bring my own mobility scooter?", INF, None),
    ("Do babies get their own seat or sit on my lap?", INF, None),
    ("Can I request a cot for my infant on a long flight?", INF, None),
    ("I had an operation last week, can I still fly?", INF, None),
    ("Is there a form my doctor needs to fill before I travel?", INF, None),
    ("I'm 30 weeks pregnant, will I be allowed to board?", INF, None),
    ("What paperwork do I need to enter Kenya?", INF, None),
    ("Is a transit visa needed when connecting through Nairobi?", INF, None),
    ("What are the charges for changing my travel date?", INF, None),
    ("If I cancel my ticket, how long does the refund take?", INF, None),
    ("Do I have to pay to pick a seat in advance?", INF, None),
    ("Who is allowed to sit in the emergency exit row?", INF, None),
    ("What happens if my suitcase is over the weight limit?", INF, None),
    ("Can I take my golf clubs as checked baggage?", INF, None),
    ("My luggage arrived damaged, how do I report it?", INF, None),
    ("How do I trace a bag that didn't arrive?", INF, None),
    ("Can I carry a power bank in checked luggage?", INF, None),
    ("Are e-cigarettes allowed on the plane?", INF, None),
    ("How do I request a vegetarian meal?", INF, None),
    ("How can I contact Kenya Airways customer care?", INF, None),

    # ---------------- transactional: flight status ----------------------------
    ("Is my flight still leaving on time today?", TX, STATUS),
    ("Can you tell me if my flight to London is delayed?", TX, STATUS),
    ("What's the current status of booking ABC123?", TX, STATUS),
    ("Has my flight tomorrow been cancelled?", TX, STATUS),
    ("Please check my booking for me", TX, STATUS),
    ("When does my flight depart? Reference RT9K3L", TX, STATUS),
    ("Is KQ 100 on schedule?", TX, STATUS),
    ("I'd like an update on my flight", TX, STATUS),
    ("Look up my reservation, surname Doe", TX, STATUS),
    ("Is my Nairobi to Dubai flight running late?", TX, STATUS),
    ("Can you confirm my flight details?", TX, STATUS),
    ("What time does my plane take off?", TX, STATUS),
    ("Has my flight been rescheduled?", TX, STATUS),
    ("Give me the latest on my booking", TX, STATUS),
    ("Am I checked in for my flight?", TX, STATUS),
    ("Is there any delay on my booked flight?", TX, STATUS),

    # ---------------- transactional: seat change ------------------------------
    ("I want to change my seat", TX, SEAT),
    ("Please move me to seat 14C", TX, SEAT),
    ("Can I switch to an aisle seat on my booking?", TX, SEAT),
    ("Put me in a window seat please", TX, SEAT),
    ("I'd like a different seat on my flight", TX, SEAT),
    ("Can you reassign my seat to 22A?", TX, SEAT),
    ("I'm not happy with my seat, can I swap it?", TX, SEAT),
    ("Change my seat on booking RT9K3L to 3D", TX, SEAT),
    ("Move me closer to the front of the plane", TX, SEAT),
    ("Can I sit by the window instead?", TX, SEAT),
    ("I need to swap seats so I can sit with my son", TX, SEAT),
    ("Upgrade my seat to an exit row seat", TX, SEAT),
    ("Can you move me to 9F?", TX, SEAT),
    ("I'd rather have an aisle, can you change it?", TX, SEAT),
    ("Book me a different seat on KQ 101", TX, SEAT),
    ("Can I pick another seat for my flight?", TX, SEAT),

    # ---------------- out of scope --------------------------------------------
    ("Are there any flights from Nairobi to Kisumu on Friday?", OOS, None),
    ("How much is a return ticket to Lagos?", OOS, None),
    ("Find me the cheapest flight to Johannesburg next week", OOS, None),
    ("Book me a flight to Zanzibar for the weekend", OOS, None),
    ("Which airlines fly from Mombasa to Dar es Salaam?", OOS, None),
    ("Show me flights to Paris in December", OOS, None),
    ("What's the fare for a business class ticket to Dubai?", OOS, None),
    ("Is there a direct flight from Nairobi to New York?", OOS, None),
    ("Recommend a hotel near JKIA", OOS, None),
    ("Can you book me a taxi from the airport?", OOS, None),
    ("Where can I hire a car in Mombasa?", OOS, None),
    ("What's the weather like in Kisumu today?", OOS, None),
    ("What is the dollar to shilling exchange rate?", OOS, None),
    ("Who won the Premier League last season?", OOS, None),
    ("Tell me a funny joke", OOS, None),
    ("Write me a short poem about the sea", OOS, None),
    ("What is the capital of Australia?", OOS, None),
    ("Help me fix my Python code", OOS, None),
    ("Translate good morning into French", OOS, None),
    ("What's 15 percent of 2,400?", OOS, None),
    ("What time is it in London right now?", OOS, None),
    ("Recommend a good restaurant in Westlands", OOS, None),
    ("What's the latest news in Kenya?", OOS, None),
    ("How do I renew my Kenyan passport?", OOS, None),
    ("Can you order me food?", OOS, None),
    ("What are the best tourist spots in Mombasa?", OOS, None),
    ("Are there cheap flights to Entebbe this month?", OOS, None),
    ("List flights from Nairobi to Accra", OOS, None),
    ("Do any planes go to Cape Town on Sunday?", OOS, None),
    ("What's the price of a ticket from Kisumu to Nairobi?", OOS, None),
    ("Give me the share price of Kenya Airways", OOS, None),
    ("Can you help me write a CV?", OOS, None),
]


# Set B: a second held-out set, written after the baseline run on Set A, used
# only for the final test after any changes. Set A guided the changes, so its
# post-change figures are validation results, not the final test.
TEST_SET_B = [
    # ---------------- informational ----------------
    ("What's the free baggage allowance for business class?", INF, None),
    ("Can I take two cabin bags on board?", INF, None),
    ("When does online check-in close for international flights?", INF, None),
    ("Can I bring liquids through security in my hand luggage?", INF, None),
    ("Are knives allowed in checked baggage?", INF, None),
    ("Can my dog fly in the cargo hold?", INF, None),
    ("Is there an age limit for children travelling without parents?", INF, None),
    ("Who do I call to arrange help for a passenger in a wheelchair?", INF, None),
    ("How old must a baby be to fly?", INF, None),
    ("Can I bring a stroller to the gate?", INF, None),
    ("Do I need a doctor's note to fly with a broken leg?", INF, None),
    ("Can I travel with insulin and needles?", INF, None),
    ("Until which week of pregnancy can I fly with twins?", INF, None),
    ("Do I need an eTA to visit Kenya?", INF, None),
    ("Can I change the name on my ticket?", INF, None),
    ("Is my fare refundable if I cancel?", INF, None),
    ("What is the 24-hour cancellation rule?", INF, None),
    ("Can I choose my seat for free?", INF, None),
    ("Is a surfboard accepted as checked luggage?", INF, None),
    ("How much extra do I pay for an overweight bag?", INF, None),
    ("My bag hasn't come out on the belt, who do I tell?", INF, None),
    ("Can I carry spare lithium batteries?", INF, None),
    ("Are aerosols allowed in hand baggage?", INF, None),
    ("Can I bring a portable oxygen concentrator?", INF, None),
    ("How early should I get to JKIA for an international flight?", INF, None),
    ("Are pets allowed in the cabin on Kenya Airways?", INF, None),
    ("Can my 16-year-old use the unaccompanied minor service?", INF, None),
    ("Is there a fee for wheelchair assistance?", INF, None),
    ("How do I get a special meal for my child?", INF, None),
    ("Can I bring my musical instrument on board?", INF, None),
    ("What happens if I miss the check-in deadline?", INF, None),
    ("Can a pregnant woman travel without a medical certificate?", INF, None),
    # ---------------- transactional: flight status ----------------
    ("Is my flight to Mombasa on time?", TX, STATUS),
    ("Check the status of my booking RT9K3L", TX, STATUS),
    ("Has there been any change to my flight time?", TX, STATUS),
    ("Is my flight tonight delayed?", TX, STATUS),
    ("Can you look up my booking? Surname Mwangi", TX, STATUS),
    ("I want to know if my flight is still on", TX, STATUS),
    ("What's the departure time for my booking?", TX, STATUS),
    ("Is KQ 101 delayed today?", TX, STATUS),
    ("Could you check whether my flight has been cancelled?", TX, STATUS),
    ("Tell me the status of my trip to Dubai", TX, STATUS),
    ("Can you pull up my reservation?", TX, STATUS),
    ("Is my flight boarding on time?", TX, STATUS),
    ("I need my flight details, booking reference QW5D9F", TX, STATUS),
    ("Is everything okay with my flight tomorrow?", TX, STATUS),
    ("When will my flight leave?", TX, STATUS),
    ("Can you verify my booking is still active?", TX, STATUS),
    # ---------------- transactional: seat change ----------------
    ("I'd like to change seats on my flight", TX, SEAT),
    ("Can I move to an aisle?", TX, SEAT),
    ("Please put me in 12A", TX, SEAT),
    ("Switch my seat to a window one", TX, SEAT),
    ("Can you seat me next to my husband?", TX, SEAT),
    ("I want a seat with more legroom", TX, SEAT),
    ("Change my booking's seat to 18D", TX, SEAT),
    ("Could I sit further back in the plane?", TX, SEAT),
    ("Move me to the exit row please", TX, SEAT),
    ("Can I get a different seat number?", TX, SEAT),
    ("Is it possible to switch to 7C?", TX, SEAT),
    ("I don't like where I'm sitting, can you change it?", TX, SEAT),
    ("Swap my seat for one near the front", TX, SEAT),
    ("Can you move me away from the toilets?", TX, SEAT),
    ("I'd like to sit by the window on my flight to London", TX, SEAT),
    ("Assign me seat 30F", TX, SEAT),
    # ---------------- out of scope ----------------
    ("Are there flights from Nairobi to Malindi tomorrow?", OOS, None),
    ("How much does a flight to Kigali cost?", OOS, None),
    ("Find me a cheap ticket to London", OOS, None),
    ("I want to book a flight to Addis Ababa", OOS, None),
    ("What time is the next flight to Mumbai?", OOS, None),
    ("Do you have flights to Bangkok on Monday?", OOS, None),
    ("Which is cheaper, flying to Dubai or Doha?", OOS, None),
    ("Show me flight options to Kinshasa", OOS, None),
    ("Recommend a hotel in Mombasa", OOS, None),
    ("Can you get me an Uber to the airport?", OOS, None),
    ("Where can I rent a car at the airport?", OOS, None),
    ("Will it rain in Nairobi tomorrow?", OOS, None),
    ("What is the euro exchange rate today?", OOS, None),
    ("Who is the president of Kenya?", OOS, None),
    ("Tell me a riddle", OOS, None),
    ("Write a birthday message for my friend", OOS, None),
    ("What is the tallest mountain in Africa?", OOS, None),
    ("Help me with my maths homework", OOS, None),
    ("How do you say thank you in Swahili?", OOS, None),
    ("What's 250 divided by 5?", OOS, None),
    ("Which football team should I support?", OOS, None),
    ("Suggest a nice cafe near the airport", OOS, None),
    ("What's happening in the news today?", OOS, None),
    ("How do I apply for a Kenyan ID card?", OOS, None),
    ("Can you deliver groceries to my house?", OOS, None),
    ("What are the top safari destinations in Kenya?", OOS, None),
    ("Are there flights to Zanzibar this weekend?", OOS, None),
    ("Book me a ticket to Cairo", OOS, None),
    ("What airlines fly to Lusaka?", OOS, None),
    ("How much is a business class ticket to Paris?", OOS, None),
    ("What's the stock price of Safaricom?", OOS, None),
    ("Can you write an email to my boss?", OOS, None),
]


def check_held_out(test_set):
    examples = getattr(router_module, "EXAMPLES", None) or getattr(router_module, "EXEMPLARS", None)
    if not examples:
        print("Could not find the router's exemplar list; skipping the overlap check.")
        return
    norm = lambda s: " ".join(s.lower().replace("’", "'").split()).rstrip("?.!")
    exemplars = {norm(p) for phrases in examples.values() for p in phrases}
    overlap = [m for m, _, _ in test_set if norm(m) in exemplars]
    if overlap:
        print("These test messages are also router exemplars, so the test would not be held-out:")
        for m in overlap:
            print("  ", m)
        sys.exit(2)
    print(f"Held-out check passed: none of the {len(test_set)} messages is a router exemplar.")


def classify_with_retry(text, attempts=4):
    for i in range(attempts):
        try:
            return classify(text)
        except Exception as e:
            if i == attempts - 1:
                raise
            wait = 5 * (i + 1)
            print(f"    (retry in {wait}s: {type(e).__name__})")
            time.sleep(wait)


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--delay", type=float, default=0.7)
    ap.add_argument("--set", choices=["A", "B"], default="A",
                    help="A = baseline/validation set, B = final held-out test set")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    test_set = TEST_SET if args.set == "A" else TEST_SET_B
    if args.out is None:
        args.out = f"intent_eval_set{args.set}.csv"

    a = {m.lower() for m, _, _ in TEST_SET}
    dup = [m for m, _, _ in TEST_SET_B if m.lower() in a]
    if dup:
        print("Set B repeats Set A messages:", dup); sys.exit(2)
    check_held_out(test_set)
    print(f"Evaluating Set {args.set}.")
    counts = collections.Counter(r for _, r, _ in test_set)
    print("Test set: " + ", ".join(f"{k} {v}" for k, v in counts.items()) + "\n")

    rows = []
    for i, (msg, want, want_sub) in enumerate(test_set, 1):
        r = classify_with_retry(msg)
        got = r["route"]
        sub = classify_transactional_intent(msg) if want == TX else None
        rows.append({
            "message": msg, "expected_route": want, "got_route": got,
            "route_correct": got == want,
            "expected_subintent": want_sub or "", "got_subintent": sub or "",
            "subintent_correct": (sub == want_sub) if want == TX else "",
            "biased": r.get("biased", ""),
            "score_informational": round(float(r.get("scores", {}).get(INF, 0)), 3),
            "score_transactional": round(float(r.get("scores", {}).get(TX, 0)), 3),
            "score_out_of_scope": round(float(r.get("scores", {}).get(OOS, 0)), 3),
        })
        if i % 24 == 0:
            print(f"  {i}/{len(test_set)} done")
        time.sleep(args.delay)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    labels = [INF, TX, OOS]
    n = len(rows)
    correct = sum(r["route_correct"] for r in rows)
    print(f"\nRouting accuracy: {correct}/{n} = {100 * correct / n:.1f}%")

    print("\nPer-class precision / recall / F1")
    f1s = []
    for c in labels:
        tp = sum(1 for r in rows if r["expected_route"] == c and r["got_route"] == c)
        fp = sum(1 for r in rows if r["expected_route"] != c and r["got_route"] == c)
        fn = sum(1 for r in rows if r["expected_route"] == c and r["got_route"] != c)
        p, rc, f = prf(tp, fp, fn)
        f1s.append(f)
        print(f"  {c:15} precision {p:.3f}   recall {rc:.3f}   F1 {f:.3f}   (n={counts[c]})")
    print(f"  macro-F1 {sum(f1s) / len(f1s):.3f}")

    print("\nConfusion matrix (rows = expected, columns = predicted)")
    print("  " + " " * 15 + "".join(f"{c[:13]:>15}" for c in labels))
    for e in labels:
        line = "".join(f"{sum(1 for r in rows if r['expected_route'] == e and r['got_route'] == g):>15}" for g in labels)
        print(f"  {e:15}{line}")

    tx = [r for r in rows if r["expected_route"] == TX]
    sub_ok = sum(1 for r in tx if r["subintent_correct"] is True)
    both = sum(1 for r in tx if r["route_correct"] and r["subintent_correct"] is True)
    print(f"\nTransactional sub-intent accuracy (status vs seat): {sub_ok}/{len(tx)} = {100 * sub_ok / len(tx):.1f}%")
    print(f"End-to-end transactional intent accuracy (route AND sub-intent correct): "
          f"{both}/{len(tx)} = {100 * both / len(tx):.1f}%   (target: 90%)")
    biased = sum(1 for r in rows if r["biased"] is True)
    print(f"Margin safeguard fired on {biased}/{n} messages.")

    wrong = [r for r in rows if not r["route_correct"] or r["subintent_correct"] is False]
    if wrong:
        print("\nErrors")
        for r in wrong:
            extra = f", sub-intent {r['got_subintent']}" if r["subintent_correct"] is False else ""
            print(f"  [{r['expected_route']} -> {r['got_route']}{extra}] {r['message']}")
    print(f"\nFull results written to {args.out}")


if __name__ == "__main__":
    main()