#!/usr/bin/env bash
# Build a standalone tsctl binary with PyQt5 bundled (PyInstaller).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PY="${PYTHON:-python3}"

# PyQt5 must be importable from the very interpreter that runs PyInstaller,
# so always drive PyInstaller as "$PY -m PyInstaller" rather than the script.
if ! "$PY" -c 'import PyQt5' 2>/dev/null; then
  echo "PyQt5 not found for $PY. Install one of:" >&2
  echo "  sudo apt install python3-pyqt5" >&2
  echo "  $PY -m pip install --user PyQt5" >&2
  exit 1
fi

if ! "$PY" -c 'import PyInstaller' 2>/dev/null; then
  echo "Installing PyInstaller for $PY ..."
  "$PY" -m pip install --user 'pyinstaller>=6.0'
fi

rm -rf build dist
"$PY" -m PyInstaller --noconfirm --clean tsctl.spec

OUT="$ROOT/dist/tsctl"
echo
echo "Built: $OUT"
ls -lh "$OUT"
echo
echo "Run:  $OUT"
echo "Note: recipients still need Tailscale installed; this bundle only ships"
echo "      Python + PyQt5 + tsctl. Build on the same OS/arch you distribute to."
