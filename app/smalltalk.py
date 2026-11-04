"""
Lightweight social layer ahead of the semantic router. Greetings, thanks and
farewells are a small, closed set — a deterministic rule handles them more
reliably than the embedding router, which otherwise lumps them in with
out-of-scope requests. English only, matching the project scope. detect()
returns a short reply for a pure pleasantry, or None to let the router handle
the message normally.
"""
from __future__ import annotations
import random, re

_GREETING = {"hi", "hello", "hey", "hiya", "howdy", "hey there", "hi there",
             "hello there", "good morning", "good afternoon", "good evening",
             "how are you", "how are you doing", "hows it going", "how is it going",
             "hey how are you", "hi how are you", "hello how are you"}
_THANKS = {"thanks", "thank you", "thanks a lot", "thank you so much", "thankyou",
           "many thanks", "cheers", "much appreciated", "appreciate it", "thx", "ty"}
_FAREWELL = {"bye", "goodbye", "good bye", "see you", "see ya", "thats all",
             "that is all", "no thanks", "nothing else", "im good", "i am good"}

_REPLIES = {
    "greeting": ["Hello! How can I help with your trip today — baggage, check-in, or your booking?",
                 "Hi there! Ask me about Kenya Airways policies or your booking whenever you're ready."],
    "thanks":   ["You're welcome! Anything else about your trip?",
                 "Happy to help! Is there anything else you'd like to check?"],
    "farewell": ["Safe travels! ✈️", "Take care — reach out any time you need a hand with your trip."],
}

def _norm(message: str) -> str:
    return re.sub(r"[^a-z\s]", "", message.lower()).strip()

def detect(message: str) -> str | None:
    text = _norm(message)
    if not text or len(text.split()) > 5:   # only short, pure pleasantries
        return None
    for bucket, phrases in (("greeting", _GREETING), ("thanks", _THANKS), ("farewell", _FAREWELL)):
        if text in phrases:
            return random.choice(_REPLIES[bucket])
    return None