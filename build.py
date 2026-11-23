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
            "refreshOn": ["reminders", "feed", "calendar"],
            "actions": {
                # The tick on a row. `args.id` is the row it was on, and the
                # route is the one Reminders already serves to a person, so
                # this page gets no privilege of its own.
                "complete": {
                    "method": "PATCH",
                    "path": "/api/reminders/items/{args.id}/toggle",
                    "body": {},
                    "refresh": "reload",
                },
                # The way out of the "nothing answered" state: ask again.
                "refresh": {
                    "method": "GET",
                    "path": "/api/packages/today/ui/data",
                    "refresh": "reload",
                },
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
        "graph_scopes": ["calendar:read", "reminders:read", "feed:read"],
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
