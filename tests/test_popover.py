import unittest
from unittest.mock import MagicMock
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
