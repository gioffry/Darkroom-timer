#!/usr/bin/env python3
from pathlib import Path

p = Path('experiments/v090/apply_v090_split_grade.py')
s = p.read_text(encoding='utf-8')
old = """rep(service,\n'''        cueIo.shutdownNow();\\n        io.shutdownNow();''',\n'''        cancelVoicePrompt();\\n        cueIo.shutdownNow();\\n        if (tts != null) { try { tts.stop(); tts.shutdown(); } catch (Exception ignored) {} tts = null; }\\n        io.shutdownNow();''', 'tts shutdown')"""
new = """rep(service,\n'''        cueIo.shutdownNow();''',\n'''        cancelVoicePrompt();\\n        cueIo.shutdownNow();\\n        if (tts != null) { try { tts.stop(); tts.shutdown(); } catch (Exception ignored) {} tts = null; }''', 'tts shutdown')"""
if old not in s:
    raise SystemExit('prepare v0.9.0: blocco tts shutdown non trovato')
p.write_text(s.replace(old, new, 1), encoding='utf-8')
print('prepare v0.9.0 OK: shutdown TTS robusto')
