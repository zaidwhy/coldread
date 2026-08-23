"""One-off verification script - drives the running server as two real seats.

Not part of the app. Run with the server already started (python server.py),
then: python verify_run.py
"""

import json

import requests

BASE = "http://127.0.0.1:8420"

A_MESSAGES = [
    "hey, glad we're finally doing this. work has been insane lately.",
    "I've been pulling long nights trying to get a release out the door "
    "before the deadline and honestly I am running on fumes at this point.",
    "my manager keeps adding scope to the project and I do not know how "
    "to push back without sounding like I am complaining all the time.",
    "outside of work I mostly just want to sleep but I also feel guilty "
    "for not exercising or seeing my friends as much as I used to.",
    "I guess I am worried that if I do not deliver this on time it will "
    "reflect badly on me during the next review cycle, that is the honest "
    "thing keeping me up.",
    "anyway enough about that, how has your week been going, anything "
    "interesting happen on your end lately or is it the same grind.",
]

B_MESSAGES = [
    "honestly not bad, I finally finished a big paper I was writing.",
    "it took forever because my advisor kept asking for another round of "
    "revisions and I was starting to lose confidence in the whole thing.",
]


def post(path, payload):
    r = requests.post(f"{BASE}{path}", json=payload, timeout=180)
    r.raise_for_status()
    return r.json()


def get_state():
    r = requests.get(f"{BASE}/api/state", timeout=30)
    r.raise_for_status()
    return r.json()


def main():
    print("== consenting both seats ==")
    print(post("/api/consent", {"seat": "a"}))
    print(post("/api/consent", {"seat": "b"}))

    state = get_state()
    print("both_consented:", state["both_consented"])
    assert state["both_consented"]

    print("\n== seat a sends messages, crossing the 100-word threshold ==")
    for i, text in enumerate(A_MESSAGES, 1):
        result = post("/api/message", {"seat": "a", "text": text})
        va = result["seats"]["a"]
        print(f"a[{i}] words={va['word_count']} drain='{va['drain']}' "
              f"age_inferable={va['age_inferable']} gender_inferable={va['gender_inferable']} "
              f"below_chance={va['below_chance']}")
        print(f"       profile={json.dumps(va['profile'])}")
        if va["error"]:
            print("       ERROR:", va["error"])

    print("\n== seat b sends a couple of messages ==")
    for i, text in enumerate(B_MESSAGES, 1):
        result = post("/api/message", {"seat": "b", "text": text})
        vb = result["seats"]["b"]
        print(f"b[{i}] words={vb['word_count']} drain='{vb['drain']}' "
              f"age_inferable={vb['age_inferable']} gender_inferable={vb['gender_inferable']} "
              f"below_chance={vb['below_chance']}")
        print(f"       profile={json.dumps(vb['profile'])}")
        if vb["error"]:
            print("       ERROR:", vb["error"])

    print("\n== final state check ==")
    state = get_state()
    print("message count:", len(state["messages"]))
    for seat in ("a", "b"):
        v = state["seats"][seat]
        print(f"seat {seat}: words={v['word_count']} "
              f"age_inferable={v['age_inferable']} gender_inferable={v['gender_inferable']} "
              f"drain='{v['drain']}'")
        print(f"  profile={json.dumps(v['profile'])}")
        assert v["profile"] is not None, f"seat {seat} never got a profile"
        assert "sign" in v["profile"], f"seat {seat} profile missing sign"

    va = state["seats"]["a"]
    assert va["word_count"] >= 100, "seat a should have crossed 100 words"
    assert va["age_inferable"], "seat a should be past the age threshold"
    assert not va["gender_inferable"], "seat a should not be past 800 words yet"

    print("\nALL CHECKS PASSED")


if __name__ == "__main__":
    main()
