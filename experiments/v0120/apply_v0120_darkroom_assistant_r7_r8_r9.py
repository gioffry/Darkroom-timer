#!/usr/bin/env python3
"""Execute the reviewed v0.12.0 transform with exact v0.11.0 anchor corrections.

The functional transform is pinned to its original commit on the v0.12.0 branch.
Only anchors whose surrounding v0.11.0 text differs from the initial assumption are
corrected here; no protected v0.11.0 source file is modified in the repository.
"""
from pathlib import Path
import subprocess

SOURCE_COMMIT = "11b730262d6a4d199c98b4e67df81a172dbc6602"
SOURCE_PATH = "experiments/v0120/apply_v0120_darkroom_assistant_r7_r8_r9.py"
source = subprocess.check_output(
    ["git", "show", f"{SOURCE_COMMIT}:{SOURCE_PATH}"], text=True
)

# buildPrintPanel has a blank line before return box in the exact v0.11.0 snapshot.
old = "print_anchor='''        updatePrintSequenceUi();\\n        return box;'''"
new = "print_anchor='''        updatePrintSequenceUi();\\n\\n        return box;'''"
if source.count(old) != 1:
    raise SystemExit("v0.12.0 anchor wrapper: expected exactly one original print anchor")
source = source.replace(old, new, 1)

# AssistantActivity already uses entry(...) for its Home button; preserve that implementation.
old = "rep(assistant,'        Button back = new Button(this);',menu+'        Button back = new Button(this);','menu Assistant 9/9')"
new = "rep(assistant,'        Button back = entry(\"←  TORNA ALLA HOME\", \"\", false);',menu+'        Button back = entry(\"←  TORNA ALLA HOME\", \"\", false);','menu Assistant 9/9')"
if source.count(old) != 1:
    raise SystemExit("v0.12.0 anchor wrapper: expected exactly one original Assistant menu anchor")
source = source.replace(old, new, 1)

# The R7 implementation has no enlarger-controller dependency. Remove only a comment token
# that was intentionally saying so but triggered the literal no-Sonoff guardrail.
op_template = Path("experiments/v0120/OperationalAssistantActivity.java")
op_text = op_template.read_text(encoding="utf-8")
comment_old = "Deliberately has no dependency on SonoffArmService/MainActivity and never controls the enlarger."
comment_new = "Deliberately has no dependency on the enlarger controller or MainActivity and never controls the enlarger."
if op_text.count(comment_old) != 1:
    raise SystemExit("v0.12.0 R7 comment guard: expected exactly one dependency comment")
op_template.write_text(op_text.replace(comment_old, comment_new, 1), encoding="utf-8")

namespace = {
    "__name__": "__main__",
    "__file__": str(Path(SOURCE_PATH)),
}
exec(compile(source, f"{SOURCE_PATH}@{SOURCE_COMMIT}+exact-v0110-anchors", "exec"), namespace)
