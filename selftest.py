#!/usr/bin/env python3
"""Build a whole payload with the hub stubbed out.

Two crashes reached the installed package today — a local shadowing a source
function, and a block spliced out by position — and both were invisible to
`ast.parse` and to `leo packages validate`, because both are about names
RESOLVING at run time. Nothing short of calling payload() finds them, so
this calls payload().
"""
import ast, importlib.util, json, os, sys, tempfile
os.environ["LEO_DATA_DIR"] = tempfile.mkdtemp(prefix="today-selftest-")
from datetime import datetime, timedelta

spec = importlib.util.spec_from_loader("today", loader=None)
m = importlib.util.module_from_spec(spec); sys.modules["today"] = m
src = open("leo-today").read().replace('if __name__ == "__main__":\n    main()', '')
exec(compile(src, "leo-today", "exec"), m.__dict__)

# No module-level function may be shadowed by a local anywhere.
tree = ast.parse(src)
top = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
shadow = {f"{fn.name}() binds {n.id!r}" for fn in tree.body if isinstance(fn, ast.FunctionDef)
          for n in ast.walk(fn) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and n.id in top}
assert not shadow, "shadowed module functions: " + "; ".join(sorted(shadow))

now = datetime.now().astimezone()
iso = lambda h, mi=0, d=0: (now.replace(hour=h, minute=mi, second=0, microsecond=0)
                            + timedelta(days=d)).isoformat()
CAL = {"events": [
    {"id": "1", "title": "Engineering Product Meeting", "start": iso(8), "end": iso(9), "calendar": "Work"},
    {"id": "2", "title": "Mike surgery", "start": (now.date()).isoformat(), "calendar": "Family"},
    {"id": "3", "title": "Weekly Sales Meeting", "start": iso(10), "end": iso(11), "calendar": "Work"},
    {"id": "4", "title": "Flight to Austin", "start": iso(8, 0, 1), "end": iso(11, 0, 1), "calendar": "Work"}]}
REM = {"items": [
    {"id": "r1", "title": "Renew the passport for Austin", "due": iso(9, 0, -4)},
    {"id": "r2", "title": "Fix light switch", "due": iso(9, 0, -155)},
    {"id": "r3", "title": "Book the Austin flights", "due": iso(9)}]}
FEED = {"items": [{"id": "f1", "title": "Amex is running hot", "chat_summary": "$2,341 this week.",
                   "created_at": now.isoformat()}]}
INBOX = [{"from": "Maya Chen <maya@acme.com>", "subject": "Austin itinerary — need your dates",
          "is_read": False, "id": "m1"},
         {"from": "Newegg <news@email1.newegg.com>", "subject": "Black Friday Sales", "is_read": False, "id": "m2"}]
HOUSE = [{"available": True, "entity_id": "lock.front_door", "friendly_name": "Front Door", "state": "unlocked"}]

m.acting = lambda g: "acting-token"
COSTS = {"data": {"spent_usd": 137.42, "projected_usd": 179.21, "daily_run_rate_usd": 5.97}}
JOBS = {"data": [{"id": "j1", "name": "Nightly release", "enabled": True,
                  "last_status": "failed", "last_run_at": iso(11, 15, -1)},
                 {"id": "j2", "name": "Gmail sync", "enabled": True, "last_status": "success"}]}
RELS = {"releases": [{"id": "r1", "version": "1.4.0"}]}
LOCS = {"data": [{"user_id": "u1", "address": "3 Maple St, Austin", "recorded_at": iso(14, 50)}]}
PEOPLE = {"data": [{"id": "u1", "name": "Scott"}]}

def _graph(path, token=None, **kw):
    if path.startswith("calendar"):   return CAL
    if path.startswith("reminders"):  return REM
    if path.startswith("feed"):       return FEED
    if path.startswith("costs"):      return COSTS
    if path.startswith("scheduler"):  return JOBS
    if path.startswith("releases"):   return RELS
    if path.startswith("locations"):  return LOCS
    if path.startswith("people"):     return PEOPLE
    raise m.Gap(f"no stub for {path}")

m.graph = _graph
m.tool = lambda name, args, tok: (
    json.dumps(INBOX) if name == "email" else
    json.dumps(HOUSE) if name == "home_assistant" else
    json.dumps({"total_spending": 2341.0,
                "categories": [{"category_name": "Travel", "total": 980.0}]}) if name == "finance" else
    "Cloudy. 5° now, 2° / 7° today.")
m.ask_claude = lambda *a, **k: json.dumps(
    {"headline": "Three meetings done, afternoon clear.",
     "focus": {"what": "Answer Maya", "why": "She has asked twice and you fly tomorrow."},
     "notes": [{"what": "Flight at 08:00", "why": "Earlier than your usual start."}],
     "mood": "busy"})
m.nudge = lambda: None

d = m.payload("grant", "selftest")
m.write_brief("selftest", m.digest_of([], []), "ctx")   # exercise the model path too
d = m.payload("grant", "selftest")

for key in ("strip", "at", "now", "rail", "loose", "suggestions", "keys"):
    assert key in d, f"payload is missing {key!r}"
print("payload keys :", len(d))
print("strip        :", " ".join((b["label"] or "·") for b in d["strip"]))
print("window       :", d["strip_from"], "→", d["strip_to"], "|", d["strip_note"], "| now", d["at"]["label"])
print("hero         :", d["now"]["lead"], d["now"]["time"], "|", d["now"]["title"][:34])
print("rail         :", [(r["time"], r["title"][:22]) for r in d["rail"]])
print("threads      :", [(t["title"], t["clock"], len(t["strands"])) for t in d.get("threads", [])]
      or d.get("no_threads", "")[:70])
print("loose        :", [(x["what"][:26], x["when"]) for x in d["loose"]])
print("house        :", [h["what"] for h in d.get("house", [])])
print("weather      :", d.get("weather", {}).get("temp"), d.get("weather", {}).get("range"))
print("brief        :", (d.get("brief") or {}).get("headline", "(none)")[:60],
      "| focus:", ((d.get("brief") or {}).get("focus") or {}).get("what", "")[:30])
print("money        :", (d.get("money") or {}).get("amount"), "|", (d.get("money") or {}).get("note", "")[:40])
print("leo cost     :", (d.get("spend") or {}).get("amount"), "|", (d.get("spend") or {}).get("note", "")[:46])
print("around you   :", [h["what"] for h in d.get("house", [])])
print("gaps         :", [g["id"] for g in d.get("gaps", [])] or "none")
assert not d.get("gaps"), "every stubbed source should have answered"

# --- the action channel ----------------------------------------------------
# `ui_action` is what a press reaches. It was added with no test and the first
# thing a test found was that it answers from a context file the page writes,
# so a press before a draw is a real state and not a crash.
assert m.ui_action("nope", {}, "selftest")["ok"] is False, "an unknown action must refuse"

# The query string is the channel, because `path` is the half of a descriptor
# action the hub templates. Parse it the way the handler does, including a
# question with the two characters that would break a naive split.
from urllib.parse import urlsplit, parse_qs, quote
hairy = "What about A & B? 50% done"
url = "/leo/ui/action?name=ask&text=" + quote(hairy, safe="")
sp = urlsplit(url)
q = {k: v[0] for k, v in parse_qs(sp.query, keep_blank_values=True).items()}
assert sp.path == "/leo/ui/action", sp.path
assert q.pop("name") == "ask", q
assert q == {"text": hairy}, q
print("query        :", hairy, "survived & and %")

assert m.ui_action("ask", {"text": ""}, "selftest")["ok"] is False, "an empty question must refuse"

import time
answered = {}
m.ask_claude = lambda *a, **k: "The nightly release. It has been failing since Saturday."
m.nudge = lambda: answered.setdefault("nudged", True)
assert m.ui_action("ask", {"text": "What should I do first?"}, "selftest")["ok"], "ask refused"
for _ in range(100):
    got, pending = m.answer_for("selftest", now)
    if got:
        break
    time.sleep(0.05)
assert got, "no answer was ever filed"
assert got["question"] == "What should I do first?", got
assert "nightly release" in got["text"], got
assert not got["failed"], got
assert answered.get("nudged"), "the open page was never told"
print("ask          :", got["question"], "->", got["text"][:40], "|", got["age"])

# A model that refuses must leave a sentence, not an empty card.
def boom(*a, **k):
    raise m.Gap("the hub refused the model call (503)")
m.ask_claude = boom
m.ui_action("ask", {"text": "And then?"}, "selftest")
for _ in range(100):
    got, _p = m.answer_for("selftest", now)
    if got and got["question"] == "And then?":
        break
    time.sleep(0.05)
assert got["failed"], "a refused call must say so"
print("ask refused  :", got["failed"])

# --- telling it it is wrong ------------------------------------------------
# A correction is about the WRITER, so it has to reach the next briefing and
# every one after it — a note that only fixes the briefing it was filed
# against teaches the person that saying so is pointless.
assert m.ui_action("correct", {"text": ""}, "selftest")["ok"] is False, "empty correction must refuse"
assert m.fixes("selftest") == [], "started dirty"
assert m.ui_action("correct", {"text": "Mike's surgery is an all-day thing, never a 9am meeting"},
                   "selftest")["ok"]
assert m.ui_action("correct", {"text": "Never mention model spend; I read the card"}, "selftest")["ok"]
m.ui_action("correct", {"text": "NEVER MENTION MODEL SPEND; I READ THE CARD"}, "selftest")
told = m.fixes("selftest")
assert len(told) == 2, f"a correction was stored twice in different case: {told}"

seen = {}
m.ask_claude = lambda system, turns, **k: seen.setdefault("system", system) and "" or json.dumps(
    {"headline": "h", "focus": {"what": "f", "why": ""}, "mood": "calm"})
m.write_brief("selftest", "k", "CONTEXT")
assert "CORRECTED YOU" in seen["system"], "corrections never reached the writer"
assert "all-day thing" in seen["system"], seen["system"][-400:]
assert seen["system"].index("CORRECTED YOU") > seen["system"].index("mood"), \
    "corrections must come LAST, nearest the request"
print("corrections  :", len(told), "standing, and they reach the writer")

m.ui_action("uncorrect", {"id": told[0]["id"]}, "selftest")
assert len(m.fixes("selftest")) == 1, "uncorrect did not remove exactly one"
print("uncorrect    : one removed, one left")

# A briefing must not carry notes any more — four shipped and every one
# restated a row drawn elsewhere on the page.
m.ask_claude = lambda *a, **k: json.dumps(
    {"headline": "h", "focus": {"what": "f", "why": ""},
     "notes": [{"what": "n", "why": "w"}], "mood": "calm"})
m.write_brief("selftest", "k2", "CONTEXT")
d2 = m.payload("grant", "selftest")
assert "notes" not in (d2.get("brief") or {}), "notes came back"
print("brief        : headline + focus, no notes")

assert m.ui_action("clear", {}, "selftest")["ok"]
assert m.answer_for("selftest", now) == (None, ""), "clear left something behind"
print("clear        : nothing left")

print("\nOK — a whole payload built with the hub stubbed out, and the action channel answers.")
