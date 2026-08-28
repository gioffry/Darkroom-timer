#!/usr/bin/env python3
from pathlib import Path

p = Path('combined/src/main/java/it/darkroom/timer/MainActivity.java')
if not p.exists():
    raise SystemExit('v0.3.9 settings order: MainActivity missing')
s = p.read_text(encoding='utf-8')

plane_start_marker = '        TextView paperPlaneTitle = text("ALTEZZA PIANO CARTA (spessore marginatore)", 12, TEXT_PRIMARY, true);'
button_start_marker = '        Button change = compactButton(selectedDeviceId == null || selectedDeviceId.isEmpty() ? "SCEGLI SONOFF" : "CAMBIA SONOFF");'
button_end_marker = '        hardwareGroup.addView(change, lp(-1,dp(50)));\n'

plane_start = s.find(plane_start_marker)
if plane_start < 0:
    raise SystemExit('v0.3.9 settings order: paper-plane block missing')
button_start = s.find(button_start_marker, plane_start)
if button_start < 0:
    raise SystemExit('v0.3.9 settings order: SONOFF button missing after paper-plane block')
button_end = s.find(button_end_marker, button_start)
if button_end < 0:
    raise SystemExit('v0.3.9 settings order: SONOFF button end missing')
button_end += len(button_end_marker)

plane_block = s[plane_start:button_start]
button_block = s[button_start:button_end]
if 'enlargementPaperPlaneHeightMm' not in plane_block:
    raise SystemExit('v0.3.9 settings order: persistent paper-plane logic not contained in moved block')
if 'showDevicePicker()' not in button_block:
    raise SystemExit('v0.3.9 settings order: SONOFF action not contained in moved block')

s = s[:plane_start] + button_block + '\n' + plane_block + s[button_end:]
p.write_text(s, encoding='utf-8')

out = p.read_text(encoding='utf-8')
button_pos = out.find(button_start_marker)
plane_pos = out.find(plane_start_marker)
if button_pos < 0 or plane_pos < 0 or button_pos > plane_pos:
    raise SystemExit('v0.3.9 settings order: final order invalid')
for marker in [
    'enlargementPaperPlaneHeightMm',
    'ALTEZZA PIANO CARTA (spessore marginatore)',
    'showDevicePicker()',
    'CAMBIA SONOFF',
]:
    if marker not in out:
        raise SystemExit('v0.3.9 settings order: regression guard missing ' + marker)

print('Darkroom v0.3.9 settings order patch ready')
