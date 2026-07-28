# Specter Patch — Full PR Review + Final Audit Report

**Date:** 2026-07-26  
**Base:** `main` @ `860a1fa` (includes merged #148 full INI repair + #150 Egypt CC)  
**IMPORTANT:** No open PRs were merged in this pass.

---

## Step 1 — Classification of all 49 open PRs

Legend:
- **A** Safe and useful — ready to merge
- **B** Needs modification before merge
- **C** Not needed — reject (obsolete / superseded / conflicts / harmful)

| PR | Title (short) | Class | Rationale |
|----|---------------|-------|-----------|
| #3 | North Korea full faction | **C** | Large expansion; conflicts with current CC/MHQ/AAB structure on main; not integrated with post-#133 CC donors |
| #4 | Iraq playable faction | **C** | Explicitly conflicts with Iraq-identity removal policy; adds `Iraq_*` / `irq_*` surface area |
| #5 | Custom units audit B-2/B-52 | **C** | Mega stacked branch (~306f); superseded by later AAB/aircraft work already on main |
| #6 | Faction expansion nuclear | **C** | Mega stack; overlaps #5–#13; would regress CC/MHQ repairs |
| #7 | Faction completion Russia–Pakistan | **C** | Mega stack; superseded |
| #8 | Final balance audit | **C** | Mega stack; superseded by country CC/MHQ balance on main |
| #9 | Saudi/UAE/Ukraine playable | **C** | Already playable on main with repaired CC/MHQ |
| #10 | Custom units repair | **C** | Mega stack; superseded |
| #11 | Strategic weapons audit | **C** | Mega stack; superseded |
| #12 | Aircraft expansion | **C** | Mega stack; conflicts with current AAB aircraft on main |
| #13 | Ground systems expansion | **C** | Mega stack; superseded |
| #14 | AWACS air support balance | **C** | Narrow but outdated vs later AWACS/CC gunship wiring |
| #15 | Strategic Air Base system | **C** | Superseded by AAB already on main |
| #16 | Advanced Air Base system | **C** | Superseded |
| #17 | Strategic bomber balance | **C** | Superseded by main AAB bomber pools |
| #18 | Missile system expansion | **C** | Overlaps later Turkey/missile fixes already merged |
| #19 | AAB finalize all factions | **C** | Superseded |
| #20 | Aircraft combat system | **C** | Superseded / conflicts |
| #21 | Ground combat system | **C** | Superseded / conflicts |
| #22 | Strategic missile system | **C** | Superseded / conflicts |
| #23 | Faction tech general stars | **C** | Superseded / conflicts |
| #24 | Turkey faction selection | **C** | Turkey already in `PlayerTemplate_SpecterPatch.ini` on main |
| #25 | Turkey select minimal | **C** | Already present on main |
| #26 | Air systems module | **C** | Superseded by main AAB modules |
| #27 | Turkey faction complete | **C** | Conflicts with later Turkey CC/unit identity fixes (#105–#117 merged lineage) |
| #28 | AAB final 16-pad | **C** | AAB already on main |
| #38 | Full Object INI integrity PASS | **C** | Superseded by merged **#148** |
| #39 | Skirmish load-test crash report | **A** | Docs-only (`CRASH_RUNTIME_REPORT.md`); no game data risk |
| #49 | FULL REPAIR LiteralPath fix | **C** | Obsolete installer runner; superseded by overlay BIG workflow |
| #50 | New folder INI repaired | **C** | Obsolete release package |
| #51 | INI REPAIRED installer | **C** | Obsolete installer |
| #52 | Full engine INI repair | **C** | Obsolete; superseded by #148 + CC fixes |
| #53 | ENGINE REPAIR FINAL | **C** | Obsolete installer |
| #55 | INI scan tool | **B** | Useful tooling, but needs rebase onto current tree; not required for playable overlay |
| #56 | Crash reference diagnose | **B** | Useful tooling; rebase first; not required for overlay |
| #57 | GAME_BOOT_FIX_FINAL | **C** | Large obsolete installer; superseded |
| #58 | Boot fix pure BAT | **C** | Obsolete installer |
| #61 | Manifest hash fix | **C** | Obsolete vs current packages |
| #63 | BOOT_MENU_FIX (1459 files) | **C** | Dangerous structure rewrite; conflicts with clean `Data/INI` overlay layout |
| #66 | Publish merged SPEC BIGs | **C** | Superseded by later playable/merge packages on main |
| #76 | Turkey aircraft playable BIG | **C** | Superseded by #143/#145/#148 overlays |
| #77 | UAE/Japan MQ-9 + MHQ BIG | **C** | Superseded |
| #78 | Multi-unit INI playable BIG | **C** | Superseded |
| #81 | Ultimate Expansion installer | **C** | Obsolete installer path |
| #82 | Ultimate BAT installer | **C** | Obsolete |
| #83 | Ultimate working BAT | **C** | Obsolete |
| #84 | Ultimate flat BAT | **C** | Obsolete |
| #88 | Britain CombatDrone fix | **C** | Already identical on main |
| #146 | `_SPECTER_PATCH_FINAL.big` only | **C** | Stale vs main after #148/#150; would regress Egypt CC + repair pass |

### Summary counts
- **A (approve):** 1 — `#39`
- **B (modify first):** 2 — `#55`, `#56`
- **C (reject):** 46 — all remaining open PRs

### Focus areas checked
| Area | Open-PR risk | Main status |
|------|--------------|-------------|
| CommandCenter | Early PRs would overwrite USA-donor CC fixes | 21 country CCs present; Israel CC parse corruption fixed in this audit branch |
| MilitaryHQ | Mega-PRs conflict with USA-donor MHQ | Present for listed countries |
| Advanced Air Base | #15–#28 duplicate/conflict | On main under `PatchSystems` + per-country buildings |
| Aircraft / Drones / Weapons | Stacked expansions conflict | Live under country folders + PatchSystems |
| ART / W3D | Loose `patch/Art` is minimal; models in `_SPEC_ART_ONE.big` | Expected |
| INI structure | #63 would break root layout | Keep flat `Data/INI/CommandSet_*.ini` |

---

## Step 2 — Clean merge plan (DO NOT EXECUTE YET)

**Do not merge the mega stacks (#3–#28), Iraq (#4), or obsolete installers (#49–#84, #146).**

Recommended order if/when merging is allowed:

1. **Optional docs:** merge `#39` (report only).
2. **Optional tools (after rebase):** `#55` then `#56` — tooling only, no Object INI.
3. **Do not merge** any other currently open PR.
4. **Instead:** land audit remediation from this branch (`cursor/full-pr-review-final-audit-f792`) which cleans Israel identity + critical Iraq leftovers on current main.
5. After that single remediation lands, rebuild `_SPECTER_PATCH_FINAL.big` from `main` (artifact already staged under `patch/Release/SPECTER_FULL_PR_AUDIT/`).

**Conflict avoidance rule:** never stack two PRs that both touch `CommandCenter` / `MilitaryHQ` / `AdvancedAirBase` / `CommandButton.ini` / `PlayerTemplate_SpecterPatch.ini`.

---

## Step 3 — Full patch audit (current tree + this remediation)

### Structure scanned
- `patch/Data/`
- `patch/Data/INI/`
- `patch/Data/INI/Object/`
- `patch/Data/INI/Object/Specter/`
- `patch/Art/`

### Results
| Check | Result |
|-------|--------|
| INI files under `patch/Data` | 1442 |
| Duplicate `Object` names | **0** |
| Duplicate `ModuleTag` within files | **0** hard errors |
| Missing `CommandSet` definitions (overlay-local) | **0** |
| Country CC/MHQ present (Turkey, Egypt, India, Pakistan, UAE, SaudiArabia, Israel, Ukraine, Syria, Libya, SouthAfrica) | **All present** (1 CC + 1 MHQ each) |
| Loose W3D in `patch/Art` | None (expected; ART lives in `_SPEC_ART_ONE.big`) |
| Israel CC parse fields | **Fixed** (`BuildCost`/`BuildTime`/`MaxHealth` were corrupted to `P00`/`e.0`/`h00.0`) |
| Israel PlayerTemplate Iraq leftovers | **Fixed** (`SCIENCE_Iraq` / `Iraq_VT72B` / GLA chrome → Israel/USA donors) |
| `Upgrade_Irq_Tier*` / `SpecialPowerIraqiRadarSearch` | **Remapped** to Specter tiers / `SpecialPowerSpySatellite` |
| `GUI:BioFeatures_Iraq` on playable sides | **Cleared** to per-country BioFeatures |
| `irq_*` ButtonImage/SelectPortrait | **582 remaining** — these are UI texture names shipped in `_SPEC_ART`; not broken refs, but still Iraq-branded chrome |
| Dormant Iraq kit (`Command_Iraqi*`, `SpecialPowerShortcutIraq`, `Iraq_*` construct buttons) | Still present as unused definitions; not wired to playable PlayerTemplates after Israel fix |
| `Patch_Iraq_*` aircraft objects | Retained (defined objects for AAB pools) |
| `Model=` / `Animation=` `Irq_*` | Retained as W3D filenames in SPEC ART |

### Country balance snapshot (CC / MHQ)
| Country | CC Side | CC Cost/Time/HP | MHQ Cost (approx) |
|---------|---------|-----------------|-------------------|
| Turkey | Turkey | 2000 / 45s / 5000 | 1615 |
| Egypt | Egypt | 2000 / 45s / 5000 | 1615 |
| India | India | 2000 / 45s / 5000 | 1696 |
| Pakistan | Pakistan | 2000 / 45s / 5000 | 1373 |
| UAE | UAE | 2000 / 45s / 5000 | 1809 |
| SaudiArabia | SaudiArabia | 2000 / 45s / 5000 | 1809 |
| Israel | Israel | 2000 / 45s / 5000 | 1776 |
| Ukraine | Ukraine | 2000 / 45s / 5000 | 1454 |
| Syria | Syria | 2000 / 45s / 5000 | 1421 |
| Libya | Libya | 2000 / 45s / 5000 | 1454 |
| SouthAfrica | SouthAfrica | 2000 / 45s / 5000 | 1615 |

### Soft warnings (not overlay-blocking)
- Many `OCL_*` / `SUPERWEAPON_*` references resolve from base `_SPEC_DATA_ONE.big`, not the overlay — static overlay audit flags them as “missing” falsely.
- A few projectile `Weapon=` self-kill names may live only in SPEC DATA.
- Armor.ini End-count soft mismatch (pre-existing).

---

## Step 4 — Final lists

### Approved PRs (A)
- **#39** — Skirmish load-test report (docs only)

### Rejected PRs (C)
- **#3–#28, #38, #49–#53, #57–#58, #61, #63, #66, #76–#78, #81–#84, #88, #146** (and #4 Iraq especially)

### Needs modification (B)
- **#55, #56** — rebase tooling onto current main if still wanted

### Remaining errors / debt
1. **582** `irq_*` UI image references in CommandButtons (ART-valid, brand-dirty)
2. Dormant **Iraq command kit** still defined in `CommandButton.ini` / `CommandSet.ini` (unused by playable templates)
3. **~93** `Iraq_*` Object= references in buttons without overlay Object defs (dead buttons)
4. Israel still lacks true `SuperweaponIsrael*` (uses USA specials by design)

### Duplicate files
- No duplicate `Object` names in live `patch/Data`
- Many **Release/** snapshot duplicates under `patch/Release/*` (installers/old packages) — not loaded by overlay BIG; leave as archive debt

### Missing assets
- No missing CommandSets in overlay
- No loose W3D required in overlay (SPEC ART provides models)
- Dead `Iraq_*` construct targets are missing objects (buttons should eventually be removed)

### Final patch health status
**CONDITIONAL PASS for playable overlay** after this remediation:
- Critical parse break on Israel CC fixed
- Playable Israel no longer boots as Iraq science/dozer
- Tier upgrades no longer point at undefined `Upgrade_Irq_Tier*`
- Country CC/MHQ identity intact

**Not a perfect clean slate** until `irq_*` CommandButton chrome and dormant Iraq kits are purged in a dedicated UI pass.

---

## `_SPECTER_PATCH_FINAL.big`

Built from cleaned tree (this branch):

- Path: `patch/Release/SPECTER_FULL_PR_AUDIT/_SPECTER_PATCH_FINAL.big`
- Entries: 1484
- Size: ~39 MB
- SHA256: `a702ee49d7b25b0db8ba92117314a2047f0a2521fe53c5de02cda8f5a9f109d4`

Structure inside BIG:
- `Data/`
- `Data/INI/`
- `Data/INI/Object/`
- `Data/INI/Object/Specter/`
- `Art/`

Install: copy beside `_SPEC_ART_ONE.big` / `_SPEC_DATA_ONE.big` / `EnglishZH.big` / `AudioZH.big`. Do **not** replace original Specter BIGs.
