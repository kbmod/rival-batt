#!/usr/bin/env python3
"""Small battery monitor for the SteelSeries Rival 3 Wireless USB receiver."""
import argparse
from dataclasses import asdict, dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import threading
import time

NAME = "rival-batt"
MODEL = "Rival 3 Wireless"
VID, PID, INTERFACE = 0x1038, 0x1830, 3


@dataclass(frozen=True)
class Reading:
    level: int | None
    status: str
    checked_at: str


def decode_response(data):
    # The receiver returns the percentage followed by two status bytes.
    if len(data) < 3:
        raise ValueError("Incomplete battery response")
    if not 0 <= data[0] <= 100:
        raise ValueError("Mouse asleep, unavailable, or invalid battery response")
    return int(data[0])


def poll(hid_module=None):
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    try:
        if hid_module is None:
            import hid as hid_module
        endpoints = [d for d in hid_module.enumerate(VID, PID)
                     if d["interface_number"] == INTERFACE]
        if not endpoints:
            return Reading(None, "Receiver not found; connect the 2.4 GHz USB receiver", timestamp)
        errors = []
        for endpoint in endpoints:
            device = hid_module.device()
            try:
                device.open_path(endpoint["path"])
                if device.write(bytes([0, 0xAA, 0x01])) <= 0:
                    raise OSError("Battery request failed")
                time.sleep(0.05)
                response = device.read(64, 1000)
                if not response:
                    raise ValueError("No response; wake the mouse and refresh")
                return Reading(decode_response(response), "Battery reported by receiver", timestamp)
            except (OSError, ValueError) as error:
                errors.append(str(error))
            finally:
                device.close()
        return Reading(None, "; ".join(dict.fromkeys(errors)), timestamp)
    except (OSError, ImportError) as error:
        return Reading(None, str(error), timestamp)


def state_dir():
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "rival-batt"
    return Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state"))) / "rival-batt"


class InstanceLock:
    """OS releases the lock on exit, including after a crash."""
    def __enter__(self):
        directory = state_dir()
        directory.mkdir(parents=True, exist_ok=True)
        self.file = (directory / "instance.lock").open("a+b")
        if os.fstat(self.file.fileno()).st_size == 0:
            self.file.write(b"0")
            self.file.flush()
        self.file.seek(0)
        try:
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.file.close()
            raise RuntimeError("rival-batt is already running in the tray")
        return self

    def __exit__(self, *_):
        self.file.close()


def make_icon(level):
    from PIL import Image, ImageDraw, ImageFont
    image = Image.new("RGBA", (64, 64))
    draw = ImageDraw.Draw(image)
    color = "#94a3b8" if level is None else ("#f87171" if level <= 20 else "#5eead4")
    draw.rounded_rectangle((2, 8, 57, 56), radius=9, fill="#111827", outline=color, width=3)
    draw.rectangle((58, 23, 63, 41), fill=color)
    label = "?" if level is None else str(level)
    font = ImageFont.load_default()
    box = draw.textbbox((0, 0), label, font=font)
    text_image = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]))
    ImageDraw.Draw(text_image).text((-box[0], -box[1]), label, font=font, fill=color)
    scale = min(43 / text_image.width, 27 / text_image.height)
    text_image = text_image.resize((int(text_image.width * scale), int(text_image.height * scale)), Image.Resampling.LANCZOS)
    image.alpha_composite(text_image, (30 - text_image.width // 2, 32 - text_image.height // 2))
    return image


def run_tray(interval):
    # Prefer the indicator backend for Wayland as well as X11.
    if sys.platform.startswith("linux"):
        os.environ.setdefault("PYSTRAY_BACKEND", "appindicator")
    import pystray
    from pystray import Menu, MenuItem
    stop = threading.Event()
    refresh = threading.Event()
    current = Reading(None, "Checking battery...", "")
    last_good = None

    def refresh_now(icon, item):
        refresh.set()

    def quit_app(icon, item):
        stop.set()
        refresh.set()
        icon.stop()

    def title():
        return f"{MODEL}: {current.level}%" if current.level is not None else f"{MODEL}: unavailable"

    icon = pystray.Icon("rival-batt", make_icon(None), NAME, Menu(
        MenuItem(lambda item: title(), None, enabled=False),
        MenuItem(lambda item: current.status, None, enabled=False),
        MenuItem(lambda item: f"Checked: {current.checked_at or 'pending'}", None, enabled=False),
        MenuItem(lambda item: f"Last reading: {last_good or 'none'}", None, enabled=False),
        Menu.SEPARATOR,
        MenuItem("Refresh now", refresh_now, default=True),
        MenuItem("Quit", quit_app)))

    def worker():
        nonlocal current, last_good
        while not stop.is_set():
            refresh.clear()
            current = poll()
            if stop.is_set():
                break
            if current.level is not None:
                last_good = f"{current.level}% at {current.checked_at}"
            icon.icon = make_icon(current.level)
            icon.title = title()
            icon.update_menu()
            refresh.wait(interval)

    def setup(tray):
        tray.visible = True
        threading.Thread(target=worker, name="battery-poll", daemon=True).start()

    try:
        icon.run(setup)
    finally:
        stop.set()
        refresh.set()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Print battery and exit")
    parser.add_argument("--json", action="store_true", help="Print JSON and exit")
    parser.add_argument("--interval", type=int, default=300, metavar="SECONDS", help="Refresh interval, minimum 30 (default: 300)")
    args = parser.parse_args(argv)
    if args.interval < 30:
        parser.error("--interval must be at least 30 seconds")
    if args.once or args.json:
        result = poll()
        if args.json:
            print(json.dumps({"model": MODEL, **asdict(result)}))
        else:
            print(f"{MODEL}: {result.level}%" if result.level is not None else result.status)
        return 0 if result.level is not None else 1
    try:
        with InstanceLock():
            run_tray(args.interval)
    except Exception as error:
        message = f"{NAME}: {error}"
        if sys.platform == "win32" and sys.stderr is None:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, message, NAME, 0x10)
        else:
            print(message, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
