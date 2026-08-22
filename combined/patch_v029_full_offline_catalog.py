from pathlib import Path
parts = sorted(Path('combined/v029_catalog_parts').glob('*.part'))
if not parts:
    raise SystemExit('v029 catalog patch parts missing')
source = ''.join(p.read_text(encoding='utf-8') for p in parts)
exec(compile(source, 'patch_v029_full_offline_catalog.generated.py', 'exec'))
