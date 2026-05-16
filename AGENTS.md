# Bluetooth Manager - Budgie Panel Applet

A modern, minimal Budgie panel applet for managing Bluetooth devices on CachyOS/Budgie.

## Project Structure

```
bluetooth_manager/
  bluetooth_manager/          # Source files (installed flat into plugin dir)
    applet.py                 # Budgie Plugin + Applet entry points
    popover.py                # GTK3 popover UI
    bluez_client.py           # BlueZ D-Bus communication layer
  data/
    org.budgie.BluetoothManager.plugin   # Budgie plugin descriptor
  tests/
    test_bluez_client.py      # Unit tests for BlueZ client (mocked D-Bus)
    test_popover.py           # UI tests
  docs/
    superpowers/specs/        # Design documents
  meson.build                 # Build system
  AGENTS.md                   # This file
```

## Tech Stack

- Python 3 + PyGObject (gi)
- GTK 3 + Budgie 3.0 plugin API
- BlueZ D-Bus (via Gio.DBusProxy)
- Meson build system
- pytest for testing

## Development

### Install for testing

```bash
meson setup builddir --prefix=/usr
sudo ninja -C builddir install
```

Then add "Bluetooth Manager" in Budgie's "Add Applet" dialog.

### Run tests

```bash
python -m pytest tests/ -v
```

### Before pushing to remote

Always run tests and verify:

```bash
python -m pytest tests/ -v
```

Ensure all tests pass before merging or pushing.
