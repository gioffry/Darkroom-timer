#!/usr/bin/env python3
"""Darkroom 0.6.7: keep the Large Format title on one responsive line."""

from pathlib import Path


SOURCE = Path("combined/src/main/java/it/darkroom/timer/largeformat/LargeFormatActivity.java")


def java_method(text: str, signature: str) -> str:
    start = text.find(signature)
    if start < 0:
        raise SystemExit(f"v0.6.7 method missing: {signature}")
    opening = text.find("{", start)
    depth = 0
    in_string = in_char = escaped = line_comment = block_comment = False
    i = opening
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if ch == "\n": line_comment = False
        elif block_comment:
            if ch == "*" and nxt == "/": block_comment = False; i += 1
        elif in_string:
            if escaped: escaped = False
            elif ch == "\\": escaped = True
            elif ch == '"': in_string = False
        elif in_char:
            if escaped: escaped = False
            elif ch == "\\": escaped = True
            elif ch == "'": in_char = False
        elif ch == "/" and nxt == "/": line_comment = True; i += 1
        elif ch == "/" and nxt == "*": block_comment = True; i += 1
        elif ch == '"': in_string = True
        elif ch == "'": in_char = True
        elif ch == "{": depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0: return text[start:i + 1]
        i += 1
    raise SystemExit(f"v0.6.7 unterminated method: {signature}")


source = SOURCE.read_text(encoding="utf-8")
if "LARGE_FORMAT_HEADER_067" in source:
    print("large_format_header_067=ALREADY_APPLIED")
    raise SystemExit(0)
if "LARGE_FORMAT_VISUAL_066" not in source:
    raise SystemExit("v0.6.7 requires the exact v0.6.6 Large Format source")

protected = [
    "    private void showList()",
    "    private View sideRow(Chassis chassisItem, Side side, String sideName)",
    "    private String sideSummary(Side side)",
    "    private void showSideEditor(Chassis chassisItem, Side side, String sideName)",
    "    private void load()",
    "    private boolean readV2(String raw)",
    "    private void save()",
    "    private JSONObject sideJson(Side side)",
]
before = {signature: java_method(source, signature) for signature in protected}

old_marker = "// LARGE_FORMAT_VISUAL_066 — presentation only; chassis data model unchanged.\n"
new_marker = old_marker + "// LARGE_FORMAT_HEADER_067 — responsive single-line title only.\n"
if source.count(old_marker) != 1:
    raise SystemExit("v0.6.7 marker mismatch")
source = source.replace(old_marker, new_marker)

old = '''        TextView title = label("GRANDE FORMATO", 25, IVORY, true);
        title.setGravity(Gravity.CENTER);
        title.setLetterSpacing(0.035f);
'''
new = '''        TextView title = label("GRANDE FORMATO", 23, IVORY, true);
        title.setGravity(Gravity.CENTER);
        title.setSingleLine(true);
        title.setAutoSizeTextTypeUniformWithConfiguration(
                18, 23, 1, android.util.TypedValue.COMPLEX_UNIT_SP);
        title.setLetterSpacing(0.02f);
'''
if source.count(old) != 1:
    raise SystemExit("v0.6.7 title block mismatch")
source = source.replace(old, new)

after = {signature: java_method(source, signature) for signature in protected}
for signature in protected:
    if before[signature] != after[signature]:
        raise SystemExit(f"v0.6.7 protected logic changed: {signature}")

build_frame = java_method(source, "    private void buildFrame()")
for required in [
    'back.setOnClickListener(v -> finish());',
    'title.setSingleLine(true);',
    'title.setAutoSizeTextTypeUniformWithConfiguration(',
    'android.util.TypedValue.COMPLEX_UNIT_SP',
    'root.addView(top, lp(-1, dp(46)));',
]:
    if required not in build_frame:
        raise SystemExit(f"v0.6.7 header integrity failure: {required}")

SOURCE.write_text(source, encoding="utf-8")
print("large_format_header_067=APPLIED")
print("title_lines=ONE")
print("title_size_sp=RESPONSIVE_18_TO_23")
print("large_format_behaviour_changes=ZERO")
