"""
Manual check for entity extraction (Issue #8). Runs the regex extractor (no
model) and the surname extractor (one Groq call each) over sample transactional
messages.

Usage (repo root, venv active, .env with GROQ_API_KEY):
    python -m scripts.try_entities
"""
from dotenv import load_dotenv

from app.entities import extract_structured, extract_surname

load_dotenv()

MESSAGES = [
    "I want to change my seat to 14C, booking RT9K3L, surname Mwangi",
    "check my flight status, PNR ABC123, last name Doe",
    "move me to seat 2A",                       # no PNR / surname yet
    "my name is Wanjiru and my reference is ZN4P8Q",
    "is KQ100 on time",                         # no surname present -> None
]

for m in MESSAGES:
    structured = extract_structured(m)
    surname = extract_surname(m)
    print(f"\nMSG: {m}")
    print(f"   structured: {structured}")
    print(f"   surname:    {surname}")
