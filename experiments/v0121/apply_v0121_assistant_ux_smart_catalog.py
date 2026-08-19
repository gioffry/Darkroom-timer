#!/usr/bin/env python3
"""Run the reviewed v0.12.1 transform and patch only the inherited builder preflight.

The full functional transform is pinned to commit 435312de8f5144ce33652ffbc21f3e1f66eeda0b.
After that transform completes, this wrapper changes only the v0.12.0 builder's literal
versionCode regex in the generated v0.12.1 work copy. The protected materialized v0.12.0
snapshot is never edited.
"""
from pathlib import Path
import subprocess
import sys

SOURCE_COMMIT = "435312de8f5144ce33652ffbc21f3e1f66eeda0b"
SOURCE_PATH = "experiments/v0121/apply_v0121_assistant_ux_smart_catalog.py"
source = subprocess.check_output(["git", "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"], text=True)
namespace = {"__name__":"__main__", "__file__":str(Path(SOURCE_PATH))}
exec(compile(source, f"{SOURCE_PATH}@{SOURCE_COMMIT}", "exec"), namespace)

builder = Path(sys.argv[1]) / "build_darkroom.py"
s = builder.read_text(encoding="utf-8")
old = 'r"versionCode\\s+57\\b"'
new = 'r"versionCode\\s+58\\b"'
if s.count(old) != 1:
    raise SystemExit(f"v0.12.1 builder post-fix: expected one inherited regex, found {s.count(old)}")
builder.write_text(s.replace(old, new, 1), encoding="utf-8")
print("v0.12.1 OK inherited builder preflight regex 57 -> 58", flush=True)
