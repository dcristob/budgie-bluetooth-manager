# Bluetooth Manager - Budgie Panel Applet

## Overview

A modern, minimal Budgie panel applet for managing Bluetooth devices on CachyOS/Budgie. Replaces blueman with a focused, clean popover UI for device pairing, connection, removal, and battery monitoring.

## Architecture

Three modules:

1. **`bluez_client.py`** - D-Bus communication layer. Uses `Gio.DBusProxy` to talk to BlueZ's `org.bluez` on the system bus. Manages adapter state (powered, discovering), device CRUD (list, pair, connect, remove), and battery level queries. Emits GLib signals on device changes so the UI stays in sync.

2. **`popover.py`** - GTK3 Budgie popover UI. Contains a header with Bluetooth on/off toggle and scan button, a scrollable device list with connected/available grouping, and per-device action buttons.

3. **`applet.py`** - Budgie plugin entry point. Implements `Budgie.Plugin` and `Budgie.Applet`. Shows a Bluetooth icon in the panel, opens the popover on click. Shows a visual indicator when devices are connected.

**Data flow:** Panel click -> popover opens -> `bluez_client` fetches current devices -> popover renders list. User actions (pair, remove, etc.) -> popover calls `bluez_client` method -> BlueZ D-Bus -> PropertiesChanged signal -> popover updates.

## Technology Stack

- Python 3 + PyGObject (gi)
- GTK 3 (required by Budgie Plugin API)
- Budgie 3.0 (`gi.require_version('Budgie', '3.0')`)
- BlueZ D-Bus API (via Gio.DBusProxy, no external dependencies)
- Meson build system

## Popover UI Layout

```
+------------------------------+
|  Bluetooth        [ON/OFF]   |
|------------------------------|
|  [Scan for devices]          |
|------------------------------|
|  Connected                   |
|  +----------------------+    |
|  | Headphones   85%   x |    |
|  | Mouse              x |    |
|  +----------------------+    |
|  Available                   |
|  +----------------------+    |
|  | Speaker      [Pair]  |    |
|  | Keyboard     [Pair]  |    |
|  +----------------------+    |
+------------------------------+
```

- Icon per device inferred from BlueZ `Icon` property (audio-headphones, input-mouse, input-keyboard, phone, generic)
- Connected devices: name, battery percentage (if available), disconnect button
- Available (paired but disconnected) devices: name, connect button
- Discovered (new) devices: name, "Pair" button
- Remove device: small trash icon button on any device row
- Scanning: Scan button shows a spinner, auto-stops after ~10 seconds
- No battery info: percentage simply omitted

## D-Bus Integration

**BlueZ interfaces:**

- `org.bluez.Adapter1` - StartDiscovery, StopDiscovery, RemoveDevice, Powered property
- `org.bluez.Device1` - Connect, Disconnect, Pair, Name, Connected, Paired, Icon, RSSI
- `org.bluez.Battery1` - Percentage property (per-device, when available)
- `org.freedesktop.DBus.ObjectManager` - GetManagedObjects for initial device list, InterfacesAdded/InterfacesRemoved for live tracking
- `org.freedesktop.DBus.Properties` - PropertiesChanged signal for real-time updates

**Connection approach:** Single Gio.DBusProxy on org.bluez at the system bus. On startup, call GetManagedObjects to enumerate all existing devices, then subscribe to InterfacesAdded/InterfacesRemoved and PropertiesChanged. No polling.

**Error handling:** D-Bus call failures surface as brief in-popover status messages that auto-dismiss after 3 seconds. No modal dialogs.

## Project Structure

```
bluetooth_manager/
  bluetooth_manager/
    __init__.py
    applet.py          # Budgie Plugin + Applet classes
    popover.py         # Popover UI
    bluez_client.py    # D-Bus/BlueZ communication
  data/
    org.budgie.BluetoothManager.plugin        # Plugin descriptor
  meson.build
```

**Installation via Meson:** Copies Python module to `/usr/lib/budgie-desktop/plugins/budgie-bluetooth-manager/`, copies `.plugin` file to the same directory. After install, applet appears in Budgie's "Add Applet" dialog.

No external Python dependencies - standard library + gi (PyGObject) only.

## Feature Scope

**Included (v1):**

- Bluetooth adapter on/off toggle
- Scan for new devices (auto-stop after 10s)
- Pair with new devices
- Connect/disconnect paired devices
- Remove (unpair and forget) devices
- Battery percentage display (when available)
- Real-time updates via D-Bus signals
- Panel icon reflects adapter state and connected device count

**Excluded:**

- Audio profile switching (A2DP/HFP)
- File transfer (OBEX)
- Device renaming
- Network/PAN tethering
- HID/input device configuration
- Multiple adapter support
- Settings/preferences panel
