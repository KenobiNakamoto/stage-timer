# Set up at the venue

Three devices. The Mac runs the timer. The iPad shows it. The phone controls it.

This file starts from zero on a network you have never used. Read it in order.

---

## 1. Put all three devices on one Wi-Fi

This is the whole trick. The Mac, the iPad and the phone must join the **same** Wi-Fi network,
before anything else. Nothing works if one of them is on a different network.

Join the iPad and the phone to the same network the Mac is on. Check each one by hand. Do not
assume. An iPad often holds an old network from the last venue and rejoins it.

If the venue Wi-Fi does not work, go to section 6. It has a fallback that always works.

---

## 2. Start the timer

```sh
cd stage-timer
python3 timer.py
```

It prints two URLs:

```
  iPad  →  http://10.30.4.137:8000/
  Phone →  http://10.30.4.137:8000/c
```

**The address changes on every new network.** The number above is the address right now, at this
venue. It was a different number yesterday. Always read the address the program prints. Never
type an address you wrote down before.

Leave the terminal window open. `Ctrl-C` stops the timer.

### If you need the address again

The terminal scrolled away, or the timer already runs. Get the address with one command:

```sh
ipconfig getifaddr en0
```

`en0` is the Wi-Fi. The answer is the `10.30.4.137` part. Add `:8000/` for the iPad and `:8000/c`
for the phone.

---

## 3. Set up the iPad

1. Open Safari. Type the iPad URL. The clock appears.
2. **Share → Add to Home Screen.** Name it *Timer*. This step matters: the icon opens the page
   with no address bar and no tab strip. Safari alone always keeps its bars.
3. Close Safari. Open the timer from the new icon.
4. **Settings → Display & Brightness → Auto-Lock → Never.**

Step 4 is the one that catches people. An iPad that sleeps shows a black screen to the room. The
page asks the iPad to stay awake, but that request needs https and this runs on plain http. So the
request never works. Change the setting by hand.

Then plug the iPad into power and connect it to the screen or projector.

---

## 4. Set up the phone

1. Open the phone URL in Safari or Chrome.
2. Add it to the Home Screen as well. The buttons are then full height, with no browser bars.

The controls:

| Control | What it does |
|---|---|
| **Duration** | 1, 5, 10, 15, 20, 30 minutes. It also stops the clock, so a preset never starts a countdown by surprise. |
| **−1 / +1** | One minute off or on. It works while the clock runs. |
| **Start** | Starts the clock. |
| **Pause** | Holds the clock. Start continues from the same number. |
| **Restart** | Goes back to the duration you chose, and runs again. |
| **WRAP IT UP** | Puts a flashing red message on the iPad, over the clock. The button then reads **Hide message**. Press it to show the clock again. |

The clock keeps running under the message. Nothing is lost.

Two phones can control the timer at the same time. Each button sends an instruction, not a
change of state, so two people cannot fight each other into a wrong result.

---

## 5. Test it before the room fills

Do this test while you can still fix it.

1. On the phone, press **10 min**, then **Start**. The iPad must count down.
2. Press **Pause**. The iPad must stop.
3. Press **WRAP IT UP**. The red message must fill the iPad. Press **Hide message**. The clock
   must come back.
4. Press **Restart**. The clock must return to 10:00 and run.

Every step must show on the iPad within about half a second. If it does, you are ready.

---

## 6. When the venue Wi-Fi does not work

Venue and guest networks often separate the devices on them from each other. Each device reaches
the internet, but no device reaches another device. This is a setting on the venue's equipment.
You cannot change it, and it stops the timer completely.

**How to recognise it.** The Mac opens `http://localhost:8000/` and the page works. The iPad,
on the same Wi-Fi, opens the printed address and gets nothing. That difference means the network
separates its devices. It is not a fault in the timer.

**The fix: use a phone as the network.** It takes two minutes and it always works.

1. On the phone, turn on **Settings → Personal Hotspot**.
2. Join the **Mac** to the hotspot.
3. Join the **iPad** to the hotspot.
4. Stop the timer with `Ctrl-C` and start it again. It prints a new address, usually
   `172.20.10.x`.
5. Open the new address on the iPad and on the phone.

The phone makes the network, so the phone is already on it. The three devices then talk directly
and no venue equipment is involved.

This is also the safer choice. The timer has no password. Anyone on the venue Wi-Fi who finds the
address can control it. On a hotspot, only your three devices can reach it.

Keep the Mac on AC power. A hotspot empties a phone battery, so keep the phone on a charger too.

---

## 7. When something is wrong

| What you see | What it means | What to do |
|---|---|---|
| The iPad shows nothing, or Safari cannot open the page | Wrong address, wrong network, or the network separates devices | Read the address again with `ipconfig getifaddr en0`. Check the iPad's Wi-Fi name against the Mac's. Then go to section 6. |
| `Address already in use` when you start it | An older copy still runs | `pkill -f timer.py`, wait five seconds, start it again. |
| Every page fails, and `curl` says `000` | Nothing listens on port 8000 | The program is not running. Start it. A page that loads but looks wrong is a different problem. |
| The clock runs on the iPad but the phone does nothing | The phone left the Wi-Fi, or it sits on mobile data | Rejoin the phone to the same Wi-Fi. |
| The iPad screen went black | The iPad slept | Set Auto-Lock to Never. Section 3, step 4. |
| The address changed while you worked | The Mac rejoined a different network, or the network gave a new address | Read it again and reopen both pages. |
| The Home Screen icon opens an old address | The icon holds the address from the last venue | Delete the icon. Open the new address in Safari. Add it to the Home Screen again. |

The last row is the most common problem at a new venue. The Home Screen icon is a saved address,
not a saved application.

---

## 8. This network, right now

Measured on 2026-09-16 at the venue.

| Item | Value |
|---|---|
| Mac Wi-Fi address | `10.30.4.137` |
| iPad page | `http://10.30.4.137:8000/` |
| Phone page | `http://10.30.4.137:8000/c` |
| Network | `10.30.4.0/22`, router `10.30.4.1` |
| macOS firewall | Off, so it blocks nothing |
| Timer | Running, answers on both pages |

**These values expire.** They are correct for this network only. Read section 2 again at the next
venue.

---

## 9. Check the program before you travel

```sh
python3 timer.py --check
```

It tests the time arithmetic and the message button. It prints `checks pass`. Run it after any
change to `timer.py`.
