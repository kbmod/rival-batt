# rival-batt

A small Windows and Debian tray utility for **SteelSeries Rival 3 Wireless, first generation**, using its **2.4 GHz USB receiver** (`1038:1830`). It queries the battery directly; SteelSeries GG is not required. Bluetooth and other mouse models are not supported by this version.

The tray icon shows the percentage, turns red at 20% or below, and refreshes every five minutes. Right-click it for details, **Refresh now**, or **Quit**. A question mark means the reading is unavailable; the previous successful reading is listed separately with its timestamp. There is no telemetry, network access, browser runtime, or background service. It sends only the battery query, and does not change mouse settings.

## Windows

Extract `rival-batt-windows-x64.zip` and double-click `rival-batt.exe`. Python does not need to be installed. Look in the tray overflow arrow if the icon is hidden. This portable executable is unsigned.

Optional startup: press Win+R, enter `shell:startup`, and place a **shortcut** to the executable there. Keep the executable in a permanent folder. Remove that shortcut to stop launching at login. Quit through the tray menu before deleting the app.

## Debian 12 / 13

Install the supplied architecture-independent package from its download folder:

```sh
sudo apt install ./rival-batt_0.1.0_all.deb
```

Reconnect the USB receiver so the new device-access rule takes effect, then launch **rival-batt** from your applications menu, or run `rival-batt`. Run it as your normal desktop user, without sudo.

The package uses Debian's Python, HIDAPI, Pillow, PyGObject, and AppIndicator libraries. GNOME needs a tray extension such as Debian's `gnome-shell-extension-appindicator`; enable it in Extensions. Other desktops need an indicator-compatible tray. CLI mode works without a desktop:

```sh
rival-batt --once
rival-batt --json
rival-batt --interval 60
```

To start at login, copy `/usr/share/applications/rival-batt.desktop` to `~/.config/autostart/` (create the folder first). To uninstall: `sudo apt remove rival-batt`, and remove your autostart copy if you made one.

Alternatively, extract the source archive and run `sh linux/install.sh`. That installs under `/usr/local`; remove that installation with `sh linux/uninstall.sh`. Choose one installation method.

## Source and development

Python 3.10 or newer is required. On Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe rival_batt.py
.\.venv\Scripts\python.exe rival_batt.py --json
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

`build-windows.ps1` builds the portable executable using PyInstaller. The executable uses a GUI subsystem, so use the source commands above for terminal output. `build-debian.py` creates the Debian package using Python's standard library, including on Windows.

## Troubleshooting and limits

* Wake the mouse and choose Refresh now if it does not respond. A receiver can report a cached battery value when the mouse sleeps; the app displays what it reports and cannot guarantee freshness inside the receiver.
* If the receiver cannot be opened, close other mouse-monitoring programs and try again. Debian permissions require a logged-in local desktop session and reconnecting the receiver after installing the udev rule.
* Battery percentages are the device's estimate; AAA battery chemistry can affect accuracy.
* A missing receiver is retried at the next refresh. Only one tray instance runs per user. No low-battery popup notifications are included.
* Hardware query and tray startup were verified on Windows with the connected Rival 3 Wireless. Debian package contents were checked, but Debian installation, permissions and GUI behavior have **not been runtime-tested**.

## Protocol reference and licenses

The USB interface and battery command were checked against [rivalcfg's Rival 3 Wireless profile](https://github.com/flozz/rivalcfg/blob/master/rivalcfg/devices/rival3_wireless.py) and [HID transport](https://github.com/flozz/rivalcfg/blob/master/rivalcfg/usbhid.py). This is an independent implementation. Dependencies retain their own licenses; Windows dependency notices are included in the portable archive. This project is MIT licensed; see LICENSE.
