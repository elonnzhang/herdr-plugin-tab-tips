#!/bin/sh
# Launch plugin.py with whichever Python is available (python3, else python).
cd "$(dirname "$0")" || exit 1
for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1; then
    exec "$py" plugin.py "$@"
  fi
done
echo "herdr-plugin-tab-tips: no python found" >&2
exit 127
