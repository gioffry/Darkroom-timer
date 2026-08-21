#!/usr/bin/env bash
set -euo pipefail

# Canonical Darkroom build entry point.
# Do not hard-code an old release: always execute the highest numbered
# combined/build_vNNN.sh present on the current branch.

SCRIPT="$(find combined -maxdepth 1 -type f -name 'build_v[0-9][0-9][0-9].sh' | sort -V | tail -n 1)"
if [ -z "$SCRIPT" ]; then
  echo "No Darkroom build_vNNN.sh wrapper found" >&2
  exit 1
fi

# Some historical wrappers expect the compatibility Home fragment to exist.
if [ -d combined/v015_assets/home_bottom_parts ]; then
  cat combined/v015_assets/home_bottom_parts/*.part > combined/v015_assets/home_bottom.jpg
fi

echo "Canonical build wrapper: $SCRIPT"
bash "$SCRIPT"
