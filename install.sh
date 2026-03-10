#!/bin/bash
# Omagotchi installer for Omarchy (Arch Linux + Hyprland + Waybar)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WAYBAR_SCRIPTS="$HOME/.config/waybar/scripts"
WAYBAR_CONFIG="$HOME/.config/waybar/config.jsonc"
WAYBAR_STYLE="$HOME/.config/waybar/style.css"
STATE_DIR="$HOME/.local/state/omagotchi"
SPRITE_CSS="$STATE_DIR/sprites/omagotchi.css"

echo "=== Omagotchi Installer ==="
echo ""

# ── Check dependencies ──
missing=()
python3 -c "import cairo" 2>/dev/null || missing+=("python-cairo (pycairo)")
python3 -c "import gi; gi.require_version('Gtk','3.0')" 2>/dev/null || missing+=("python-gobject + gtk3")
command -v hyprctl &>/dev/null || missing+=("hyprland")
command -v waybar &>/dev/null || missing+=("waybar")

if [ ${#missing[@]} -gt 0 ]; then
    echo "Missing dependencies:"
    for m in "${missing[@]}"; do
        echo "  - $m"
    done
    echo ""
    echo "Install with: sudo pacman -S python-cairo python-gobject gtk3"
    echo ""
    read -p "Continue anyway? [y/N] " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]] || exit 1
fi

# ── Backup waybar config ──
BACKUP="$HOME/.config/waybar.bak.$(date +%s)"
echo "Backing up waybar config to $BACKUP..."
cp -r "$HOME/.config/waybar" "$BACKUP"

# ── Copy scripts ──
echo "Copying scripts to $WAYBAR_SCRIPTS..."
mkdir -p "$WAYBAR_SCRIPTS"
cp "$SCRIPT_DIR/scripts/omagotchi.py" "$WAYBAR_SCRIPTS/omagotchi.py"
cp "$SCRIPT_DIR/scripts/omagotchi-garden.py" "$WAYBAR_SCRIPTS/omagotchi-garden.py"
cp "$SCRIPT_DIR/scripts/omagotchi-select.py" "$WAYBAR_SCRIPTS/omagotchi-select.py"
cp "$SCRIPT_DIR/scripts/omagotchi-hover.sh" "$WAYBAR_SCRIPTS/omagotchi-hover.sh"
chmod +x "$WAYBAR_SCRIPTS/omagotchi-hover.sh"

# ── Generate sprites ──
echo "Generating sprites..."
python3 "$WAYBAR_SCRIPTS/omagotchi.py" --generate

# ── Add CSS import to waybar style ──
IMPORT_LINE="@import \"$SPRITE_CSS\";"
if [ -f "$WAYBAR_STYLE" ]; then
    if ! grep -qF "$IMPORT_LINE" "$WAYBAR_STYLE"; then
        echo "Adding CSS import to $WAYBAR_STYLE..."
        echo "$IMPORT_LINE" >> "$WAYBAR_STYLE"
    else
        echo "CSS import already present in $WAYBAR_STYLE"
    fi
else
    echo "Creating $WAYBAR_STYLE with CSS import..."
    echo "$IMPORT_LINE" > "$WAYBAR_STYLE"
fi

# ── Add waybar module config ──
OMAGOTCHI_MODULE='"custom/omagotchi"'
if grep -qF "$OMAGOTCHI_MODULE" "$WAYBAR_CONFIG" 2>/dev/null; then
    echo "Waybar module already configured in $WAYBAR_CONFIG"
else
    echo ""
    echo "Add this module to your waybar config ($WAYBAR_CONFIG):"
    echo ""
    echo '  1. Add "custom/omagotchi" to your modules-center (or modules-left/right):'
    echo '     "modules-center": ["clock", "custom/omagotchi"],'
    echo ""
    echo '  2. Add this module definition:'
    cat <<'JSONC'
  "custom/omagotchi": {
    "exec": "python3 ~/.config/waybar/scripts/omagotchi.py",
    "return-type": "json",
    "interval": 1,
    "on-click": "python3 ~/.config/waybar/scripts/omagotchi.py --pet",
    "on-click-middle": "python3 ~/.config/waybar/scripts/omagotchi-select.py",
    "on-click-right": "python3 ~/.config/waybar/scripts/omagotchi-garden.py",
    "on-scroll-up": "python3 ~/.config/waybar/scripts/omagotchi.py --hover",
    "on-scroll-down": "python3 ~/.config/waybar/scripts/omagotchi.py --hover",
    "format": "{}",
    "tooltip": true
  }
JSONC
    echo ""
fi

# ── Restart waybar ──
echo ""
read -p "Restart waybar now? [Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    if command -v omarchy-restart-waybar &>/dev/null; then
        omarchy-restart-waybar
    else
        killall waybar 2>/dev/null || true
        waybar &disown
    fi
    echo "Waybar restarted!"
fi

echo ""
echo "=== Omagotchi installed! ==="
echo ""
echo "Controls:"
echo "  Left-click   -> Pet (+1 min life) / Hatch egg"
echo "  Middle-click -> Choose character"
echo "  Right-click  -> Open Zen Garden"
echo "  Scroll       -> Hover reaction"
echo ""
echo "Your pet starts as an egg. Click 3 times to hatch!"
