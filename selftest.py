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
          "snippet": "Can you confirm which days you are in town?", "is_read": False, "id": "m1"},
         {"from": "Newegg <Promo@promo.newegg.com>", "subject": "Black Friday Sales",
          "snippet": "Faster loads, smoother frames", "is_read": False, "id": "m2"},
         {"from": "Wells Fargo <WF@mail17.wellsfargo.com>", "subject": "Your auto loan payment is past due",
          "snippet": "For account ending in 2564", "is_read": True, "id": "m3"},
         {"from": "katie@patiokitsdirect.com", "subject": "What Tools do you need?",
          "snippet": "are you still interested in a Patio Cover Kit?", "is_read": False, "id": "m4"}]
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
    (json.dumps(INBOX) if not args.get("offset") else "No messages in inbox.") if name == "email" else
    json.dumps(HOUSE) if name == "home_assistant" else
    json.dumps({"total_spending": 2341.0,
                "categories": [{"category_name": "Travel", "total": 980.0}]}) if name == "finance" else
    "Cloudy. 5° now, 2° / 7° today.")
FIRST = {"focus": ["Auto loan payment is past due — pay it."],
         "next": ["Flight to Austin, tomorrow 08:00."],
         "place": [{"id": "mm1", "new": "Austin trip"}, {"id": "tr1", "new": "Austin trip"},
                   {"id": "tr3", "new": "Austin trip"}, {"id": "e4", "new": "austin trip"},
                   {"id": "ghost", "new": "Austin trip"},
                   {"id": "mm3", "new": "Auto loan past due"},
                   {"id": "mm2", "to": "noise"}, {"id": "mm4", "to": "noise"},
                   {"id": "tr2", "to": "backlog"},
                   {"id": "e2", "to": "background"}],
         "states": {"Austin trip": "Flying tomorrow; passport and dates still open.",
                    "Auto loan past due": "Wells Fargo says the payment is late.",
                    "Backlog": "One chore, five months old."}}
m.ask_claude = lambda *a, **k: json.dumps(FIRST)
m.nudge = lambda: None

d = m.payload("grant", "selftest")
m.write_brief("selftest", m.digest_of([], []), "ctx")   # exercise the model path too
d = m.payload("grant", "selftest")

import time
for _ in range(100):                     # the grouping is written on a thread
    d = m.payload("grant", "selftest")
    if any(x["title"] == "Austin trip" and x["state"] for x in d.get("subjects", [])):
        break
    time.sleep(0.05)
subs = d["subjects"]
print("brief        :", [f["text"] for f in d["brief"]["focus"]], "|", [n["text"] for n in d["brief"]["next"]])
for sub in subs:
    print("subject      :", sub["id"], sub["title"], "—", sub["state"][:34], "|", [r["what"][:20] for r in sub["rows"]])
named = {sub["title"]: sub for sub in subs}
austin = named["Austin trip"]
assert {r["iid"] for r in austin["rows"]} == {"mm1", "tr1", "tr3", "e4"}, \
    "a subject must hold a message, reminders AND an event — one title whatever its case, and no invented id"
assert austin["state"].startswith("Flying tomorrow"), "a new subject's state is filed under its id"
every = [r["iid"] for sub in subs for r in sub["rows"]]
assert len(every) == len(set(every)), "an item is in two subjects"
# THE INBOX. Judged by what it says: the bank's notice came from a bulk
# subdomain and is the most important thing here; the promotion and the
# vendor's follow-up never reach the page, in any subject, under any name.
assert [r["iid"] for r in named["Auto loan past due"]["rows"]] == ["mm3"], "the past-due notice must be a subject"
assert "mm2" not in every and "mm4" not in every, "a promotion or a sales follow-up is on the page"
assert not any("Newegg" in r["what"] or "patiokits" in r["what"].lower() for sub in subs for r in sub["rows"])
assert subs[-1]["id"] == "backlog" and [r["iid"] for r in subs[-1]["rows"]] == ["tr2"], "the backlog sits last"
# Under the lock, because that is how PRODUCTION calls it: `apply_places` has
# exactly one caller (leo-today:1112) and it is already inside
# `with _regen_lock:`. Called bare here, the write and the read either side of
# it race the background organiser writing the same record — measured at ~12%
# of runs across these two assertions. The lock is not reentrant, so the fix
# cannot go inside `apply_places` without deadlocking its only caller; it
# belongs here, where the test is the one skipping it.
with m._regen_lock:
    m.apply_places("selftest", [{"id": "mzz", "to": "backlog"}, {"id": "tzz", "to": "noise"}], {"mzz", "tzz"})
    _r = m.load_subjects("selftest")
assert "mzz" in _r["background"] and "tzz" in _r["background"] and "tzz" not in _r["noise"], \
    "mail is never a chore, and only mail can be spam"
assert subs[-1]["real"] == "", "a pile cannot be swept"
# What the model SKIPPED is not hidden. The first real run placed 6 of 45 and
# an earlier rule sent the other 39 to the background — a friend's surgery
# among them. A skipped item stays on the page under "New", in the open.
with m._regen_lock:          # same race, same reason
    rec = m.load_subjects("selftest")
assert {"mm2", "mm4"} <= set(rec["noise"]) and "e2" in rec["background"]
skipped = [r["iid"] for r in subs[0]["rows"]] if subs[0]["id"] == "new" else []
assert skipped and not set(skipped) & set(rec["background"]), "what the model skipped was hidden instead of shown"
assert all(not i.startswith("mm") for i in skipped), "unjudged MAIL must never be shown"
assert next(t for t in d["tiles"] if t["id"] == "mail")["n"] == "2", "the Mail tile counts mail that MATTERS"
ids = [r["id"] for sub in subs for r in sub["rows"]]
assert len(ids) == len(set(ids)), "two rows share an element id"
routes = {r["iid"]: r["route"] for sub in subs for r in sub["rows"]}
assert routes["mm1"] == "/inbox?selectedId=m1" and routes["e4"].startswith("/calendar?day=") and routes["tr1"] == "/reminders"
assert all(sub["rows"][-1]["last"] == "1" for sub in subs)
assert not d.get("gaps_line"), "every stubbed source should have answered"
# `now` is whichever timed event is next from the REAL clock, so a hardcoded
# title made this assertion true only between ~09:00 and midnight: run it at
# 02:10 and today's 08:00 "Engineering Product Meeting" is genuinely next,
# not tomorrow's flight. It failed for that reason on 2026-11-24 and the
# failure text named no hour, so it read as a regression in `payload`.
# Assert the PROPERTY — now is the next timed event — instead of the hour the
# test was written in.
_timed = sorted((e for e in CAL["events"] if e.get("end")), key=lambda e: e["start"])
_next = next((e["title"] for e in _timed if e["start"] > now.isoformat()), None)
assert _next, "the fixture has no event ahead of the clock, so `now` is untestable"
assert d["rail"] and d["now"]["title"] == _next and d["rail"][0]["first"] == "1", (
    f'now={d["now"]["title"]!r}, expected {_next!r} at {now:%H:%M}')
assert m._scene.split("-")[1] == ("day" if 7 <= now.hour < 18 else "night"), m._scene

# Mail is never drawn before it is judged: a message that has just arrived
# and is still being filed must not appear under "New".
m.ask_claude = lambda *a, **k: (time.sleep(0.4), json.dumps({"focus": [], "next": [], "place": [], "states": {}}))[1]
INBOX.append({"from": "Deals <x@promo.shop.com>", "subject": "70% OFF EVERYTHING", "snippet": "", "is_read": False, "id": "m8"})
peek = m.payload("grant", "selftest")
assert not any(r["iid"] == "mm8" for sub in peek["subjects"] for r in sub["rows"]), "unjudged mail reached the page"
time.sleep(0.8); INBOX.pop()

# --- THE PAGE HOLDS STILL ---------------------------------------------------
# The complaint this exists for: "the data keeps shuffling". A subject keeps
# its id, title, colour and place; an item stays where it was put; the model
# is asked only about what is new, and cannot move the rest even if it tries.
shape = lambda d: [(x["id"], x["title"], x["tint"], [r["iid"] for r in x["rows"]])  # noqa: E731
                   for x in d["subjects"] if x["id"] != "new"]
d = m.payload("grant", "selftest")
before = shape(d)
words_before = [f["text"] for f in d["brief"]["focus"]]
asked_for = {}
def _noise(system, turns, **k):
    asked_for["ctx"] = turns[0]["content"]
    return json.dumps({"focus": ["DIFFERENT WORDS"], "next": [], "states": {},
                       "place": [{"id": "mm9", "to": "noise"},
                                 {"id": "tr2", "new": "Somewhere else entirely"},      # already homed
                                 {"id": "tr1", "into": "s999"}]})                      # already homed
m.ask_claude = _noise
INBOX.append({"from": "Shop <x@promo.shop.com>", "subject": "Cyber Monday", "snippet": "", "is_read": False, "id": "m9"})
LOCS["data"][0]["address"] = "99 Elm Rd, Austin"            # a phone moved
for _ in range(100):
    d = m.payload("grant", "selftest")
    if "mm9" in m.load_subjects("selftest")["noise"]:
        break
    time.sleep(0.05)
time.sleep(0.2); d = m.payload("grant", "selftest")
new_ctx = asked_for["ctx"].split("NEW ITEMS", 1)[1].split("TODAY'S CALENDAR", 1)[0]
assert "mm9" in new_ctx and "tr1 |" not in new_ctx, "the model must be asked about the new item ONLY"
assert shape(d) == before, "a promotion arriving (or a phone moving) changed the page"
assert [f["text"] for f in d["brief"]["focus"]] == words_before, \
    "filing a promotion as noise rewrote the summary at the top of the page"
calls = []
m.ask_claude = lambda *a, **k: calls.append(1) or json.dumps({"focus": [], "next": [], "place": [], "states": {}})
m.payload("grant", "selftest"); time.sleep(0.3); m.payload("grant", "selftest"); time.sleep(0.2)
assert not calls, f"nothing is new and nothing moved, yet the model was called {len(calls)}x"

def _real(system, turns, **k):
    return json.dumps({"focus": ["Now two things from Maya."], "next": [], "place": [{"id": "mm7", "into": austin["id"]}],
                       "states": {austin["id"]: "Now with a new message."}})
m.ask_claude = _real
INBOX.append({"from": "Maya Chen <maya@acme.com>", "subject": "Austin — hotel?", "snippet": "", "is_read": False, "id": "m7"})
for _ in range(100):
    d = m.payload("grant", "selftest")
    if d["brief"]["focus"] and d["brief"]["focus"][0]["text"].startswith("Now two"):
        break
    time.sleep(0.05)
after = shape(d)
for (sid, title, tint, members), (sid2, title2, tint2, members2) in zip(before, after):
    assert (sid, title, tint) == (sid2, title2, tint2), f"a subject changed identity: {title} -> {title2}"
    assert members2[:len(members)] == members, f"{title}: its rows moved"
assert len(after) == len(before), "a subject appeared or vanished"
assert "mm7" in dict((t, m_) for _, t, _, m_ in after)["Austin trip"], "the new message was not filed where it belongs"
print("inbox        : the past-due notice is a subject; the promotion and the sales follow-up never appear")
print("stable       : same subjects, order, colours, rows — a promotion changes nothing, not even the summary")
INBOX.pop(); INBOX.pop()
m.ask_claude = lambda *a, **k: json.dumps({"focus": ["f"], "next": [], "place": [], "states": {}})
time.sleep(0.2); d = m.payload("grant", "selftest"); time.sleep(0.3); d = m.payload("grant", "selftest")

# --- rename, and the sweep ----------------------------------------------------
sid = austin["id"]
assert m.ui_action("rename", {"id": sid, "title": ""}, "selftest")["ok"] is False, "an empty name must refuse"
assert m.ui_action("rename", {"id": sid, "title": "Austin, Thursday"}, "selftest")["ok"]
d = m.payload("grant", "selftest")
renamed = next(x for x in d["subjects"] if x["id"] == sid)
assert renamed["title"] == "Austin, Thursday" and renamed["tint"] == austin["tint"], "a rename must not recolour or move"
assert [x["id"] for x in d["subjects"] if x["id"] != "new"] == [x[0] for x in after], "a rename reordered the page"

BASE_TOOL = m.tool
def run_sweep(plan, verdict, results):
    m.ask_claude = lambda system, turns, **k: json.dumps(
        plan if system is m.SWEEP_PLAN else verdict if system is m.SWEEP_JUDGE
        else {"focus": ["f"], "next": [], "place": [], "states": {}})
    m.tool = lambda name, args, tok: (
        json.dumps({"results": results}) if name == "search_everything" else
        json.dumps([{"id": "m77", "from": "Maya Chen <maya@acme.com>", "subject": "Austin — hotel confirmation"}])
        if name == "email" and args.get("action") == "search" else BASE_TOOL(name, args, tok))
    assert m.ui_action("sweep", {"id": sid}, "selftest", "grant")["ok"]
    # The loop exists because the payload is eventually consistent: `payload`
    # kicks off organising under `_regen_lock` and the sweep note arrives on a
    # later pass. The SUBJECT'S PRESENCE is eventually consistent too, and the
    # bare `next(...)` was not retry-safe — on a pass where the list did not
    # yet carry `sid` it raised StopIteration instead of waiting, which is a
    # retry loop whose first step cannot be retried.
    #
    # Measured at ~20-30% of runs across three commits (2/10 at dfc5a63, 3/10
    # at d8f4800, 1/10 with the clock fix) — the same failure in all three, so
    # it predates both. A gate that flakes one run in four makes every green
    # three-quarters of an answer.
    for _ in range(100):
        d = m.payload("grant", "selftest")
        me = next((x for x in d["subjects"] if x["id"] == sid), None)
        if me and me["sweep_note"]:
            return me
        time.sleep(0.05)
    raise AssertionError("the sweep never reported")

RES = [{"id": "k1", "source": "knowledge", "source_label": "Knowledge", "title": "Austin conference notes",
        "route": "/knowledge?selectedId=k1", "icon": "brain", "snippet": "", "updated_at": "2026-11-20T00:00"},
       {"id": "f9", "source": "feed", "source_label": "Feed", "title": "Finances clear",
        "route": "/feed?selectedId=f9", "icon": "square.stack.3d.up", "snippet": "", "updated_at": "2026-11-05T00:00"}]
me = run_sweep({"specific": True, "why": "", "queries": ["Austin", "Maya Chen"]},
               {"keep": [{"key": "knowledge:k1", "why": "notes for the same trip"},
                         {"key": "mail:m77", "why": "the hotel for it"},
                         {"key": "made:up", "why": "invented"}]}, RES)
keys = [f["key"] for f in me["found"]]
assert keys == ["knowledge:k1", "mail:m77"], f"found must be exactly what was judged to belong, and real: {keys}"
assert me["found"][1]["route"] == "/inbox?selectedId=m77"
assert len(me["rows"]) == len(renamed["rows"]), "a sweep OFFERS; it must not file anything by itself"
assert m.ui_action("keep", {"id": sid, "key": "knowledge:k1"}, "selftest")["ok"]
assert m.ui_action("drop", {"id": sid, "key": "mail:m77"}, "selftest")["ok"]
me = next(x for x in m.payload("grant", "selftest")["subjects"] if x["id"] == sid)
assert any(r["iid"] == "knowledge:k1" for r in me["rows"]) and not me["found"], "keep files it; drop removes the offer"
me = run_sweep({"specific": True, "why": "", "queries": ["Austin"]},
               {"keep": [{"key": "mail:m77", "why": "x"}, {"key": "knowledge:k1", "why": "x"}]}, RES)
assert not me["found"], "a dismissed or kept result must never be offered again"
os.rename(m.subjects_path("selftest"), m.subjects_path("selftest") + ".bak")
# Carries the CURRENT spec: this case is about the sweep, and a record with
# no spec is a migration case that load_subjects correctly empties.
json.dump({"seq": 50, "spec": m.SUBJECT_SPEC,
           "subjects": [{"sid": "s50", "title": "Work", "ids": ["tr1"]}]},
          open(m.subjects_path("selftest"), "w"))
sid_keep, sid = sid, "s50"
me = run_sweep({"specific": False, "why": "name one project or person", "queries": []}, {"keep": []}, RES)
assert me["sweep_note"].startswith("Too broad to sweep") and not me["found"], me["sweep_note"]
os.replace(m.subjects_path("selftest") + ".bak", m.subjects_path("selftest")); sid = sid_keep

# A record grouped under the OLD spec is re-derived once, and only once.
# Asserted in both directions: a spec-less record loses its subjects (so the
# person stops seeing an arrangement built to a definition they rejected),
# and noise/background/asked survive (so what is marketing does not have to
# be decided again). Without the second half this would be a regroup wearing
# a migration's clothes.
#
# Its OWN user, deliberately. The first version wrote fixtures over
# "selftest"'s record and read them straight back, which races the background
# organiser writing the same file under _regen_lock — it failed about 1 run
# in 10, in both directions. The behaviour under test belongs to
# load_subjects, not to the live user, so the race is removable rather than
# something to sleep through.
_MU = "migprobe"
json.dump({"seq": 7, "subjects": [{"sid": "s7", "title": "Auto loan past due", "ids": ["x1"]}],
           "noise": ["n1"], "background": ["b1"], "asked": {"a1": 2}},
          open(m.subjects_path(_MU), "w"))
_mig = m.load_subjects(_MU)
assert _mig["subjects"] == [], "a record under the old spec must be re-derived, not frozen"
assert _mig["noise"] == ["n1"] and _mig["background"] == ["b1"] and _mig["asked"] == {"a1": 2}, \
    "the migration must keep what grouping does not decide"
assert _mig["spec"] == m.SUBJECT_SPEC
json.dump({"seq": 7, "spec": m.SUBJECT_SPEC,
           "subjects": [{"sid": "s7", "title": "Money", "ids": ["x1"]}]},
          open(m.subjects_path(_MU), "w"))
assert len(m.load_subjects(_MU)["subjects"]) == 1, "a current record must NOT be re-derived"
os.remove(m.subjects_path(_MU))
print("migration   : old spec re-derived once; current spec untouched")
print("rename       : keeps its colour and its place")
print("sweep        : offers only what was judged to belong; keep files, drop forgets; 'Work' is refused")
m.ask_claude = lambda *a, **k: json.dumps({"focus": ["f"], "next": [], "place": [], "states": {}})
d = m.payload("grant", "selftest")

# --- the verbs: done, later, not for me, undo -------------------------------
shown = lambda d: [r["iid"] for sub in d.get("subjects", []) for r in sub["rows"]]  # noqa: E731
n = len(shown(d))
assert m.ui_action("done", {"id": "tr2", "what": "Fix light switch"}, "selftest")["ok"]
d = m.payload("grant", "selftest")
assert "tr2" not in shown(d) and len(shown(d)) == n - 1, "done did not remove the row"
assert d["undo"].startswith("Done: Fix light switch"), d.get("undo")
assert m.ui_action("undo", {}, "selftest")["ok"]
d = m.payload("grant", "selftest")
assert "tr2" in shown(d) and "undo" not in d, "undo did not bring it back"
assert m.ui_action("undo", {}, "selftest")["ok"] is False, "a second undo must refuse"
m.ui_action("later", {"id": "tr2", "what": "Fix light switch"}, "selftest")
d = m.payload("grant", "selftest")
assert "tr2" not in shown(d) and d["later_note"] == "1 back tomorrow", d.get("later_note")
st = m.load_state("selftest")
st["later"]["tr2"] = (now - timedelta(minutes=1)).isoformat(); m.save_state("selftest", st)
assert "tr2" in shown(m.payload("grant", "selftest")), "a snooze that has ended must come back"
m.ui_action("mute", {"id": "mm1", "what": "Maya"}, "selftest")
assert any(f["text"] == "Not for me: Maya" for f in m.fixes("selftest")), "mute taught nothing"
m.ui_action("undo", {}, "selftest")
assert not m.fixes("selftest"), "undoing a mute must withdraw its rule"
print("verbs        : done, later (and its return), not-for-me, undo")
os.remove(m.state_path("selftest"))
d = m.payload("grant", "selftest")

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
def _spy(system, turns, **k):
    seen["system"] = system
    return json.dumps({"focus": ["f"], "next": [], "place": [], "states": {}})
m.ask_claude = _spy
m.write_brief("selftest", "k", "CONTEXT")
assert "STANDING RULES" in seen["system"] and "all-day thing" in seen["system"], "rules never reached the organiser"
assert seen["system"].rindex("STANDING RULES") > seen["system"].index("Never invent"), "rules must come LAST"
print("rules        :", len(told), "standing, and they reach the organiser")
rang = []
m.nudge = lambda: rang.append(1)
m.write_brief("selftest", "k3", "CONTEXT"); assert rang, "a ranking never nudged the open page"
rang.clear()
m.ask_claude = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
m.write_brief("selftest", "k4", "CONTEXT"); assert rang, "a FAILED ranking must nudge too"
print("nudge        : on success and on failure")

m.ui_action("uncorrect", {"id": told[0]["id"]}, "selftest")
assert len(m.fixes("selftest")) == 1, "uncorrect did not remove exactly one"
print("uncorrect    : one removed, one left")

assert m.ui_action("clear", {}, "selftest")["ok"]
assert m.answer_for("selftest", now) == (None, ""), "clear left something behind"
print("clear        : nothing left")

print("\nOK — a whole payload built with the hub stubbed out, and the action channel answers.")
