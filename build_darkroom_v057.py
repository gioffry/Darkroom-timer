#!/usr/bin/env python3
"""
Darkroom Timer v0.5.7 - build APK senza Gradle.

Dipendenze: SOLO Python 3 standard library + JDK (javac/jar/keytool)
e Android SDK già presente sul PC (platform android-34 + build-tools 34.0.0 o compatibili).
NON scarica nulla e NON usa Gradle.

Uso minimo:
    python build_darkroom_v057.py DarkroomTimer-source-v0.5.7-WIP.zip

Opzionale:
    python build_darkroom_v057.py SOURCE.zip --sdk "C:\\Users\\NOME\\AppData\\Local\\Android\\Sdk"
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import secrets
import shutil
import string
import subprocess
import sys
import tempfile
import zipfile

PACKAGE_ID = "it.darkroom.timer"
VERSION_NAME = "0.5.7"
VERSION_CODE = "22"
MIN_SDK = "26"
TARGET_SDK = "34"
COMPILE_SDK = "34"
PREFERRED_BUILD_TOOLS = "34.0.0"


def log(msg: str) -> None:
    print(f"[Darkroom v0.5.7] {msg}", flush=True)


def fail(msg: str, code: int = 2) -> "None":
    print(f"\nERRORE: {msg}", file=sys.stderr, flush=True)
    raise SystemExit(code)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_windows() -> bool:
    return os.name == "nt"


def exe_name(name: str) -> str:
    if is_windows() and name in {"aapt2", "zipalign"}:
        return name + ".exe"
    if is_windows() and name in {"d8", "apksigner"}:
        return name + ".bat"
    return name


def run(cmd, cwd: Path | None = None, capture: bool = False, check: bool = True):
    cmd = [str(x) for x in cmd]
    # .bat files need cmd.exe on Windows.
    if is_windows() and cmd and cmd[0].lower().endswith((".bat", ".cmd")):
        cmd = ["cmd.exe", "/d", "/s", "/c"] + cmd
    shown = " ".join(f'"{x}"' if " " in x else x for x in cmd)
    log(f"> {shown}")
    p = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=False,
    )
    if check and p.returncode != 0:
        if capture and p.stdout:
            print(p.stdout, file=sys.stderr)
        fail(f"Comando fallito ({p.returncode}): {shown}")
    return p


def version_key(text: str):
    parts = re.split(r"[^0-9]+", text)
    nums = [int(x) for x in parts if x.isdigit()]
    return tuple(nums or [0])


def sdk_candidates(explicit: str | None):
    seen = set()
    raw = []
    if explicit:
        raw.append(explicit)
    for var in ("ANDROID_SDK_ROOT", "ANDROID_HOME"):
        if os.environ.get(var):
            raw.append(os.environ[var])
    home = Path.home()
    if is_windows():
        local = os.environ.get("LOCALAPPDATA")
        if local:
            raw.append(str(Path(local) / "Android" / "Sdk"))
        raw += [r"C:\Android\Sdk", r"C:\Android\sdk"]
    elif sys.platform == "darwin":
        raw.append(str(home / "Library" / "Android" / "sdk"))
    else:
        raw += [str(home / "Android" / "Sdk"), str(home / "Android" / "sdk")]
    for x in raw:
        p = Path(x).expanduser().resolve()
        if p not in seen:
            seen.add(p)
            yield p


def find_toolchain(explicit_sdk: str | None):
    checked = []
    for sdk in sdk_candidates(explicit_sdk):
        checked.append(sdk)
        platforms = sdk / "platforms"
        build_tools_root = sdk / "build-tools"
        if not platforms.is_dir() or not build_tools_root.is_dir():
            continue

        android_jar = platforms / f"android-{COMPILE_SDK}" / "android.jar"
        if not android_jar.is_file():
            # Prefer an installed platform >= 34 as a fallback.
            plats = []
            for p in platforms.glob("android-*"):
                m = re.fullmatch(r"android-(\d+)", p.name)
                if m and int(m.group(1)) >= int(COMPILE_SDK) and (p / "android.jar").is_file():
                    plats.append((int(m.group(1)), p / "android.jar"))
            if plats:
                android_jar = sorted(plats)[0][1]
            else:
                continue

        bt_dirs = [p for p in build_tools_root.iterdir() if p.is_dir()]
        preferred = build_tools_root / PREFERRED_BUILD_TOOLS
        ordered = ([preferred] if preferred.is_dir() else []) + [
            p for p in sorted(bt_dirs, key=lambda q: version_key(q.name), reverse=True) if p != preferred
        ]
        for bt in ordered:
            tools = {
                "aapt2": bt / exe_name("aapt2"),
                "d8": bt / exe_name("d8"),
                "zipalign": bt / exe_name("zipalign"),
                "apksigner": bt / exe_name("apksigner"),
            }
            if all(p.is_file() for p in tools.values()):
                return sdk, android_jar, bt, tools

    msg = "Android SDK/build-tools non trovati. Ho controllato:\n" + "\n".join(f"  - {p}" for p in checked)
    msg += (
        "\n\nLo script NON scarica nulla. Serve un SDK Android già presente con "
        "platform android-34 (o superiore) e build-tools con aapt2, d8, zipalign, apksigner. "
        "Se l'SDK è in un'altra cartella, rilancia con --sdk PERCORSO."
    )
    fail(msg)


def find_jdk_tool(name: str) -> Path:
    names = [name + ".exe", name] if is_windows() else [name]
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        for n in names:
            p = Path(java_home) / "bin" / n
            if p.is_file():
                return p
    for n in names:
        q = shutil.which(n)
        if q:
            return Path(q)
    fail(f"JDK mancante: non trovo '{name}'. Installa/usa un JDK 17 e imposta JAVA_HOME.")


def locate_project(source: Path, work_root: Path) -> Path:
    if source.is_dir():
        roots = [source]
    elif source.is_file() and source.suffix.lower() == ".zip":
        dest = work_root / "source"
        dest.mkdir(parents=True, exist_ok=True)
        log(f"Estraggo sorgenti: {source.name}")
        with zipfile.ZipFile(source, "r") as z:
            z.extractall(dest)
        roots = [dest]
    else:
        fail(f"Sorgente non valido: {source}")

    matches = []
    for root in roots:
        for manifest in root.rglob("app/src/main/AndroidManifest.xml"):
            project = manifest.parents[3]  # .../<project>/app/src/main/AndroidManifest.xml
            if (project / "app" / "src" / "main" / "java").is_dir():
                matches.append(project)
    if not matches:
        fail("Non trovo un progetto Android con app/src/main/AndroidManifest.xml nei sorgenti.")
    # Prefer the v0.5.7 project if nested copies exist.
    matches = sorted(set(matches), key=lambda p: ("v057" not in str(p).lower(), len(str(p))))
    project = matches[0]
    log(f"Progetto: {project}")
    return project


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def preflight(project: Path):
    manifest = project / "app" / "src" / "main" / "AndroidManifest.xml"
    gradle = project / "app" / "build.gradle"
    if not manifest.is_file():
        fail(f"Manifest mancante: {manifest}")
    text = read_text(manifest)
    required = [
        (f'package="{PACKAGE_ID}"', "package ID"),
        ('android:usesCleartextTraffic="true"', "usesCleartextTraffic=true"),
        ('android:foregroundServiceType="connectedDevice"', "foregroundServiceType=connectedDevice"),
        ('android.permission.INTERNET', "permesso INTERNET"),
        ('android.permission.WAKE_LOCK', "permesso WAKE_LOCK"),
        ('android.permission.FOREGROUND_SERVICE_CONNECTED_DEVICE', "permesso FOREGROUND_SERVICE_CONNECTED_DEVICE"),
        (f'android:versionCode="{VERSION_CODE}"', f"versionCode {VERSION_CODE}"),
        (f'android:versionName="{VERSION_NAME}"', f"versionName {VERSION_NAME}"),
    ]
    missing = [label for needle, label in required if needle not in text]
    if missing:
        fail("Preflight manifest fallito. Mancano/sono errati: " + ", ".join(missing))
    if gradle.is_file():
        g = read_text(gradle)
        if not re.search(r"versionCode\s+22\b", g) or not re.search(r"versionName\s+['\"]0\.5\.7['\"]", g):
            fail("app/build.gradle non riporta versionCode 22 / versionName 0.5.7")
    log("Preflight v0.5.7 OK: manifest/versione/requisiti SONOFF invarianti verificati")


def write_sources_argfile(paths, out: Path):
    # javac argfile: quote every path, escape backslashes and quotes.
    lines = []
    for p in paths:
        s = str(p.resolve()).replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'"{s}"')
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_signing(jdk_keytool: Path, out_dir: Path, provided_ks: str | None,
                 alias: str, storepass: str | None, keypass: str | None):
    if provided_ks:
        ks = Path(provided_ks).expanduser().resolve()
        if not ks.is_file():
            fail(f"Keystore non trovato: {ks}")
        if not storepass:
            fail("Con --keystore devi indicare anche --storepass")
        return ks, alias, storepass, keypass or storepass

    ks = out_dir / "DarkroomTimer-v057-local-signing.p12"
    meta = out_dir / "DarkroomTimer-v057-local-signing.json"
    if ks.exists() and meta.exists():
        try:
            info = json.loads(meta.read_text(encoding="utf-8"))
            return ks, info["alias"], info["storepass"], info.get("keypass", info["storepass"])
        except Exception:
            pass

    alphabet = string.ascii_letters + string.digits
    password = "".join(secrets.choice(alphabet) for _ in range(24))
    log("Creo una nuova firma locale per la v0.5.7 (non sovrascrive la firma 0.5.6)")
    run([
        jdk_keytool, "-genkeypair", "-noprompt", "-v",
        "-keystore", ks,
        "-storetype", "PKCS12",
        "-storepass", password,
        "-keypass", password,
        "-alias", alias,
        "-keyalg", "RSA", "-keysize", "2048",
        "-validity", "10000",
        "-dname", "CN=Darkroom Timer DIY, OU=Local Build, O=Darkroom Timer, C=IT",
    ])
    meta.write_text(json.dumps({
        "keystore": str(ks), "alias": alias,
        "storepass": password, "keypass": password
    }, indent=2), encoding="utf-8")
    try:
        if os.name != "nt":
            os.chmod(meta, 0o600)
            os.chmod(ks, 0o600)
    except OSError:
        pass
    return ks, alias, password, password


def build(args):
    source = Path(args.source).expanduser().resolve()
    out = Path(args.output).expanduser().resolve() if args.output else (Path.cwd() / f"DarkroomTimer-DIY-v{VERSION_NAME}.apk")
    out.parent.mkdir(parents=True, exist_ok=True)

    javac = find_jdk_tool("javac")
    jar = find_jdk_tool("jar")
    keytool = find_jdk_tool("keytool")
    sdk, android_jar, bt, tools = find_toolchain(args.sdk)
    log(f"SDK: {sdk}")
    log(f"android.jar: {android_jar}")
    log(f"Build Tools: {bt.name}")

    temp_ctx = tempfile.TemporaryDirectory(prefix="darkroom-v057-")
    temp = Path(temp_ctx.name)
    try:
        project = locate_project(source, temp)
        preflight(project)

        manifest = project / "app" / "src" / "main" / "AndroidManifest.xml"
        res = project / "app" / "src" / "main" / "res"
        java_src = project / "app" / "src" / "main" / "java"
        if not res.is_dir() or not java_src.is_dir():
            fail("Cartelle res/java mancanti nel progetto")

        b = temp / "build"
        gen = b / "gen"
        classes = b / "classes"
        dex = b / "dex"
        gen.mkdir(parents=True)
        classes.mkdir(parents=True)
        dex.mkdir(parents=True)

        compiled = b / "compiled.zip"
        base_apk = b / "base.apk"
        classes_jar = b / "classes.jar"
        app_work = b / "app-work.apk"
        aligned = b / "app-aligned.apk"

        log("1/7 Compilo risorse con aapt2")
        run([tools["aapt2"], "compile", "--dir", res, "-o", compiled])

        log("2/7 Link risorse + genero R.java")
        run([
            tools["aapt2"], "link",
            "-I", android_jar,
            "--manifest", manifest,
            "-o", base_apk,
            compiled,
            "--java", gen,
            "--auto-add-overlay",
            "--min-sdk-version", MIN_SDK,
            "--target-sdk-version", TARGET_SDK,
            "--version-code", VERSION_CODE,
            "--version-name", VERSION_NAME,
        ])

        log("3/7 Compilo Java")
        sources = sorted(java_src.rglob("*.java")) + sorted(gen.rglob("*.java"))
        if not sources:
            fail("Nessun sorgente Java trovato")
        sources_file = b / "sources.txt"
        write_sources_argfile(sources, sources_file)
        run([
            javac,
            "-encoding", "UTF-8",
            "-source", "8",
            "-target", "8",
            "-cp", android_jar,
            "-d", classes,
            f"@{sources_file}",
        ])
        run([jar, "cf", classes_jar, "-C", classes, "."])

        log("4/7 Converto bytecode Java in DEX")
        run([
            tools["d8"],
            "--lib", android_jar,
            "--min-api", MIN_SDK,
            "--output", dex,
            classes_jar,
        ])
        dex_files = sorted(dex.glob("classes*.dex"))
        if not dex_files:
            fail("d8 non ha prodotto classes.dex")

        log("5/7 Inserisco classes.dex nell'APK")
        shutil.copy2(base_apk, app_work)
        with zipfile.ZipFile(app_work, "a", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for df in dex_files:
                z.write(df, df.name)

        log("6/7 Zipalign")
        run([tools["zipalign"], "-f", "4", app_work, aligned])

        log("7/7 Firma APK")
        ks, alias, storepass, keypass = make_signing(
            keytool, out.parent, args.keystore, args.alias, args.storepass, args.keypass
        )
        if out.exists():
            out.unlink()
        run([
            tools["apksigner"], "sign",
            "--ks", ks,
            "--ks-key-alias", alias,
            "--ks-pass", f"pass:{storepass}",
            "--key-pass", f"pass:{keypass}",
            "--v1-signing-enabled", "true",
            "--v2-signing-enabled", "true",
            "--out", out,
            aligned,
        ])

        log("Verifica zipalign")
        run([tools["zipalign"], "-c", "-v", "4", out], capture=True)

        log("Verifica firma")
        sig = run([tools["apksigner"], "verify", "--verbose", "--print-certs", out], capture=True)
        sig_text = sig.stdout or ""
        if "Verified using v2 scheme" in sig_text and "true" not in sig_text.lower():
            fail("Firma v2 non verificata")
        print(sig_text.strip())

        log("Verifica package/versione")
        badging = run([tools["aapt2"], "dump", "badging", out], capture=True)
        badging_text = badging.stdout or ""
        first = badging_text.splitlines()[0] if badging_text else ""
        print(first)
        if f"name='{PACKAGE_ID}'" not in badging_text:
            fail(f"Package finale errato: atteso {PACKAGE_ID}")
        if f"versionCode='{VERSION_CODE}'" not in badging_text:
            fail(f"versionCode finale errato: atteso {VERSION_CODE}")
        if f"versionName='{VERSION_NAME}'" not in badging_text:
            fail(f"versionName finale errato: atteso {VERSION_NAME}")

        with zipfile.ZipFile(out, "r") as z:
            names = set(z.namelist())
            if "classes.dex" not in names or "AndroidManifest.xml" not in names:
                fail("APK incompleto: classes.dex o AndroidManifest.xml mancante")

        digest = sha256(out)
        log(f"APK COMPLETATO: {out}")
        log(f"Dimensione: {out.stat().st_size:,} byte")
        log(f"SHA-256: {digest}")
        print("\nOK. Installa questo file sul telefono:")
        print(out)
    finally:
        if args.keep_build:
            keep = out.parent / "DarkroomTimer-v057-build-debug"
            if keep.exists():
                shutil.rmtree(keep)
            shutil.copytree(temp, keep)
            log(f"Build intermedia conservata in: {keep}")
        temp_ctx.cleanup()


def default_source() -> str | None:
    candidates = list(Path.cwd().glob("DarkroomTimer-source-v0.5.7-WIP*.zip"))
    if len(candidates) == 1:
        return str(candidates[0])
    return None


def main():
    p = argparse.ArgumentParser(
        description="Compila Darkroom Timer v0.5.7 in APK senza Gradle e senza download automatici."
    )
    p.add_argument("source", nargs="?", default=default_source(),
                   help="ZIP WIP v0.5.7 oppure cartella progetto Android")
    p.add_argument("--output", "-o", help="Percorso APK finale")
    p.add_argument("--sdk", help="Percorso Android SDK già installato")
    p.add_argument("--keystore", help="Keystore esistente; se omesso ne crea uno locale nuovo")
    p.add_argument("--alias", default="darkroomtimer", help="Alias chiave (default: darkroomtimer)")
    p.add_argument("--storepass", help="Password keystore esistente")
    p.add_argument("--keypass", help="Password chiave esistente; default=storepass")
    p.add_argument("--keep-build", action="store_true", help="Conserva i file intermedi per diagnosi")
    args = p.parse_args()
    if not args.source:
        p.print_help()
        fail("Indica lo ZIP WIP v0.5.7 come primo argomento.")
    build(args)


if __name__ == "__main__":
    main()
