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

```bash
meson setup builddir --prefix=/usr
sudo ninja -C builddir install
```

Then add "Bluetooth Manager" in Budgie's "Add Applet" dialog.

## Uninstall

```bash
sudo ninja -C builddir uninstall
```

## Development

### Run tests

```bash
python -m pytest tests/ -v
```

### Debug logging

Logs are written to `/tmp/bt-manager-debug.log` when the applet is loaded.

## License

[MIT](LICENSE)
