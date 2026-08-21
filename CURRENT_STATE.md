# DARKROOM — CANONICAL CURRENT STATE

**This file is the authoritative development pointer for ChatGPT, Codex and manual work.**

## Current app
- App: **Darkroom**
- Current stable version: **0.2.8**
- versionCode: **19**
- Android applicationId: **it.darkroom.darkroom**
- Timer internal version: **0.13.11**
- Assistant version: **0.3.8**
- Canonical branch: **main**
- Compatibility alias: **darkroom-main**
- Frozen release branch: **archive/darkroom-v028-release**
- Verified release source commit: **84d2755c351b67859578e701b9bc58ea8310bd6c**
- Last verified build run: **32471989336** — SUCCESS
- Verified artifact: **Darkroom-v0.2.8**
- Artifact id: **9442925987**
- Artifact digest: **sha256:2ee3c34077989d4e57efe4914b8cfc02aa36d0229b64d8678a8b05b124fdf3b5**

## Current stable scope
Darkroom 0.2.8 includes the validated Timer/SONOFF flow, Split Grade provino + print integration, revision-safe return to provino, voice guidance, safelight transition fix, enlargement/resize flow, Log, Uso e Manutenzione and the native graphical refresh/Home.

## Immutable safety branches
These are rollback/build references and must never be rewritten or deleted:
- `archive/timer-v0137-baseline`
- `archive/assistant-v038-baseline`
- `archive/darkroom-v011-baseline`
- `archive/darkroom-v028-release`
- `archive/main-pre-v028-cleanup`
- `archive/darkroom-main-pre-v028-cleanup`

## Development rule
1. **Start every new change from `main`.**
2. `darkroom-main` is only a compatibility alias and should point to the same canonical commit as `main`.
3. Never start new work from historical `feature-*` branches.
4. Never overwrite a completed release branch. Create a new feature branch/version for each new release.
5. Build APKs only with GitHub Actions.
6. Preserve SONOFF operational rounding to 0.5 s.
7. Before a new release, verify branch, versionName, versionCode, successful run and artifact.

## Historical branches
Historical `feature-*` branches are retained only as audit/history. They are not valid development bases unless this file explicitly says otherwise.

## Codex rule
Codex must treat **`main` + this file + `AGENTS.md`** as the source of truth. If another prompt or old document names an older branch/version as canonical, this file wins unless the user explicitly requests a historical rollback.

## Build strategy
The repository still contains historical build wrappers/patches because the current APK is reconstructed through that chain. Do not casually delete build dependencies. Cleanup should target obsolete workflow/trigger noise, not files required by `combined/build_v028.sh` or its transitive dependencies.
