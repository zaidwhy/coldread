"""COLD READ - two-seat live profiling chat.

Two people, both consenting, hold a conversation through this. After every
message, the seat that sent it gets re-profiled from all the words they have
typed so far, and both seats watch both profiles fill in.

The thresholds below are not invented - they are the measured result in
RESULT.md: age band becomes inferable around 100 words, gender around 800,
star sign never (it is the control). One session at a time, kept in memory.

Usage: python server.py
Then open http://127.0.0.1:8420/?seat=a in one window and
http://127.0.0.1:8420/?seat=b in another.
"""

import json
import re
import threading
from pathlib import Path

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

ROOT = Path(__file__).parent
INDEX_HTML = ROOT / "index.html"

# localhost resolves IPv6 first on this machine and hangs to timeout.
ENDPOINT = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen2.5:7b-instruct"

# Measured in the sweep (RESULT.md), not chosen for this app.
AGE_THRESHOLD = 100
GENDER_THRESHOLD = 800

SEATS = ("a", "b")

GENDERS = ["male", "female"]
BANDS = ["13-17", "23-27", "33-47"]
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SYSTEM = (
    "You are a forensic profiler. Given text a person has written you "
    "estimate their attributes. You must always commit to a specific "
    "answer for every field, even when uncertain. Never refuse and never "
    "answer 'unknown'. Reply with JSON only."
)

PROMPT = """Text written by this person so far:
\"\"\"
{text}
\"\"\"

Infer the author. Reply with exactly this JSON and nothing else:
{{"gender": {genders}, "age_band": {bands}, "sign": one of {signs}, \
"occupation_guess": "<your best short guess>", \
"anxious_about": "<your best short guess of what they seem anxious about>"}}"""


def ask_model(text, timeout=120):
    prompt = PROMPT.format(
        text=text,
        genders=" or ".join(f'"{g}"' for g in GENDERS),
        bands=" or ".join(f'"{b}"' for b in BANDS),
        signs=", ".join(SIGNS),
    )
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
    }
    r = requests.post(ENDPOINT, json=body, timeout=timeout)
    r.raise_for_status()
    return r.json()["message"]["content"]


def parse_reply(raw):
    """Pull the first JSON object out of a model reply."""
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def new_session():
    return {
        "consent": {"a": False, "b": False},
        "messages": [],
        "profiles": {"a": None, "b": None},
        "errors": {"a": None, "b": None},
    }


SESSION = new_session()
LOCK = threading.Lock()

app = FastAPI()


class ConsentBody(BaseModel):
    seat: str


class MessageBody(BaseModel):
    seat: str
    text: str


def check_seat(seat):
    if seat not in SEATS:
        raise HTTPException(400, "seat must be 'a' or 'b'")


def seat_word_count(seat):
    return sum(len(m["text"].split()) for m in SESSION["messages"] if m["seat"] == seat)


def seat_text(seat):
    return " ".join(m["text"] for m in SESSION["messages"] if m["seat"] == seat)


def drain_text(word_count):
    if word_count < AGE_THRESHOLD:
        return f"anonymous for {AGE_THRESHOLD - word_count} more words"
    if word_count < GENDER_THRESHOLD:
        return f"anonymous for {GENDER_THRESHOLD - word_count} more words"
    return "as known as this gets"


def seat_view(seat):
    word_count = seat_word_count(seat)
    return {
        "seat": seat,
        "word_count": word_count,
        "profile": SESSION["profiles"][seat],
        "error": SESSION["errors"][seat],
        # Below 100 words the sweep measured accuracy BELOW chance, not just
        # low - the model is confidently wrong, not merely uninformed.
        "below_chance": word_count < AGE_THRESHOLD,
        "age_inferable": word_count >= AGE_THRESHOLD,
        "gender_inferable": word_count >= GENDER_THRESHOLD,
        "drain": drain_text(word_count),
    }


@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML.read_text(encoding="utf-8")


@app.get("/api/state")
def state():
    with LOCK:
        both = SESSION["consent"]["a"] and SESSION["consent"]["b"]
        return {
            "consent": dict(SESSION["consent"]),
            "both_consented": both,
            "messages": list(SESSION["messages"]),
            "seats": {s: seat_view(s) for s in SEATS},
        }


@app.post("/api/consent")
def consent(body: ConsentBody):
    check_seat(body.seat)
    with LOCK:
        SESSION["consent"][body.seat] = True
        both = SESSION["consent"]["a"] and SESSION["consent"]["b"]
    return {"ok": True, "both_consented": both}


@app.post("/api/message")
def message(body: MessageBody):
    check_seat(body.seat)
    text = body.text.strip()
    if not text:
        raise HTTPException(400, "empty message")

    with LOCK:
        if not (SESSION["consent"]["a"] and SESSION["consent"]["b"]):
            raise HTTPException(403, "both seats must consent before the session starts")

        SESSION["messages"].append({"seat": body.seat, "text": text})
        full_text = seat_text(body.seat)

        try:
            raw = ask_model(full_text)
            pred = parse_reply(raw)
            if pred:
                SESSION["profiles"][body.seat] = pred
                SESSION["errors"][body.seat] = None
            else:
                SESSION["errors"][body.seat] = f"unparsed reply: {raw[:200]}"
        except Exception as exc:
            SESSION["errors"][body.seat] = f"{type(exc).__name__}: {exc}"

        return {"ok": True, "seats": {s: seat_view(s) for s in SEATS}}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8420)
