# SPE 1–58 — new original-game reference inventory

Read-only identification of the newly uploaded original game set.  
No gameplay files, INI, ART, BIG archives, or Release assets were modified for this record.

**Recorded (UTC):** 2026-10-19T19:54:47Z  
**Repository:** `sajadabedi941-lang/Specter-Patch`  
**Baseline git HEAD (unchanged main):** `aac7ffc1e9e2a8541e2abc3d185e97a24c66cb61`  
**HEAD subject/time:** `2026-10-19 23:05:42 +0330 Add files via upload`  
**Working-tree SPE blobs:** identical to `HEAD` (0 mismatches)

This is **archive-structure validation**, not an in-game run. This environment cannot launch Zero Hour.

---

## Verdict

`SPE.part001.rar` through `SPE.part058.rar` are **one RAR 5 multi-volume archive**, not 58 independent games.

| Check | Result |
|---|---|
| Count | 58 / 58 present at repo root; no gaps |
| Format | RAR 5 (`Rar!\x1a\x07\x01\x00`), non-solid, not encrypted |
| Volume chain | Part 001 is volume 0 (first). Parts 002–058 carry volume numbers 1–57 in order |
| Last volume | `SPE.part058.rar` is the only smaller volume (19,763,416 bytes vs 25,165,824) |
| Inner payload | One folder: `SPECTER FINAL (GeneralsMode.com)/` |
| Members | 347 files + 16 folders |
| Packed size | 1,454,215,384 bytes (1,386.85 MiB) |
| Unpacked size (7-Zip listing) | 4,165,296,106 bytes |
| `unrar t SPE.part001.rar` | **exit 0** — every member CRC OK across volumes 1–58 |
| 7-Zip extract | **fails** (`Unsupported Method`) — listing works; recovery requires WinRAR/`unrar` |
| Git | All 58 files tracked; SHA-256 of working copies matches HEAD blobs |

**How to restore the original install:** keep all 58 files in one directory, then extract starting at `SPE.part001.rar` with WinRAR or `unrar x SPE.part001.rar`. Do not extract a later volume by itself.

---

## What this set is (and is not)

The recovered tree is a **complete Specter / Zero Hour game folder**, not a patch overlay:

- `generals.exe` (2003-09-18) and `WorldBuilder.exe`
- Stock ZH BIG files (`INIZH.big`, `MapsZH.big`, `TexturesZH.big`, audio/speech, …)
- Specter packed archives:
  - `_SPEC_ART_ONE.big` — 2,144,972,013 bytes (2026-10-13)
  - `_SPEC_ART_TWO.big` — 307,254,782 bytes (2026-10-13)
  - `_SPEC_DATA_ONE.big` — 373,898,957 bytes (2026-10-13)
- Root overlays already inside this original (do not confuse with later repo Releases):
  - `0_SPECTER_ABMDedicatedRadar.big` (2026-10-18)
  - `0_SPECTER_CountrySupplyIncome.big` (2026-10-17)
  - `0_SPECTER_NatoSpainDisplay.big` (2026-10-17)
  - `0_SPECTER_NoGeneralSpySatellite.big` (2026-10-15)
  - `z_SPECTER_CameraZoom.big` (2026-10-14)
  - `INIZHZ.big` (2026-09-03)
- Launchers: `Launch_Specter.bat`, `Install_SpecterPatch.bat`
- Inner folder timestamp: **2026-10-18 19:48:56**

Loose `Data/INI/` inside the archive is an **empty directory**. Game INI lives in packed BIGs. The only loose INI found in the listing are `Data/Scripts/Scripts.ini` and `NorthKoreaUAVSaetbyol.ini`.

Text files inside the pack (`README.txt`, `README_INSTALL.txt`, `VERIFY.json`, `SHA256.txt`) are **historical notes from earlier patch stages bundled into this install**. Their hashes do not describe the current packed `_SPEC_*.big` files and must not be used as the live checksum of this reference.

---

## Priority for future edits

From this point, **SPE.part001–058 is the original-game source**. Previously approved overlay work under `patch/` stays as overlay and is not replaced by this identification.

| Role | Source | Priority |
|---|---|---|
| Original game (new reference) | `SPE.part001.rar` … `SPE.part058.rar` | Highest for restoring the shipped game folder |
| Packed ART (inside SPE) | `_SPEC_ART_ONE.big` then `_SPEC_ART_TWO.big` | Canonical packed ART after extract |
| Packed DATA (inside SPE) | `_SPEC_DATA_ONE.big` | Canonical packed DATA after extract |
| Overlays already in SPE | `0_SPECTER_*.big`, `z_SPECTER_CameraZoom.big`, `INIZHZ.big` | Part of this original install; later same-path / 0-prefix load rules still apply |
| Approved project overlay | `patch/` (untouched in this pass) | Keep; do not overwrite from old archives |
| Stock ZH | `INIZH.big` and other ZH BIGs inside SPE | Stock layer inside the recovered folder |

**Do not use as the new original** (same repo, different families):

- `SPECTER1.part001–069.rar`
- `SPECTER.part001–054.rar`
- `s.part001–057.rar`
- `Sp).part001–059.rar`
- `_SPEC.part01–15.rar`, `_SPEC_DATA_ONE.zip` / `.z01–z15`, `_SPEC_ART_ONE.zip` / `.z01–z09`
- `art_data.part01–22.rar`, `DONOR_Art.part001–069.rar`, `New donor.part001–132.rar`
- Split zip `SPECTER FINAL (GeneralsMode.com).zip` + `.z01–.z28` (29 volumes, 568,996,681 bytes). Inner folder **name** matches SPE, but this is a **different, smaller zip-split set**, not SPE 1–58.

---

## Git provenance of SPE 1–58

Uploaded on **2026-10-19** via GitHub “Add files via upload”, one or a few volumes per commit.

- First volume added: `SPE.part001.rar` in `47dbc108` at 2026-10-19 22:23:52 +0330
- Last volume added: `SPE.part058.rar` in `585512c4` at 2026-10-19 22:59:03 +0330

Per-volume add commits and git blob IDs are in `SPE_REFERENCE_INVENTORY.json`.

---

## Recoverability procedure (validation performed)

1. Confirmed 58 sequential names `SPE.part001.rar` … `SPE.part058.rar` at repository root.
2. Parsed RAR 5 main headers: every volume has `MHFL_VOLUME`; part 001 has no volume number (first volume); parts 002–058 number 1–57.
3. `7z l SPE.part001.rar` reported `Multivolume = +`, `Volumes = 58`, 347 files / 16 folders.
4. `unrar x` of small docs succeeded and **walked volumes 016–058** to pull files that start later in the set.
5. `unrar t SPE.part001.rar` CRC-tested every member, including files split across volumes (`AudioEnglishZH.big`, `SpeechEnglishZH.big`, `_SPEC_ART_ONE.big`, `_SPEC_ART_TWO.big`, `_SPEC_DATA_ONE.big`). **Exit code 0.**

A full 4.16 GiB extract was **not** written into the repository (identification only). CRC success across all volumes is the archive-integrity proof.

**Tool note:** 7-Zip 23.01 cannot extract this RAR 5 method. Use `unrar` 7.00 or WinRAR.

---

## Companion files in this inventory

| File | Purpose |
|---|---|
| `SPE_REFERENCE_INVENTORY.md` | This report |
| `SPE_REFERENCE_INVENTORY.json` | Machine-readable HEAD, sizes, SHA-256, git blobs |
| `SPE_REFERENCE_SHA256.txt` | `sha256sum` lines for the 58 volumes |
| `SPE_REFERENCE_ARCHIVE_LISTING.txt` | Full `7z l SPE.part001.rar` listing |

The 58 `SPE.part*.rar` files themselves were **not** modified.

---

## Volume table

Typical volume size is 25,165,824 bytes (24 MiB). Only part 058 differs.

See `SPE_REFERENCE_SHA256.txt` and `SPE_REFERENCE_INVENTORY.json` for SHA-256 and git blob of every volume.

| Vol | File | Bytes | SHA-256 (prefix) | Git blob (prefix) |
|---:|---|---:|---|---|
| 1 | SPE.part001.rar | 25165824 | ce3a2426d0c46741 | 93df8e6154b41044 |
| 2 | SPE.part002.rar | 25165824 | 21a3d1a5af6a88bf | 9ba9e17f03be76bc |
| 3 | SPE.part003.rar | 25165824 | f8a6e49754b669f9 | 3032090130224f98 |
| 4 | SPE.part004.rar | 25165824 | c4c8afab48c372e9 | be862859723bba3c |
| 5 | SPE.part005.rar | 25165824 | aadfb64300bbb35a | 68763393517ec3cf |
| 6 | SPE.part006.rar | 25165824 | 80cfe5dbe989bf1c | 429a85848c935a2d |
| 7 | SPE.part007.rar | 25165824 | 453352637b438d92 | 176fb5de72d4537e |
| 8 | SPE.part008.rar | 25165824 | 09b5d00fba46bbd1 | 379754a6b16948df |
| 9 | SPE.part009.rar | 25165824 | f4ed0f3789b59206 | 5d04055843522eff |
| 10 | SPE.part010.rar | 25165824 | bec30fa063ecceb8 | 8f8cdba085056bca |
| 11 | SPE.part011.rar | 25165824 | 325098d95093a00d | 430faf83a8e1d234 |
| 12 | SPE.part012.rar | 25165824 | 02d7cb80906f2c3d | 8c4d37f90c73b9fe |
| 13 | SPE.part013.rar | 25165824 | db9f7553a03a7915 | b19e045b865b0cc4 |
| 14 | SPE.part014.rar | 25165824 | 9eed4808992cc7a3 | 2c2292f14a095d63 |
| 15 | SPE.part015.rar | 25165824 | cc784063b1a4adcb | 1da9ef79e95116f1 |
| 16 | SPE.part016.rar | 25165824 | 90d710691764c174 | 05e98be832f2556b |
| 17 | SPE.part017.rar | 25165824 | c989c954c38337fa | 144862ab8a51c389 |
| 18 | SPE.part018.rar | 25165824 | 755eb2242c1c7c06 | ec787ce585b65810 |
| 19 | SPE.part019.rar | 25165824 | 2650d8668452de0f | a8ca45fdc35ce941 |
| 20 | SPE.part020.rar | 25165824 | 474a803c5e4d8b88 | 59d634ec1a015f82 |
| 21 | SPE.part021.rar | 25165824 | c6c5abaef9fc8643 | 7877d7e8aa5574f9 |
| 22 | SPE.part022.rar | 25165824 | 9d0229bb267757f5 | 713ed90b44d0fe96 |
| 23 | SPE.part023.rar | 25165824 | d0c65cf22d7e1719 | f9f762dd4a7f50ae |
| 24 | SPE.part024.rar | 25165824 | 8773a2ddba511d35 | a8fba206e4d02d1d |
| 25 | SPE.part025.rar | 25165824 | 707ff66116eec772 | 4b3e1201f82d6159 |
| 26 | SPE.part026.rar | 25165824 | ddcd59e8a2279d20 | a2799f85bcd1140a |
| 27 | SPE.part027.rar | 25165824 | 261f2415f4ee8645 | 5ef8347cc1aade7f |
| 28 | SPE.part028.rar | 25165824 | 749544d262f8e03d | 54f017cf8935536b |
| 29 | SPE.part029.rar | 25165824 | de469581b754d1a0 | fccd1e5c6134d836 |
| 30 | SPE.part030.rar | 25165824 | aecc642dc3288cda | 5873e65dd2a1b400 |
| 31 | SPE.part031.rar | 25165824 | 5fa267a0913a2389 | 708be066d2b15a1f |
| 32 | SPE.part032.rar | 25165824 | 16dc1645862d592c | 7b453de04c32dfec |
| 33 | SPE.part033.rar | 25165824 | afa2f820f9f4b796 | 8bd26e62a7587eed |
| 34 | SPE.part034.rar | 25165824 | 982e3fb09de6ba21 | 3da1cf901c0d37a8 |
| 35 | SPE.part035.rar | 25165824 | ca849e8aa7b166c0 | 44502cf656835347 |
| 36 | SPE.part036.rar | 25165824 | 11be5ea4e7a176b8 | 615e13ba06789a79 |
| 37 | SPE.part037.rar | 25165824 | e87b4f68cd3db88e | 809496755ca442d9 |
| 38 | SPE.part038.rar | 25165824 | 5f0f02709fd7eb2c | 4097b9d3e798e60a |
| 39 | SPE.part039.rar | 25165824 | db08aca1989a2d02 | 464c0ef911f087be |
| 40 | SPE.part040.rar | 25165824 | 7064308106bd8aa6 | 94b2a4823a092b2a |
| 41 | SPE.part041.rar | 25165824 | ba907127795cc0de | 131440cea3f2de6a |
| 42 | SPE.part042.rar | 25165824 | c4fa882bcd8be222 | 5772c86cd8e2b66c |
| 43 | SPE.part043.rar | 25165824 | 8beceebec5241979 | a425b7a0d5813bb2 |
| 44 | SPE.part044.rar | 25165824 | 2d3e54beaafa75e2 | 08c712d56668c001 |
| 45 | SPE.part045.rar | 25165824 | bd64843dd5a5ec63 | 28eacc566c1f49c4 |
| 46 | SPE.part046.rar | 25165824 | 7295ea5cc9ce8daf | 5c106ac94dfa47d2 |
| 47 | SPE.part047.rar | 25165824 | 7d87c0068afb91f2 | 96521ffd1fc5ec52 |
| 48 | SPE.part048.rar | 25165824 | 6cc234532624af25 | 65868b60e7aab457 |
| 49 | SPE.part049.rar | 25165824 | 10f96bb73dbfb3a0 | 5b5ad550f28b20c7 |
| 50 | SPE.part050.rar | 25165824 | 9961263dc833fde9 | 6bf4341cf57e34af |
| 51 | SPE.part051.rar | 25165824 | 4ccefad093381311 | d3fa47b27155aa0d |
| 52 | SPE.part052.rar | 25165824 | 37b84627320368ba | 1f446f3c52091c2e |
| 53 | SPE.part053.rar | 25165824 | e9835ff0e28175c7 | 140c54804e4170b4 |
| 54 | SPE.part054.rar | 25165824 | c6ad92d2832971f5 | 498374ec432ad526 |
| 55 | SPE.part055.rar | 25165824 | ca0f142ef424224d | d2ae431a6e77ba2c |
| 56 | SPE.part056.rar | 25165824 | 3871ad8dc4d0e625 | 14828ea76a9801e3 |
| 57 | SPE.part057.rar | 25165824 | c1329c048410097c | b14915cb8d3b08ea |
| 58 | SPE.part058.rar | 19763416 | ecb9647de8a289aa | 505599c602993f99 |

Full SHA-256 strings: `SPE_REFERENCE_SHA256.txt`.
