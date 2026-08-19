#!/usr/bin/env python3
"""Run the reviewed v0.12.1 transform and normalize only the inherited builder preflight.

The full functional transform is pinned to commit 435312de8f5144ce33652ffbc21f3e1f66eeda0b.
After that transform completes, this wrapper rewrites the single builder preflight condition
for v0.12.1. The protected materialized v0.12.0 snapshot is never edited.
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
lines = builder.read_text(encoding="utf-8").splitlines(True)
matches = [i for i,line in enumerate(lines) if "re.search" in line and "versionCode" in line]
if len(matches) != 1:
    raise SystemExit(f"v0.12.1 builder post-fix: expected one versionCode preflight line, found {len(matches)}")
i = matches[0]
lines[i] = '        if not re.search(r"versionCode\\s+58\\b", g) or "versionName \'0.12.1\'" not in g:\n'
builder.write_text("".join(lines), encoding="utf-8")
print("v0.12.1 OK builder preflight normalized to versionCode 58 / versionName 0.12.1", flush=True)
