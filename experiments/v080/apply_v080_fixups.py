#!/usr/bin/env python3
from pathlib import Path
import sys

work = Path(sys.argv[1])
project = work / 'project'
manifest = project / 'app/src/main/AndroidManifest.xml'
main = project / 'app/src/main/java/it/darkroom/timer/MainActivity.java'
service = project / 'app/src/main/java/it/darkroom/timer/SonoffArmService.java'

m = manifest.read_text(encoding='utf-8')
needle = '    <uses-permission android:name="android.permission.WAKE_LOCK" />\n'
if 'android.permission.VIBRATE' not in m:
    if needle not in m: raise SystemExit('v0.8.0 fixup: punto permesso VIBRATE non trovato')
    m = m.replace(needle, needle + '    <uses-permission android:name="android.permission.VIBRATE" />\n', 1)
manifest.write_text(m, encoding='utf-8')

s = main.read_text(encoding='utf-8')
# I cue molto brevi sarebbero dominati dalla latenza di rilevamento LAN: 1,0 s è il minimo pratico.
s = s.replace('ms[0] = Math.max(500, ms[0] - 500);', 'ms[0] = Math.max(c.isDodge() ? 1000 : 500, ms[0] - 500);')
s = s.replace('c.milliseconds = TimingMath.snap500(ms[0], 500, Math.max(500, printWidthMs - 500));', 'c.milliseconds = TimingMath.snap500(Math.max(1000, ms[0]), 1000, Math.max(1000, printWidthMs - 500));')

# Rifiniture locali dell'editor correzione: cambio SECONDI/F-STOP immediatamente visibile
# e nessuna correzione fantasma se si annulla una voce appena aggiunta.
start = s.index('    private void showPrintCorrectionEditor(final int index) {')
end = s.index('    private boolean validatePrintSequenceForBase()', start)
b = s[start:end]
b = b.replace(
    '        final PrintCorrection original = printSequence.corrections.get(index);\n        final PrintCorrection c = original.copy();',
    '        final PrintCorrection original = printSequence.corrections.get(index);\n        final boolean newCorrection = original.label == null || original.label.trim().isEmpty();\n        final PrintCorrection c = original.copy();', 1)
b = b.replace(
    '        final int[] quarters = {Math.max(1, c.quarterStops > 0 ? c.quarterStops : 1)};\n\n        if (c.isBurn()) {',
    '        final int[] quarters = {Math.max(1, c.quarterStops > 0 ? c.quarterStops : 1)};\n        final TextView[] sequenceValueRef = {null};\n\n        if (c.isBurn()) {', 1)
b = b.replace(
    '            secondsMode.setOnClickListener(v -> { useStops[0] = false; styleMethods.run(); });\n            stopMode.setOnClickListener(v -> { useStops[0] = true; styleMethods.run(); });',
    '            secondsMode.setOnClickListener(v -> {\n                useStops[0] = false;\n                styleMethods.run();\n                if (sequenceValueRef[0] != null) sequenceValueRef[0].setText(formatTime(ms[0]));\n            });\n            stopMode.setOnClickListener(v -> {\n                useStops[0] = true;\n                styleMethods.run();\n                if (sequenceValueRef[0] != null) sequenceValueRef[0].setText(TimingMath.stopLabel(quarters[0]) + "  →  " + formatTime(TimingMath.burnExtraMs(printWidthMs, quarters[0])));\n            });', 1)
b = b.replace(
    '        final TextView value = text("", 30, c.isDodge() ? BLUE : AMBER, true);\n        value.setGravity(Gravity.CENTER);',
    '        final TextView value = text("", 30, c.isDodge() ? BLUE : AMBER, true);\n        sequenceValueRef[0] = value;\n        value.setGravity(Gravity.CENTER);', 1)
old_cancel = '''        Button cancel = compactButton("ANNULLA");
        cancel.setOnClickListener(v -> dialog.dismiss());
        panel.addView(cancel, margin(lp(-1, dp(46)), 0, 6, 0, 0));

        dialog.setContentView(panel);'''
new_cancel = '''        Button cancel = compactButton("ANNULLA");
        cancel.setOnClickListener(v -> {
            if (newCorrection && index < printSequence.corrections.size() && printSequence.corrections.get(index) == original) {
                printSequence.corrections.remove(index);
                persistPrintSequence();
            }
            dialog.dismiss();
        });
        panel.addView(cancel, margin(lp(-1, dp(46)), 0, 6, 0, 0));
        dialog.setOnCancelListener(d -> {
            if (newCorrection && index < printSequence.corrections.size() && printSequence.corrections.get(index) == original) {
                printSequence.corrections.remove(index);
                persistPrintSequence();
            }
        });

        dialog.setContentView(panel);'''
if old_cancel not in b: raise SystemExit('v0.8.0 fixup: cancel editor non trovato')
b = b.replace(old_cancel, new_cancel, 1)
s = s[:start] + b + s[end:]
main.write_text(s, encoding='utf-8')

svc = service.read_text(encoding='utf-8')
svc = svc.replace("printSequence.detail(widthMs).replace('\\n', ' • ')", 'printSequence.detail(widthMs).replace("\\n", " • ")')
service.write_text(svc, encoding='utf-8')

final_main = main.read_text(encoding='utf-8')
if 'android.permission.VIBRATE' not in manifest.read_text(encoding='utf-8'):
    raise SystemExit('v0.8.0 fixup: VIBRATE mancante')
if 'Math.max(1000, ms[0])' not in final_main:
    raise SystemExit('v0.8.0 fixup: minimo DODGE non applicato')
if 'sequenceValueRef[0]' not in final_main or 'newCorrection' not in final_main:
    raise SystemExit('v0.8.0 fixup: rifiniture editor non applicate')
if "replace('\\n', ' • ')" in service.read_text(encoding='utf-8'):
    raise SystemExit('v0.8.0 fixup: replace Java invalido ancora presente')
print('v0.8.0 FIXUPS OK: VIBRATE + DODGE min 1,0 s + editor + log Java', flush=True)
