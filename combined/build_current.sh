#!/usr/bin/env bash
set -euo pipefail

# Canonical Darkroom build wrapper.
# It deliberately maps the historical branch names expected by build_v011.sh
# to immutable archive branches, so future builds do not depend on mutable
# feature branches remaining untouched.

git fetch origin archive/timer-v0137-baseline archive/assistant-v038-baseline

git update-ref refs/remotes/origin/feature-v0137-flat-bottom-nav \
  "$(git rev-parse origin/archive/timer-v0137-baseline)"

git update-ref refs/remotes/origin/feature-darkroom-assistant-v038-edit-persistence \
  "$(git rev-parse origin/archive/assistant-v038-baseline)"

# Guard the exact frozen dependency commits before building.
test "$(git rev-parse origin/archive/timer-v0137-baseline)" = "bd7291e4d0e875f4664fbe034be4b901059c1e4f"
test "$(git rev-parse origin/archive/assistant-v038-baseline)" = "7ff0e0324376c3465777b08e3949cc284e4a8487"

bash combined/build_v011.sh
