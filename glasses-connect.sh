#!/bin/bash
# Auto-run when TCL VRGT782 glasses connect.
# Install: copy udev rule to /etc/udev/rules.d/99-tcl-glasses.rules

sleep 2   # let hidraw and DP nodes settle

# 1. Enable display via HID (CMD 0x09 val=1)
python3 "$(dirname "$0")/rayneo.py" display_on

# 2. Add 1080p mode and activate the glasses display output
export DISPLAY=:0
XAUTHORITY="$(ls /home/*/.Xauthority 2>/dev/null | head -1)"
export XAUTHORITY

xrandr --newmode "1920x1080_cea" 148.50 1920 2008 2052 2200 1080 1084 1089 1125 +hsync +vsync 2>/dev/null || true
xrandr --addmode DisplayPort-1 "1920x1080_cea" 2>/dev/null || true
xrandr --output DisplayPort-1 --mode "1920x1080_cea" --right-of eDP
