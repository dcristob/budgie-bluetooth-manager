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
        return result[0]

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
                "name": props.get("Name", "Unknown"),
                "connected": props.get("Connected", False),
                "paired": props.get("Paired", False),
                "icon": props.get("Icon", "bluetooth"),
                "rssi": props.get("RSSI", -70),
                "battery": None,
            }
            if BATTERY_IFACE in interfaces:
                bat_props = interfaces[BATTERY_IFACE]
                device["battery"] = bat_props.get("Percentage", 0)
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
