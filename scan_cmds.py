#!/usr/bin/env python3
"""Scan HID commands 0x00-0x1F to find what VRGT782 responds to."""
import glob, os, select, sys, time

def find_dev():
    for p in glob.glob("/sys/class/hidraw/hidraw*"):
        if "00001BBB:0000AF50" in open(p + "/device/uevent").read():
            return "/dev/" + os.path.basename(p)
    sys.exit("glasses not found")

def send(fd, cmd, value=0):
    frame = bytes([0x66, cmd, value]) + b"\x00" * 61
    os.write(fd, b"\x00" + frame)

def drain(fd, timeout=0.3):
    responses = []
    end = time.time() + timeout
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], end - time.time())
        if r:
            b = os.read(fd, 64)
            responses.append(b)
    return responses

fd = os.open(find_dev(), os.O_RDWR)
print("Scanning commands 0x00-0x1F with value=0 and value=1\n")

for cmd in range(0x20):
    for val in (0, 1):
        send(fd, cmd, val)
        resps = drain(fd, 0.25)
        if resps:
            for r in resps:
                if r[1] != 0x65:  # skip IMU
                    print(f"  CMD 0x{cmd:02x} val={val} -> {r[:16].hex(' ')}")
        time.sleep(0.05)

os.close(fd)
print("\nDone.")
