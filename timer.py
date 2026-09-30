#!/usr/bin/env python3
"""Phone controls, iPad displays. One countdown, nothing else.

    python3 timer.py        # then open the two printed URLs

ponytail: one timer, one process, no auth, no storage. It is a LAN countdown.
Rooms/auth/persistence only if a second show needs to run at the same time.
"""
import json, math, pathlib, re, socket, time, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8000
WARN_MS, DANGER_MS = 120_000, 30_000

now_ms = lambda: int(time.time() * 1000)
# ends_at set => running. Otherwise `remaining` is frozen.
# preset is what Stop resets to. wrap replaces the number with a WRAP IT UP message.
state = {"remaining": 300_000, "ends_at": None, "preset": 300_000, "wrap": False}


def remaining_ms():
    return state["remaining"] if state["ends_at"] is None else state["ends_at"] - now_ms()


def snapshot():
    return {"ms": remaining_ms(), "warn": WARN_MS, "danger": DANGER_MS,
            "wrap": state["wrap"], "running": state["ends_at"] is not None}


def apply(action, value=0):
    left = remaining_ms()
    if action == "start" and state["ends_at"] is None:
        state["ends_at"] = now_ms() + left
    elif action == "pause":
        state.update(remaining=left, ends_at=None)
    elif action == "restart":                   # back to the chosen duration, running again
        state.update(remaining=state["preset"], ends_at=now_ms() + state["preset"])
    elif action == "wrap":                      # explicit on/off, never a flip
        state["wrap"] = bool(value)
    elif action == "set":                       # also stops, so a preset never starts by surprise
        state.update(remaining=value, ends_at=None, preset=value)
    elif action == "adjust":
        if state["ends_at"] is None:
            state["remaining"] = left + value
        else:
            state["ends_at"] += value


# ---------------------------------------------------------------------------
# Background ground — ported from one of my own slide decks. Flor de Barcelona
# alternating with the Bitcoin mark on a staggered checkerboard: the B keeps its
# native 14 deg tilt, the flower stays upright, and the whole field turns 21 deg.
# Marks that would land in the live area are dropped, so it frames the screen
# instead of running under the number.
#
# The deck's geometry was tuned by eye, one variable at a time — its own notes say
# not to re-tune blind, so the angles, the stagger and the grid ratio are unchanged.
# Only two things differ here: the palette is inverted (parchment marks on ink,
# not ink on parchment), and the canvas is the live viewport rather than a slide,
# so the motif scales with the screen and survives rotating the iPad.
# ---------------------------------------------------------------------------
BTC_TILT, TILT = 14, 21           # mark tilt, whole-field rotation
REF_W = 1058                      # the deck's slide width; CELL and SIZE scale off it
CELL_REF, SIZE_REF = 40, 27       # grid spacing and flower width at REF_W
# Frame depth per side (top, right, bottom, left) as a fraction of the short side.
# Deliberately DEEPER than the 10vmin body padding: the pattern now reaches past the
# content box into the slack the clock does not use, which is what tightens the margins.
# The limit is the widest string the clock ever shows, "-MM:SS" in overtime — push the
# left/right numbers much past .13 and the pattern starts covering the minus sign.
BANDS = (0.13, 0.13, 0.13, 0.13)
A_FLOR, A_BTC = .11, .09


def load_mark(fname, ink, knockout):
    """Normalise a supplied SVG to a 100-unit box centred on (0,0).

    Each source file ships a white background rect plus white counters inside the mark.
    The background path is dropped; the counters are repainted in the ground colour so the
    mark reads as a knockout rather than a solid blob.
    """
    src = (pathlib.Path(__file__).with_name("art") / fname).read_text()
    paths = re.findall(r'<path\b[^>]*?fill="([^"]+)"[^>]*?d="\s*(.*?)"', src, re.S)
    keep = [(f, d) for f, d in paths if f.upper() != "#FFFFFF"]
    assert keep, f"no drawable path in {fname}"
    solid = [d for f, d in keep if f.upper() != "#FEFEFE"]        # bbox from the mark only
    nums = [float(n) for d in solid for n in re.findall(r"-?\d+\.?\d*", d)]
    xs, ys = nums[0::2], nums[1::2]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    k = 100 / max(max(xs) - min(xs), max(ys) - min(ys))
    body = "".join(f"<path fill='{knockout if f.upper() == '#FEFEFE' else ink}' d='{d}'/>"
                   for f, d in keep)
    return f"<g transform='scale({k:.5f}) translate({-cx:.1f},{-cy:.1f})'>{body}</g>"


def ground(w, h, ink="#f0e8d5", knockout="#010101"):
    """The framing pattern for a w x h viewport, as a standalone SVG."""
    scale = w / REF_W
    cell, size = CELL_REF * scale, SIZE_REF * scale
    short = min(w, h)
    bt, br, bb, bl = (f * short for f in BANDS)
    half = size / 2
    th = math.radians(TILT)
    cos, sin = math.cos(th), math.sin(th)
    defs = (f"<defs><g id='mflor'>{load_mark('flor-solid.svg', ink, knockout)}</g>"
            f"<g id='mbtc'>{load_mark('bitcoin-mark.svg', ink, knockout)}</g></defs>")

    # Generate across a square of the viewport's DIAGONAL — rotate a screen-sized field
    # and the corners come up bare.
    d = math.hypot(w, h) + 2 * cell
    x0, y0 = (w - d) / 2, (h - d) / 2
    out, row, y = [], 0, y0
    while y <= y0 + d:
        x, col = x0 + (cell / 2 if row % 2 else 0), 0
        while x <= x0 + d:
            # Filters run against each mark's ROTATED centre, computed by hand because the
            # group transform has not happened yet. Test the whole extent, not the centre,
            # or a mark straddles the boundary and a fragment shows inside the live area.
            rx = w / 2 + (x - w / 2) * cos - (y - h / 2) * sin
            ry = h / 2 + (x - w / 2) * sin + (y - h / 2) * cos
            in_live = (bl - half < rx < w - br + half) and (bt - half < ry < h - bb + half)
            off_screen = not (-size < rx < w + size and -size < ry < h + size)
            if not (in_live or off_screen):
                flor = (row + col) % 2 == 0
                sz = size * (1.0 if flor else .84)   # the letterform carries more ink per unit
                out.append(f"<use href='#{'mflor' if flor else 'mbtc'}' "
                           f"opacity='{A_FLOR if flor else A_BTC}' "
                           f"transform='translate({x:.1f},{y:.1f}) "
                           f"rotate({0 if flor else BTC_TILT}) scale({sz / 100:.4f})'/>")
            x += cell
            col += 1
        y += cell
        row += 1
    assert out, "the ground came out empty — check BANDS against the viewport"
    return (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}' "
            f"preserveAspectRatio='none' aria-hidden='true'>"
            f"{defs}<g transform='rotate({TILT} {w / 2} {h / 2})'>{''.join(out)}</g></svg>")



DISPLAY = """<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name=apple-mobile-web-app-capable content=yes>
<meta name=apple-mobile-web-app-status-bar-style content=black-translucent>
<meta name=theme-color content="#010101">
<link rel=apple-touch-icon href=logo.svg>
<title>Timer</title><style>
/* Barcelona Bitcoin Hub palette. Ink ground, parchment numerals, orange warning. */
:root{--ink:#010101;--paper:#f0e8d5;--orange:#f7931a}
html,body{margin:0;height:100%;overflow:hidden;background:var(--ink);
 -webkit-user-select:none;user-select:none;-webkit-tap-highlight-color:transparent}
body{display:flex;flex-direction:column;box-sizing:border-box;
 /* The clock's box. Independent of BANDS now — the pattern reaches further in. */
 padding:calc(10vmin + env(safe-area-inset-top)) calc(10vmin + env(safe-area-inset-right))
         calc(10vmin + env(safe-area-inset-bottom)) calc(10vmin + env(safe-area-inset-left))}
#ground{position:fixed;inset:0;width:100%;height:100%;pointer-events:none}
#logo{position:relative;height:20vh;margin:0 auto 1vh;flex:none}
#fit{position:relative;flex:1;width:100%;min-height:0;display:block;fill:var(--paper);
 overflow:visible}   /* ZOOM below lets the number spill into the padding */
.warn #fit{fill:var(--orange)}
.danger #fit{fill:var(--orange)}
.danger{animation:pulse 1s ease-in-out infinite}
/* Overtime: only the number changes, alternating red and parchment. The ground, the
   logo and the pattern stay put, so nothing flashes at the room except the clock. */
.over #fit{fill:#e01b24;animation:overred 1s steps(1,end) infinite}
@keyframes overred{50%{fill:var(--paper)}}
@keyframes pulse{50%{opacity:.55}}
/* WRAP IT UP: red and white, alternating. Two animations of equal duration start
   together, so the ground and the letters always swap on the same frame. */
.wrap{background:#fff;animation:wrapbg .6s steps(1,end) infinite}
.wrap #fit{fill:#e01b24;animation:wrapfg .6s steps(1,end) infinite}
.wrap{padding:0}                          /* the message goes full bleed */
.wrap #logo,.wrap #ground{display:none}   /* no frame, no logo, just the message */
@keyframes wrapbg{50%{background:#e01b24}}
@keyframes wrapfg{50%{fill:#fff}}
</style>
<img id=ground alt="">
<img id=logo src=logo.svg alt="Barcelona Bitcoin Hub">
<svg id=fit preserveAspectRatio="xMidYMid meet" aria-live=polite>
  <text id=t x=0 y=0 font-size=100 font-weight=700 text-anchor=middle
        font-family="ui-sans-serif,-apple-system,Helvetica,sans-serif"
        style="font-variant-numeric:tabular-nums">--:--</text>
</svg>
<script>
const svg = document.getElementById('fit'), txt = document.getElementById('t');

// The ground is generated for this exact viewport, so the frame hugs the real edges and
// survives rotating the iPad. Debounced: a rotate fires resize many times.
const gnd = document.getElementById('ground');
let gndTimer;
const sizeGround = () => {
  clearTimeout(gndTimer);
  gndTimer = setTimeout(() => {
    gnd.src = `ground.svg?w=${Math.round(innerWidth)}&h=${Math.round(innerHeight)}`;
  }, 150);
};
sizeGround();
addEventListener('resize', sizeGround);
const pad = n => String(n).padStart(2,'0');
let shown = null;
const ZOOM = 1.10;   // how far the number oversteps its box. The 10vmin padding is the
                     // headroom; past ~1.25 it starts touching the pattern frame.

// The SVG viewBox is set from the text's own ink box, so the number always fills the
// screen exactly — no magic font sizes, and a minus sign or an hours field cannot overflow.
const SVGNS = 'http://www.w3.org/2000/svg';

// lines is an array; one entry is the clock, two are the WRAP / IT UP message.
// getBBox() unions the tspans, so the autofit needs no special case for multi-line.
function render(lines, cls){
  const key = lines.join('|');
  if (key !== shown){
    shown = key;
    txt.textContent = '';
    lines.forEach((line, i) => {
      const ts = document.createElementNS(SVGNS, 'tspan');
      ts.setAttribute('x', 0);
      ts.setAttribute('dy', i ? '1.02em' : '0');
      ts.textContent = line;
      txt.appendChild(ts);
    });
    const b = txt.getBBox();
    // Shrinking the viewBox around the same centre scales the glyphs up by ZOOM.
    const w = b.width / ZOOM, h = b.height / ZOOM;
    svg.setAttribute('viewBox',
      `${b.x + (b.width - w) / 2} ${b.y + (b.height - h) / 2} ${w} ${h}`);
  }
  if (document.body.className !== cls) document.body.className = cls;
}

async function tick(){
  try{
    const {ms, warn, danger, wrap} = await (await fetch('state',{cache:'no-store'})).json();
    if (wrap) return render(['WRAP', 'IT UP'], 'wrap');
    const over = ms < 0, a = Math.abs(ms);
    const h = Math.floor(a/3600000), m = Math.floor(a/60000)%60, s = Math.floor(a/1000)%60;
    render([(over?'-':'') + (h?h+':':'') + pad(m) + ':' + pad(s)],
           over ? 'over' : ms < danger ? 'danger' : ms < warn ? 'warn' : '');
  }catch(e){ render(['--:--'],'') }   // server gone: show nothing rather than a frozen lie
}
tick(); setInterval(tick, 250);

// Tap anywhere for real fullscreen. Safari only grants it from a user gesture.
addEventListener('click', () => {
  const r = document.documentElement;
  (r.requestFullscreen || r.webkitRequestFullscreen)?.call(r).catch(()=>{});
});

// Best-effort only. Wake Lock needs a secure context, and this is served over plain
// http on a LAN IP, so on the iPad it does nothing — set Auto-Lock to Never instead.
// Kept because it costs three lines and works if this is ever served over https.
let lock = null;
const keepAwake = async () => {
  try{ lock = await navigator.wakeLock.request('screen') }catch(e){}
};
keepAwake();
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && !lock?.released) keepAwake();
});
</script>"""

CONTROL = """<!doctype html><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name=apple-mobile-web-app-capable content=yes>
<title>Control</title><style>
:root{color-scheme:dark}
body{margin:0;padding:16px;background:#010101;color:#f0e8d5;
 padding-bottom:calc(16px + env(safe-area-inset-bottom));
 font:600 17px/1.3 ui-sans-serif,-apple-system,Helvetica,sans-serif}
#t{font-size:15vw;text-align:center;font-variant-numeric:tabular-nums;margin:8px 0 16px}
.g{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:10px}
.g2{grid-template-columns:repeat(2,1fr)}
h2{font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:#8c8274;margin:18px 0 8px}
button{font:inherit;padding:18px 0;border:0;border-radius:12px;background:#1c1a17;color:#f0e8d5;
 -webkit-tap-highlight-color:transparent}
button:active{background:#2b2b2b}
.go{background:#f7931a;color:#010101}
.wide{grid-column:span 3}
#wrapbtn.on{background:#e01b24;color:#fff}
</style>
<div id=t>--:--</div>

<h2>Duration</h2>
<div class=g id=presets></div>

<h2>Adjust</h2>
<div class="g g2">
 <button onclick="cmd('adjust',-60000)">− 1 min</button>
 <button onclick="cmd('adjust',60000)">+ 1 min</button>
</div>

<h2>Transport</h2>
<div class=g>
 <button class=go onclick="cmd('start')">Start</button>
 <button onclick="cmd('pause')">Pause</button>
 <button onclick="cmd('restart')">Restart</button>
</div>

<h2>Message</h2>
<div class=g><button class=wide id=wrapbtn>WRAP IT UP</button></div>

<script>
const el = document.getElementById('t'), pad = n => String(n).padStart(2,'0');
document.getElementById('presets').innerHTML =
  [1,5,10,15,20,30].map(m => `<button onclick="cmd('set',${m*60000})">${m} min</button>`).join('');
const cmd = (action, value=0) =>
  fetch('cmd',{method:'POST',body:JSON.stringify({action,value})}).then(tick);
const wrapBtn = document.getElementById('wrapbtn');
let wrapOn = false;
// The button says what it will DO, and sends that explicitly. Tapping "Hide message"
// twice hides it twice — it cannot bring the message back.
wrapBtn.onclick = () => cmd('wrap', wrapOn ? 0 : 1);

async function tick(){
  const {ms, wrap} = await (await fetch('state',{cache:'no-store'})).json();
  const over = ms < 0, a = Math.abs(ms);
  el.textContent = (over?'-':'') + pad(Math.floor(a/60000)) + ':' + pad(Math.floor(a/1000)%60);
  wrapOn = wrap;
  wrapBtn.className = wrap ? 'wide on' : 'wide';
  wrapBtn.textContent = wrap ? 'Hide message' : 'WRAP IT UP';
}
tick(); setInterval(tick, 500);
</script>"""


class H(BaseHTTPRequestHandler):
    def send(self, body, ctype):
        body = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        raw, _, query = self.path.partition("?")
        path = raw.rstrip("/").rsplit("/", 1)[-1]
        if path in ("", "display"):
            self.send(DISPLAY, "text/html")
        elif path == "c":
            self.send(CONTROL, "text/html")
        elif path == "logo.svg":
            f = pathlib.Path(__file__).with_name("logo.svg")
            if not f.is_file():
                return self.send_error(404)
            # ponytail: tint white -> parchment on the way out, so the logo matches the
            # numerals without keeping a second copy of the file.
            self.send(f.read_text().replace("#fff", "#f0e8d5"), "image/svg+xml")
        elif path == "ground.svg":
            q = urllib.parse.parse_qs(query)
            try:
                w, h = int(q.get("w", ["1194"])[0]), int(q.get("h", ["834"])[0])
            except ValueError:
                return self.send_error(400, "w and h must be integers")
            if not (200 <= w <= 8000 and 200 <= h <= 8000):
                return self.send_error(400, "viewport out of range")
            self.send(ground(w, h), "image/svg+xml")
        elif path == "state":
            self.send(json.dumps(snapshot()), "application/json")
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path.rstrip("/").rsplit("/", 1)[-1] != "cmd":
            return self.send_error(404)
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"] or 0)) or "{}")
        action = body.get("action")
        if action not in ("start", "pause", "restart", "set", "adjust", "wrap"):
            return self.send_error(400, "unknown action")
        value = body.get("value", 0)
        if not isinstance(value, int) or abs(value) > 24 * 3600_000:
            return self.send_error(400, "bad value")
        apply(action, value)
        self.send(json.dumps(snapshot()), "application/json")

    def log_message(self, *a):
        pass


def check():
    """One runnable check: the only non-trivial part is the running/paused time math."""
    global now_ms
    clock = [1_000_000]
    now_ms = lambda: clock[0]
    state.update(remaining=60_000, ends_at=None)
    assert remaining_ms() == 60_000
    apply("start"); clock[0] += 10_000
    assert remaining_ms() == 50_000, remaining_ms()
    apply("adjust", 60_000)                       # +1 min while running
    assert remaining_ms() == 110_000, remaining_ms()
    apply("pause"); clock[0] += 99_000            # paused: the clock must not move it
    assert remaining_ms() == 110_000, remaining_ms()
    apply("set", 5_000); apply("start"); clock[0] += 8_000
    assert remaining_ms() == -3_000, remaining_ms()   # overtime goes negative, never clamps
    apply("restart")                                  # back to the chosen 5s, running again
    assert remaining_ms() == 5_000 and state["ends_at"] is not None, remaining_ms()
    assert state["wrap"] is False
    apply("wrap", 1); assert state["wrap"] is True
    apply("wrap", 1); assert state["wrap"] is True    # idempotent: a double tap cannot flip it
    apply("wrap", 0); assert state["wrap"] is False
    apply("wrap", 0); assert state["wrap"] is False   # off stays off, whatever the client thinks
    print("checks pass")


if __name__ == "__main__":
    import sys
    if "--check" in sys.argv:
        check(); sys.exit()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("1.1.1.1", 80))
    ip = s.getsockname()[0]; s.close()
    print(f"  iPad  →  http://{ip}:{PORT}/")
    print(f"  Phone →  http://{ip}:{PORT}/c")
    HTTPServer(("0.0.0.0", PORT), H).serve_forever()
