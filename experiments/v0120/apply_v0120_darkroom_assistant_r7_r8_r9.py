#!/usr/bin/env python3
"""Execute the reviewed v0.12.0 transform with one whitespace-safe anchor correction.

The functional transform is pinned to its original commit on the v0.12.0 branch.
Only the buildPrintPanel anchor is corrected: v0.11.0 contains one blank line
between updatePrintSequenceUi() and return box.
"""
from pathlib import Path
import subprocess

SOURCE_COMMIT = "11b730262d6a4d199c98b4e67df81a172dbc6602"
SOURCE_PATH = "experiments/v0120/apply_v0120_darkroom_assistant_r7_r8_r9.py"
source = subprocess.check_output(
    ["git", "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"], text=True
)
old = "print_anchor='''        updatePrintSequenceUi();\\n        return box;'''"
new = "print_anchor='''        updatePrintSequenceUi();\\n\\n        return box;'''"
if source.count(old) != 1:
    raise SystemExit("v0.12.0 anchor wrapper: expected exactly one original print anchor")
source = source.replace(old, new, 1)
namespace = {
    "__name__": "__main__",
    "__file__": str(Path(SOURCE_PATH)),
}
exec(compile(source, f"{SOURCE_PATH}@{SOURCE_COMMIT}+print-anchor-fix", "exec"), namespace)
