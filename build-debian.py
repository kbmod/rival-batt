"""Build a no-compilation Debian package with standard Python libraries."""
import io
from pathlib import Path
import tarfile
import time

ROOT = Path(__file__).resolve().parent


def tarball(entries):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz", format=tarfile.GNU_FORMAT) as archive:
        for name, data, mode in entries:
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(data), mode, int(time.time())
            info.uname = info.gname = "root"
            archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def build(destination):
    control = b'''Package: rival-batt
Version: 0.1.0
Section: utils
Priority: optional
Architecture: all
Maintainer: rival-batt contributors <rival-batt@example.invalid>
Depends: python3 (>= 3.10), python3-hid, python3-pystray, python3-pil, python3-gi, gir1.2-ayatanaappindicator3-0.1
Suggests: gnome-shell-extension-appindicator
Description: Small Rival 3 Wireless battery tray monitor
 Queries the 2.4 GHz USB receiver directly without SteelSeries GG.
 Includes a command-line mode for desktop-free use.
'''
    control_archive = tarball([
        ("./control", control, 0o644),
        ("./postinst", b'#!/bin/sh\nset -e\nif command -v udevadm >/dev/null 2>&1; then udevadm control --reload-rules || true; fi\nexit 0\n', 0o755),
        ("./postrm", b'#!/bin/sh\nset -e\nif command -v udevadm >/dev/null 2>&1; then udevadm control --reload-rules || true; fi\nexit 0\n', 0o755)])
    files = [
        ("./usr/bin/rival-batt", "rival_batt.py", 0o755),
        ("./usr/share/applications/rival-batt.desktop", "linux/rival-batt.desktop", 0o644),
        ("./usr/lib/udev/rules.d/70-rival-batt.rules", "linux/70-rival-batt.rules", 0o644),
        ("./usr/share/doc/rival-batt/README.md", "README.md", 0o644),
        ("./usr/share/doc/rival-batt/copyright", "LICENSE", 0o644)]
    data_archive = tarball([(name, (ROOT / source).read_bytes().replace(b'\r\n', b'\n'), mode) for name, source, mode in files])
    with Path(destination).open("wb") as output:
        output.write(b"!<arch>\n")
        for name, data in [("debian-binary", b"2.0\n"), ("control.tar.gz", control_archive), ("data.tar.gz", data_archive)]:
            header = f"{name + '/':<16}{int(time.time()):<12}{0:<6}{0:<6}{'100644':<8}{len(data):<10}`\n"
            output.write(header.encode("ascii"))
            output.write(data)
            if len(data) % 2:
                output.write(b"\n")
    print(destination)


if __name__ == "__main__":
    build(ROOT.parent / "rival-batt_0.1.0_all.deb")
