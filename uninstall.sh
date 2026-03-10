#!/bin/bash
# Omagotchi uninstaller
set -euo pipefail

WAYBAR_SCRIPTS="$HOME/.config/waybar/scripts"
WAYBAR_STYLE="$HOME/.config/waybar/style.css"
STATE_DIR="$HOME/.local/state/omagotchi"

echo "=== Omagotchi Uninstaller ==="
echo ""
echo "This will remove:"
echo "  - $WAYBAR_SCRIPTS/omagotchi*.py"
echo "  - $WAYBAR_SCRIPTS/omagotchi-hover.sh"
echo "  - $STATE_DIR/ (sprites, state, garden data)"
echo "  - CSS import from $WAYBAR_STYLE"
echo ""
echo "NOTE: You'll need to manually remove the module from waybar config.jsonc"
echo ""
read -p "Continue? [y/N] " -n 1 -r
echo
[[ $REPLY =~ ^[Yy]$ ]] || exit 0

echo "Removing scripts..."
rm -f "$WAYBAR_SCRIPTS/omagotchi.py"
rm -f "$WAYBAR_SCRIPTS/omagotchi-garden.py"
rm -f "$WAYBAR_SCRIPTS/omagotchi-select.py"
rm -f "$WAYBAR_SCRIPTS/omagotchi-hover.sh"

echo "Removing state and sprites..."
rm -rf "$STATE_DIR"

echo "Removing CSS import..."
if [ -f "$WAYBAR_STYLE" ]; then
    sed -i '/omagotchi\.css/d' "$WAYBAR_STYLE"
fi

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
fi

echo ""
echo "Omagotchi uninstalled. Goodbye!"
