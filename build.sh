#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python not found or not executable: $PYTHON_BIN"
  exit 1
fi

"$PYTHON_BIN" "$ROOT_DIR/tools/generate_icon.py"

ICON_PATH="$ROOT_DIR/assets/app_icon.ico"
if [[ "$(uname -s)" == "Darwin" ]]; then
  ICON_PATH="$ROOT_DIR/assets/app_icon.icns"
fi

"$PYTHON_BIN" -m PyInstaller \
  --noconfirm \
  --clean \
  --name "FTS_Scanner" \
  --windowed \
  --paths "$ROOT_DIR/src" \
  --hidden-import pyvisa \
  --hidden-import pyvisa_py \
  --add-data "$ROOT_DIR/ximc:ximc" \
  --add-data "$ROOT_DIR/assets:assets" \
  --icon "$ICON_PATH" \
  "$ROOT_DIR/src/main.py"

echo "Build complete: $ROOT_DIR/dist/FTS_Scanner"
