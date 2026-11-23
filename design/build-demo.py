#!/usr/bin/env python3
"""Write the design study as `today` itself.

It REPLACES the working package rather than sitting beside it: a design you
have to go and find a second nav entry for is not the one you judge. Nothing
is fetched — one sample payload — so what this shows is the markup, in the
real window, with the platform's own controls.

`git checkout main && ./build.py` puts the working page back.
"""
import json, pathlib
here = pathlib.Path(__file__).parent
d = {
  "name": "today", "label": "Today",
  "description": "What today holds, at a glance — the design study, on sample data.",
  "details": "Nothing is live. It serves one sample payload so the markup can be judged in "
             "the real app with the platform's own controls, type and spacing.",
  "setup_hint": "Nothing to set up.",
  "icon": "sun.max", "category": "package", "kind": "app", "default_enabled": False,
  "pages": [{"path": "today", "label": "Today", "icon": "sun.max", "show_in_nav": True}],
  "ui": {"today": {"kind": "html", "html": (here / "today.html").read_text(),
                   "title": "Today — design study",
                   "actions": {}}},
  "fields": [{"key": "today_payload", "label": "Which sample (ready | evening)",
              "field_type": "text", "required": False}],
  "entitlements": {"settings_read": ["today_payload"]},
  "app": {"repo": "https://github.com/TheBananaStand/leo-today", "branch": "design",
          "build": "make", "bin": "design/serve-demo", "port": 8477, "supervised": False},
}
(here / "demo.descriptor.json").write_text(json.dumps(d, indent=2) + "\n")
print("design/demo.descriptor.json written")
