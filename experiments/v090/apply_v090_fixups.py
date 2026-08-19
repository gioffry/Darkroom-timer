#!/usr/bin/env python3
from pathlib import Path
import sys

work = Path(sys.argv[1])
service = work / 'project/app/src/main/java/it/darkroom/timer/SonoffArmService.java'
s = service.read_text(encoding='utf-8')

# Un solo reset del promemoria all'armamento.
s = s.replace('        cancelDodgeCues();\n        cancelVoicePrompt();\n        cancelVoicePrompt();\n',
              '        cancelDodgeCues();\n        cancelVoicePrompt();\n')

# Qualunque annullamento/fine/errore deve fermare subito la voce ripetuta.
old = '''    private void cancelTimers() {\n        cancelPoll();\n        cancelDodgeCues();\n'''
new = '''    private void cancelTimers() {\n        cancelPoll();\n        cancelDodgeCues();\n        cancelVoicePrompt();\n'''
if old not in s:
    raise SystemExit('v0.9.0 fixup: cancelTimers non trovato')
s = s.replace(old, new, 1)
service.write_text(s, encoding='utf-8')

check = service.read_text(encoding='utf-8')
if 'private void cancelVoicePrompt()' not in check or 'tts.shutdown()' not in check:
    raise SystemExit('v0.9.0 fixup: verifica TTS fallita')
if 'cancelDodgeCues();\n        cancelVoicePrompt();\n        if (nextTask != null)' not in check:
    raise SystemExit('v0.9.0 fixup: cancelTimers non ferma la voce')
print('v0.9.0 FIXUPS OK: promemoria vocale fermato su cancel/fine/errore')
