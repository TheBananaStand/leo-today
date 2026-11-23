#!/usr/bin/env python3
"""Write the design study's descriptor. A second package on purpose: the
working `today` keeps its page while this one is looked at beside it."""
import json, pathlib
here = pathlib.Path(__file__).parent
d = {
  "name": "todaydesign", "label": "Today (design)",
  "description": "The Today design study — the page as it should look, on sample data.",
  "details": "Nothing is live. It serves one sample payload so the markup can be judged in "
             "the real app with the platform's own controls, type and spacing.",
  "setup_hint": "Nothing to set up.",
  "icon": "sparkles", "category": "package", "kind": "app", "default_enabled": False,
  "pages": [{"path": "today", "label": "Today (design)", "icon": "sparkles", "show_in_nav": True}],
  "ui": {"today": {"kind": "html", "html": (here / "today.html").read_text(),
                   "title": "Today — design study",
                   "actions": {}}},
  "fields": [{"key": "todaydesign_payload", "label": "Which sample (ready | evening)",
              "field_type": "text", "required": False}],
  "entitlements": {"settings_read": ["todaydesign_payload"]},
  "app": {"repo": "https://github.com/TheBananaStand/leo-today", "branch": "design",
          "build": "make", "bin": "design/serve-demo", "port": 8478, "supervised": False},
}
(here / "demo.descriptor.json").write_text(json.dumps(d, indent=2) + "\n")
print("design/demo.descriptor.json written")
