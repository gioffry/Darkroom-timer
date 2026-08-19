#!/usr/bin/env python3
"""Run the reviewed v0.12.1 transform with the exact builder-regex correction.

The full functional transform is pinned to commit 435312de8f5144ce33652ffbc21f3e1f66eeda0b.
Only the inherited v0.12.0 builder preflight regex is corrected in-memory before execution;
the protected base/v0.12.0-materialized snapshot is never edited.
"""
from pathlib import Path
import subprocess

SOURCE_COMMIT = "435312de8f5144ce33652ffbc21f3e1f66eeda0b"
SOURCE_PATH = "experiments/v0121/apply_v0121_assistant_ux_smart_catalog.py"
source = subprocess.check_output(["git", "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"], text=True)

anchor = "wr(build,s)\nrep(gradle"
injected = "s=s.replace('versionCode\\\\s+57\\\\b','versionCode\\\\s+58\\\\b')\nwr(build,s)\nrep(gradle"
if source.count(anchor) != 1:
    raise SystemExit("v0.12.1 wrapper: builder write anchor not unique")
source = source.replace(anchor, injected, 1)

namespace = {"__name__":"__main__", "__file__":str(Path(SOURCE_PATH))}
exec(compile(source, f"{SOURCE_PATH}@{SOURCE_COMMIT}+builder-regex-fix", "exec"), namespace)
