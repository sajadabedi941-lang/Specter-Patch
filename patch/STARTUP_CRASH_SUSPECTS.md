# STARTUP_CRASH_SUSPECTS.md

Baseline: PR/BUILD **#414** is the last user-confirmed runtime-safe boot
(PR https://github.com/sajadabedi941-lang/Specter-Patch/pull/414).
There was no dedicated #414 GitHub Release. Packed comparison uses published
PR **#413** `china-aircraft-icon-fix-v1` DATA + `china-h20` ART as the closest
packed BIG pair from that era.

Current package: repaired v2 DATA/ART after stripping proven-invalid post-414
declarations. Cursor cannot launch Generals Zero Hour.

**STATIC STARTUP VALIDATION: PASS — USER RUNTIME TEST REQUIRED**

Do not treat this document as a claim that the crash is fixed in-game.

## CRITICAL (definite initialization-invalid, repaired in v2)

| Rank | Issue | Introduced | Repair |
|---|---|---|---|
| 1 | Duplicate **CommandSet** names for France/Germany/Britain/Italy `*_HeavyAirBaseCommandSet` and `*GM406CommandSet` in both `CommandSet.ini` and `CommandSet_{Faction}.ini` | First appears with PR **#415** France rebuild (CommandSet.ini inject while faction file retained). Germany/Italy/UK copies follow in **#417**. | Removed faction-file copies. Canonical 12-fighter menus remain in `CommandSet.ini`. |
| 2 | Duplicate **CommandButton** `Command_ConstructGermanyJetTornadoECR` and `Command_ConstructItalyJetTornadoECR` in `CommandButton.ini` **and** `CommandSet.ini` | PR **#417** Europe air force (buttons inlined into CommandSet.ini while already present in CommandButton.ini) | Removed the CommandSet.ini copies. |
| 3 | Duplicate **Weapon** `Japan_Weapon_AAM4B_F15J` twice in packed `Weapon.ini` (identical blocks) | Donor-unused / global-donor overlay inlining after **#423** | Kept first block, removed second. |
| 4 | PRELOAD + `Animation=` on W3D with **zero** animation chunks: `ItalyAircraftG550CAEW` (`KVE737.W3D`) and `GermanyHelicopterH145M` (`LSFFenneck.W3D`) | PR **#417**; v1 already stripped Animation lines | Still stripped in v2. Units kept. |

Historical Specter init-crash report (`INIT_CRASH_AUDIT_FIX_REPORT.md`) treated **duplicate CommandSet names as fatal**. #414 packed DATA did not have the eight European Heavy/GM406 collisions.

## HIGH (not changed: either pre-414 or not proven init-fatal)

| Issue | Notes |
|---|---|
| 129 PRELOAD objects with Animation= on 0-anim W3Ds | Already present in #413 DATA. User booted #414. Not the post-414 regression. |
| `CommandButton` blocks inside `CommandSet.ini` | #413/#414 already had 24 (China construct buttons). Current pack still has unique-only-in-CommandSet.ini buttons required by post-414 air menus. Duplicate-named ones were removed. |
| `END` vs `End` in stock CommandSet.ini (86 tokens) | Present in #413. Not post-414. |
| Pakistan/Egypt CommandSet name overlap with CommandSet.ini | Present in #413. Not touched. |
| SPEC_China MappedImage declared in `HandCreatedMappedImages.INI` and `zChina_AirbasePortrait_Images.INI` | #414 portrait work. User-booted. Preserved. |
| France/Germany/Italy/Britain `_HelicopterBase` objects | PRELOAD STRUCTURE files added after #414. Draw uses `HXUSABigAirPort` which **has** animation chunks. Not on dozer menus. Left in place (no third-airbase dozer slot added). |
| New W3D texture names that are TGA in the mesh but DDS (or EnglishZH) at runtime | 59 new W3Ds list a TGA/DDS string not packed as that exact filename in SPEC ART. ZH commonly resolves DDS caches / EnglishZH. Not treated as definite init crash. |

## MEDIUM

- TEOD fighter meshes (`AVF-35`, `NVJ31`, `NVJ-20`, `UVMirage`, …) have 0 animation chunks. Packed objects using them as `Model=` do **not** set `Animation=`.
- `AVF-35.W3D` is small (~41 KB) with texture `housecolor2.dds` only. Used as a visual stand-in, not as a zero-byte stub. Not removed.
- CommandSet.ini still contains unique CommandButton declarations for post-414 aircraft that are not duplicated in CommandButton.ini. Same pattern as #414 China buttons.

## LOW

- Tiny/zero W3Ds among new ART: **none** under 2 KB.
- USA / Russia / China live CommandSets: hash-protected, unchanged.
- Rally / Sell / Nuclear-Atomic structure: unchanged.

## Earliest bad PR still present (repaired, not reverted)

**PR #415** is the earliest post-414 change that introduced a duplicate CommandSet name (`France_HeavyAirBaseCommandSet` in CommandSet.ini while `CommandSet_France.ini` still declared it).

PR **#417** added the G550/H145M animation crash class and the Germany/Italy/UK CommandSet collisions plus TornadoECR duplicate buttons.

This v2 build **keeps** those PRs' aircraft. It only removes the invalid duplicate declarations and leftover invalid Animation lines.
