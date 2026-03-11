#!/usr/bin/env python3
"""Omagotchi Zen Garden - 8-bit pixel art interactive popup."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
import cairo
import math
import random
import json
import time
import fcntl
import sys
from pathlib import Path

SCALE = 4
LW, LH = 120, 80
WIN_W, WIN_H = LW * SCALE, LH * SCALE
FPS = 8

STATE_DIR = Path.home() / ".local" / "state" / "omagotchi"
STATE_FILE = STATE_DIR / "state.json"
GARDEN_FILE = STATE_DIR / "garden.json"
LOCK_FILE = STATE_DIR / "garden.lock"

PET_NAMES = ["tama", "neko", "usagi", "kuma", "obake", "hiyoko"]

# ── Palette ──
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
    # Food
    "r": (0.92, 0.32, 0.28), "n": (0.18, 0.22, 0.15),
    "m": (0.70, 0.88, 0.70), "d": (0.88, 0.55, 0.68),
    "t": (0.78, 0.58, 0.28),
    # Bird
    "W": (0.92, 0.92, 0.92), "R": (0.85, 0.18, 0.15),
    # Snake
    "s": (0.30, 0.55, 0.20), "S": (0.45, 0.70, 0.30),
}

# ── Pet Sprites ──
PETS = {
    "tama":   ["..cccc..", ".cccccc.", ".cDwwDc.", ".ckwwkc.", ".cccccc.", "..cDDc..", "..c..c.."],
    "neko":   ["a......a", "aa....aa", ".aaaaaa.", ".aAwwAa.", ".akwwka.", "..aAAa..", "..a..a.."],
    "usagi":  [".pp..pp.", ".pp..pp.", "..pppp..", ".pPwwPp.", ".pkwwkp.", "..pPPp..", "..p..p.."],
    "kuma":   ["bb...bb.", ".bbbbb..", ".bBwwBb.", ".bkwwkb.", "..bbbb..", "..bBb...", "..b.b..."],
    "obake":  ["..vvvv..", ".vvvvvv.", ".vVwwVv.", ".vkwwkv.", ".vvvvvv.", "..vvvv..", "..v..v.."],
    "hiyoko": ["..yyyy..", ".yyyyyy.", ".yYwwYy.", ".ykwwky.", ".yyoyyy.", "..yyyy..", "...yy..."],
}

# ── Food Sprites with life values and rarity weights ──
FOODS = {
    "onigiri": {
        "name": "Onigiri", "life": 3, "weight": 30,
        "sprite": ["..ww..", ".wwww.", "wwwwww", "wnnnww", ".nnnn.", "..nn.."],
    },
    "sushi": {
        "name": "Sushi", "life": 6, "weight": 20,
        "sprite": [".rrrr.", "rrrrrr", "wwwwww", ".wwww."],
    },
    "dango": {
        "name": "Dango", "life": 4, "weight": 25,
        "sprite": [".dd.", ".dd.", ".ww.", ".ww.", ".mm.", ".kk."],
    },
    "ramen": {
        "name": "Ramen", "life": 8, "weight": 15,
        "sprite": ["kwwwwk", ".yyyy.", ".yoyy.", ".yyyy.", "..kk.."],
    },
    "mochi": {
        "name": "Mochi", "life": 3, "weight": 25,
        "sprite": ["..mm..", ".mmmm.", "mmmmmm", ".mmmm.", "..mm.."],
    },
    "taiyaki": {
        "name": "Taiyaki", "life": 5, "weight": 20,
        "sprite": ["..tt..", ".tttt.", "tttttt", ".ttkt.", "..tt.."],
    },
    "ambrosia": {
        "name": "Ambrosia", "life": 20, "weight": 2,
        "sprite": ["..oo..", ".yyyy.", "yyyyyy", "kyyyyk", ".kkkk."],
    },
    "dragon_fruit": {
        "name": "Dragon Fruit", "life": 35, "weight": 1,
        "sprite": ["..rr..", ".rVVr.", "rVwwVr", ".rVVr.", "..rr.."],
    },
}

FOOD_KEYS = list(FOODS.keys())
FOOD_WEIGHTS = [FOODS[k]["weight"] for k in FOOD_KEYS]

# ── Bird Frames ──
BIRD = [
    ["..W..W..", ".WW..WW.", "WWWWWWWW", ".WWRWWW.", "..WWWW..", "...WW..."],
    ["........", "........", "WWWWWWWW", "WWWRWWWW", "WWWWWWWW", ".WW..WW."],
]

ROCK = ["..gGg.", ".gGGGg", "gkgGkg", "ggGGgg", ".gggg."]

# ── Snake Frames ──
SNAKE_FRAMES = [
    ["sS..", ".ss.", "..Ss"],
    ["..Ss", ".ss.", "sS.."],
]

# ── Sakura Tree ──
SAKURA = [
    "..ppp..",
    ".pwpwp.",
    "ppppppp",
    ".ppppp.",
    "...B...",
    "...B...",
    "..BBB..",
]


def draw_px(cr, sprite, x, y, flip=False):
    s = SCALE
    for ry, row in enumerate(sprite):
        w = len(row)
        for rx, ch in enumerate(row):
            if ch in C:
                cr.set_source_rgb(*C[ch])
                fx = (w - 1 - rx) if flip else rx
                cr.rectangle((x + fx) * s, (y + ry) * s, s, s)
                cr.fill()


def load_json(path, default):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(default)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


class Pet:
    def __init__(self, kind, x, y):
        self.kind = kind
        self.x, self.y = float(x), float(y)
        self.target_x = self.x
        self.flip = False
        self.eat_t = 0
        self.joy = 0
        self.sick_t = 0

    def update(self):
        if self.eat_t > 0:
            self.eat_t -= 1
            return
        if self.sick_t > 0:
            self.sick_t -= 1
            return
        dx = self.target_x - self.x
        if abs(dx) > 0.8:
            self.x += 0.6 if dx > 0 else -0.6
            self.flip = dx < 0
        elif random.random() < 0.03:
            self.target_x = random.randint(12, LW - 20)
        if self.joy > 0:
            self.joy -= 1

    def draw(self, cr):
        sprite = PETS.get(self.kind, PETS["tama"])
        draw_px(cr, sprite, int(self.x), int(self.y), self.flip)
        s = SCALE
        if self.sick_t > 0 and self.sick_t % 3 != 0:
            # Sick swirl
            cr.set_source_rgb(0.50, 0.80, 0.40)
            sx = (int(self.x) + 9) * s
            sy = (int(self.y) + 1) * s
            for dx, dy in [(0, 1), (1, 0), (2, 1), (1, 2)]:
                cr.rectangle(sx + dx * s, sy + dy * s, s, s)
            cr.fill()
        elif self.joy > 0 and self.joy % 3 != 0:
            # Heart
            cr.set_source_rgb(1, 0.35, 0.35)
            hx = (int(self.x) + 3) * s
            hy = (int(self.y) - 4) * s
            for dx, dy in [(0, 1), (1, 0), (2, 1), (1, 2), (3, 0), (4, 1)]:
                cr.rectangle(hx + dx * s, hy + dy * s, s, s)
            cr.fill()

    def contains(self, mx, my):
        return self.x - 3 <= mx <= self.x + 11 and self.y - 3 <= my <= self.y + 10


class FlyingBird:
    def __init__(self):
        self.x = -14.0
        self.y = float(random.randint(4, 18))
        self.food = random.choices(FOOD_KEYS, weights=FOOD_WEIGHTS, k=1)[0]
        self.speed = random.uniform(0.3, 0.65)
        self.phase = random.uniform(0, 6.28)
        self.frame = 0

    def update(self):
        self.x += self.speed
        self.frame = (self.frame + 1) % 8
        return self.x < LW + 15

    def draw(self, cr):
        bx = int(self.x)
        by = int(self.y + math.sin(self.x * 0.07 + self.phase) * 3)
        draw_px(cr, BIRD[self.frame // 4], bx, by)
        draw_px(cr, FOODS[self.food]["sprite"], bx + 1, by + 7)

    def contains(self, mx, my):
        return self.x - 2 <= mx <= self.x + 12 and self.y - 5 <= my <= self.y + 16


class Snake:
    def __init__(self, pet_x):
        side = random.choice(["left", "right"])
        self.x = -6.0 if side == "left" else float(LW + 2)
        self.y = float(random.randint(35, 60))
        self.speed = random.uniform(0.15, 0.3)
        self.frame = 0
        self.flip = side == "right"

    def update(self, pet):
        dx = pet.x - self.x
        dy = pet.y + 4 - self.y
        dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
        self.x += (dx / dist) * self.speed
        self.y += (dy / dist) * self.speed
        self.flip = dx < 0
        self.frame = (self.frame + 1) % 8
        return dist > 4

    def draw(self, cr):
        draw_px(cr, SNAKE_FRAMES[self.frame // 4], int(self.x), int(self.y), self.flip)

    def contains(self, mx, my):
        return self.x - 2 <= mx <= self.x + 6 and self.y - 1 <= my <= self.y + 5


class Garden(Gtk.Window):
    def __init__(self):
        super().__init__(title="Omagotchi Garden")
        self.set_default_size(WIN_W, WIN_H)
        self.set_resizable(False)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.state = load_json(STATE_FILE, {
            "character": 0, "phase": "egg", "last_pet": 0,
        })
        self.gstate = load_json(GARDEN_FILE, {"inventory": {}})
        self.inv = self.gstate.get("inventory", {})

        if self.state.get("phase") == "dead":
            self._show_dead_garden()
            return
        if self.state.get("phase") == "egg":
            self._show_dead_garden()
            return
        self.state["last_pet"] = time.time()
        save_json(STATE_FILE, self.state)

        kind = PET_NAMES[self.state.get("character", 0) % len(PET_NAMES)]
        self.pet = Pet(kind, LW // 2, 48)
        self.birds = []
        self.snakes = []
        self.rocks = [(20, 40), (75, 32), (48, 55)]
        self.sakuras = [(6, 18), (98, 22)]
        self.msg = ""
        self.msg_t = 0

        da = Gtk.DrawingArea()
        da.connect("draw", self.on_draw)
        da.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        da.connect("button-press-event", self.on_click)
        self.add(da)
        self.da = da

        GLib.timeout_add(1000 // FPS, self.tick)
        GLib.timeout_add(3500, self.spawn_bird)
        GLib.timeout_add(random.randint(8000, 15000), self.spawn_snake)
        self.spawn_bird()
        self.show_all()

    def _show_dead_garden(self):
        phase = self.state.get("phase", "egg")
        msg = "Your pet has passed. Click to rebirth." if phase == "dead" else "Your egg hasn't hatched yet."
        dialog = Gtk.MessageDialog(
            transient_for=self,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=msg,
        )
        dialog.run()
        dialog.destroy()
        self.destroy()

    def spawn_bird(self):
        if len(self.birds) < 3:
            self.birds.append(FlyingBird())
        return True

    def spawn_snake(self):
        if len(self.snakes) < 2:
            self.snakes.append(Snake(self.pet.x))
        GLib.timeout_add(random.randint(10000, 20000), self.spawn_snake)
        return False

    def tick(self):
        self.pet.update()
        self.birds = [b for b in self.birds if b.update()]

        # Update snakes — check if any reach the pet
        alive_snakes = []
        for snake in self.snakes:
            if snake.update(self.pet):
                alive_snakes.append(snake)
            else:
                # Snake reached pet — attack!
                self.pet.sick_t = 16
                self.state["life_hours"] = max(0, self.state.get("life_hours", 0) - 30)
                self.state["sick_until"] = time.time() + 30
                save_json(STATE_FILE, self.state)
                self.notify("Snake bite! -30m")
        self.snakes = alive_snakes

        if self.msg_t > 0:
            self.msg_t -= 1
        self.da.queue_draw()
        return True

    def notify(self, text):
        self.msg = text
        self.msg_t = 16

    def on_click(self, w, ev):
        mx, my = ev.x / SCALE, ev.y / SCALE

        # Kill snake
        for snake in list(self.snakes):
            if snake.contains(mx, my):
                self.snakes.remove(snake)
                self.notify("Snake killed!")
                return

        # Catch bird food
        for bird in list(self.birds):
            if bird.contains(mx, my):
                name = FOODS[bird.food]["name"]
                self.inv[bird.food] = self.inv.get(bird.food, 0) + 1
                self.birds.remove(bird)
                self.notify(f"Caught {name}!")
                self.save_garden()
                return

        # Feed / pet the pet
        if self.pet.contains(mx, my):
            for key in FOOD_KEYS:
                if self.inv.get(key, 0) > 0:
                    self.inv[key] -= 1
                    if self.inv[key] <= 0:
                        del self.inv[key]
                    food = FOODS[key]
                    self.pet.eat_t = 6
                    self.pet.joy = 16
                    self.state["last_pet"] = time.time()
                    self.state["life_hours"] = self.state.get("life_hours", 0) + food["life"]
                    self.state["total_clicks"] = self.state.get("total_clicks", 0) + 1
                    save_json(STATE_FILE, self.state)
                    self.save_garden()
                    self.notify(f"Fed {food['name']}! +{food['life']}m")
                    return
            # No food, just pet
            self.pet.joy = 10
            self.state["last_pet"] = time.time()
            self.state["life_hours"] = self.state.get("life_hours", 0) + 1
            self.state["total_clicks"] = self.state.get("total_clicks", 0) + 1
            save_json(STATE_FILE, self.state)
            self.notify("Pet! +1m  Catch birds for food!")

    def save_garden(self):
        self.gstate["inventory"] = self.inv
        save_json(GARDEN_FILE, self.gstate)

    def on_draw(self, w, cr):
        cr.set_antialias(cairo.ANTIALIAS_NONE)
        s = SCALE

        # ── Sand background ──
        cr.set_source_rgb(0.84, 0.78, 0.66)
        cr.rectangle(0, 0, WIN_W, WIN_H)
        cr.fill()

        # ── Raked sand lines ──
        cr.set_source_rgb(0.79, 0.73, 0.61)
        cr.set_line_width(s * 0.5)
        for i in range(0, LH, 3):
            cr.move_to(0, i * s)
            for px in range(0, WIN_W, 3):
                cr.line_to(px, i * s + math.sin(px * 0.015 + i * 0.4) * s * 1.8)
            cr.stroke()

        # ── Sakura trees ──
        for sx, sy in self.sakuras:
            draw_px(cr, SAKURA, sx, sy)

        # ── Rocks with concentric rings ──
        for rx, ry in self.rocks:
            cr.set_source_rgb(0.79, 0.73, 0.61)
            cr.set_line_width(s * 0.4)
            cx, cy = (rx + 3) * s, (ry + 2) * s
            for rad in range(4, 8):
                cr.arc(cx, cy, rad * s, 0, 2 * math.pi)
                cr.stroke()
            draw_px(cr, ROCK, rx, ry)

        # ── Snakes ──
        for snake in self.snakes:
            snake.draw(cr)

        # ── Flying birds with food ──
        for bird in self.birds:
            bird.draw(cr)

        # ── Pet ──
        self.pet.draw(cr)

        # ── Bottom inventory panel ──
        panel_y = (LH - 12) * s
        cr.set_source_rgba(0.10, 0.10, 0.10, 0.88)
        cr.rectangle(0, panel_y, WIN_W, 12 * s)
        cr.fill()

        ix = 1
        for key in FOOD_KEYS:
            count = self.inv.get(key, 0)
            draw_px(cr, FOODS[key]["sprite"], ix, LH - 10)
            cr.set_source_rgb(1, 1, 1)
            cr.select_font_face("monospace",
                                cairo.FONT_SLANT_NORMAL,
                                cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(9)
            cr.move_to((ix + 6) * s, (LH - 5) * s)
            cr.show_text(str(count))
            ix += 14

        # ── Notification ──
        if self.msg_t > 0:
            cr.select_font_face("monospace",
                                cairo.FONT_SLANT_NORMAL,
                                cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(14)
            ext = cr.text_extents(self.msg)
            bw = ext.width + 6 * s
            bx = (WIN_W - bw) / 2
            cr.set_source_rgba(0.08, 0.08, 0.08, 0.88)
            cr.rectangle(bx, 1 * s, bw, 7 * s)
            cr.fill()
            cr.set_source_rgb(1, 1, 1)
            cr.move_to(bx + 3 * s, 6 * s)
            cr.show_text(self.msg)


def main():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    lock = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        sys.exit(0)

    win = Garden()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    main()
