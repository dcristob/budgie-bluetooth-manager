import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import gi
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
from gi.repository import GLib
from bluetooth_manager.bluez_client import BlueZClient


def _make_variant_dict(py_dict):
    result = {}
    for k, v in py_dict.items():
        if isinstance(v, bool):
            inner = GLib.Variant("b", v)
        elif isinstance(v, str):
            inner = GLib.Variant("s", v)
        elif isinstance(v, int):
            inner = GLib.Variant("i", v)
        else:
            inner = v
        result[k] = GLib.Variant("v", inner)
    return result


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

        result_v = GLib.Variant("(v)", [GLib.Variant("b", True)])
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
        sender_args = [c[0][0] for c in subscribe_calls]
        self.assertIn("org.bluez", sender_args)


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


if __name__ == "__main__":
    unittest.main()
