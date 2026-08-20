# DARKROOM — CANONICAL CURRENT STATE

**This file is the authoritative development pointer.**

## Current app
- App: **Darkroom**
- Darkroom version: **0.1.1**
- Android applicationId: **it.darkroom.darkroom**
- Canonical development branch: **darkroom-main**
- Baseline source commit: **20309a225573503f93088496d977a828630db209**
- Last verified build run: **32331452671** — SUCCESS
- Verified artifact: **Darkroom-v0.1.1**
- Artifact id: **9393187604**
- Artifact digest: **sha256:3a555085acc06f71c8eb2235f66492fc8ecdece1ebd7ddc789989c999336344e**

## Components frozen inside Darkroom 0.1.1
### Timer
- Version: **0.13.7**
- Original branch: `feature-v0137-flat-bottom-nav`
- Exact source commit: `bd7291e4d0e875f4664fbe034be4b901059c1e4f`
- Immutable safety branch: **`archive/timer-v0137-baseline`**

### Assistant
- Version/base: **0.3.8**, plus Darkroom 0.1.1 persistence fix for the last film dilution
- Original branch: `feature-darkroom-assistant-v038-edit-persistence`
- Exact source commit: `7ff0e0324376c3465777b08e3949cc284e4a8487`
- Immutable safety branch: **`archive/assistant-v038-baseline`**

### Darkroom 0.1.1 baseline
- Exact source commit: `20309a225573503f93088496d977a828630db209`
- Immutable safety branch: **`archive/darkroom-v011-baseline`**

## Non-negotiable development rule
All future Timer, chemistry, development, paper-bath, Home and UI changes start from **`darkroom-main`**.

Do **not** start future work from `main`, from a historical Timer branch, or from a historical Assistant branch.

The three `archive/*-baseline` branches are rollback/build dependencies and **must never be deleted or rewritten**.

Historical feature branches may remain for audit/history. Closing an old technical PR does not delete its branch.

## Build strategy
Darkroom 0.1.1 is reconstructed from the exact frozen Timer 0.13.7 and Assistant 0.3.8 baselines, then applies the Darkroom integration layer. Future releases should preserve these references until the relevant component is intentionally advanced inside `darkroom-main`.
