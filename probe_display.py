#!/usr/bin/env python3
"""Probe TCL NXTWEAR G (1bbb:af50) for display-enable HID commands.

Run this immediately after plugging in the glasses.
It tries CMD_3D/CMD_2D first (most likely candidates),
then scans 0x03-0x1f to find what gets a response.
"""
import glob, os, select, time, sys

def find_dev():
    for p in glob.glob("/sys/class/hidraw/hidraw*"):
        try:
            if "00001BBB:0000AF50" in open(p + "/device/uevent").read():
                return "/dev/" + os.path.basename(p)
        except OSError:
            pass
    return None

def send(fd, cmd, value=0, payload=b""):
    frame = bytes([0x66, cmd, value]) + payload
    os.write(fd, b"\x00" + frame.ljust(64, b"\x00"))

def drain(fd, timeout=0.3):
    replies = []
    end = time.time() + timeout
    while time.time() < end:
        if select.select([fd], [], [], 0.05)[0]:
            b = os.read(fd, 64)
            replies.append(b)
    return replies

# --- wait for device ---
print("Waiting for glasses...", flush=True)
dev = None
for _ in range(30):
    dev = find_dev()
    if dev:
        break
    time.sleep(0.1)
if not dev:
    sys.exit("Glasses not found")
print(f"Found: {dev}")

fd = os.open(dev, os.O_RDWR)

# --- device info ---
send(fd, 0x00)
for r in drain(fd, 0.3):
    print(f"  device_info reply: {r[:16].hex(' ')}")

# --- CMD_3D (0x06) and CMD_2D (0x07) with values 0 and 1 ---
for cmd, name in [(0x06, "CMD_3D"), (0x07, "CMD_2D")]:
    for val in [0, 1]:
        send(fd, cmd, val)
        replies = drain(fd, 0.3)
        tag = f"{name} val={val}"
        if replies:
            for r in replies:
                print(f"  {tag} -> {r[:16].hex(' ')}")
        else:
            print(f"  {tag} -> (no reply)")

# --- scan 0x03-0x1f ---
print("\nScanning commands 0x03..0x1f:")
for cmd in range(0x03, 0x20):
    if cmd in (0x06, 0x07):
        continue
    send(fd, cmd, 0)
    replies = drain(fd, 0.2)
    if replies:
        for r in replies:
            print(f"  cmd=0x{cmd:02x} -> {r[:16].hex(' ')}")

# --- heartbeat loop: keep sending CMD_3D every 500ms for 30s ---
print("\nSending CMD_3D heartbeat for 30s — does the display stay on?")
send(fd, 0x06, 0)
end = time.time() + 30
while time.time() < end:
    time.sleep(0.5)
    send(fd, 0x06, 0)
    if select.select([fd], [], [], 0)[0]:
        b = os.read(fd, 64)
        print(f"  rx: {b[:12].hex(' ')}")
    print(f"  heartbeat... {int(end - time.time())}s left", end="\r", flush=True)

print("\nDone.")
os.close(fd)
