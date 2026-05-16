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
        label = Gtk.Label(label="Bluetooth")
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
