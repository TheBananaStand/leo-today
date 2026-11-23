# Today

One page for what today holds: the next thing, what is due, and what is worth
knowing. It is a Leo **app package** — a descriptor plus a small process — so
it installs over a running hub with no rebuild of Leo and no checkout.

```bash
git clone https://github.com/TheBananaStand/leo-today /tmp/leo-today
leo packages install /tmp/leo-today/today.descriptor.json --enabled

# The page needs a credential to read the hub with. See "The token" below
# for why this step is not automatic yet.
leo packages token mint today --scope calendar:read,reminders:read,feed:read --label "Today's Graph reads"
leo packages set today today_graph_token=<the token it printed>
leo packages disable today && leo packages enable today   # respawn, so it picks the token up
```

Then open **Today** in the sidebar, or go to `/p/today/today`.

## The token, and why that step exists

A package declares what it needs to read as `entitlements.graph_scopes`, and
this one declares `calendar:read`, `reminders:read`, `feed:read`. The install
consent shows them. **They are never minted for an app package:**
`graph_scopes_for()` in `crates/leo-package/src/manager.rs` builds its scope
list from `entitlements.inference` alone, so an app that declares Graph scopes
and nothing else is spawned with no `LEO_PACKAGE_TOKEN` at all. The call site's
own comment says an entitled app gets the credential to reach back with; that
is true only for inference.

So the token comes the other supported way — a settings key this package
declares in `settings_read`, which the hub hands to the process as an
environment variable at spawn. When the mint path is fixed, the three lines
above collapse into the first one and nothing else here changes.

**Reading for a person is separate from that.** Reminders and the feed answer
for ONE person and refuse a bare package credential outright. The hub stamps a
single-use grant (`x-leo-acting-grant`) on its call to `/leo/ui/data`; this
spends it at `/graph/v1/acting/exchange` and carries the result on those two
reads, so the page is each person's own. The calendar is a household domain
and keeps the package credential.

## What it is made of

| File | What it is |
|---|---|
| `today.html` | the whole screen, in Leo's HTML subset (`leo examples show docs/html-subset.md`) |
| `leo-today` | the process behind it: fetches a few hub domains over the Graph and answers `GET /leo/ui/data` |
| `build.py` | puts the markup into `today.descriptor.json` — the markup stays a file you can open in a browser |
| `samples/*.json` | the four states the screen was designed against: ready, empty, nothing-answered, and awkward data |

## The two ideas worth stealing

**The page is data, the payload decides what is on it.** Every block is gated
on having something in it (`if="events"`), and an empty array is false in this
language — so a quiet day is a short page and a busy one is a long page, with
no code choosing. Ordering, capping and wording all live in the payload, which
is why the markup never changed while the process was rewritten.

**Every source fails on its own.** The three sources are fetched in parallel
with a 2.5s budget each. One that errors, times out, or that this package's
token may not reach leaves its key missing: its block is simply absent, the
others are unaffected, and a line at the foot says which one did not answer.
Only when *nothing* answers does the page become an error state — with a way
out. A page that is down whenever any one package is down is not a page you
would keep open.

## Looking at it without installing

The preview needs no hub, no Mac and no screen. Point it at the **markup**, not
at the descriptor — the descriptor path still uses the old node painter and
draws an `html` node as a placeholder:

```bash
leo packages preview today.html --data samples/ready.json   --out /tmp/ready.png
leo packages preview today.html --data samples/error.json   --out /tmp/error.png
leo packages preview today.html --data samples/awkward.json --phone --out /tmp/phone.png
```

## What it does not do yet

- **No agent to ask.** The language has a `<conversation>` element, so a thread
  on this page is markup plus two routes this process would have to serve. It
  is the obvious next thing and deliberately not faked.
- **Three sources.** Calendar, reminders, feed. Adding a fourth is a function
  and a scope, and the markup only changes if the block is a new *shape*.
- **The ordering is fixed**, not scored. Blocks appear in a set order; only
  their presence varies.

## Scopes it asks for

`calendar:read`, `reminders:read`, `feed:read` — read-only. Ticking a reminder
goes through the route Reminders already serves to a person, so the page holds
no privilege of its own.
