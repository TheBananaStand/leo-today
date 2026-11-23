# Today — the design study

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
