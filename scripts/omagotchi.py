#!/usr/bin/env python3
"""Omagotchi - Waybar tamagotchi with 8-bit pixel art sprites."""

import cairo
import json
import random
import subprocess
import sys
import time
from pathlib import Path

# ── Paths ──
STATE_DIR = Path.home() / ".local" / "state" / "omagotchi"
STATE_FILE = STATE_DIR / "state.json"
HOVER_FILE = STATE_DIR / "hover.json"
SPRITE_DIR = STATE_DIR / "sprites"
SPRITE_CSS = SPRITE_DIR / "omagotchi.css"

# ── Config (life in minutes) ──
SCALE = 3
HATCH_CLICKS = 3
LIFE_START = 1440.0       # 24 hours in minutes
DECAY_RATE = 1.0 / 60     # 1 life-min per 60 real seconds
CLICK_LIFE = 1.0           # 1 minute per click
WALK_STEPS = 6
HAPPY_SEC = 5
MISS_SEC = 300
HUNGRY_SEC = 12 * 3600     # 12 real hours without food → cry

PET_NAMES = ["tama", "neko", "usagi", "kuma", "obake", "hiyoko"]
PET_LABELS = ["Tama", "Neko", "Usagi", "Kuma", "Obake", "Hiyoko"]

# ── Palette: char -> (r, g, b) ──
C = {
    "w": (1.0, 1.0, 1.0), "k": (0.15, 0.15, 0.15),
    "g": (0.50, 0.50, 0.50), "G": (0.65, 0.65, 0.65),
    "c": (0.88, 0.48, 0.37), "D": (0.75, 0.38, 0.29),
    "a": (0.60, 0.60, 0.60), "A": (0.45, 0.45, 0.45),
    "p": (0.95, 0.75, 0.80), "P": (0.82, 0.58, 0.65),
    "b": (0.65, 0.45, 0.25), "B": (0.50, 0.33, 0.18),
    "v": (0.72, 0.62, 0.88), "V": (0.58, 0.48, 0.72),
    "y": (1.0, 0.85, 0.30), "Y": (0.88, 0.73, 0.18),
    "o": (0.95, 0.65, 0.20),
}

# ── Pet Sprites (8x7) ──
PETS = {
    "tama":   ["..cccc..", ".cccccc.", ".cDwwDc.", ".ckwwkc.", ".cccccc.", "..cDDc..", "..c..c.."],
    "neko":   ["a......a", "aa....aa", ".aaaaaa.", ".aAwwAa.", ".akwwka.", "..aAAa..", "..a..a.."],
    "usagi":  [".pp..pp.", ".pp..pp.", "..pppp..", ".pPwwPp.", ".pkwwkp.", "..pPPp..", "..p..p.."],
    "kuma":   ["bb...bb.", ".bbbbb..", ".bBwwBb.", ".bkwwkb.", "..bbbb..", "..bBb...", "..b.b..."],
    "obake":  ["..vvvv..", ".vvvvvv.", ".vVwwVv.", ".vkwwkv.", ".vvvvvv.", "..vvvv..", "..v..v.."],
    "hiyoko": ["..yyyy..", ".yyyyyy.", ".yYwwYy.", ".ykwwky.", ".yyoyyy.", "..yyyy..", "...yy..."],
}

EGG_SPRITE = ["..gGgg..", ".gGGGGg.", "gGGGGGGg", "gGGGGGGg", "gGGGGGGg", ".gGGGGg.", "..gggg.."]
DEAD_SPRITE = ["..gggg..", ".gggggg.", ".gkggkg.", ".ggkkgg.", ".gggggg.", "..gggg..", "kkkkkkkk"]

# Decorations: (rows, color, position)
DECORATIONS = {
    "sleep":  (["ww.", ".w.", "ww."], (0.60, 0.65, 0.82), "right"),
    "happy-s": ([".w.w.", "wwwww", ".www.", "..w.."], (1.0, 0.35, 0.35), "top"),
    "happy-b": (["w.w.w", "wwwww", "wwwww", ".www.", "..w.."], (1.0, 0.25, 0.25), "top"),
    "cry-1":  (["...w....w.....", ".w........w..."], (0.40, 0.60, 0.90), "tears"),
    "cry-2":  (["..ww...ww.....", "w..........w.."], (0.40, 0.60, 0.90), "tears"),
    "cry-3":  ([".ww.......ww..", "...w....w....."], (0.40, 0.60, 0.90), "tears"),
    "cry-4":  (["ww..........ww", "..w......w...."], (0.40, 0.60, 0.90), "tears"),
    "cry-5":  ([".w.........ww.", "...w....w....."], (0.40, 0.60, 0.90), "tears"),
    "cry-6":  (["..w.......w...", "ww.........ww."], (0.40, 0.60, 0.90), "tears"),
    "sick":   ([".w.", "w..", ".w."], (0.50, 0.80, 0.40), "right"),
    "miss":   (["w", "w", ".", "w"], (1.0, 0.85, 0.30), "top"),
    "scared": (["w", "w"], (1.0, 0.85, 0.30), "top"),
    "lol":    (["ww", "ww"], (0.95, 0.65, 0.20), "right"),
}

# ── Sprite Layout (logical pixels) ──
CW, CH = 14, 10   # canvas size (extra margin for tears)
BX, BY = 2, 3     # body offset (2px left margin for tears)

# ── State ──
DEFAULT_STATE = {
    "character": 0, "phase": "egg", "frame": 0,
    "pos": 0, "direction": 1,
    "last_pet": 0.0, "hatch_clicks": 0, "hatch_time": 0.0,
    "life_hours": 0.0, "total_clicks": 0, "last_tick": 0.0,
    "next_switch": 0.0, "current_idle": "sleep",
    "awake_until": 0.0, "sleep_since": 0.0, "state_version": 2,
}


def load_state():
    try:
        s = json.loads(STATE_FILE.read_text())
        for k, v in DEFAULT_STATE.items():
            s.setdefault(k, v)
        # Migrate v1 (hours) → v2 (minutes)
        if s.get("state_version", 1) < 2:
            s["life_hours"] = s.get("life_hours", 0) * 60
            s["state_version"] = 2
        return s
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULT_STATE)


def save_state(s):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(s))


# ── Sprite Generation ──
def needs_gen():
    return not SPRITE_CSS.exists() or len(list(SPRITE_DIR.glob("*.png"))) < 86


def generate_all():
    SPRITE_DIR.mkdir(parents=True, exist_ok=True)
    s = SCALE
    css = []

    css.append(f"""#custom-omagotchi {{
  background-color: transparent;
  background-repeat: no-repeat;
  background-position: 0px center;
  background-size: 33px 22px;
  min-width: 75px;
  min-height: 22px;
  padding: 0;
  font-size: 9px;
  font-family: monospace;
  color: alpha(@foreground, 0.6);
}}""")

    _render("egg", EGG_SPRITE, None, s, css)
    _render("dead", DEAD_SPRITE, None, s, css)

    for name in PET_NAMES:
        sp = PETS[name]
        _render(f"{name}-walk", sp, None, s, css)
        for st, deco in DECORATIONS.items():
            _render(f"{name}-{st}", sp, deco, s, css)

    step = 7
    for i in range(WALK_STEPS + 1):
        css.append(f"#custom-omagotchi.p{i} {{ background-position: {i*step}px center; }}")

    # Hover handled by script-side cursor detection (no CSS :hover teleport)

    SPRITE_CSS.write_text("\n\n".join(css))


def _render(name, sprite, deco, s, css):
    w, h = CW * s, CH * s
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr = cairo.Context(surf)
    cr.set_antialias(cairo.ANTIALIAS_NONE)

    # Body
    for ry, row in enumerate(sprite):
        for rx, ch in enumerate(row):
            if ch in C:
                cr.set_source_rgba(*C[ch], 1.0)
                cr.rectangle((BX + rx) * s, (BY + ry) * s, s, s)
                cr.fill()

    # Decoration
    if deco:
        drows, (dr, dg, db), pos = deco
        dw = max(len(r) for r in drows)
        dh = len(drows)
        if pos == "top":
            dx = BX + 4 - dw // 2
            dy = BY - dh - 1
        elif pos == "tears":
            dx = BX
            dy = BY + 4
        else:
            dx = BX + 9
            dy = BY
        for ry, row in enumerate(drows):
            for rx, ch in enumerate(row):
                if ch == "w":
                    cr.set_source_rgba(dr, dg, db, 1.0)
                    cr.rectangle((dx + rx) * s, (dy + ry) * s, s, s)
                    cr.fill()

    path = SPRITE_DIR / f"{name}.png"
    surf.write_to_png(str(path))
    css.append(f'#custom-omagotchi.{name} {{ background-image: url("{path}"); }}')


# ── Game Logic ──
def decay_life(state, now):
    if state["phase"] != "alive":
        return
    last = state.get("last_tick", 0)
    if last <= 0:
        state["last_tick"] = now
        return
    elapsed = max(0, now - last)
    state["life_hours"] = max(0, state["life_hours"] - elapsed * DECAY_RATE)
    state["last_tick"] = now


def compute_mood(state, now):
    if state["phase"] == "egg":
        return "egg"

    life = state["life_hours"]
    if life <= 0 and state["phase"] == "alive":
        state["phase"] = "dead"
        return "dead"

    if state["phase"] == "dead":
        return "dead"

    since = now - state.get("last_pet", 0)
    frame = state.get("frame", 0)

    # Just petted
    if since < HAPPY_SEC:
        return "happy"

    # Sick from snake bite only (set by garden)
    if now < state.get("sick_until", 0):
        return "sick"

    # Hover reaction — read from separate file (no race condition)
    try:
        hover = json.loads(HOVER_FILE.read_text())
        hover_until = hover.get("until", 0)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        hover_until = 0
    if now < hover_until:
        remaining = hover_until - now
        if remaining > 4:
            return "scared"
        if remaining > 2:
            return "lol"
        return "happy"

    # Miss — brief flash every ~30s, not permanent
    if since > MISS_SEC and frame % 30 < 3:
        return "miss"

    # Forced awake after petting — always walk, no cry
    if now < state.get("awake_until", 0):
        return "walk"

    # Mostly sleep, brief walk after timer expires
    if now >= state.get("next_switch", 0):
        if state.get("current_idle") == "sleep":
            state["current_idle"] = "walk"
            state["next_switch"] = now + random.uniform(5, 12)
        else:
            state["current_idle"] = "sleep"
            state["sleep_since"] = now
            state["next_switch"] = now + random.uniform(120, 600)

    idle = state.get("current_idle", "sleep")
    # Hungry — cry during walk if no food in 12h
    if idle == "walk" and since > HUNGRY_SEC:
        return "cry"
    return idle


# ── Commands ──
def cmd_pet():
    state = load_state()
    now = time.time()

    if state["phase"] == "egg":
        state["hatch_clicks"] += 1
        if state["hatch_clicks"] >= HATCH_CLICKS:
            state["phase"] = "alive"
            state["hatch_time"] = now
            state["last_pet"] = now
            state["life_hours"] = LIFE_START
            state["last_tick"] = now
    elif state["phase"] == "alive":
        state["last_pet"] = now
        state["life_hours"] += CLICK_LIFE
        state["total_clicks"] = state.get("total_clicks", 0) + 1
        # Wake up! Stay awake (happy + walk) then back to sleep
        awake_time = HAPPY_SEC + random.uniform(10, 20)
        state["awake_until"] = now + awake_time
        state["current_idle"] = "walk"
        state["next_switch"] = now + awake_time
    elif state["phase"] == "dead":
        state["phase"] = "egg"
        state["hatch_clicks"] = 0
        state["life_hours"] = 0
        state["total_clicks"] = 0

    save_state(state)


def cmd_display():
    if needs_gen():
        generate_all()

    state = load_state()
    now = time.time()
    decay_life(state, now)

    # Auto-detect cursor hover over widget → trigger scared/lol/happy
    if state["phase"] == "alive":
        try:
            hdata = json.loads(HOVER_FILE.read_text())
            h_active = now < hdata.get("until", 0)
            h_cooldown = now < hdata.get("cooldown", 0)
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            h_active = False
            h_cooldown = False
        if not h_active and not h_cooldown and _cursor_near_widget(state):
            _trigger_hover(now)

    mood = compute_mood(state, now)

    idx = state["character"] % len(PET_NAMES)
    name = PET_NAMES[idx]
    label = PET_LABELS[idx]

    frame = state.get("frame", 0)
    if mood == "cry":
        sprite_mood = f"cry-{(frame % 6) + 1}"
    elif mood == "happy":
        sprite_mood = "happy-s" if frame % 2 == 0 else "happy-b"
    else:
        sprite_mood = mood
    sprite_cls = sprite_mood if sprite_mood in ("egg", "dead") else f"{name}-{sprite_mood}"

    # Position
    pos = state.get("pos", 0)
    d = state.get("direction", 1)
    if mood == "scared":
        # Dash to the far edge!
        if pos < WALK_STEPS:
            pos = min(pos + 2, WALK_STEPS)
        d = -1
    elif mood == "walk":
        pos += d
        if pos >= WALK_STEPS:
            pos, d = WALK_STEPS, -1
        elif pos <= 0:
            pos, d = 0, 1
    state["pos"] = pos
    state["direction"] = d

    # Animated sleep text — builds up over time, cycles within max length
    sleep_dur = now - state.get("sleep_since", now)
    if sleep_dur < 30:
        max_z = 1
    elif sleep_dur < 60:
        max_z = 2
    elif sleep_dur < 120:
        max_z = 3
    elif sleep_dur < 300:
        max_z = 4
    elif sleep_dur < 600:
        max_z = 5
    else:
        max_z = 6
    full = "zZzZzZ"
    zlen = (frame % max_z) + 1
    ztxt = full[:zlen]
    lols = ["lol", "LOL", "haha", "xD", "hehe", "meh"]
    scares = ["!!!", "AAH", "catch me", "ARRR", "EEK", "noo", "waa", "!!"]
    mood_text = {
        "sleep":  ztxt,
        "happy":  "♡" if frame % 2 == 0 else "♥",
        "cry":    "",
        "sick":   "~@~" if frame % 2 == 0 else "~",
        "miss":   "!" if frame % 2 == 0 else "!!",
        "walk":   "",
        "egg":    "",
        "dead":   "x_x",
        "scared": scares[frame % len(scares)],
        "lol":    lols[frame % len(lols)],
    }
    text = mood_text.get(mood, "")

    # Tooltip
    life = state["life_hours"]  # in minutes
    clicks = state.get("total_clicks", 0)
    hrs, mins_left = int(life) // 60, int(life) % 60
    life_str = f"{hrs}h{mins_left:02d}m"
    if mood == "egg":
        left = HATCH_CLICKS - state["hatch_clicks"]
        tip = f"🥚 {label} egg\nClick {left}x to hatch!\nRight-click → choose pet"
    elif mood == "dead":
        tip = f"💀 {label} has passed\nClicks: {clicks}\nClick to rebirth"
    else:
        tip = f"{label} [{mood}]\n❤️ {life_str}  🖱️ {clicks}\nRight-click → choose pet"

    state["frame"] = frame + 1
    save_state(state)

    print(json.dumps({
        "text": text if text else "\u00a0",
        "tooltip": tip,
        "class": [sprite_cls, f"p{pos}"],
    }))


def _cursor_near_widget(state):
    """Check if cursor is hovering near the omagotchi widget in waybar."""
    try:
        r = subprocess.run(["hyprctl", "cursorpos"],
                           capture_output=True, text=True, timeout=0.3)
        if r.returncode != 0:
            return False
        parts = r.stdout.strip().split(",")
        x, y = int(parts[0].strip()), int(parts[1].strip())
        if y > 26:
            return False
        # Get waybar logical width fresh (adapts to resolution/scale changes)
        r2 = subprocess.run(["hyprctl", "layers", "-j"],
                            capture_output=True, text=True, timeout=0.3)
        layers = json.loads(r2.stdout)
        for data in layers.values():
            for surfaces in data.get("levels", {}).values():
                for s in surfaces:
                    if "waybar" in s.get("namespace", "").lower():
                        center = s["w"] // 2
                        return center - 80 < x < center + 200
        return False
    except Exception:
        return False


def _trigger_hover(now):
    """Write hover.json with duration and cooldown."""
    dur = random.uniform(5, 8)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    HOVER_FILE.write_text(json.dumps({
        "until": now + dur,
        "cooldown": now + dur + 12,
    }))


def cmd_hover():
    state = load_state()
    if state["phase"] != "alive":
        return
    now = time.time()
    try:
        hover = json.loads(HOVER_FILE.read_text())
        if now < hover.get("until", 0) or now < hover.get("cooldown", 0):
            return
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        pass
    if random.random() < 0.6:
        _trigger_hover(now)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--pet":
            cmd_pet()
        elif sys.argv[1] == "--hover":
            cmd_hover()
        elif sys.argv[1] == "--generate":
            generate_all()
            print("Sprites generated.")
    else:
        cmd_display()
