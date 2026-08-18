#!/usr/bin/env python3
from pathlib import Path
p=Path('experiments/v0103/apply_v0103_split_short_exposure.py')
s=p.read_text(encoding='utf-8')
start=s.find("# Quando il pulsante fisico avvia davvero la fase")
end=s.find("\nchecks={", start)
if start < 0 or end < 0:
    raise SystemExit('prepare v0.10.3: blocco TTS non trovato')
# v0.9.1 ha già reso cancelVoicePrompt() responsabile anche di tts.stop().
# Non serve una seconda patch nel punto di avvio fisico: basta mantenerne la verifica sorgente.
s=s[:start]+"# La voce TTS corrente e i repeat vengono già fermati da cancelVoicePrompt() in v0.9.1.\n"+s[end:]
p.write_text(s,encoding='utf-8')
print('prepare v0.10.3 OK: TTS già interrotto da cancelVoicePrompt()',flush=True)
