#!/usr/bin/env python3
"""Try each candidate command individually for 5s to find which one keeps the display on."""
import glob, os, select, sys, time

CANDIDATES = [0x07, 0x08, 0x09, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f,
              0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x17, 0x18, 0x19, 0x1a,
              0x1b, 0x1d, 0x1e, 0x1f]

def find_dev():
    for p in glob.glob("/sys/class/hidraw/hidraw*"):
        if "00001BBB:0000AF50" in open(p + "/device/uevent").read():
            return "/dev/" + os.path.basename(p)
    sys.exit("glasses not found")

def send(fd, cmd, value=0):
    frame = bytes([0x66, cmd, value]) + b"\x00" * 61
    os.write(fd, b"\x00" + frame)

fd = os.open(find_dev(), os.O_RDWR)
test_cmd = int(sys.argv[1], 16) if len(sys.argv) > 1 else None

if test_cmd is not None:
    val = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    print(f"Sending CMD 0x{test_cmd:02x} val={val} once — watch display for 5s...")
    send(fd, 0x00)
    time.sleep(0.1)
    send(fd, test_cmd, val)
    r, _, _ = select.select([fd], [], [], 0.5)
    if r:
        b = os.read(fd, 64)
        print(f"  ack: {b[:12].hex(' ')}")
    print("Waiting 5s — did display come on?")
    time.sleep(5)
    print("Done.")
else:
    print("Sending each candidate ONCE — note which cmd lights up the display.\n")
    send(fd, 0x00)
    time.sleep(0.1)
    for cmd in CANDIDATES:
        for val in (0, 1):
            print(f"CMD 0x{cmd:02x} val={val}", flush=True)
            try:
                send(fd, cmd, val)
                r, _, _ = select.select([fd], [], [], 0.3)
                if r:
                    b = os.read(fd, 64)
                    if b[1] != 0x65:
                        print(f"  ack: {b[:12].hex(' ')}")
            except OSError as e:
                print(f"  !!! device error (glasses reset) — replug and restart")
                os.close(fd)
                sys.exit(1)
            time.sleep(0.5)  # long enough to notice display change

os.close(fd)
print("All done.")
