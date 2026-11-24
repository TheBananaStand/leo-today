#!/usr/bin/env python3
"""Generate today.descriptor.json from today.html.

The markup is a FILE, not a string pasted into JSON: it is what
`leo packages preview today.html --data samples/ready.json` draws, what a
browser opens, and what anyone editing this package actually edits. This
script is the only thing that knows they end up in one blob.
"""
import json
import pathlib
import subprocess

here = pathlib.Path(__file__).parent
markup = (here / "today.html").read_text()

try:
    rev = subprocess.check_output(["git", "-C", str(here), "rev-parse", "HEAD"]).decode().strip()
except Exception:
    rev = ""

descriptor = {
    "name": "today",
    "label": "Today",
    "description": "What today holds, at a glance \u2014 the next thing, what is due, what is worth knowing.",
    "details": (
        "One page assembled from whatever this hub can answer: the calendar, reminders and the feed. "
        "Every block is gated on having something in it, so the page is as long as the day is busy. "
        "Each source is fetched on its own \u2014 one that fails or times out leaves its block off the "
        "page and a line at the foot saying so, rather than taking the page down."
    ),
    "setup_hint": "Nothing to set up. Enable it and open Today.",
    "use_cases": ["What does my day look like?", "What's overdue?"],
    "icon": "sun.max",
    "category": "package",
    "kind": "app",
    "default_enabled": False,
    "pages": [{"path": "today", "label": "Today", "icon": "sun.max", "show_in_nav": True}],
    "ui": {
        "today": {
            "kind": "html",
            "html": markup,
            "title": "Today",
            # A tick or a new feed item redraws the page; nothing here polls.
            # A topic is the first path segment after /api/ on a successful
            # write — so a tick on /api/reminders/... rings "reminders".
            #
            # What this does NOT cover, measured rather than assumed:
            #   · a calendar changed on the Mac. The satellite sync writes
            #     rows straight to the database with no HTTP request, so the
            #     path rule structurally cannot see it.
            #   · mail ARRIVING. Nothing email-shaped is published at all;
            #     `notifications` is the nearest thing and it is gated on the
            #     notification policy, so quiet mail lands silently.
            # `email` covers your own actions on a message; `notifications`
            # covers arrivals loud enough to badge. Both are partial and are
            # here because partial beats nothing.
            #
            # "today" is ours, published when the briefing has been rewritten.
            "refreshOn": ["reminders", "feed", "calendar",
                          "email", "notifications", "today"],
            "actions": {
                # The tick on a row, through the route Reminders already
                # serves to a person — this page holds no privilege of its own.
                # `packageAction` is the kind that reaches a package's own
                # `ui_action` — `POST /leo/ui/action` for a hosted process.
                # It is NOT a hand-written HTTP call: two were tried first and
                # both are recorded here because the failures look like
                # successes.
                #
                #   body-templated   the hub passes a declared `body` through
                #                    VERBATIM, so the process was handed the
                #                    literal string "{args.text}" and the
                #                    model answered "I don't see your question"
                #   query-templated  the hub strips the query when it proxies,
                #                    and fills its own {"name","args"} body —
                #                    which for a generic HTTP action is
                #                    {"args":null,"name":""}
                #
                # Both returned 200. Neither did anything.
                "ask": {"kind": "packageAction", "name": "ask",
                        "args": {"text": "{args.text}"}, "refresh": "reload"},
                "clear": {"kind": "packageAction", "name": "clear",
                          "refresh": "reload"},
                # The inbox's verbs. All four are this package's own state —
                # it holds no write scope for mail or reminders — and every
                # one can be undone.
                "done": {"kind": "packageAction", "name": "done",
                         "args": {"id": "{args.id}", "what": "{args.what}"}, "refresh": "reload"},
                "later": {"kind": "packageAction", "name": "later",
                          "args": {"id": "{args.id}", "what": "{args.what}"}, "refresh": "reload"},
                "mute": {"kind": "packageAction", "name": "mute",
                         "args": {"id": "{args.id}", "what": "{args.what}"}, "refresh": "reload"},
                "undo": {"kind": "packageAction", "name": "undo", "refresh": "reload"},
                # Telling it it is wrong. `correct` is standing — it is handed
                # to every rewrite from here on, not just the next one.
                "correct": {"kind": "packageAction", "name": "correct",
                            "args": {"text": "{args.text}"}, "refresh": "reload"},
                "uncorrect": {"kind": "packageAction", "name": "uncorrect",
                              "args": {"id": "{args.id}"}, "refresh": "reload"},
                # Drop the cached briefing; the next draw rebuilds it.
                # The way out of the "nothing answered" state, and the header's
                # own refresh.
                "refresh": {"method": "GET", "path": "/api/packages/today/ui/data",
                            "refresh": "reload"},
            },
        }
    },
    "fields": [{
        "key": "today_graph_token",
        "label": "Graph token",
        "field_type": "password",
        "required": False,
    }],
    "entitlements": {
        # Declared because it is what this package actually needs, and so the
        # install consent names it — but see the note in `leo-today`: the app
        # spawn path does not mint from this today.
        "graph_scopes": ["calendar:read", "reminders:read", "feed:read",
                         "hub_tools:read", "hub_tools:invoke",
                         "inference:messages", "surfaces:refresh",
                         # the census the research turned up: money, this hub's own
                         # model spend, who is where, and what is wrong with the box.
                         # All four are `global_list!` routes or tools we already reach.
                         "finance:read", "costs:read", "locations:read",
                         "people:read", "scheduler:read", "releases:read"],
        # The route that DOES reach the process: a declared settings key,
        # handed over as an env var at spawn.
        "settings_read": ["today_graph_token"],
        # Asking about the day goes through the hub's own model routing — this
        # package never holds a key, and the household's ceiling and costs page
        # apply to it like anything else.
        "inference": {
            "classes": ["prompts"],
            "purpose": "to answer questions about what is on the person's Today screen",
        },
    },
    "app": {
        "repo": "https://github.com/TheBananaStand/leo-today",
        "branch": "main",
        # No compiler is involved: the process is a dependency-free Python 3
        # script, so installing it is a clone and a chmod. Building a binary
        # inside the install request would be minutes of waiting for a few
        # hundred lines that spend all their time on HTTP anyway.
        "build": "make",
        "bin": "leo-today",
        "port": 8477,
        "supervised": False,
    },
}
# No `rev`: the branch is the pin. A stamped rev can only ever name the
# commit BEFORE the one carrying it, which reads as a mistake every time.

(here / "today.descriptor.json").write_text(json.dumps(descriptor, indent=2) + "\n")
print(f"today.descriptor.json written ({len(markup)} bytes of markup, rev {rev[:9] or 'none'})")
