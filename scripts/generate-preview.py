#!/usr/bin/env python3
"""Generate upscaled preview images for README."""

import cairo
from pathlib import Path

PREVIEW_DIR = Path(__file__).parent.parent / "preview"
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

SCALE = 8  # Big enough for README visibility

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
    "r": (0.92, 0.32, 0.28), "n": (0.18, 0.22, 0.15),
    "m": (0.70, 0.88, 0.70), "d": (0.88, 0.55, 0.68),
    "t": (0.78, 0.58, 0.28),
    "s": (0.30, 0.55, 0.20), "S": (0.45, 0.70, 0.30),
    "W": (0.92, 0.92, 0.92), "R": (0.85, 0.18, 0.15),
}

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

DECORATIONS = {
    "sleep":  (["ww.", ".w.", "ww."], (0.60, 0.65, 0.82), "right"),
    "happy":  ([".w.w.", "wwwww", ".www.", "..w.."], (1.0, 0.35, 0.35), "top"),
    "cry":    (["..ww...ww.....", "w..........w.."], (0.40, 0.60, 0.90), "tears"),
    "sick":   ([".w.", "w..", ".w."], (0.50, 0.80, 0.40), "right"),
    "miss":   (["w", "w", ".", "w"], (1.0, 0.85, 0.30), "top"),
    "scared": (["w", "w"], (1.0, 0.85, 0.30), "top"),
    "lol":    (["ww", "ww"], (0.95, 0.65, 0.20), "right"),
}

FOODS = {
    "onigiri": ["..ww..", ".wwww.", "wwwwww", "wnnnww", ".nnnn.", "..nn.."],
    "sushi":   [".rrrr.", "rrrrrr", "wwwwww", ".wwww."],
    "dango":   [".dd.", ".dd.", ".ww.", ".ww.", ".mm.", ".kk."],
    "ramen":   ["kwwwwk", ".yyyy.", ".yoyy.", ".yyyy.", "..kk.."],
    "mochi":   ["..mm..", ".mmmm.", "mmmmmm", ".mmmm.", "..mm.."],
    "taiyaki": ["..tt..", ".tttt.", "tttttt", ".ttkt.", "..tt.."],
    "ambrosia": ["..oo..", ".yyyy.", "yyyyyy", "kyyyyk", ".kkkk."],
    "dragon_fruit": ["..rr..", ".rVVr.", "rVwwVr", ".rVVr.", "..rr.."],
}

BIRD = ["..W..W..", ".WW..WW.", "WWWWWWWW", ".WWRWWW.", "..WWWW..", "...WW..."]

SNAKE = ["sS..", ".ss.", "..Ss"]

SAKURA = [
    "..ppp..",
    ".pwpwp.",
    "ppppppp",
    ".ppppp.",
    "...B...",
    "...B...",
    "..BBB..",
]


def render_sprite(sprite, filename, deco=None, bg_color=None):
    s = SCALE
    rows = len(sprite)
    cols = max(len(r) for r in sprite)
    # Extra margin for decorations
    mx, my = 4, 4
    cw = cols + mx * 2
    ch = rows + my * 2
    if deco:
        cw += 6
        ch += 4

    w, h = cw * s, ch * s
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr = cairo.Context(surf)
    cr.set_antialias(cairo.ANTIALIAS_NONE)

    if bg_color:
        cr.set_source_rgb(*bg_color)
        cr.rectangle(0, 0, w, h)
        cr.fill()

    bx, by = mx, my
    for ry, row in enumerate(sprite):
        for rx, ch in enumerate(row):
            if ch in C:
                cr.set_source_rgba(*C[ch], 1.0)
                cr.rectangle((bx + rx) * s, (by + ry) * s, s, s)
                cr.fill()

    if deco:
        drows, (dr, dg, db), pos = deco
        dw = max(len(r) for r in drows)
        dh = len(drows)
        if pos == "top":
            dx = bx + cols // 2 - dw // 2
            dy = by - dh - 1
        elif pos == "tears":
            dx = bx
            dy = by + 4
        else:
            dx = bx + cols + 1
            dy = by
        for ry, row in enumerate(drows):
            for rx, ch in enumerate(row):
                if ch == "w":
                    cr.set_source_rgba(dr, dg, db, 1.0)
                    cr.rectangle((dx + rx) * s, (dy + ry) * s, s, s)
                    cr.fill()

    path = PREVIEW_DIR / filename
    surf.write_to_png(str(path))
    print(f"  {filename}")


def render_gallery(sprites_dict, filename, bg_color=(0.12, 0.12, 0.15)):
    """Render all pets in a horizontal row."""
    s = SCALE
    rows = 7  # all pets are 8x7
    cols = 8
    pad = 4
    count = len(sprites_dict)
    total_w = count * (cols + pad) + pad
    total_h = rows + pad * 2

    w, h = total_w * s, total_h * s
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr = cairo.Context(surf)
    cr.set_antialias(cairo.ANTIALIAS_NONE)

    cr.set_source_rgb(*bg_color)
    cr.rectangle(0, 0, w, h)
    cr.fill()

    for i, (name, sprite) in enumerate(sprites_dict.items()):
        bx = pad + i * (cols + pad)
        by = pad
        for ry, row in enumerate(sprite):
            for rx, ch in enumerate(row):
                if ch in C:
                    cr.set_source_rgba(*C[ch], 1.0)
                    cr.rectangle((bx + rx) * s, (by + ry) * s, s, s)
                    cr.fill()

        # Label
        cr.set_source_rgb(0.7, 0.7, 0.7)
        cr.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(s * 1.2)
        cr.move_to((bx + 1) * s, (by + rows + 2.5) * s)
        cr.show_text(name.capitalize())

    total_h += 3
    # Re-render with labels space
    w2, h2 = total_w * s, (total_h) * s
    surf2 = cairo.ImageSurface(cairo.FORMAT_ARGB32, w2, h2)
    cr2 = cairo.Context(surf2)
    cr2.set_antialias(cairo.ANTIALIAS_NONE)
    cr2.set_source_rgb(*bg_color)
    cr2.rectangle(0, 0, w2, h2)
    cr2.fill()

    for i, (name, sprite) in enumerate(sprites_dict.items()):
        bx = pad + i * (cols + pad)
        by = pad
        for ry, row in enumerate(sprite):
            for rx, ch in enumerate(row):
                if ch in C:
                    cr2.set_source_rgba(*C[ch], 1.0)
                    cr2.rectangle((bx + rx) * s, (by + ry) * s, s, s)
                    cr2.fill()
        cr2.set_source_rgb(0.7, 0.7, 0.7)
        cr2.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr2.set_font_size(s * 1.2)
        cr2.move_to((bx) * s, (by + rows + 2.5) * s)
        cr2.show_text(name.capitalize())

    surf2.write_to_png(str(PREVIEW_DIR / filename))
    print(f"  {filename}")


def render_food_gallery():
    s = SCALE
    pad = 3
    items = list(FOODS.items())
    cols_per = 8
    max_rows = max(len(sp) for sp in FOODS.values())
    total_w = len(items) * (cols_per + pad) + pad
    total_h = max_rows + pad * 2 + 4
    bg = (0.12, 0.12, 0.15)

    w, h = total_w * s, total_h * s
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr = cairo.Context(surf)
    cr.set_antialias(cairo.ANTIALIAS_NONE)
    cr.set_source_rgb(*bg)
    cr.rectangle(0, 0, w, h)
    cr.fill()

    for i, (name, sprite) in enumerate(items):
        bx = pad + i * (cols_per + pad)
        by = pad + (max_rows - len(sprite)) // 2
        sw = max(len(r) for r in sprite)
        ox = (cols_per - sw) // 2
        for ry, row in enumerate(sprite):
            for rx, ch in enumerate(row):
                if ch in C:
                    cr.set_source_rgba(*C[ch], 1.0)
                    cr.rectangle((bx + ox + rx) * s, (by + ry) * s, s, s)
                    cr.fill()
        cr.set_source_rgb(0.6, 0.6, 0.6)
        cr.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(s * 0.9)
        label = name.replace("_", " ").title()[:6]
        cr.move_to((bx) * s, (pad + max_rows + 2.5) * s)
        cr.show_text(label)

    surf.write_to_png(str(PREVIEW_DIR / "foods.png"))
    print("  foods.png")


def render_garden_elements():
    s = SCALE
    # Bird + Snake + Sakura in one image
    total_w = 40
    total_h = 14
    bg = (0.84, 0.78, 0.66)

    w, h = total_w * s, total_h * s
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cr = cairo.Context(surf)
    cr.set_antialias(cairo.ANTIALIAS_NONE)
    cr.set_source_rgb(*bg)
    cr.rectangle(0, 0, w, h)
    cr.fill()

    # Sakura
    for ry, row in enumerate(SAKURA):
        for rx, ch in enumerate(row):
            if ch in C:
                cr.set_source_rgba(*C[ch], 1.0)
                cr.rectangle((2 + rx) * s, (3 + ry) * s, s, s)
                cr.fill()

    # Bird
    for ry, row in enumerate(BIRD):
        for rx, ch in enumerate(row):
            if ch in C:
                cr.set_source_rgba(*C[ch], 1.0)
                cr.rectangle((14 + rx) * s, (4 + ry) * s, s, s)
                cr.fill()

    # Snake
    for ry, row in enumerate(SNAKE):
        for rx, ch in enumerate(row):
            if ch in C:
                cr.set_source_rgba(*C[ch], 1.0)
                cr.rectangle((28 + rx) * s, (7 + ry) * s, s, s)
                cr.fill()

    # Labels
    cr.set_source_rgb(0.2, 0.2, 0.2)
    cr.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(s * 1.1)
    cr.move_to(2 * s, 12 * s)
    cr.show_text("Sakura")
    cr.move_to(14 * s, 12 * s)
    cr.show_text("Crane")
    cr.move_to(28 * s, 12 * s)
    cr.show_text("Snake")

    surf.write_to_png(str(PREVIEW_DIR / "garden-elements.png"))
    print("  garden-elements.png")


if __name__ == "__main__":
    dark_bg = (0.12, 0.12, 0.15)

    print("Generating character gallery...")
    render_gallery(PETS, "characters.png")

    print("Generating individual emotions...")
    pet = PETS["tama"]
    render_sprite(EGG_SPRITE, "egg.png", bg_color=dark_bg)
    render_sprite(DEAD_SPRITE, "dead.png", bg_color=dark_bg)
    render_sprite(pet, "walk.png", bg_color=dark_bg)
    render_sprite(pet, "sleep.png", deco=DECORATIONS["sleep"], bg_color=dark_bg)
    render_sprite(pet, "happy.png", deco=DECORATIONS["happy"], bg_color=dark_bg)
    render_sprite(pet, "cry.png", deco=DECORATIONS["cry"], bg_color=dark_bg)
    render_sprite(pet, "sick.png", deco=DECORATIONS["sick"], bg_color=dark_bg)
    render_sprite(pet, "miss.png", deco=DECORATIONS["miss"], bg_color=dark_bg)
    render_sprite(pet, "scared.png", deco=DECORATIONS["scared"], bg_color=dark_bg)
    render_sprite(pet, "lol.png", deco=DECORATIONS["lol"], bg_color=dark_bg)

    print("Generating food gallery...")
    render_food_gallery()

    print("Generating garden elements...")
    render_garden_elements()

    print("Done!")
