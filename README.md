# Stage Timer

A countdown. Your phone controls it. The iPad shows it. Nothing else.

## Run it

```sh
python3 timer.py
```

It prints two URLs. Open them:

| Device | URL |
|---|---|
| **iPad** | `http://<this-mac>:8000/` |
| **Phone** | `http://<this-mac>:8000/c` |

All three devices must sit on the same Wi-Fi. Stop it with `Ctrl-C`.

**At a venue, on a network you have never used, read [`SETUP.md`](SETUP.md).** It is the
show-day runbook: find the address, set up both devices, test it, and what to do when the
venue Wi-Fi separates its devices.

The phone gives you:

- **Duration** — 1, 5, 10, 15, 20, 30 minutes. Choosing one also stops the clock, so a preset
  never starts a countdown by surprise.
- **Adjust** — minus one minute, plus one minute. Works while running.
- **Transport** — Start, Pause, Restart. Restart goes back to the duration you chose and runs
  again. To reset and hold instead, press the preset.
- **WRAP IT UP** — replaces the countdown on the iPad with a full-screen message, flashing red
  and white. The button then turns red and reads **Hide message**; press it to go back to the
  clock. The clock keeps running underneath, so nothing is lost.

The message button sends an explicit on or off, never a flip. Pressing "Hide message" twice hides
it twice — it cannot bring the message back. The label always says what the next press will do.
The iPad shows the Barcelona Bitcoin Hub palette: parchment numerals on ink, orange below two
minutes, orange pulsing below thirty seconds. In overtime the number goes negative and alternates
red and parchment — only the number. The ground, the logo and the pattern do not move, so the
room sees the clock change, not the screen flash.

The number is drawn as SVG and refits itself to the screen on every change, so a minus sign or an
hours field can never push it off the edge.

## Full screen on the iPad

Two ways, both already built in:

- **Tap the screen.** The page asks Safari for real fullscreen. Safari only grants this from a
  tap, so it cannot happen on its own.
- **Add to Home Screen** (Share → Add to Home Screen), then open it from the icon. It launches
  with no Safari chrome at all — no address bar, no tab strip. This is the one to use for a show.

## Before a show

1. **iPad → Settings → Display & Brightness → Auto-Lock → Never.** A sleeping iPad is a black
   screen. This is the one that catches people. The page does ask for a screen Wake Lock, but
   that needs https and this runs over plain http on the LAN, so it will not fire. Change the
   setting.
2. Add the page to the Home Screen and launch it from there.
3. Keep the Mac on AC power.

## Check it still works

```sh
python3 timer.py --check
```

It tests the running and paused time arithmetic, which is the only part that can be wrong in a
way you would not see immediately.

## Branding

`logo.svg` is the full BBH lockup — Sagrada Família, Bitcoin B and the wordmark — the square
white variant from the Barcelona Bitcoin Hub site. Colours come from that site's tokens: ink `#010101`, parchment `#f0e8d5`, orange `#f7931a`.

The file is the white variant. `timer.py` recolours `#fff` to parchment as it serves it, so the
logo matches the numerals without a second copy of the file.

The logo is `20vh` tall — the `#logo` rule in `timer.py`. Raise it and the number shrinks to
suit, because the number refits itself to whatever space is left.

## The background pattern

The edges carry the Flor de Barcelona alternating with the Bitcoin mark, tilted — the same ground
as one of my own slide decks. `ground()` in `timer.py` is a port of that deck's generator.

Its geometry was tuned by eye, one variable at a time, and the deck's own notes say not to
re-tune blind. The angles, the stagger and the grid ratio here are unchanged. Two things differ:

- **The palette is inverted** — parchment marks on ink, not ink on parchment.
- **The canvas is the live viewport**, not a fixed slide. The page asks for
  `ground.svg?w=&h=` with its own size and re-asks on rotate, so the frame always hugs the real
  edges.

### The two knobs

| Knob | In `timer.py` | What it does |
|---|---|---|
| `BANDS` | `(top, right, bottom, left)`, fractions of the short side | How far the pattern reaches in. Bigger = tighter margins. |
| `ZOOM` | in the display script | How far the clock oversteps its box. Bigger = bigger number. |

They are independent: the pattern reaches past the clock's box into the slack the clock does not
use. That is what makes the margins tight without shrinking the number.

**The left and right numbers are near their limit at `.13`.** The widest thing the clock ever
shows is `-MM:SS` in overtime, and at `.13` the pattern already comes within a few pixels of the
minus sign and the last digit. Push them further and the pattern starts covering the number when
a speaker runs over — exactly when it must stay readable. Top and bottom have far more room.

Check any change against overtime, not against a fresh clock.

The marks live in `art/`. They came from the deck; they are not BBH logo files.

Red (`#e01b24`) is not a BBH colour. It is used in exactly two places, both alarms: the overtime
number and the WRAP IT UP message. Everything else stays inside the brand. Swap `logo.svg` to
re-brand for another event.

## What it does not do

No rundown, no cue list, no speaker names, no OSC, no recording, no accounts. Add none of that
until a show actually needs it.

There is **no password**. Anyone on the same Wi-Fi who finds the URL can control the timer. On a
venue's open guest Wi-Fi, use a phone hotspot for the three devices instead.

## History

Ontime v4 was installed first, then removed on 2026-09-16. It is a full show-control system —
rundowns, groups, cues, Stream Deck, multi-operator — and it was too much for one countdown.
`memory/journal.md` records what was compared and why this replaced it. Nothing here needs it.

## Licence

The code is MIT. See `LICENSE`.

The artwork is mine as well, and the same licence covers `logo.svg` and `art/`. One limit is
worth stating: the Barcelona Bitcoin Hub lockup and wordmark are that community's marks. The
licence lets you reuse and change the files. It does not let you present your event as a BBH
event. Swap `logo.svg` for your own mark and the screen is yours.
