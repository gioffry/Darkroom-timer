# DARKROOM — CODEX / AGENT INSTRUCTIONS

This repository has substantial historical material. **Do not infer the current development base from branch names, old prompts, old workflows or old build outputs.**

## Source of truth
Read `CURRENT_STATE.md` before changing anything.

Current canonical development base:
- branch: `main`
- stable app: Darkroom `0.2.8`
- versionCode: `19`
- Timer internal: `0.13.11`
- Assistant: `0.3.8`
- verified release archive: `archive/darkroom-v028-release`

`darkroom-main` is only a compatibility alias and should normally match `main`.

## Never use as a new-work base
- historical `feature-*` branches
- `archive/*` branches
- old Timer-only branches
- old Assistant-only branches
- old `CURRENT_STATE.md` copies from historical branches

## Release workflow
1. Start from current `main`.
2. Create a new feature branch with a new unused version.
3. Do not rewrite previous release branches.
4. Build APK only via GitHub Actions.
5. Verify versionName, versionCode, successful Actions run, artifact and signing continuity.
6. Preserve SONOFF exposure granularity at 0.5 s.
7. Update `CURRENT_STATE.md` only after the new release is tested/accepted.

## Safety / regression constraints
Do not regress:
- SONOFF LAN control and physical pushbutton
- safelight automation/interlock
- seconds / f-stop modes
- normal provino
- Split Grade guided provino and print sequence
- Dodge / Burn
- print-plan revisions and Log
- enlargement / resize flow
- Uso e Manutenzione
- native Home/navigation

## Repository hygiene
Historical files may remain because current build wrappers can depend on them. Do not delete build scripts, patches or assets merely because their version number is old unless their dependency chain has been verified first.

When there is any conflict between an old instruction and `CURRENT_STATE.md`, **CURRENT_STATE.md wins** unless the user explicitly asks for a rollback.
