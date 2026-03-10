#!/usr/bin/env python3
"""Omagotchi character selection popup."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
import json
import fcntl
import sys
from pathlib import Path

STATE_DIR = Path.home() / ".local" / "state" / "omagotchi"
STATE_FILE = STATE_DIR / "state.json"
SPRITE_DIR = STATE_DIR / "sprites"
LOCK_FILE = STATE_DIR / "select.lock"

PET_NAMES = ["tama", "neko", "usagi", "kuma", "obake", "hiyoko"]
PET_LABELS = ["Tama", "Neko", "Usagi", "Kuma", "Obake", "Hiyoko"]


def load_state():
    try:
        return json.loads(STATE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {"character": 0, "phase": "egg"}


def save_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state))


class SelectWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Choose Your Pet")
        self.set_default_size(320, 220)
        self.set_resizable(False)
        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        self.set_position(Gtk.WindowPosition.CENTER)

        state = load_state()
        current = state.get("character", 0)

        grid = Gtk.Grid()
        grid.set_column_spacing(8)
        grid.set_row_spacing(8)
        grid.set_column_homogeneous(True)
        grid.set_margin_top(12)
        grid.set_margin_bottom(12)
        grid.set_margin_start(12)
        grid.set_margin_end(12)

        for i, (name, label) in enumerate(zip(PET_NAMES, PET_LABELS)):
            col, row = i % 3, i // 3

            btn = Gtk.Button()
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

            sprite_path = SPRITE_DIR / f"{name}-walk.png"
            if sprite_path.exists():
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    str(sprite_path), 48, 48, True)
                img = Gtk.Image.new_from_pixbuf(pixbuf)
            else:
                img = Gtk.Label(label="?")

            box.pack_start(img, True, True, 0)
            box.pack_start(Gtk.Label(label=label), False, False, 0)
            btn.add(box)

            if i == current:
                btn.get_style_context().add_class("current")

            btn.connect("clicked", self.on_select, i)
            grid.attach(btn, col, row, 1, 1)

        self.add(grid)

        css = Gtk.CssProvider()
        css.load_from_data(b"""
            window { background-color: #2a2a2a; }
            button {
                background-color: #3a3a3a;
                color: white;
                border: 2px solid #555;
                border-radius: 8px;
                padding: 8px;
                min-width: 70px;
            }
            button:hover { background-color: #4a4a4a; border-color: #E07A5F; }
            button.current { border-color: #E07A5F; background-color: #4a3a35; }
            label { color: white; font-size: 11px; }
        """)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.show_all()

    def on_select(self, _btn, idx):
        state = load_state()
        state["character"] = idx
        state["phase"] = "egg"
        state["hatch_clicks"] = 0
        state["hatch_time"] = 0.0
        state["life_hours"] = 0.0
        state["total_clicks"] = 0
        state["frame"] = 0
        state["pos"] = 0
        state["last_pet"] = 0.0
        save_state(state)
        self.destroy()


def main():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    lock = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        sys.exit(0)

    win = SelectWindow()
    win.connect("destroy", Gtk.main_quit)
    Gtk.main()


if __name__ == "__main__":
    main()
