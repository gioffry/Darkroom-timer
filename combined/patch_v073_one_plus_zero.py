#!/usr/bin/env python3
"""Darkroom 0.7.3: accept 1+0 as undiluted for bath-volume calculations."""
from pathlib import Path

ACT = Path("combined/src/main/java/it/darkroom/assistant/AssistantActivityV2.java")
s = ACT.read_text(encoding="utf-8")

old = '''        if ("a".equals(d)) return "1+15";
        if ("b".equals(d)) return "1+31";'''
new = '''        if ("1+0".equals(d)) return "stock";
        if ("a".equals(d)) return "1+15";
        if ("b".equals(d)) return "1+31";'''
if old not in s:
    raise SystemExit("v0.7.3 normalizedMixDilution marker missing")
s = s.replace(old, new, 1)

marker = "public class AssistantActivityV2 extends Activity {\n"
if marker not in s:
    raise SystemExit("v0.7.3 Assistant class marker missing")
s = s.replace(marker, marker + "    // ONE_PLUS_ZERO_MIX_073\n", 1)

if 'if ("1+0".equals(d)) return "stock";' not in s:
    raise SystemExit("v0.7.3 1+0 conversion missing")
if 'if ("stock".equals(d)) return new double[]{total, 0};' not in s:
    raise SystemExit("v0.7.3 stock mix path missing")

ACT.write_text(s, encoding="utf-8")
print("one_plus_zero_mix_073=APPLIED")
print("1+0=UNDILUTED")
print("example_250ml=250_PRODUCT_0_WATER")
