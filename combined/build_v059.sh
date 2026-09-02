#!/usr/bin/env bash
set -euo pipefail

# v0.5.9 uses the consolidated single-pass source checkpoint.
bash combined/build_consolidated.sh
