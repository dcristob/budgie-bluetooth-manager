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
