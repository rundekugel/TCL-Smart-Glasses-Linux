#!/usr/bin/env python3
"""Dump raw 64-byte input reports from the TCL glasses (1bbb:af50)."""
import glob, os, select, sys, time

def find_dev():
    for p in glob.glob("/sys/class/hidraw/hidraw*"):
        if "00001BBB:0000AF50" in open(p + "/device/uevent").read():
            return "/dev/" + os.path.basename(p)
    sys.exit("glasses not found")

dev = find_dev()
fd = os.open(dev, os.O_RDWR)
print(f"opened {dev}; Ctrl-C to stop", file=sys.stderr)
prev, t0 = None, time.time()
while True:
    r, _, _ = select.select([fd], [], [], 2.0)
    if not r:
        print(f"{time.time()-t0:8.3f} (no data)")
        continue
    data = os.read(fd, 64)
    if data != prev:  # print only changes to keep the stream readable
        print(f"{time.time()-t0:8.3f} {data.hex(' ')}")
        prev = data
