#!/usr/bin/env python3
"""Minimal hidraw client for RayNeo Air 3S Pro / Air 4 Pro (TCL, 1bbb:af50).

Protocol from https://github.com/verncat/RayNeo-Air-3S-Pro-OpenVR (src/RayneoApi.cpp):
  host -> glasses: 64 bytes  [0x66, cmd, value, payload...]
  glasses -> host: 64 bytes  [0x99, type, ...]  type 0xC8 = ack/notify, 0x65 = IMU sample
"""
import glob, os, select, struct, sys, time

CMD_DEVICE_INFO, CMD_IMU_ON, CMD_IMU_OFF = 0x00, 0x01, 0x02
CMD_DISPLAY_ON = 0x07   # val=0 or 1 enables panel
CMD_BRIGHTNESS = 0x08   # val=0 max bright, val=1 black, val=20 moderate, val=80 oversaturated
CMD_3D, CMD_2D = 0x06, 0x07
ACK_COMMAND, ACK_IMU = 0xC8, 0x65

BRIGHTNESS_DEFAULT = 20


def find_dev():
    for p in glob.glob("/sys/class/hidraw/hidraw*"):
        if "00001BBB:0000AF50" in open(p + "/device/uevent").read():
            return "/dev/" + os.path.basename(p)
    sys.exit("glasses not found")


def send(fd, cmd, value=0, payload=b""):
    frame = bytes([0x66, cmd, value]) + payload[:52]
    # hidraw: leading 0x00 because the report descriptor has no report IDs
    os.write(fd, b"\x00" + frame.ljust(64, b"\x00"))


def parse_imu(b):
    acc = struct.unpack_from("<3f", b, 4)
    gyro = struct.unpack_from("<3f", b, 16)
    temp, mx, my = struct.unpack_from("<3f", b, 28)
    tick, = struct.unpack_from("<I", b, 40)
    psensor, lsensor, mz = struct.unpack_from("<3f", b, 44)
    return dict(tick=tick, acc=acc, gyro=gyro, temp=temp, mag=(mx, my, mz),
                psensor=psensor, lsensor=lsensor)


def display_on(brightness=BRIGHTNESS_DEFAULT):
    """Enable the glasses display panel and set brightness (one-shot)."""
    fd = os.open(find_dev(), os.O_RDWR)
    send(fd, CMD_DEVICE_INFO)
    time.sleep(0.1)
    send(fd, CMD_DISPLAY_ON, 0)
    time.sleep(0.05)
    send(fd, CMD_BRIGHTNESS, brightness)
    r, _, _ = select.select([fd], [], [], 0.5)
    if r:
        b = os.read(fd, 64)
        print(f"ack: {b[:12].hex(' ')}")
    os.close(fd)
    print(f"Display enabled (brightness={brightness}).")


def main(seconds=3.0):
    fd = os.open(find_dev(), os.O_RDWR)
    send(fd, CMD_DEVICE_INFO)
    send(fd, CMD_IMU_ON)
    time.sleep(0.15)
    n, t0, end = 0, time.time(), time.time() + seconds
    try:
        while time.time() < end:
            if not select.select([fd], [], [], 0.5)[0]:
                continue
            b = os.read(fd, 64)
            if len(b) < 2 or b[0] != 0x99:
                print("?", b.hex(" "))
            elif b[1] == ACK_IMU:
                n += 1
                if n % 100 == 1:
                    s = parse_imu(b)
                    print(f"imu tick={s['tick']} acc={tuple(round(v, 3) for v in s['acc'])} "
                          f"gyro={tuple(round(v, 3) for v in s['gyro'])} temp={s['temp']:.1f}")
            else:
                print(f"type=0x{b[1]:02x}", b[:24].hex(" "))
    finally:
        send(fd, CMD_IMU_OFF)
        os.close(fd)
    dt = time.time() - t0
    print(f"{n} IMU samples in {dt:.1f}s ({n / dt:.0f} Hz)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("display", "display_on"):
        display_on(int(sys.argv[2]) if len(sys.argv) > 2 else BRIGHTNESS_DEFAULT)
    else:
        main(float(sys.argv[1]) if len(sys.argv) > 1 else 3.0)
