# Today — the design study

**Version 2 is `today.html`.** Version 1 is kept beside it as `v1-today.html`
/ `v1-ready.json` — it was organised by SOURCE (calendar, tasks, mail, home).
This one is organised by SUBJECT, which is the whole difference:

- *Renew the passport*, *book the flights*, *Maya wants your dates* and
  *flight 8:00 tomorrow* were four rows in three blocks of v1. They are one
  thing — **the Austin trip** — and v2 draws them as one, with the clock on
  it (`17h`) and the next move under it.
- **The day is one object, not a list.** The strip at the top is proportional:
  a 2h review is four times the width of a 30m standup, free time is actually
  empty, and the marker underneath says where you are in it. Both come from
  `grow`, so the shape is the payload's.
- **What changed since you last looked** is a chip in the header. A page you
  open six times a day has to say what is new, or you read it six times.
- **Loose ends** is what is left when every subject has taken its own: the
  things that are only a line.

Not wired to anything. This is the page as it should look, with sample data
rich enough to judge it by. `today.html` is valid in the subset, so you can
draw it on any box with no hub, no Mac and no screen:

```bash
leo packages preview design/today.html --data design/ready.json   --out /tmp/day.png --width 1680 --height 1500
leo packages preview design/today.html --data design/evening.json --out /tmp/eve.png --width 1680 --height 1100
leo packages preview design/today.html --data design/ready.json   --phone --out /tmp/phone.png
```

## What it adds over the shipped page

| | |
|---|---|
| **A day arc** | where in today you are, before anything else |
| **A focus line** | the one judgement on the page — what to START with, and *why*. Everything else is a fact |
| **A hero that answers "what now"** | the time at 48pt, who is in it, and the one action |
| **A real rail** | events, their people, their length — and the **holes**, drawn rather than omitted, because the shape of a day is where the gaps are |
| **Leave-by** | on the row it belongs to, with the drive time. The thing you actually get wrong |
| **Done today** | a bar, not a count: 3 means nothing without the 11 |
| **Waiting on you** | mail and messages that have gone unanswered, with how long |
| **The house** | anything not right, in one list |
| **Spending as pace** | $2,341 against the $1,400 usual by now — a total alone says nothing |
| **Tomorrow** | one line, so tonight can be planned |
| **Suggestion chips** | the four questions worth asking about this particular day |
| **Keyboard** | j/k through the day, e to tick, / to ask — shown, so they exist |

## The rules it follows

- **Five row templates and nothing else.** A block added next year picks a
  form; it does not invent one. That is the whole consistency mechanism.
- **The hue is on the glyph.** Figures wear ink. The one exception is a
  danger chip, which has to be seen.
- **One accent.** `Join` is the only accent-filled control on the page.
- **Order comes from the payload.** Events and free gaps are ONE list in time
  order — two loops put the 12:00 hole after 18:30, and that bug is in the
  commit history.
- **The arc is blue, done-today is green.** Two bars, two meanings; one colour
  for both read as the same fact.
- **Every block is `if`-gated.** The evening render is the same markup with a
  quieter day in it.

## Known, and deliberate

- The right column runs short on a quiet evening. Fixing it would mean
  branching the layout on how much there is, and a page whose geography moves
  with its content costs a power user the thing a glance page is for.
- Icons draw as plain tiles in the preview — it has the real type scale and
  spacing but no SF Symbols.
