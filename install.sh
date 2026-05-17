#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/dcristob/budgie-bluetooth-manager.git"
INSTALL_DIR="/usr/lib/budgie-desktop/plugins/budgie-bluetooth-manager"
CLONE_DIR="$HOME/.local/share/budgie-bluetooth-manager"

if [ ! -d "$CLONE_DIR" ]; then
    echo "==> Cloning budgie-bluetooth-manager..."
    git clone "$REPO_URL" "$CLONE_DIR"
else
    echo "==> Updating budgie-bluetooth-manager..."
    git -C "$CLONE_DIR" pull
fi

echo "==> Building..."
meson setup "$CLONE_DIR/builddir" "$CLONE_DIR" --prefix=/usr 2>/dev/null || \
    meson setup "$CLONE_DIR/builddir" "$CLONE_DIR" --prefix=/usr --reconfigure

echo "==> Installing..."
sudo ninja -C "$CLONE_DIR/builddir" install

echo "==> Done. Add 'Bluetooth Manager' in Budgie's Add Applet dialog."
