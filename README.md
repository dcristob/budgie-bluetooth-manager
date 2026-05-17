# Bluetooth Manager

A modern Budgie panel applet for managing Bluetooth devices. Built for CachyOS/Budgie as a lightweight alternative to blueman.

## Features

- Toggle Bluetooth adapter on/off from the panel
- Scan for nearby devices
- Pair, connect, disconnect, and remove devices
- Device battery level display (when available)
- Live updates via BlueZ D-Bus signals
- Devices grouped by status: Connected, Paired, Discovered

## Requirements

- Budgie Desktop
- BlueZ (bluetoothd)
- Python 3 + PyGObject (`python-gobject`)
- Meson (build system)

## Install

One-liner (install or update):

```bash
bash <(curl -s https://raw.githubusercontent.com/dcristob/budgie-bluetooth-manager/main/install.sh)
```

Or build manually:

```bash
meson setup builddir --prefix=/usr
sudo ninja -C builddir install
```

Then add "Bluetooth Manager" in Budgie's "Add Applet" dialog.

## Update

Re-run the install script — it pulls the latest changes and reinstalls.

## Uninstall

```bash
sudo rm -rf /usr/lib/budgie-desktop/plugins/budgie-bluetooth-manager
rm -rf ~/.local/share/budgie-bluetooth-manager
```

## Development

### Run tests

```bash
python -m pytest tests/ -v
```

### Debug logging

Enable with `BT_MANAGER_DEBUG=1` before loading the applet. Logs go to `~/.local/state/bt-manager/debug.log`.

## License

[MIT](LICENSE)
