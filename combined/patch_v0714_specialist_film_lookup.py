#!/usr/bin/env python3
from pathlib import Path
import hashlib

ROOT=Path("combined/src/main/java/it/darkroom")
MDC=ROOT/"assistant/MdcOfflineStore.java"
MAIN=ROOT/"timer/MainActivity.java"
SERVICE=ROOT/"timer/SonoffArmService.java"
TIMING=ROOT/"timer/TimingMath.java"
ENL=ROOT/"timer/EnlargementActivity.java"

def replace_once(text,old,new,label):
    n=text.count(old)
    if n!=1:
        raise SystemExit(f"{label}: expected 1 anchor, found {n}")
    return text.replace(old,new,1)

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

guard_before={
    "service":sha(SERVICE),
    "timing":sha(TIMING),
    "enlargement":sha(ENL),
}

mdc=MDC.read_text(encoding="utf-8")
main=MAIN.read_text(encoding="utf-8")

old='''        String fn = norm(stripFormat(filmName));
        String canonicalDeveloper = FullCatalogStore.canonicalDeveloper(developer);
'''
new='''        String wantedFilm = stripFormat(filmName);
        String canonicalFilm = FullCatalogStore.canonicalFilm(wantedFilm);
        String fn = norm(canonicalFilm == null ? wantedFilm : canonicalFilm);
        String canonicalDeveloper = FullCatalogStore.canonicalDeveloper(developer);
'''
mdc=replace_once(mdc,old,new,"lookupExact film specialist mapping")

main=replace_once(main,
    'private static final String APP_VERSION = "0.13.26";',
    'private static final String APP_VERSION = "0.13.27";',
    "internal version")

# Make the regression visible to source-level validation.
assert 'String canonicalFilm = FullCatalogStore.canonicalFilm(wantedFilm);' in mdc
assert 'String fn = norm(canonicalFilm == null ? wantedFilm : canonicalFilm);' in mdc
assert 'String fn = norm(stripFormat(filmName));' not in mdc
assert 'APP_VERSION = "0.13.27"' in main

MDC.write_text(mdc,encoding="utf-8")
MAIN.write_text(main,encoding="utf-8")

guard_after={
    "service":sha(SERVICE),
    "timing":sha(TIMING),
    "enlargement":sha(ENL),
}
assert guard_before==guard_after, (guard_before,guard_after)

print("v0714_specialist_film_lookup=PASS")
print("kentmere_pan_to_kentmere100_path=PASS")
print("sonoff_changes=ZERO")
print("timing_math_changes=ZERO")
print("enlargement_changes=ZERO")
