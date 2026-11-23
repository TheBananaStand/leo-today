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
m.graph = lambda path, token=None, **kw: (
    CAL if path.startswith("calendar") else REM if path.startswith("reminders") else FEED)
m.tool = lambda name, args, tok: (
    json.dumps(INBOX) if name == "email" else
    json.dumps(HOUSE) if name == "home_assistant" else
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
print("gaps         :", [g["id"] for g in d.get("gaps", [])] or "none")
print("\nOK — a whole payload built with the hub stubbed out.")
