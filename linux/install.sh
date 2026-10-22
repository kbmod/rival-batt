#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
sudo apt-get install python3 python3-hid python3-pystray python3-pil python3-gi gir1.2-ayatanaappindicator3-0.1
sudo install -Dm755 rival_batt.py /usr/local/bin/rival-batt
sudo install -Dm644 linux/rival-batt.desktop /usr/local/share/applications/rival-batt.desktop
sudo install -Dm644 linux/70-rival-batt.rules /etc/udev/rules.d/70-rival-batt.rules
sudo udevadm control --reload-rules
printf '\nInstalled. Reconnect your receiver, then run rival-batt.\n'
