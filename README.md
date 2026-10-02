# TCL Smart Glasses on Linux

Get TCL VRGT782 (NXTWEAR G) smart glasses working as a display and IMU device on Linux.

**USB ID:** `1bbb:af50` — T & A Mobile Phones / Smart Glasses Human Interface

Tested on: Linux 7.0, X11, AMD GPU (DisplayPort Alt Mode over USB-C)

---

## What works

- Display output (1920×1080)
- Brightness control
- IMU streaming (accelerometer, gyroscope, magnetometer, temperature) at ~1 kHz

## What does not work out of the box

The glasses expose no EDID, so Linux falls back to 640×480 and the display stays dark. The panel also needs a HID enable command that the Windows driver sends silently.

---

## Setup

### 1. udev rule (USB access + auto-enable)

Create `/etc/udev/rules.d/99-tcl-glasses.rules`:

```
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1bbb", ATTRS{idProduct}=="af50", MODE="0660", GROUP="plugdev"
SUBSYSTEM=="usb", ATTRS{idVendor}=="1bbb", ATTRS{idProduct}=="af50", RUN+="/path/to/glasses-connect.sh"
```

Reload:

```bash
sudo udevadm control --reload-rules && sudo udevadm trigger --subsystem-match=hidraw
```

Make sure your user is in the `plugdev` group:

```bash
sudo usermod -aG plugdev $USER
```

### 2. Custom display mode

The glasses have no EDID. Add a 1080p mode manually:

```bash
xrandr --newmode "1920x1080_cea" 148.50 1920 2008 2052 2200 1080 1084 1089 1125 +hsync +vsync
xrandr --addmode DisplayPort-1 "1920x1080_cea"
xrandr --output DisplayPort-1 --mode "1920x1080_cea"
```

Replace `DisplayPort-1` with the output name shown by `xrandr` for your system.

### 3. Enable the display

```bash
python3 rayneo.py display_on
# or with custom brightness (0–255, default 20):
python3 rayneo.py display_on 15
```

The glasses stay on without a keepalive — the command is one-shot.

### 4. Auto-connect (optional)

`glasses-connect.sh` runs automatically via the udev rule on plug-in. It calls `display_on` and sets up the xrandr mode. Edit the script to adjust the monitor layout (`--right-of`, `--same-as`, etc.).

---

## HID protocol

Frames are 64 bytes in each direction.

**Host → glasses:**
```
00  66  <cmd>  <value>  00 00 ... (pad to 64)
^   ^
|   magic
report ID (no report IDs used → always 0x00)
```

**Glasses → host:**
```
99  <type>  ...
^   ^
|   0xC8 = command ack, 0x65 = IMU sample
magic
```

### Commands

| Cmd  | Value | Function |
|------|-------|----------|
| 0x00 | 0     | Device info — returns firmware version / serial |
| 0x01 | 1     | IMU on |
| 0x02 | 0     | IMU off |
| 0x07 | 0     | **Display enable** |
| 0x08 | 0–255 | **Brightness** — 0 = max, 1 = off, 20 = good default, >60 = colors degrade |
| 0x06 | 1     | **AVOID** — triggers full device reset, DP link retrain, all monitors flicker |

### IMU packet layout (type 0x65, 64 bytes)

| Offset | Type    | Field      |
|--------|---------|------------|
| 4      | 3× f32  | Accel XYZ  |
| 16     | 3× f32  | Gyro XYZ   |
| 28     | f32     | Temperature |
| 28+4   | f32     | Mag X      |
| 28+8   | f32     | Mag Y      |
| 40     | u32     | Tick       |
| 44     | f32     | Proximity sensor |
| 48     | f32     | Light sensor |
| 52     | f32     | Mag Z      |

---

## Usage

```bash
# Enable display (default brightness)
python3 rayneo.py display_on

# Stream IMU for 10 seconds
python3 rayneo.py 10

# Stream IMU indefinitely
python3 rayneo.py
```

---

## Troubleshooting

**Display stays black after display_on**
Run `xrandr` and confirm `DisplayPort-1` is listed as connected. If stuck at 640×480, re-apply the custom mode.

**Permission denied on /dev/hidrawN**
Check group membership (`groups`) and that the udev rule has been reloaded. Replug the glasses after reloading.

**CMD 0x06 val=1 sent accidentally**
The glasses reset and all monitors flicker. Unplug, replug, and run `display_on` again.

**IMU data but no display**
The HID and DisplayPort interfaces are independent. Run `display_on` after the DP link is established.
