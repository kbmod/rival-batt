#!/bin/sh
set -eu
sudo rm -f /usr/local/bin/rival-batt /usr/local/share/applications/rival-batt.desktop /etc/udev/rules.d/70-rival-batt.rules
rm -f "${XDG_CONFIG_HOME:-$HOME/.config}/autostart/rival-batt.desktop"
sudo udevadm control --reload-rules
printf 'Removed rival-batt. Shared Python dependencies were retained.\n'
