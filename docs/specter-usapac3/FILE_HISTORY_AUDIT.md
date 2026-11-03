# USAPAC3 file-history audit

**Read-only.** This document does not delete, move, rewrite, or replace any
game file, archive, commit, PR, or GitHub Release. DATA and ART packages were
not modified while writing it.

Zero Hour was **not** run. “Used by the active version” means referenced by the
current packed/overlay install on branch `cursor/usapac3-base-thaad-2c93`
(commit `e4d5fb74`, PR **#747**), not an in-game playtest.

Items that cannot be proven from git + packed BIG contents are marked
**نیازمند بررسی**. This audit does **not** guess that a file is unused.

---

## Scope and timeline

First PAC-3 work in this repo: commit `1003f8e5` (2026-11-02 16:04 UTC /
19:34 Asia/Tehran). Current unit: PR **#747**.

| When (UTC) | Commit | PR | What |
|---|---|---|---|
| 2026-11-02 | `1003f8e5` | #744 | First add: New Donor art, overlay Object/Weapon/Projectile, HQ slot 6, sidecar BIG |
| | `36fc14c6` | #744 | Load-path / launcher so ZH would see the overlay |
| | `b09c0a99` | #744 | Merge into `_SPEC_DATA_ONE` / truncated ART ONE; delete sidecar from git |
| | `59eb7a11` | #744 | Move art into `_SPEC_ART_TWO`; leave canonical ART ONE |
| | `5e53e817` | #744 | Live CC `AmericaCommandCenterCommandSet` slot 6 |
| | `26ed9253` | #744 | Append `Command_ConstructUSAPAC3` into `CommandButton.ini` |
| | `e1f8d009` | #744 | Rank-3 Science lock |
| | `5183b3da` | #744 | Remove Science/Rank/Prerequisite |
| | `92e2d327` | #744 | spawnfix (detach wheel Draw) |
| | `9b2bd7c9` | #744 | spawnfix2 (Draw closer to US_THAAD) |
| | `588cc77d` | #744 | spawnfix3 (strip empty UsaPac3F animation) |
| | `85ccdaa1` | #745 | Experiment B: US_M1120 Draw |
| 2026-11-03 | `5e5e7015` | #746 | Remove failed impl from **active** SPECTER; archive sources |
| | `e4d5fb74` | #747 | Stage-1 rebuild: clone packed `Object US_THAAD`, THAAD Draw, CC slot 6 |

PRs (none merged to `main` at audit time):

| PR | Head | Base | URL |
|---|---|---|---|
| #744 | `cursor/usapac3-2c93` | `main` | https://github.com/sajadabedi941-lang/Specter-Patch/pull/744 |
| #745 | `cursor/usapac3-abtest-2c93` | `cursor/usapac3-2c93` | https://github.com/sajadabedi941-lang/Specter-Patch/pull/745 |
| #746 | `cursor/usapac3-cleanup-2c93` | `cursor/usapac3-abtest-2c93` | https://github.com/sajadabedi941-lang/Specter-Patch/pull/746 |
| #747 | `cursor/usapac3-base-thaad-2c93` | `cursor/usapac3-cleanup-2c93` | https://github.com/sajadabedi941-lang/Specter-Patch/pull/747 |

GitHub Releases created during this work (all still present; not rewritten):

`specter-usapac3`, `specter-usapac3-loadfix`, `specter-usapac3-spec-merge`,
`specter-usapac3-art-two`, `specter-usapac3-cc-slot6`,
`specter-usapac3-cc-crashfix`, `specter-usapac3-rank3-lock`,
`specter-usapac3-no-prereq`, `specter-usapac3-no-prereq-files`,
`specter-usapac3-spawnfix`, `specter-usapac3-spawnfix2`,
`specter-usapac3-spawnfix3`, `specter-usapac3-abtest-b`,
`specter-usapac3-base-thaad`.

Lookalike name that is **not** this project: `patch/Data/INI/Object/Specter/Japan Self-Defense Forces/Projectiles/Japan_Projectile_PatriotPAC3.ini` (`Object Japan_Projectile_PatriotPAC3`). Pre-existing Japan content. Do not treat as USAPAC3.

---

## 1. Files added in earlier PAC-3 stages that the **active** version still uses

These were introduced or first wired for USAPAC3 before PR #747, and the
current stage-1 unit still depends on them at runtime or install time.

| Path | Name | Commit / PR | Why it stays in this category |
|---|---|---|---|
| `docs/specter-usapac3/merged/CommandSet.ini` | `CommandSet.ini` | Added `5e53e817` / #744; slot 6 restored `e4d5fb74` / #747 | Loose ControlBar first-wins file. Current `AmericaCommandCenterCommandSet` slot 6 = `Command_ConstructUSAPAC3`. |
| `docs/specter-usapac3/merged/CommandButton.ini` | `CommandButton.ini` | Added `26ed9253` / #744; button re-appended `e4d5fb74` / #747 | Defines `CommandButton Command_ConstructUSAPAC3` (`Object = USAPAC3`, `ButtonImage = us_thaad`). Must exist before CommandSet names it. |
| `patch/tools/installer/CommandSet.ini` | `CommandSet.ini` | Added `5e53e817` / #744; slot 6 `e4d5fb74` / #747 | Installer copy of the live CC bar. Same slot 6 as packed DATA. |
| `patch/tools/installer/CommandButton.ini` | `CommandButton.ini` | Added `26ed9253` / #744; button `e4d5fb74` / #747 | Installer copy of the live button table including `Command_ConstructUSAPAC3`. |
| `docs/specter-usapac3/merged/Launch_Specter.bat` | `Launch_Specter.bat` | Added `5e53e817` / #744 | Current ZIP launcher. Copies DATA, ART TWO, loose CommandSet/CommandButton. |
| `docs/specter-usapac3/merged/Install_SpecterPatch.bat` | `Install_SpecterPatch.bat` | Added `5e53e817` / #744 | Current ZIP installer. Same copy set. |
| `patch/tools/installer/Launch_Specter.bat` | `Launch_Specter.bat` | Pre-existed on `main`; rewritten across #744 (`36fc14c6`…`26ed9253`); leftover sidecar warning kept in #746 | Active installer launcher. PAC-3 work taught it to copy ART TWO + ControlBar. |
| `patch/tools/installer/Install_SpecterPatch.bat` | `Install_SpecterPatch.bat` | Same as above | Active installer. |
| `patch/Data/INI/CommandSet.ini` | `CommandSet.ini` | Pre-existed; slot 6 added `5e53e817`, removed #746, re-added `e4d5fb74` / #747 | Overlay CC set. Currently has slot 6 = `Command_ConstructUSAPAC3`. Packed DATA CommandSet is the larger live copy (`docs/specter-usapac3/merged/CommandSet.ini`). |
| packed `Data\English\generals.csf` inside `_SPEC_DATA_ONE.big` | `generals.csf` | Labels injected `1003f8e5` / merge `b09c0a99`; **not** reverted in #746 | Packed CSF contains ASCII `OBJECT:USAPAC3` (×2), `CONTROLBAR:ConstructUSAPAC3`, `CONTROLBAR:ToolTipConstructUSAPAC3`. Current Object/button still use those keys. |
| `patch/Data/English/generals.csf` | `generals.csf` | Modified `1003f8e5` (1142945 → 1143509 bytes vs `main`) | Overlay CSF still differs from `main`. Installer does **not** copy this file. **نیازمند بررسی**: whether any load path uses overlay CSF instead of packed DATA CSF (packed size 1498928 ≠ overlay 1143509). |
| `docs/specter-usapac3/merged/_SPEC_DATA_ONE.big` (gitignored) | `_SPEC_DATA_ONE.big` | Pipeline from `b09c0a99`; current sha `d56e8701…` from `e4d5fb74` | Live DATA pack. Contains current Object/Weapon/CommandSet/CommandButton. |

Not listed here: New Donor W3D/textures (archived, not referenced by current Object). Not listed: `ABNPatriot02` (current Object uses `us_thaad` / `US_M1120` — see category 2).

---

## 2. Shared files other systems may depend on

Do **not** delete or rewrite these for USAPAC3. Current unit also uses many of
them. Evidence is packed DATA/ART TWO and/or git vs `main`.

| Path | Name | Commit / PR | Why shared |
|---|---|---|---|
| packed `Data\INI\Object\Specter\United States Of America\AirDefense\US_M1120.ini` | `US_M1120.ini` | Pre-USAPAC3 SPECTER | Live `Object US_THAAD` (and CombatMode/PackMode/fire-control objects). Clone parent for #747. |
| packed `Art\W3D\US_M1120.W3D` and `US_M1120D`, `US_M1120_A`, `US_M1120_AD`, `US_M1120R`, `US_M1120AI_L`, `US_M1120AI_LD` | THAAD TEL meshes | Pre-USAPAC3 ART TWO | Current USAPAC3 Draw names `US_M1120` / `_D` / `_A` / `_AD`. Also used by live `Object US_THAAD`. |
| packed `Weapon.ini` entries `S400R_Deploy`, `S400R_Deploy_ABM` | THAAD dummy deploy weapons | Pre-USAPAC3 | Originals left in place. Current unit clones them under new names; THAAD still uses the originals. |
| packed `CommandSet.ini` `S400ECommandSet`, `S400ECommandSet_AA`, `S400ECommandSet_ABM` | S400E command sets | Pre-USAPAC3 | Current USAPAC3 `CommandSet = S400ECommandSet` plus CombatMode upgrades. Shared with THAAD. |
| `Generic8x8Locomotor` in stock/packed `Locomotor.ini` | locomotor | Pre-USAPAC3 | Current unit and many trucks. |
| packed OCL `OCL_THAAD_Deployed`, `OCL_THAAD_Deployed_ABM`, `OCL_ThaadDeathEffect` | THAAD OCLs | Pre-USAPAC3 | Current SlowDeathBehavior still fires these. Changing them changes THAAD fire/death. |
| packed `MappedImage us_thaad` in `Data\INI\MappedImages\HandCreated\HandCreatedMappedImages.INI` (`Texture = US-Icons05.tga`) | `us_thaad` | Pre-USAPAC3 | Current SelectPortrait / ButtonImage / construct `ButtonImage`. |
| `Art\W3D\ABPatriot.W3D` in ART TWO | `ABPatriot.W3D` | Pre-USAPAC3 ART TWO | Other Patriot mesh. Cleanup kept it. Current USAPAC3 does not name it. |
| `Art\Textures\ABNPatriot02.dds` and `ABNPatriot02_d.tga` in ART TWO | `ABNPatriot02*` | Added to ART TWO `59eb7a11` / #744; **kept** #746 because `ABPatriot.W3D` uses them. NOTES.md: these 16 files were **not** in ART ONE or ART TWO before the ART TWO pack. | Texture for `ABPatriot.W3D`. Current USAPAC3 Draw does **not** reference them. |
| `patch/Art/Textures/ABNPatriot02.dds` and `ABNPatriot02_d.tga` | overlay copy | Added `1003f8e5` / #744; **not** archived in #746 | Same textures in git overlay. Launch ZIP does not copy `patch/Art`. **نیازمند بررسی**: whether any loose-Art load path uses these overlay copies. |
| `Art\W3D\pac3_sudarb.W3D` in ART TWO | `pac3_sudarb.W3D` | Pre-USAPAC3 ART TWO (cleanup KEEP list) | Other Patriot-related mesh; not referenced by current USAPAC3.ini. |
| `Object AmericaMobileSamSiteMIM104F` and NASAMS / overlay `America_AD_*` | Patriot truck / NASAMS / overlay AD | Pre-USAPAC3 | Untouched by design. HQ overlay slot 6 is NASAMS again after #746. |
| `CommandSet AmericaCommandCenterCommandSet` (slots 1, 12–18) | America CC | Pre-USAPAC3 | Only slot 6 is the USAPAC3 line. Other commands must stay. |
| entire packed `CommandButton.ini` / `CommandSet.ini` | ControlBar tables | Pre-USAPAC3 + PAC-3 append/slot | Thousands of other buttons/sets. |
| `_SPEC_ART_ONE.big` | ART ONE | Unchanged sha `15ffb0dc…` | Full-release textures/terrain. USAPAC3 art does not live here. |
| `_SPEC_ART_TWO.big` | ART TWO | Pre-USAPAC3 W3D archive; PAC-3 added then #746 removed unique PAC-3 meshes | All SPECTER vehicle W3Ds. Current sha `2a65d89d…` (cleanup; no UsaPac3*). |
| `patch/Data/INI/CommandSet_FactionExpansion_Armies.ini` | HQ CommandSets | Edited `1003f8e5`/`36fc14c6`; restored #746. `git diff origin/main` is empty | America HQ + other countries. Slot 6 = NASAMS. Not the live CC. |
| `AmericaJetF117Clean` / `AmericaJetB21Clean` | F-117 / B-21 | Pre-USAPAC3 | Pattern sources only; not modified. |
| `patch/Data/INI/Object/Specter/Japan Self-Defense Forces/Projectiles/Japan_Projectile_PatriotPAC3.ini` | `Japan_Projectile_PatriotPAC3` | Pre-USAPAC3 | Name contains PAC3. Unrelated object (`Model = US_AIM120`). |

---

## 3. Files unique to **failed** previous implementations

Unique New Donor / overlay pieces from `1003f8e5`–`588cc77d` / #744. They are
**not** referenced by current `Object USAPAC3` (THAAD Draw). Git still holds
them under the archive (category 4). #746 removed them from **active** DATA/ART
and from `patch/` live overlay paths.

| Original live path (before #746) | Name | Commit / PR | Why unique to the failed impl |
|---|---|---|---|
| `patch/Data/INI/Object/Specter/PatchSystems/AirDefense/USAPAC3.ini` | failed `Object USAPAC3` | `1003f8e5`; Draw edits `5183b3da`–`588cc77d` | New Donor `UsaPac3Car`/`UsaPac3F` Draw; cloned overlay THAAD gameplay. Current Object is a different file. |
| `patch/Data/INI/Object/Specter/PatchSystems/AirDefense/USAPAC3_Projectile.ini` | `Object USAPAC3_Projectile` | `1003f8e5` | Donor `pac3mis_m` projectile. Stage-1 has no projectile. |
| `patch/Data/INI/Weapon_USAPAC3.ini` (old content) | `Weapon USAPAC3_Weapon` (missile clone of overlay THAAD) | `1003f8e5` | `ProjectileObject = USAPAC3_Projectile`, range 800, etc. Current same **filename** is a new clone of `S400R_Deploy` (#747). |
| `patch/Data/INI/CommandButton_USAPAC3.ini` | unique-path construct button | `1003f8e5`; trimmed `26ed9253` | Caused CC parse crash when CommandSet named it before `CommandButton.ini` had the button. |
| `patch/Data/INI/CommandSet_ZZZZ_USAPAC3.ini` | `America_MilitaryHQCommandSet` last-wins + `USAPAC3CommandSet*` | `1003f8e5` | HQ slot 6 USAPAC3 / NASAMS to slot 12. Live CC is not this set. |
| `patch/Data/INI/MappedImages/HandCreated/USAPAC3_Images.INI` | `MappedImage USAPAC3` | `1003f8e5` | UI image `USAPAC3TB.tga`. Current button uses `us_thaad`. |
| `patch/Data/English/FactionExpansion_USAPAC3_Strings.txt` | unique-path strings | `1003f8e5` | Same four labels later injected into CSF. |
| `patch/Art/W3D/UsaPac3Car.W3D` `_d` `_w` | New Donor TEL | `1003f8e5`; F strip `588cc77d` | Failed visual. |
| `patch/Art/W3D/UsaPac3F.W3D` `_d` | New Donor launcher | `1003f8e5`; empty anim stripped `588cc77d` | Failed visual; empty ANIMATION chunk was a spawn-crash hypothesis. |
| `patch/Art/W3D/pac3mis_m.W3D` | New Donor missile mesh | `1003f8e5` | Only the failed projectile referenced it. |
| `patch/Art/Textures/usaPAC3TRUCKmap*.dds` | truck textures | `1003f8e5` | Only those W3Ds. |
| `patch/Art/Textures/ampac3map*.dds` | launcher textures | `1003f8e5` | Only those W3Ds. |
| `patch/Art/Textures/pac3missilemap.dds` | missile texture | `1003f8e5` | Only `pac3mis_m`. |
| `patch/Art/Textures/USAPAC3.tga`, `USAPAC3TB.tga` | UI TGA | `1003f8e5` | MappedImage USAPAC3. |
| `docs/specter-usapac3/_SPECTER_USAPAC3.big` | sidecar BIG | Added `1003f8e5`; deleted from git `b09c0a99` | Never loaded beside SPEC BIGs. History only. |
| `docs/specter-usapac3/abtest/USAPAC3_EXPERIMENT_A.ini` / `USAPAC3_EXPERIMENT_B.ini` | experiment objects | `85ccdaa1` / #745 | Diagnostic clones; not packed in current DATA. |

`ABNPatriot02*` is **not** unique-failed; see category 2.

---

## 4. Archived files and exact locations

### 4.1 Git archive of the failed overlay (`5e5e7015` / PR #746, `git mv`)

Root: `docs/specter-usapac3/archive/failed-impl/`

| Archived path | Original path |
|---|---|
| `.../Art/W3D/UsaPac3Car.W3D` | `patch/Art/W3D/UsaPac3Car.W3D` |
| `.../Art/W3D/UsaPac3Car_d.W3D` | `patch/Art/W3D/UsaPac3Car_d.W3D` |
| `.../Art/W3D/UsaPac3Car_w.W3D` | `patch/Art/W3D/UsaPac3Car_w.W3D` |
| `.../Art/W3D/UsaPac3F.W3D` | `patch/Art/W3D/UsaPac3F.W3D` |
| `.../Art/W3D/UsaPac3F_d.W3D` | `patch/Art/W3D/UsaPac3F_d.W3D` |
| `.../Art/W3D/pac3mis_m.W3D` | `patch/Art/W3D/pac3mis_m.W3D` |
| `.../Art/Textures/usaPAC3TRUCKmap.dds` | `patch/Art/Textures/usaPAC3TRUCKmap.dds` |
| `.../Art/Textures/usaPAC3TRUCKmap_d.dds` | `patch/Art/Textures/usaPAC3TRUCKmap_d.dds` |
| `.../Art/Textures/ampac3map.dds` | `patch/Art/Textures/ampac3map.dds` |
| `.../Art/Textures/ampac3map_d.dds` | `patch/Art/Textures/ampac3map_d.dds` |
| `.../Art/Textures/ampac3mapBaCK.dds` | `patch/Art/Textures/ampac3mapBaCK.dds` |
| `.../Art/Textures/pac3missilemap.dds` | `patch/Art/Textures/pac3missilemap.dds` |
| `.../Art/Textures/USAPAC3.tga` | `patch/Art/Textures/USAPAC3.tga` |
| `.../Art/Textures/USAPAC3TB.tga` | `patch/Art/Textures/USAPAC3TB.tga` |
| `.../Data/INI/Object/Specter/PatchSystems/AirDefense/USAPAC3.ini` | same under `patch/` |
| `.../Data/INI/Object/Specter/PatchSystems/AirDefense/USAPAC3_Projectile.ini` | same under `patch/` |
| `.../Data/INI/Weapon_USAPAC3.ini` | `patch/Data/INI/Weapon_USAPAC3.ini` (old missile weapon) |
| `.../Data/INI/CommandButton_USAPAC3.ini` | `patch/Data/INI/CommandButton_USAPAC3.ini` |
| `.../Data/INI/CommandSet_ZZZZ_USAPAC3.ini` | `patch/Data/INI/CommandSet_ZZZZ_USAPAC3.ini` |
| `.../Data/INI/MappedImages/HandCreated/USAPAC3_Images.INI` | same under `patch/` |
| `.../Data/English/FactionExpansion_USAPAC3_Strings.txt` | same under `patch/` |

### 4.2 Spawnfix3 W3D backup (`588cc77d` / #744)

| Path | Why kept |
|---|---|
| `docs/specter-usapac3/backup/w3d_empty_anim/UsaPac3F.W3D` | Pre-strip copy of the empty-animation launcher |
| `docs/specter-usapac3/backup/w3d_empty_anim/UsaPac3F_d.W3D` | Damaged variant |

### 4.3 Original BIG hashes (`b09c0a99`, `59eb7a11`)

| Path | Role |
|---|---|
| `docs/specter-usapac3/backup/_SPEC_DATA_ONE.original.sha256` | Pre-merge DATA |
| `docs/specter-usapac3/backup/_SPEC_ART_ONE.original.sha256` | Canonical ART ONE |
| `docs/specter-usapac3/backup/_SPEC_ART_TWO.original.sha256` | Pre-PAC-3 ART TWO (`a5a20d95…`) |

### 4.4 Experiment B (`85ccdaa1` / #745)

`docs/specter-usapac3/abtest/` — INIs, pack/validate scripts, reports, SHA of
experimental DATA. Gitignored on disk: `docs/specter-usapac3/abtest/_SPEC_DATA_ONE.big`.
GitHub tag `specter-usapac3-abtest-b`.

### 4.5 GitHub Releases (binaries not in git)

Every `specter-usapac3-*` tag listed in the timeline. Install ZIPs / loose BIGs
live on GitHub, not in the git tree (`merged/.gitignore` ignores the three SPEC
BIGs).

### 4.6 Local untracked / gitignored artifacts (this workspace)

| Path | Tracked? | Note |
|---|---|---|
| `docs/specter-usapac3/SPECTER_USAPAC3_SPAWNFIX.zip` | untracked | Local leftover of #744 spawnfix |
| `docs/specter-usapac3/SPECTER_USAPAC3_SPAWNFIX2.zip` | untracked | Local leftover of spawnfix2 |
| `docs/specter-usapac3/base/SPECTER_USAPAC3_BASE_THAAD.zip` | gitignored | Current #747 ZIP; also on tag `specter-usapac3-base-thaad` |
| `docs/specter-usapac3/merged/_SPEC_DATA_ONE.big` | gitignored | Current packed DATA |
| `docs/specter-usapac3/merged/_SPEC_ART_TWO.big` | gitignored | Cleanup ART TWO (no UsaPac3*) |
| `docs/specter-usapac3/abtest/_SPEC_DATA_ONE.big` | gitignored | Experiment B DATA |

### 4.7 Deleted from git but still in history

| Path | Last git commit | Note |
|---|---|---|
| `docs/specter-usapac3/_SPECTER_USAPAC3.big` | deleted `b09c0a99` | Recoverable from that commit / tag `specter-usapac3-loadfix` |
| `docs/specter-usapac3/_SPECTER_USAPAC3.big.sha256` | deleted `b09c0a99` | Sidecar hash |

---

## 5. Files PR **#746** removed from the **active** game (or moved out of `patch/`)

Commit `5e5e7015`. Active SPECTER = packed DATA + ART TWO + live ControlBar +
`patch/` overlay that the installer actually copies.

### 5.1 Moved out of live `patch/` (still in git under archive)

All rows in §4.1 (`R100` in `git show 5e5e7015`). They are no longer at
`patch/Art/...` or `patch/Data/INI/...` live paths.

### 5.2 Removed from packed DATA / ART TWO (hashes in `CLEANUP_SHA256SUMS.txt`)

Cleanup script `docs/specter-usapac3/cleanup_usapac3.py` dropped unique DATA
keys (`USAPAC3.ini`, projectile, `Weapon_USAPAC3.ini`, `CommandSet_ZZZZ_USAPAC3.ini`,
`CommandButton_USAPAC3.ini`, `USAPAC3_Images.INI`, unique strings) and unique
ART TWO keys (`UsaPac3Car*`, `UsaPac3F*`, `pac3mis_m`, unique maps, `USAPAC3.tga` /
`USAPAC3TB.tga`). **Kept** in ART TWO: `ABNPatriot02*`, `ABPatriot.W3D`,
`pac3_sudarb.W3D`, `US_M1120*`.

DATA after #746: sha `3527ea06…`, 3581 entries. ART TWO: sha `2a65d89d…`, 2686
entries.

### 5.3 ControlBar / launcher edits in #746

| Path | Change |
|---|---|
| `docs/specter-usapac3/merged/CommandSet.ini` | Removed `6 = Command_ConstructUSAPAC3` |
| `patch/Data/INI/CommandSet.ini` | Same |
| `patch/tools/installer/CommandSet.ini` | Same |
| `docs/specter-usapac3/merged/CommandButton.ini` | Removed `Command_ConstructUSAPAC3` |
| `patch/tools/installer/CommandButton.ini` | Same |
| `patch/Data/INI/CommandSet_FactionExpansion_Armies.ini` | HQ slot 6 restored to NASAMS; slot 12 USAPAC3-era NASAMS line removed |
| `Launch_Specter.bat` / `Install_SpecterPatch.bat` (merged + installer) | USAPAC3-specific echo trimmed; sidecar warning kept |

### 5.4 Explicitly **not** removed in #746

- `patch/Art/Textures/ABNPatriot02.dds` / `_d.tga`
- `patch/Data/English/generals.csf` (still differs from `main`)
- `docs/specter-usapac3/abtest/**`
- diagnosis reports, pack scripts, backup hashes/W3Ds
- previous GitHub Release tags
- THAAD / Patriot / NASAMS objects
- ART ONE

---

## 6. Files current USAPAC3 (PR **#747**) depends on

Runtime + install set for stage-1 THAAD-clone. Packed DATA sha
`d56e8701941606d847a580de0617e9066555c154fadedaff82b215f10ffc73f2`
(3583 entries). ART TWO unchanged from #746 (`2a65d89d…`).

### 6.1 Added or re-added in #747 (`e4d5fb74`)

| Path | Role |
|---|---|
| `docs/specter-usapac3/base/USAPAC3.ini` | Source Object (THAAD Draw, cost 3876, time 18.6, no Prerequisite) |
| `patch/Data/INI/Object/Specter/United States Of America/AirDefense/USAPAC3.ini` | Overlay copy; byte-identical to packed winner |
| packed `Data\INI\Object\Specter\United States Of America\AirDefense\USAPAC3.ini` | **Winning** `Object USAPAC3` (one definition) |
| `docs/specter-usapac3/base/Weapon_USAPAC3.ini` | `USAPAC3_Weapon` + `USAPAC3_Weapon_ABM` (clones of `S400R_Deploy` / `_ABM`; no projectile) |
| `patch/Data/INI/Weapon_USAPAC3.ini` | Overlay copy |
| packed `Data\INI\Weapon_USAPAC3.ini` | Unique-path weapons (not stock `Weapon.ini`) |
| `CommandButton.ini` (packed + merged + installer) | `Command_ConstructUSAPAC3` |
| `CommandSet.ini` (packed + merged + installer + `patch/Data/INI`) | CC slot 6 |
| `docs/specter-usapac3/base/pack_base_thaad.py` | Packer (not loaded by ZH) |
| `docs/specter-usapac3/base/validate_base_thaad.py` | Static validator (not loaded by ZH) |

### 6.2 Pre-existing SPECTER names the Object still points at

| Dependency | Where | Why |
|---|---|---|
| Models `US_M1120` / `US_M1120D` / `US_M1120_A` / `US_M1120_AD` | ART TWO | Draw |
| Animations `US_M1120.US_M1120` (and D/A/AD clips) | same W3Ds | ConditionState |
| Tire bones `Tire01`–`Tire08`, `ScudLauncherDust`, `EXTireTrack.tga` | ART + FX | W3DTruckDraw |
| `Generic8x8Locomotor` | Locomotor.ini | Move |
| `DeployStyleAIUpdate` | engine + Object | Pack/unpack |
| `S400ECommandSet` / `_AA` / `_ABM` | CommandSet.ini | Selected-unit commands / combat modes |
| `Upgrade_AADS_AA_Mode`, `Upgrade_AADS_ABM_Mode` | existing upgrades | CommandSetUpgrade modules (not a build gate) |
| `OCL_THAAD_Deployed`, `OCL_THAAD_Deployed_ABM`, `OCL_ThaadDeathEffect` | OCL | Deploy fire / death |
| `LargeVehicleArmor`, `TankDamageFX`, FX lists in the Object | existing | Body/death |
| `MappedImage us_thaad` + `US-Icons05.tga` | MappedImages + ART ONE **نیازمند بررسی** exact ART ONE path | Button/portrait |
| `OBJECT:USAPAC3`, `CONTROLBAR:ConstructUSAPAC3`, `CONTROLBAR:ToolTipConstructUSAPAC3` | packed `generals.csf` | Display strings |
| `_SPEC_DATA_ONE.big`, `_SPEC_ART_TWO.big`, `_SPEC_ART_ONE.big` | install | Load |
| `Launch_Specter.bat` copy of CommandSet/CommandButton into `Data\INI\` | installer | ControlBar first-wins |

Current Object does **not** depend on `UsaPac3*`, `pac3mis_m`, `MappedImage USAPAC3`,
`USAPAC3CommandSet`, or `USAPAC3_Projectile`.

---

## 7. Older files that are **probably** not on the live spawn/build path — do **not** delete

Not a deletion list. Several are required as rebuild evidence or New Donor art
for a later look pass. **نیازمند بررسی** means this audit did not prove ZH loads them.

| Path | Commit / PR | Note |
|---|---|---|
| Entire `docs/specter-usapac3/archive/failed-impl/` | #746 | Not in current Draw. **Keep** for later PAC-3 appearance. |
| `docs/specter-usapac3/backup/w3d_empty_anim/*` | #744 spawnfix3 | Historical W3D only. |
| `docs/specter-usapac3/abtest/*` | #745 | Diagnostic; not in current DATA. Keep until Experiment B is decided. |
| `docs/specter-usapac3/validate_and_pack.py` | `1003f8e5` | Sidecar packer. |
| `docs/specter-usapac3/merge_usapac3_into_spec_bigs.py` | `b09c0a99` | Old merge (truncated ART ONE). |
| `docs/specter-usapac3/repack_art_two_and_data.py` | `59eb7a11` | Old ART TWO inject of 16 Donor files. |
| `docs/specter-usapac3/patch_cc_slot6.py` | `5e53e817` | Historical CC patcher. |
| `docs/specter-usapac3/diagnose_cc_slot6.py` | `5e53e817` | Historical. |
| `docs/specter-usapac3/patch_commandbutton_usapac3.py` | `26ed9253` | Historical crash-fix packer. |
| `docs/specter-usapac3/patch_data_usapac3_object.py` | spawnfix 1–3 | Patched the **failed** Object. |
| `docs/specter-usapac3/validate_spawn_fix.py` | spawnfix | Validates failed Draw. |
| `docs/specter-usapac3/strip_empty_f_anim.py` | spawnfix3 | Stripped archived F W3D. |
| `docs/specter-usapac3/cleanup_usapac3.py` / `validate_cleanup.py` | #746 | Cleanup tools; not ZH. Keep as record of what was stripped. |
| `docs/specter-usapac3/NOTES.md` | #744 | ART ONE/TWO packing notes; partly superseded by #746/#747. |
| `docs/specter-usapac3/README_INSTALL.txt`, `Rahnama-Nasb.txt`, `SHA256SUMS.txt` | spawnfix3-era | Root copies still describe spawnfix3, not stage-1. Current install docs are under `base/` and `merged/`. |
| `docs/specter-usapac3/{CRASH,DIAGNOSIS_*,SPAWN_*,RANK3_*}*` and `merged/` duplicates | #744 | Evidence. Not loaded by ZH. |
| `docs/specter-usapac3/merged/{MERGE_REPORT,SLOT6_PATCH_REPORT,CRASHFIX_REPORT}.txt` | #744 | Evidence. |
| `patch/Release/docs/Launch_Specter_REAL.bat` | Modified `36fc14c6`–`26ed9253` | Still contains spawnfix-era USAPAC3 echo (`USAPAC3 models live in ART TWO`). Current ZIP uses `merged/Launch_Specter.bat`. **نیازمند بررسی**: whether anyone still launches via `patch/Release/docs/`. |
| `patch/Data/INI/CommandButton.ini` | Pre-USAPAC3 | **No** `ConstructUSAPAC3`. Not the file Launch_Specter copies. **نیازمند بررسی**: any other tool copying this stock table. |
| Untracked `SPECTER_USAPAC3_SPAWNFIX.zip` / `SPAWNFIX2.zip` | local only | Superseded by GitHub tags; not in git. |
| Sidecar `_SPECTER_USAPAC3.big` | git history / old Release | Launchers warn to delete leftovers in the game folder. |
| `MappedImage USAPAC3` (archived INI + TGA) | #744 / #746 | Current button uses `us_thaad`. Needed if later look restores Donor UI art. |

`docs/specter-usapac3/REBUILD_DESIGN.md` is documentation for the approved rebuild,
not a leftover. Do not treat it as unused.

---

## Must keep for continuing the project

Do not delete or rewrite:

1. Current Object sources: `docs/specter-usapac3/base/USAPAC3.ini` and
   `patch/Data/INI/Object/Specter/United States Of America/AirDefense/USAPAC3.ini`
   and the packed DATA copy of that path.
2. Current weapons: `docs/specter-usapac3/base/Weapon_USAPAC3.ini` /
   `patch/Data/INI/Weapon_USAPAC3.ini` / packed `Data\INI\Weapon_USAPAC3.ini`.
3. Live ControlBar: packed + `merged/` + `patch/tools/installer/`
   `CommandButton.ini` (`Command_ConstructUSAPAC3`) and `CommandSet.ini`
   (CC slot 6 only extra line).
4. Current `_SPEC_DATA_ONE.big` (sha `d56e8701…`) and `_SPEC_ART_TWO.big`
   (sha `2a65d89d…`) and canonical `_SPEC_ART_ONE.big` (sha `15ffb0dc…`).
5. Parent unit `Object US_THAAD` / `US_M1120.ini` and ART TWO `US_M1120*.W3D`.
6. `Generic8x8Locomotor`, `S400ECommandSet*`, original `S400R_Deploy*`,
   `OCL_THAAD_Deployed*`, `MappedImage us_thaad`.
7. `ABPatriot.W3D`, `ABNPatriot02.dds` / `_d.tga` (ART TWO and overlay),
   `pac3_sudarb.W3D`.
8. NASAMS / Patriot / THAAD objects and HQ `CommandSet_FactionExpansion_Armies.ini`
   (slot 6 NASAMS).
9. New Donor archive `docs/specter-usapac3/archive/failed-impl/` (future look).
10. `docs/specter-usapac3/REBUILD_DESIGN.md`, `base/BASE_REPORT.md`, pack/validate
    scripts under `base/`.
11. `docs/specter-usapac3/backup/*.sha256` original BIG hashes.
12. `docs/specter-usapac3/abtest/` until Experiment B is formally retired.
13. `patch/tools/installer/Launch_Specter.bat` and
    `docs/specter-usapac3/merged/Launch_Specter.bat` (ART TWO + ControlBar copy).
14. packed `generals.csf` (USAPAC3 labels). Do not rebuild CSF blindly.
15. F-117 / B-21 objects (pattern reference).
16. All existing `specter-usapac3-*` GitHub Releases.
17. This audit file and the git history of PRs #744–#747.

---

## Audit status

| Check | Result |
|---|---|
| Git history `1003f8e5`…`e4d5fb74` | Read |
| PRs #744, #745, #746, #747 file lists | Read via `gh pr view` |
| Packed DATA / ART TWO unique USAPAC3 names | DATA: Object + Weapon + button + CommandSet slot 6. ART TWO: no `UsaPac3*` / `pac3mis_m` / `USAPAC3.tga` |
| Archive tree | 21 files under `docs/specter-usapac3/archive/failed-impl/` |
| Game files / DATA / ART modified for this audit | **No** |
| In-game ZH | **Not executed** |

Open **نیازمند بررسی** items: overlay vs packed `generals.csf`; whether
`patch/Art/ABNPatriot02*` or `Launch_Specter_REAL.bat` or
`patch/Data/INI/CommandButton.ini` are on any live load path; whether `us_thaad`
texture `US-Icons05.tga` lives only in ART ONE (ART ONE BIG not on this disk).
