project('budgie-bluetooth-manager', 'c')

plugin_dir = join_paths(get_option('prefix'), 'lib', 'budgie-desktop', 'plugins', 'budgie-bluetooth-manager')

install_data(
    'data/org.budgie.BluetoothManager.plugin',
    install_dir: plugin_dir,
)

py_sources = [
    'bluetooth_manager/applet.py',
    'bluetooth_manager/bluez_client.py',
    'bluetooth_manager/popover.py',
]

install_data(
    py_sources,
    install_dir: plugin_dir,
)
