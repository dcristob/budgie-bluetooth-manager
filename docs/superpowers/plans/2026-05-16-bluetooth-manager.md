# Bluetooth Manager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Budgie panel applet for managing Bluetooth devices with a clean popover UI.

**Architecture:** Python Budgie applet (GTK3) with a BlueZ D-Bus client layer and a popover UI. Three modules: `bluez_client.py` (D-Bus), `popover.py` (UI), `applet.py` (plugin entry point).

**Tech Stack:** Python 3 + PyGObject, GTK 3, Budgie 3.0 API, BlueZ D-Bus (Gio.DBusProxy), Meson build, pytest

---

## File Structure

| File | Purpose |
|------|---------|
| `bluetooth_manager/__init__.py` | Package marker, empty |
| `bluetooth_manager/bluez_client.py` | BlueZ D-Bus communication: adapter control, device CRUD, battery, live signals |
| `bluetooth_manager/popover.py` | GTK3 Budgie popover: device list, toggle, scan, actions |
| `bluetooth_manager/applet.py` | Budgie.Plugin + Budgie.Applet: panel icon, popover wiring |
| `data/org.budgie.BluetoothManager.plugin` | Budgie plugin descriptor |
| `meson.build` | Build system: install plugin files |
| `tests/test_bluez_client.py` | Unit tests for bluez_client with mocked D-Bus |
| `tests/test_popover.py` | Unit tests for popover UI logic |

---

### Task 1: Project scaffold and Meson build

**Files:**
- Create: `bluetooth_manager/__init__.py`
- Create: `meson.build`
- Create: `data/org.budgie.BluetoothManager.plugin`

- [ ] **Step 1: Create package and directories**

```bash
mkdir -p bluetooth_manager data tests
touch bluetooth_manager/__init__.py tests/__init__.py
```

- [ ] **Step 2: Create the Budgie plugin descriptor**

Write `data/org.budgie.BluetoothManager.plugin`:

```ini
[Plugin]
Module=bluetooth_manager
Name=Bluetooth Manager
Description=Manage Bluetooth devices from the Budgie panel
Authors=dcristob
Website=
Icon=bluetooth-symbolic
```

- [ ] **Step 3: Create meson.build**

Write `meson.build`:

```meson
project('budgie-bluetooth-manager', 'c')

plugin_dir = join_paths(get_option('prefix'), 'lib', 'budgie-desktop', 'plugins', 'budgie-bluetooth-manager')

install_data(
    'data/org.budgie.BluetoothManager.plugin',
    install_dir: plugin_dir,
)

py_sources = [
    'bluetooth_manager/__init__.py',
    'bluetooth_manager/applet.py',
    'bluetooth_manager/bluez_client.py',
    'bluetooth_manager/popover.py',
]

install_data(
    py_sources,
    install_dir: join_paths(plugin_dir, 'bluetooth_manager'),
)
```

- [ ] **Step 4: Verify build configures**

Run: `meson setup builddir --prefix=/usr`
Expected: build configuration succeeds with no errors.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "chore: scaffold project with meson build and plugin descriptor"
```

---

### Task 2: BlueZ client - adapter and device listing

**Files:**
- Create: `bluetooth_manager/bluez_client.py`
- Create: `tests/test_bluez_client.py`

- [ ] **Step 1: Write failing tests for adapter power and device listing**

Write `tests/__init__.py` (empty, already created in Task 1).

Write `tests/test_bluez_client.py`:

```python
import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import gi
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import GLib
from bluetooth_manager.bluez_client import BlueZClient


def _make_variant_dict(py_dict):
    return {k: GLib.Variant("v", v) for k, v in py_dict.items()}


def _make_get_managed_objects_result(devices, adapter_powered=True):
    objects = {}
    objects["/org/bluez/hci0"] = {
        "org.bluez.Adapter1": _make_variant_dict({
            "Powered": adapter_powered,
            "Name": "test-host",
            "Address": "00:00:00:00:00:00",
            "Discovering": False,
        }),
    }
    for dev in devices:
        path = dev["path"]
        dev_props = _make_variant_dict({
            "Name": dev.get("name", "Unknown"),
            "Connected": dev.get("connected", False),
            "Paired": dev.get("paired", False),
            "Icon": dev.get("icon", "bluetooth"),
            "RSSI": dev.get("rssi", -70),
        })
        interfaces = {"org.bluez.Device1": dev_props}
        if dev.get("battery") is not None:
            interfaces["org.bluez.Battery1"] = _make_variant_dict({
                "Percentage": dev["battery"],
            })
        objects[path] = interfaces
    return GLib.Variant("(a{oa{sa{sv}}})", [objects])


class TestBlueZClientAdapter(unittest.TestCase):
    @patch("bluetooth_manager.bluez_client.Gio")
    def test_get_adapter_powered(self, mock_gio):
        mock_bus = MagicMock()
        mock_gio.bus_get_sync.return_value = mock_bus
        mock_gio.BusType.SYSTEM = 2
        mock_gio.DBusCallFlags.NONE = 0

        result_v = GLib.Variant("(v)", [True])
        mock_bus.call_sync.return_value = result_v

        client = BlueZClient()
        self.assertTrue(client.adapter_powered)

    @patch("bluetooth_manager.bluez_client.Gio")
    def test_set_adapter_powered(self, mock_gio):
        mock_bus = MagicMock()
        mock_gio.bus_get_sync.return_value = mock_bus
        mock_gio.BusType.SYSTEM = 2
        mock_gio.DBusCallFlags.NONE = 0

        client = BlueZClient()
        client.set_adapter_powered(False)
        mock_bus.call_sync.assert_called()


class TestBlueZClientDevices(unittest.TestCase):
    @patch("bluetooth_manager.bluez_client.Gio")
    def test_get_devices(self, mock_gio):
        mock_bus = MagicMock()
        mock_gio.bus_get_sync.return_value = mock_bus
        mock_gio.BusType.SYSTEM = 2
        mock_gio.DBusCallFlags.NONE = 0

        devices_data = [
            {
                "path": "/org/bluez/hci0/dev_34_88_5D_42_45_AD",
                "name": "Keyboard K380",
                "connected": True,
                "paired": True,
                "icon": "input-keyboard",
            },
            {
                "path": "/org/bluez/hci0/dev_D0_6A_E7_00_03_2E",
                "name": "M720 Triathlon",
                "connected": True,
                "paired": True,
                "icon": "input-mouse",
                "battery": 100,
            },
            {
                "path": "/org/bluez/hci0/dev_80_99_E7_6E_7A_97",
                "name": "LinkBuds Open",
                "connected": False,
                "paired": True,
                "icon": "audio-headset",
            },
        ]
        mock_bus.call_sync.return_value = _make_get_managed_objects_result(devices_data)

        client = BlueZClient()
        devices = client.get_devices()

        self.assertEqual(len(devices), 3)
        keyboard = [d for d in devices if d["name"] == "Keyboard K380"][0]
        self.assertTrue(keyboard["connected"])
        self.assertIsNone(keyboard["battery"])

        mouse = [d for d in devices if d["name"] == "M720 Triathlon"][0]
        self.assertEqual(mouse["battery"], 100)

        earbuds = [d for d in devices if d["name"] == "LinkBuds Open"][0]
        self.assertFalse(earbuds["connected"])
        self.assertTrue(earbuds["paired"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_bluez_client.py -v`
Expected: FAIL - `ModuleNotFoundError: No module named 'bluetooth_manager'` or `ImportError`

- [ ] **Step 3: Implement BlueZClient with adapter control and device listing**

Write `bluetooth_manager/bluez_client.py`:

```python
import gi
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gio, GLib, GObject

BLUEZ_BUS = "org.bluez"
BLUEZ_PATH = "/"
ADAPTER_PATH = "/org/bluez/hci0"
ADAPTER_IFACE = "org.bluez.Adapter1"
DEVICE_IFACE = "org.bluez.Device1"
BATTERY_IFACE = "org.bluez.Battery1"
OBJECT_MANAGER_IFACE = "org.freedesktop.DBus.ObjectManager"
PROPS_IFACE = "org.freedesktop.DBus.Properties"


class BlueZClient(GObject.GObject):
    __gtype_name__ = "BlueZClient"

    __gsignals__ = {
        "device-changed": (GObject.SignalFlags.RUN_LAST, None, (str,)),
        "device-added": (GObject.SignalFlags.RUN_LAST, None, (str,)),
        "device-removed": (GObject.SignalFlags.RUN_LAST, None, (str,)),
        "adapter-changed": (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        self._bus = Gio.bus_get_sync(Gio.BusType.SYSTEM)

    @property
    def adapter_powered(self):
        result = self._bus.call_sync(
            BLUEZ_BUS, ADAPTER_PATH,
            PROPS_IFACE, "Get",
            GLib.Variant("(ss)", (ADAPTER_IFACE, "Powered")),
            GLib.VariantType("(v)"),
            Gio.DBusCallFlags.NONE, -1, None,
        )
        return result[0].get_boolean()

    def set_adapter_powered(self, powered):
        self._bus.call_sync(
            BLUEZ_BUS, ADAPTER_PATH,
            PROPS_IFACE, "Set",
            GLib.Variant("(ssv)", (ADAPTER_IFACE, "Powered", GLib.Variant("b", powered))),
            None,
            Gio.DBusCallFlags.NONE, -1, None,
        )
        self.emit("adapter-changed")

    def get_devices(self):
        result = self._bus.call_sync(
            BLUEZ_BUS, BLUEZ_PATH,
            OBJECT_MANAGER_IFACE, "GetManagedObjects",
            None, GLib.VariantType("(a{oa{sa{sv}}})"),
            Gio.DBusCallFlags.NONE, -1, None,
        )
        devices = []
        for path, interfaces in result[0].items():
            if DEVICE_IFACE not in interfaces:
                continue
            props = interfaces[DEVICE_IFACE]
            device = {
                "path": path,
                "name": props.get("Name", GLib.Variant("s", "Unknown")).get_string(),
                "connected": props.get("Connected", GLib.Variant("b", False)).get_boolean(),
                "paired": props.get("Paired", GLib.Variant("b", False)).get_boolean(),
                "icon": props.get("Icon", GLib.Variant("s", "bluetooth")).get_string(),
                "rssi": props.get("RSSI", GLib.Variant("n", -70)).get_int16(),
                "battery": None,
            }
            if BATTERY_IFACE in interfaces:
                bat_props = interfaces[BATTERY_IFACE]
                device["battery"] = bat_props.get("Percentage", GLib.Variant("y", 0)).get_byte()
            devices.append(device)
        return devices

    def start_discovery(self):
        self._bus.call_sync(
            BLUEZ_BUS, ADAPTER_PATH,
            ADAPTER_IFACE, "StartDiscovery",
            None, None,
            Gio.DBusCallFlags.NONE, -1, None,
        )

    def stop_discovery(self):
        self._bus.call_sync(
            BLUEZ_BUS, ADAPTER_PATH,
            ADAPTER_IFACE, "StopDiscovery",
            None, None,
            Gio.DBusCallFlags.NONE, -1, None,
        )

    def pair_device(self, device_path):
        self._bus.call_sync(
            BLUEZ_BUS, device_path,
            DEVICE_IFACE, "Pair",
            None, None,
            Gio.DBusCallFlags.NONE, -1, None,
        )

    def connect_device(self, device_path):
        self._bus.call_sync(
            BLUEZ_BUS, device_path,
            DEVICE_IFACE, "Connect",
            None, None,
            Gio.DBusCallFlags.NONE, -1, None,
        )

    def disconnect_device(self, device_path):
        self._bus.call_sync(
            BLUEZ_BUS, device_path,
            DEVICE_IFACE, "Disconnect",
            None, None,
            Gio.DBusCallFlags.NONE, -1, None,
        )

    def remove_device(self, device_path):
        self._bus.call_sync(
            BLUEZ_BUS, ADAPTER_PATH,
            ADAPTER_IFACE, "RemoveDevice",
            GLib.Variant("(o)", (device_path,)),
            None,
            Gio.DBusCallFlags.NONE, -1, None,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_bluez_client.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add bluetooth_manager/bluez_client.py tests/test_bluez_client.py
git commit -m "feat: add BlueZ client with adapter control and device listing"
```

---

### Task 3: BlueZ client - D-Bus signal monitoring

**Files:**
- Modify: `bluetooth_manager/bluez_client.py`
- Modify: `tests/test_bluez_client.py`

- [ ] **Step 1: Write failing tests for signal subscription**

Append to `tests/test_bluez_client.py`:

```python
class TestBlueZClientSignals(unittest.TestCase):
    @patch("bluetooth_manager.bluez_client.Gio")
    def test_signal_subscription_calls_bus_signal_subscribe(self, mock_gio):
        mock_bus = MagicMock()
        mock_gio.bus_get_sync.return_value = mock_bus
        mock_gio.BusType.SYSTEM = 2
        mock_gio.DBusSignalFlags.NONE = 0

        client = BlueZClient()
        client.subscribe_signals()

        subscribe_calls = mock_bus.signal_subscribe.call_args_list
        self.assertTrue(len(subscribe_calls) >= 3)
        sender_args = [c[0][1] for c in subscribe_calls]
        self.assertIn("org.bluez", sender_args)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_bluez_client.py::TestBlueZClientSignals -v`
Expected: FAIL - `AttributeError: 'BlueZClient' object has no attribute 'subscribe_signals'`

- [ ] **Step 3: Implement signal subscription**

Add to `BlueZClient` in `bluetooth_manager/bluez_client.py`. Add the `subscribe_signals` method after `__init__`:

```python
    def subscribe_signals(self):
        self._bus.signal_subscribe(
            BLUEZ_BUS,
            OBJECT_MANAGER_IFACE,
            "InterfacesAdded",
            BLUEZ_PATH,
            None,
            Gio.DBusSignalFlags.NONE,
            self._on_interfaces_added,
            None,
        )
        self._bus.signal_subscribe(
            BLUEZ_BUS,
            OBJECT_MANAGER_IFACE,
            "InterfacesRemoved",
            BLUEZ_PATH,
            None,
            Gio.DBusSignalFlags.NONE,
            self._on_interfaces_removed,
            None,
        )
        self._bus.signal_subscribe(
            BLUEZ_BUS,
            PROPS_IFACE,
            "PropertiesChanged",
            None,
            None,
            Gio.DBusSignalFlags.NONE,
            self._on_properties_changed,
            None,
        )

    def _on_interfaces_added(self, connection, sender, path, iface, signal, params):
        object_path, interfaces = params
        if DEVICE_IFACE in interfaces:
            self.emit("device-added", object_path)

    def _on_interfaces_removed(self, connection, sender, path, iface, signal, params):
        object_path, interfaces = params
        if DEVICE_IFACE in interfaces:
            self.emit("device-removed", object_path)

    def _on_properties_changed(self, connection, sender, path, iface, signal, params):
        if iface == ADAPTER_IFACE:
            self.emit("adapter-changed")
        elif iface in (DEVICE_IFACE, BATTERY_IFACE):
            self.emit("device-changed", path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_bluez_client.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add bluetooth_manager/bluez_client.py tests/test_bluez_client.py
git commit -m "feat: add D-Bus signal monitoring for live device updates"
```

---

### Task 4: Popover UI - header and device list

**Files:**
- Create: `bluetooth_manager/popover.py`
- Create: `tests/test_popover.py`

- [ ] **Step 1: Write failing tests for popover construction**

Write `tests/test_popover.py`:

```python
import unittest
from unittest.mock import MagicMock, patch
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Budgie", "3.0")
from gi.repository import Gtk
from bluetooth_manager.popover import BluetoothPopover


class TestBluetoothPopover(unittest.TestCase):
    def test_popover_has_toggle(self):
        popover = BluetoothPopover(MagicMock())
        toggle = popover._toggle
        self.assertIsNotNone(toggle)
        self.assertIsInstance(toggle, Gtk.Switch)

    def test_popover_has_scan_button(self):
        popover = BluetoothPopover(MagicMock())
        scan_btn = popover._scan_button
        self.assertIsNotNone(scan_btn)

    def test_refresh_populates_device_rows(self):
        mock_client = MagicMock()
        mock_client.get_devices.return_value = [
            {
                "path": "/org/bluez/hci0/dev_AA",
                "name": "Test Headphones",
                "connected": True,
                "paired": True,
                "icon": "audio-headphones",
                "battery": 85,
            },
            {
                "path": "/org/bluez/hci0/dev_BB",
                "name": "Test Mouse",
                "connected": False,
                "paired": True,
                "icon": "input-mouse",
                "battery": None,
            },
        ]
        popover = BluetoothPopover(mock_client)
        popover.refresh_devices()

        rows = popover._device_rows
        self.assertEqual(len(rows), 2)

    def test_toggle_calls_client(self):
        mock_client = MagicMock()
        popover = BluetoothPopover(mock_client)
        popover._toggle.set_active(True)
        mock_client.set_adapter_powered.assert_called_with(True)

    def test_scan_calls_start_discovery(self):
        mock_client = MagicMock()
        popover = BluetoothPopover(mock_client)
        popover._on_scan_clicked(None)
        mock_client.start_discovery.assert_called_once()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_popover.py -v`
Expected: FAIL - `ModuleNotFoundError: No module named 'bluetooth_manager.popover'`

- [ ] **Step 3: Implement the popover**

Write `bluetooth_manager/popover.py`:

```python
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Budgie", "3.0")
from gi.repository import Budgie, GObject, Gtk, GLib


class BluetoothPopover(Budgie.Popover):
    __gtype_name__ = "BluetoothPopover"

    SCAN_TIMEOUT_SECONDS = 10

    def __init__(self, client, parent=None):
        Budgie.Popover.__init__(self, relative_to=parent)
        self._client = client
        self._device_rows = []

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(12)
        box.set_margin_end(12)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        label = Gtk.Label("Bluetooth")
        label.set_halign(Gtk.Align.START)
        label.get_style_context().add_class("heading")
        self._toggle = Gtk.Switch()
        self._toggle.set_halign(Gtk.Align.END)
        self._toggle.set_hexpand(True)
        self._toggle.connect("notify::active", self._on_toggle_changed)
        header.pack_start(label, False, False, 0)
        header.pack_end(self._toggle, False, False, 0)
        box.add(header)

        self._scan_button = Gtk.Button(label="Scan for devices")
        self._scan_button.connect("clicked", self._on_scan_clicked)
        box.add(self._scan_button)

        self._spinner = Gtk.Spinner()
        self._spinner.set_no_show_all(True)
        box.add(self._spinner)

        self._status_label = Gtk.Label()
        self._status_label.set_no_show_all(True)
        self._status_label.get_style_context().add_class("dim-label")
        box.add(self._status_label)

        self._device_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_max_content_height(300)
        scrolled.add(self._device_list)
        box.add(scrolled)

        self.add(box)
        box.show_all()
        self._spinner.hide()
        self._status_label.hide()

    def refresh_devices(self):
        for row in self._device_rows:
            row.destroy()
        self._device_rows = []

        try:
            devices = self._client.get_devices()
        except Exception:
            self._show_status("Error loading devices")
            return

        connected = [d for d in devices if d["connected"]]
        paired = [d for d in devices if d["paired"] and not d["connected"]]
        unpaired = [d for d in devices if not d["paired"]]

        if connected:
            self._add_section_header("Connected")
            for dev in connected:
                self._add_device_row(dev)

        if paired:
            self._add_section_header("Paired")
            for dev in paired:
                self._add_device_row(dev)

        if unpaired:
            self._add_section_header("Discovered")
            for dev in unpaired:
                self._add_device_row(dev)

        if not devices:
            self._show_status("No devices found")

        self._device_list.show_all()

    def _add_section_header(self, text):
        label = Gtk.Label()
        label.set_markup(f"<b>{text}</b>")
        label.set_halign(Gtk.Align.START)
        label.set_margin_top(6)
        self._device_list.add(label)

    def _add_device_row(self, dev):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.set_margin_top(2)
        row.set_margin_bottom(2)

        icon = Gtk.Image.new_from_icon_name(dev["icon"], Gtk.IconSize.MENU)
        row.pack_start(icon, False, False, 0)

        name_label = Gtk.Label(label=dev["name"])
        name_label.set_halign(Gtk.Align.START)
        name_label.set_hexpand(True)
        row.pack_start(name_label, True, True, 0)

        if dev["battery"] is not None:
            bat_label = Gtk.Label(label=f"{dev['battery']}%")
            bat_label.get_style_context().add_class("dim-label")
            row.pack_start(bat_label, False, False, 0)

        if dev["connected"]:
            btn = Gtk.Button.new_from_icon_name("list-remove-symbolic", Gtk.IconSize.MENU)
            btn.set_tooltip_text("Disconnect")
            btn.connect("clicked", self._on_disconnect_clicked, dev["path"])
            row.pack_start(btn, False, False, 0)
        elif dev["paired"]:
            btn = Gtk.Button.new_from_icon_name("list-add-symbolic", Gtk.IconSize.MENU)
            btn.set_tooltip_text("Connect")
            btn.connect("clicked", self._on_connect_clicked, dev["path"])
            row.pack_start(btn, False, False, 0)
        else:
            btn = Gtk.Button(label="Pair")
            btn.connect("clicked", self._on_pair_clicked, dev["path"])
            row.pack_start(btn, False, False, 0)

        remove_btn = Gtk.Button.new_from_icon_name("edit-delete-symbolic", Gtk.IconSize.MENU)
        remove_btn.set_tooltip_text("Remove device")
        remove_btn.connect("clicked", self._on_remove_clicked, dev["path"])
        row.pack_start(remove_btn, False, False, 0)

        self._device_list.add(row)
        self._device_rows.append(row)

    def _on_toggle_changed(self, switch, param):
        self._client.set_adapter_powered(switch.get_active())

    def _on_scan_clicked(self, button):
        self._scan_button.set_sensitive(False)
        self._spinner.start()
        self._spinner.show()
        try:
            self._client.start_discovery()
        except Exception as e:
            self._show_status(f"Scan failed: {e}")
            self._scan_button.set_sensitive(True)
            self._spinner.stop()
            self._spinner.hide()
            return
        GLib.timeout_add_seconds(self.SCAN_TIMEOUT_SECONDS, self._stop_scan)

    def _stop_scan(self):
        try:
            self._client.stop_discovery()
        except Exception:
            pass
        self._spinner.stop()
        self._spinner.hide()
        self._scan_button.set_sensitive(True)
        self.refresh_devices()
        return False

    def _on_connect_clicked(self, button, path):
        try:
            self._client.connect_device(path)
        except Exception as e:
            self._show_status(f"Connect failed: {e}")
        self.refresh_devices()

    def _on_disconnect_clicked(self, button, path):
        try:
            self._client.disconnect_device(path)
        except Exception as e:
            self._show_status(f"Disconnect failed: {e}")
        self.refresh_devices()

    def _on_pair_clicked(self, button, path):
        try:
            self._client.pair_device(path)
        except Exception as e:
            self._show_status(f"Pair failed: {e}")
        self.refresh_devices()

    def _on_remove_clicked(self, button, path):
        try:
            self._client.remove_device(path)
        except Exception as e:
            self._show_status(f"Remove failed: {e}")
        self.refresh_devices()

    def _show_status(self, message):
        self._status_label.set_text(message)
        self._status_label.show()
        GLib.timeout_add_seconds(3, self._hide_status)

    def _hide_status(self):
        self._status_label.hide()
        return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_popover.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add bluetooth_manager/popover.py tests/test_popover.py
git commit -m "feat: add popover UI with device list, toggle, and scan"
```

---

### Task 5: Budgie applet plugin entry point

**Files:**
- Create: `bluetooth_manager/applet.py`

- [ ] **Step 1: Implement the Budgie Plugin and Applet classes**

Write `bluetooth_manager/applet.py`:

```python
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Budgie", "3.0")
gi.require_version("Gio", "2.0")
from gi.repository import Budgie, GObject, Gtk, Gio, GLib
from bluetooth_manager.bluez_client import BlueZClient
from bluetooth_manager.popover import BluetoothPopover


class BluetoothManagerPlugin(GObject.GObject, Budgie.Plugin):
    __gtype_name__ = "BluetoothManagerPlugin"

    def __init__(self):
        GObject.Object.__init__(self)

    def do_get_panel_widget(self, uuid):
        return BluetoothManagerApplet(uuid)


class BluetoothManagerApplet(Budgie.Applet):
    __gtype_name__ = "BluetoothManagerApplet"

    def __init__(self, uuid):
        Budgie.Applet.__init__(self)
        self._uuid = uuid
        self._client = BlueZClient()
        self._client.subscribe_signals()

        self._box = Gtk.EventBox()
        self._icon = Gtk.Image.new_from_icon_name(
            "bluetooth-symbolic", Gtk.IconSize.MENU
        )
        self._box.add(self._icon)
        self.add(self._box)

        self._popover = BluetoothPopover(self._client, self._box)

        self._box.connect("button-press-event", self._on_click)

        self._client.connect("adapter-changed", self._on_adapter_changed)
        self._client.connect("device-changed", self._on_device_changed)
        self._client.connect("device-added", self._on_device_changed)
        self._client.connect("device-removed", self._on_device_changed)

        GLib.idle_add(self._update_icon)

        self._box.show_all()
        self.show_all()

    def _on_click(self, widget, event):
        if event.button == 1:
            self._popover.refresh_devices()
            self._popover.popup()

    def _on_adapter_changed(self, client):
        GLib.idle_add(self._update_icon)

    def _on_device_changed(self, client, path=None):
        GLib.idle_add(self._update_icon)
        if self._popover.is_visible():
            GLib.idle_add(self._popover.refresh_devices)

    def _update_icon(self):
        try:
            powered = self._client.adapter_powered
        except Exception:
            powered = False
        icon_name = "bluetooth-symbolic" if powered else "bluetooth-disabled-symbolic"
        self._icon.set_from_icon_name(icon_name, Gtk.IconSize.MENU)
        return False
```

- [ ] **Step 2: Verify module imports cleanly**

Run: `python -c "from bluetooth_manager.applet import BluetoothManagerPlugin, BluetoothManagerApplet; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add bluetooth_manager/applet.py
git commit -m "feat: add Budgie plugin and applet entry point"
```

---

### Task 6: Integration test and install verification

**Files:**
- Modify: `tests/test_bluez_client.py`

- [ ] **Step 1: Add integration-level test for full client flow**

Append to `tests/test_bluez_client.py`:

```python
class TestBlueZClientActions(unittest.TestCase):
    @patch("bluetooth_manager.bluez_client.Gio")
    def test_pair_calls_device_pair(self, mock_gio):
        mock_bus = MagicMock()
        mock_gio.bus_get_sync.return_value = mock_bus
        mock_gio.BusType.SYSTEM = 2
        mock_gio.DBusCallFlags.NONE = 0

        client = BlueZClient()
        client.pair_device("/org/bluez/hci0/dev_AA")
        call_args = mock_bus.call_sync.call_args
        self.assertIn("Pair", str(call_args))

    @patch("bluetooth_manager.bluez_client.Gio")
    def test_connect_calls_device_connect(self, mock_gio):
        mock_bus = MagicMock()
        mock_gio.bus_get_sync.return_value = mock_bus
        mock_gio.BusType.SYSTEM = 2
        mock_gio.DBusCallFlags.NONE = 0

        client = BlueZClient()
        client.connect_device("/org/bluez/hci0/dev_AA")
        call_args = mock_bus.call_sync.call_args
        self.assertIn("Connect", str(call_args))

    @patch("bluetooth_manager.bluez_client.Gio")
    def test_remove_calls_adapter_remove_device(self, mock_gio):
        mock_bus = MagicMock()
        mock_gio.bus_get_sync.return_value = mock_bus
        mock_gio.BusType.SYSTEM = 2
        mock_gio.DBusCallFlags.NONE = 0

        client = BlueZClient()
        client.remove_device("/org/bluez/hci0/dev_AA")
        call_args = mock_bus.call_sync.call_args
        self.assertIn("RemoveDevice", str(call_args))
```

- [ ] **Step 2: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: Verify meson install would install all files**

Run: `sudo ninja -C builddir install && ls /usr/lib/budgie-desktop/plugins/budgie-bluetooth-manager/`
Expected: Shows `bluetooth_manager/` directory and `org.budgie.BluetoothManager.plugin`

- [ ] **Step 4: Commit**

```bash
git add tests/test_bluez_client.py
git commit -m "test: add integration tests for client device actions"
```

---

### Task 7: Final commit and .gitignore

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: Create .gitignore**

Write `.gitignore`:

```
__pycache__/
*.pyc
*.pyo
builddir/
*.egg-info/
dist/
.pytest_cache/
```

- [ ] **Step 2: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: add .gitignore"
```
