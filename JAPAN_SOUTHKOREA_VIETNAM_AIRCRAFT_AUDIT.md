# Japan / South Korea / Vietnam Aircraft Status Audit

**Date:** 2026-08-31  
**Scope:** Read-only audit of live overlay `patch/Data`. **No INI, art, CommandSet, weapon, or packaging files were modified.**  
**Constraint honored:** USA, Russia, China trees and prior crash/duplicate/packaging fixes were not touched.

---

## 0. Verdict (fighters)

| Country | Live airfield fighters | Intended national fighters | Visual identity | Duplicate visual among the three |
|---------|------------------------|----------------------------|-----------------|----------------------------------|
| **Japan** | NATO F-35C / Eurofighter / F-16D Blk52 | F-15J / F-2 / F-35J | **Mismatch** | F-35, Eurofighter, F-16 shared with South Korea (and NATO clones) |
| **South Korea** | NATO F-35C / Eurofighter / F-16D Blk52 + F-15K | F-15K / F-35A / F-16 | **Partial** (F-15K is distinct; rest NATO clones) | F-35, Eurofighter, F-16 shared with Japan |
| **Vietnam** | Iraq-kit MiG-29A / Mirage F1 / Su-25K | Su-30 / MiG-21 / Su-22 | **Mismatch** | Shares Iraq-kit W3D with Egypt/India/Libya/Pakistan/etc., not with JP/KR fighters |

**Root cause:** Japan and South Korea airframes are Specter **NATO donor clones**. Vietnam airframes are Specter **Iraq donor clones**. Named national objects (`Patch_Japan_F15J`, `Patch_Japan_F2`, `Patch_Japan_F35J`, `Patch_Vietnam_Su30`, `Patch_Vietnam_Mig21`, `Patch_Vietnam_Su22`, …) exist only in **historical** Advanced Air Base snapshots and are **absent from live `patch/Data`**. Even those historical objects all used the same W3D (`US_F16CMB50`).

---

## 1. Live source of truth

| Item | Path / state |
|------|----------------|
| Overlay loaded by the patch | `patch/Data/` |
| Japan CommandSet | `patch/Data/INI/CommandSet_Japan.ini` → `Japan_AirfieldCommandSet` |
| South Korea CommandSet | `patch/Data/INI/CommandSet_SouthKorea.ini` → `SouthKorea_AirfieldCommandSet` |
| Vietnam CommandSet | `patch/Data/INI/CommandSet_Vietnam.ini` → `Vietnam_AirfieldCommandSet` (+ T1/T2/T3 copies) |
| CommandButtons | `patch/Data/INI/CommandButton_FactionExpansion_Armies.ini` |
| Strings | `patch/Data/English/FactionExpansion_ArmyStrings.txt` + Phase C/F+ overlays |
| Advanced Air Base (live) | **Disabled.** `Aircraft_AAB_Global.ini`, `CommandSet_AdvancedAirBase.ini`, and `*_AdvancedAirBase.ini` building files are stub comments: “REMOVED - AdvancedAirBase disabled completely.” |
| Air Force Final leftovers | `Aircraft_AirForceFinal.ini` still defines `Patch_Japan_*` / `Patch_SouthKorea_*` / `Patch_Vietnam_*` Light/Med/Heavy bomber, AssaultHelo, CombatDrone. Buttons exist. **No live CommandSet slot produces them.** |
| Vendor archives | `Data.zip`, `DONOR_Art.part*.rar`, `art_data.part*.rar`, `_SPEC_*` — overlay-only policy; not scanned as editable. |
| DATA / ART packaging | Existing `patch/tools/big/*.py` workflow (SPEC_DATA / SPEC_ART BIG rebuilds). Japan MQ-9 already went through `build_specter_japan_uae_mq9_fixed_big.py`. |

Historical snapshot used only as **intended-roster evidence** (not live):  
`patch/Release/SPECTER_CLEAN_PATCH_FINAL/Patch/Data/INI/CommandSet/CommandSet_AdvancedAirBase.ini`  
`…/AdvancedAirBase/Aircraft_AAB_Global.ini`

---

## 2. Prior work that must stay untouched (context)

Read from existing reports; **not re-applied in this pass**.

| Report | What it established |
|--------|---------------------|
| `FINAL_CRASH_FREE_REPORT.md` | Object/CommandSet/Weapon reference scan PASS; Israel CommandSets; AAB prereq remap |
| `FINAL_BOOT_FIX_REPORT.md` | Empty PowerPlant CommandSets (incl. Vietnam); multi-object Prerequisites cleanup |
| `FINAL_RUNTIME_FIX_REPORT.md` | Boss_CommandCenter, Russia RS-24, America upgrades |
| `MISSING_REFERENCE_REPORT.md` | Weapon/Upgrade/Locomotor verification stubs |
| `MOD_CONTENT_AUDIT.md` | Overlay-only; unique `Patch_*` IDs; Specter art (`US_*` / `Irq_*`); missing `mod.z23`/`mod.z24` blocks true W3D from mod.zip |
| `PHASE_G_REPORT.md` / `PHASE_H_REPORT.md` | Claim F-35J and F-2 “already present” — **true only as historical AAB objects / strings, not as live unique W3D** |
| `PHASE_CD_REPORT.md` / `CountryDoctrine_PhaseCD.ini` | Japan doctrine: F-35 / radar / precision defense. Vietnam: asymmetric/infantry, not Western fighters |
| Japan MQ-9 art fix | `Japan_MQ9.ini` comment: removed `US_MQ9`; stand-in `CHI_CH5` (shared with UAE_MQ9) |
| USA airfield / B-2 work | Live AAB disable comments explicitly preserve `AmericaJetB2` on stock America airfield slot 5 |

Duplicate CommandSet / CommandButton / Weapon repairs from earlier passes remain in place. This audit does not reopen them.

---

## 3. Intended national rosters (historical AAB — **not live**)

From `SPECTER_CLEAN_PATCH_FINAL` `Japan_AdvancedAirBaseCommandSet` / `SouthKorea_AdvancedAirBaseCommandSet` / `Vietnam_AdvancedAirBaseCommandSet`, plus Phase C strings.

### Japan (intended)

| Slot | CommandButton | Intended object | Display string | Historical W3D | Historical weapons |
|------|---------------|-----------------|----------------|----------------|--------------------|
| 1 | `Command_ConstructPatch_Japan_F15J` | `Patch_Japan_F15J` | Japan F-15J | **US_F16CMB50** Scale 0.9 | `Japan_Weapon_AAM_Medium` + ATGM |
| 2 | `Command_ConstructPatch_Japan_F2` | `Patch_Japan_F2` | Japan F-2 | **US_F16CMB50** Scale 0.9 | `Japan_Weapon_AAM_Medium` + ATGM |
| 3 | `Command_ConstructPatch_Japan_F35J` | `Patch_Japan_F35J` | Japan F-35J | **US_F16CMB50** Scale 0.9 | `Japan_Weapon_AAM4B_F35J` + ATGM |
| 4 | `Command_ConstructPatch_Japan_E767` | `Patch_Japan_E767` | (key only) | US_E3G 0.75 | AN_APY2_SAR_SCANMODE |
| 5 | `Command_ConstructPatch_Japan_KC767` | `Patch_Japan_KC767` | (key only) | US_C130H 0.75 | none |
| 6 | Transport | `Patch_Japan_Transport` | (key only) | US_C130H 0.76 | none |
| 7–11 | Light/Med/Heavy bomber, AssaultHelo, CombatDrone | `Patch_Japan_*` | generic class names | US_F16CMB50 / US_B1R / US_B52H / Irq_Mi8T | Patch_Weapon_* |

**Live existence of those Patch_* fighters:** all **ABSENT** from `patch/Data`.

### South Korea (intended)

| Slot | CommandButton | Intended object | Historical W3D |
|------|---------------|-----------------|----------------|
| 1 | `Command_ConstructPatch_SouthKorea_F15K` | `Patch_SouthKorea_F15K` | **US_F16CMB50** Scale 0.9 |
| 2 | `Command_ConstructPatch_SouthKorea_F35A` | `Patch_SouthKorea_F35A` | **US_F16CMB50** Scale 0.9 |
| 3 | `Command_ConstructPatch_SouthKorea_F16` | `Patch_SouthKorea_F16` | **US_F16CMB50** Scale 0.9 |
| 4 | AWACS | `Patch_SouthKorea_AWACS` | US_E3G 0.78 |
| 5 | Tanker | `Patch_SouthKorea_Tanker` | US_C130H 0.76 |
| 6 | Transport | `Patch_SouthKorea_Transport` | US_C130H 0.76 |

**Live existence:** those Patch_* objects **ABSENT**. Live `SouthKorea_F15K` is a **different** object (Saudi F-15SA donor) on airfield slot 7.

### Vietnam (intended)

| Slot | CommandButton | Intended object | Historical W3D |
|------|---------------|-----------------|----------------|
| 1 | `Command_ConstructPatch_Vietnam_Su30` | `Patch_Vietnam_Su30` | **US_F16CMB50** Scale 0.9 |
| 2 | `Command_ConstructPatch_Vietnam_Mig21` | `Patch_Vietnam_Mig21` | **US_F16CMB50** Scale 0.9 |
| 3 | `Command_ConstructPatch_Vietnam_Su22` | `Patch_Vietnam_Su22` | **US_F16CMB50** Scale 0.9 |
| 4 | AWACS | `Patch_Vietnam_AWACS` | US_E3G 0.78 |
| 5 | Transport | `Patch_Vietnam_Transport` | US_C130H 0.76 |

**Live existence:** those Patch_* objects **ABSENT**. Vietnam science still has `Upgrade_Vietnam_Su30Doctrine` and Tu-22 sciences, but no live Su-30 / MiG-21 / Su-22 airframe.

**Important historical note:** even the “correctly named” AAB fighters were **already visual duplicates** of each other (`US_F16CMB50` for F-15J, F-2, F-35J, F-15K, F-35A, F-16, Su-30, MiG-21, Su-22). Name identity was INI/string-only.

---

## 4. Live production tables (requested columns)

Texture note used throughout:

- Object Draw modules **do not declare `Texture=`**. W3D skins live in Specter art (same stem as the model, e.g. `US_F35A`).
- INI-declared UI textures are `SelectPortrait` / `ButtonImage` on the object and `ButtonImage` on the CommandButton.
- “Duplicate visual YES” means the same W3D `Model=` is used by other live air objects.

Lock note:

- **Unlocked at airfield** = no Science / Rank / extra building Prerequisite on the object (the airfield itself is the producer).
- **Locked** = extra `Science=` / Rank / building in `Prerequisites`.
- Japan/SK F-35 objects require `SCIENCE_NatoStealthJet`, but the General Star menus grant `SCIENCE_Japan_StealthJet` / `SCIENCE_SouthKorea_StealthJet`. That is a **science-ID mismatch** (likely still locked after buying the national Stealth Jet science).

---

### 4.1 Japan — live `Japan_AirfieldCommandSet`

Producer CommandSet: `Japan_AirfieldCommandSet`  
File: `patch/Data/INI/CommandSet_Japan.ini`

| Slot | Displayed name (object key → overlay string) | Object name | W3D model | Texture / UI art | Scale | Weapon setup | CommandButton | CommandSet (unit) | Locked? | Duplicate visual |
|------|----------------------------------------------|-------------|-----------|------------------|-------|--------------|---------------|-------------------|---------|------------------|
| 1 | `OBJECT:Japan_JetF35C` → **Japan F-35** (Phase C) / “Japan JetF35C” (ArmyStrings) | `Japan_JetF35C` | **US_F35A** | Portrait/button `Nat_f35a`; CB `SACRaptor` | default (1.0) | PRIMARY `Japan_Weapon_AAM4B_F35J`; PLAYER_UPGRADE `GBU_31V2_JDAM_F35C` + `AN/APG81_AESA_Radar_AGMode` | `Command_ConstructJapan_JetF35C` | `GenericMultiRoleFighter_AG_CommandSet` | **LOCKED** — `Japan_StrategyCenter` + `SCIENCE_NatoStealthJet` + `SCIENCE_Rank4` | **YES** — same `US_F35A` as SK/NATO/USA F-35 family (11+ objects) |
| 2 | `OBJECT:EF2000T4` (NATO stock key, not Japan-prefixed) | `Japan_JetEF2000T4` | **NAT_EF2000T4** | Portrait/button `Nat_ef2000t4`; CB `SACRaptor` | **0.9** | PRIMARY `Paveway_IV_EF2000`; upgrade `CAPTOR_E_AESA_RADAR_AG_Mode` | `Command_ConstructJapan_JetEF2000T4` | `GenericTacticalBomberCommandSet` | **LOCKED** — `Japan_StrategyCenter` + `SCIENCE_Rank5` | **YES** — 19 objects incl. `Japan_JetEF2000T4_CAS`, `SouthKorea_JetEF2000T4`, Britain/Germany/Italy Typhoon |
| 3 | `OBJECT:F16Dbk52` (NATO stock key) | `Japan_JetF16DBlk52` | **US_F16D_B52** | Portrait/button `us_f16c`; CB `SACRaptor` | default | PRIMARY `2x_AGM88G_AARGM-ER_F16CJ` | `Command_ConstructJapan_JetF16DBlk52` | `GenericTacticalBomberCommandSet` | **UNLOCKED** at airfield | **YES** — 16 objects incl. `SouthKorea_JetF16DBlk52`, Taiwan F-16, Turkey F-16 Blk70 |
| 4 | `OBJECT:EF2000T4CAS` (NATO stock key) | `Japan_JetEF2000T4_CAS` | **NAT_EF2000T4** | same Eurofighter art; CB `SACRaptor` | **0.9** | PRIMARY `6x_GRATGM_Brimstone3_EF2000`; SECONDARY `4x_GBU54B_500lb_LGB_EF2000` | `Command_ConstructJapan_JetEF2000T4_CAS` | `GenericTacticalBomberCommandSet` | **UNLOCKED** at airfield | **YES** — identical W3D to slot 2 and SK CAS |
| 5 | `OBJECT:Chinook` (stock) | `Japan_HelicopterCH47F` | **US_CH47F** (+ wreck `AVChinook_*`) | CB `SACRaptor` | **0.82** | none (transport) | `Command_ConstructJapan_HelicopterCH47F` | `AmericaVehicleChinookCommandSet` | **UNLOCKED** at airfield | **YES** — 8 NATO-clone CH-47s incl. South Korea |
| 6 | `OBJECT:E3A` (stock) | `Japan_E3A` | **US_E3G** | CB `SACRaptor` | **0.78** | PRIMARY `AN_APY2_SAR_SCANMODE` | `Command_ConstructJapan_E3A` | `E3G_CommandSet` | **UNLOCKED** (also CC / MilitaryHQ slot 3) | **YES** — 11 AWACS clones incl. South Korea |
| 7 | `OBJECT:Japan_MQ9` → **Japan MQ9** | `Japan_MQ9` | **CHI_CH5** / D / R | `pla_ch5` | default | PRIMARY `4x_AGM114N_Mq9`; SECONDARY `2x_GBU12II_Mq9` | `Command_ConstructJapan_MQ9` | `GenericTacticalBomberCommandSet` | **LOCKED** — `Japan_Airfield` + `SCIENCE_Rank3` | **YES** vs UAE_MQ9 only (intentional CH-5 stand-in; **not** US MQ-9) |
| 13–14 | Rally / Sell | — | — | — | — | — | `Command_SetRallyPoint` / `Command_Sell` | — | n/a | n/a |

**Off-airfield (not fighter, listed for completeness):**

| Slot / home | Displayed name | Object | W3D | Scale | Weapons | CommandButton | CommandSet | Locked? | Dup visual |
|-------------|----------------|--------|-----|-------|---------|---------------|------------|---------|------------|
| War Factory 12 | Japan UAV Combat | `Japan_CombatDrone` | US_MQ9 / D / R | default | `Japan_Weapon_ATGM` + GBU-12 | `Command_ConstructJapan_CombatDrone` | `GenericTacticalBomberCommandSet` | Rank3 + Japan_Airfield | YES vs 30 combat drones |
| Unwired AAB leftovers | Japan Light/Med/HeavyBomber, AssaultHelo, CombatDrone | `Patch_Japan_*` | US_F16CMB50 / US_B1R / US_B52H / Irq_Mi8T | 0.88 / 0.78 / 0.72 / 0.82 / 0.55 | Patch_Weapon_* | `Command_ConstructPatch_Japan_*` | generic | **UNWIRED** (no CommandSet slot) | YES (global class clones) |

**Japan vs intended fighters:** live slots 1–3 are **F-35C + Eurofighter + F-16**, not **F-15J + F-2 + F-35J**. Japan does not operate Eurofighter or F-16D Blk52. F-2 has **no unique W3D** in the live air-model catalog. Closest live F-15 mesh is `Arb_F15SA` (used by SK F-15K / Saudi F-15SA) or `US_F15C` (Turkey Hürjet). Closest F-35 mesh is `US_F35A` (already on slot 1, but shared).

INI file map:

- `patch/Data/INI/Object/Specter/Japan Self-Defense Forces/Airforce/Japan_F35A.ini` → object `Japan_JetF35C`
- `…/Japan_EF2000_T4.ini` → `Japan_JetEF2000T4`
- `…/Japan_F16DBlk52.ini` → `Japan_JetF16DBlk52`
- `…/Japan_EF2000_T4_CAS.ini` → `Japan_JetEF2000T4_CAS`
- `…/Japan_MQ9.ini` → `Japan_MQ9`
- `…/Rotary/Japan_CH47F.ini` → `Japan_HelicopterCH47F`
- `…/ScienceObjects/Japan_E3A.ini` → `Japan_E3A`

---

### 4.2 South Korea — live `SouthKorea_AirfieldCommandSet`

Producer CommandSet: `SouthKorea_AirfieldCommandSet`  
File: `patch/Data/INI/CommandSet_SouthKorea.ini`

| Slot | Displayed name | Object name | W3D model | Texture / UI art | Scale | Weapon setup | CommandButton | CommandSet (unit) | Locked? | Duplicate visual |
|------|----------------|-------------|-----------|------------------|-------|--------------|---------------|-------------------|---------|------------------|
| 1 | `OBJECT:F35C` (NATO stock; ArmyStrings `OBJECT:SouthKorea_JetF35C` unused by object) | `SouthKorea_JetF35C` | **US_F35A** | Portrait/button `Nat_f35a`; CB `SACRaptor` | default | PRIMARY `GBU_31V2_JDAM_F35C`; SECONDARY AESA AG | `Command_ConstructSouthKorea_JetF35C` | `GenericMultiRoleFighter_AG_CommandSet` | **LOCKED** — `SouthKorea_StrategyCenter` + `SCIENCE_NatoStealthJet` + `SCIENCE_Rank4` | **YES** — same mesh as Japan slot 1 |
| 2 | `OBJECT:EF2000T4` | `SouthKorea_JetEF2000T4` | **NAT_EF2000T4** | `Nat_ef2000t4`; CB `SACRaptor` | **0.9** | `Paveway_IV_EF2000` + CAPTOR AESA | `Command_ConstructSouthKorea_JetEF2000T4` | `GenericTacticalBomberCommandSet` | **LOCKED** — StrategyCenter + `SCIENCE_Rank5` | **YES** — same mesh as Japan slot 2 |
| 3 | `OBJECT:F16Dbk52` | `SouthKorea_JetF16DBlk52` | **US_F16D_B52** | `us_f16c`; CB `SACRaptor` | default | `2x_AGM88G_AARGM-ER_F16CJ` | `Command_ConstructSouthKorea_JetF16DBlk52` | `GenericTacticalBomberCommandSet` | **UNLOCKED** at airfield | **YES** — same mesh as Japan slot 3 |
| 4 | `OBJECT:EF2000T4CAS` | `SouthKorea_JetEF2000T4_CAS` | **NAT_EF2000T4** | same; CB `SACRaptor` | **0.9** | Brimstone3 + GBU-54 | `Command_ConstructSouthKorea_JetEF2000T4_CAS` | `GenericTacticalBomberCommandSet` | **UNLOCKED** at airfield | **YES** — same mesh as Japan slot 4 |
| 5 | `OBJECT:Chinook` | `SouthKorea_HelicopterCH47F` | **US_CH47F** | CB `SACRaptor` | **0.82** | none | `Command_ConstructSouthKorea_HelicopterCH47F` | `AmericaVehicleChinookCommandSet` | **UNLOCKED** | **YES** vs Japan CH-47 |
| 6 | `OBJECT:E3A` | `SouthKorea_E3A` | **US_E3G** | CB `SACRaptor` | **0.78** | AN_APY2_SAR_SCANMODE | `Command_ConstructSouthKorea_E3A` | `E3G_CommandSet` | **UNLOCKED** (also CC / MHQ) | **YES** vs Japan E-3 |
| 7 | `OBJECT:F15SA` (Saudi key) / CB label **F15K** | `SouthKorea_F15K` | **Arb_F15SA** | Portrait/button `arb_f15sa`; CB `us_airfield` (wrong icon) | default | `GBU_31V2_JDAM_F15SA` / MT variant + `AN/APG82K_AESA_Radar_AGMode` | `Command_ConstructSouthKorea_F15K` | `GenericTacticalBomberCommandSet` | **UNLOCKED** at airfield | **YES vs SaudiArabia_F15SA only** — **NO vs Japan/Vietnam** |
| 13–14 | Rally / Sell | — | — | — | — | — | — | — | n/a | n/a |

**Off-airfield:** `SouthKorea_CombatDrone` (War Factory 12, US_MQ9, Rank3) — duplicate vs Japan combat drone. `Patch_SouthKorea_*` bomber/helo/drone class objects exist, **unwired**.

**South Korea vs intended fighters:** intended AAB was F-15K / F-35A / F-16. Live airfield is **F-35C + Eurofighter + F-16 + (slot 7) F-15K**. ROK does operate F-35A, F-16, F-15K; it does **not** operate Eurofighter. KF-21 / FA-50 names do not exist anywhere in live INI. F-15K is the only JP/KR/VN fighter with a **non-NATO-clone** mesh (`Arb_F15SA`), but the in-world name is still the Saudi `OBJECT:F15SA` string.

INI file map:

- `…/Republic of Korea Armed Forces/Airforce/SouthKorea_F35A.ini` → `SouthKorea_JetF35C`
- `…/SouthKorea_EF2000_T4.ini` / `SouthKorea_EF2000_T4_CAS.ini`
- `…/SouthKorea_F16DBlk52.ini`
- `…/SouthKorea_F15K.ini`

---

### 4.3 Vietnam — live `Vietnam_AirfieldCommandSet` (T / T1 / T2 / T3 identical)

Producer: `Vietnam_AirfieldCommandSet` and `Vietnam_AirfieldCommandSet1/2/3` (same five aircraft).  
File: `patch/Data/INI/CommandSet_Vietnam.ini`  
Donor header on every fighter INI: **“Specter Iraq donor clone”**.

| Slot | Displayed name | Object name | W3D model | Texture / UI art | Scale | Weapon setup | CommandButton | CommandSet (unit) | Locked? | Duplicate visual |
|------|----------------|-------------|-----------|------------------|-------|--------------|---------------|-------------------|---------|------------------|
| 1 | `OBJECT:Mig-29A` (Iraq/stock); CB “Vietnam Mig-29A” | `Vietnam_Mig-29A` | **Irq_Mig29A** | Object portrait `us_airfield`; CB **`irq_t72a`** | default | PRIMARY `4x_R27_MRBVR_Mig29A` | `Command_ConstructVietnam_Mig-29A` | `GenericMultiRoleFighterCommandSet` | **UNLOCKED** at airfield | **YES** — 9 other Iraq-kit MiG-29s (Egypt, India, Libya, Pakistan, …) |
| 2 | `OBJECT:MirageF1_Eq` | `Vietnam_MirageF1_Bq` | **Irq_MirageF1_Bq** | portrait `us_airfield`; CB **`irq_t72a`** | default | PRIMARY `2x_KH29L_AGM_F1EQ` | `Command_ConstructVietnam_MirageF1_Bq` | `GenericTacticalBomberCommandSet` | RadarStation required | **YES** — 9 other Mirage F1 clones. **Vietnam never operated Mirage F1.** |
| 3 | `OBJECT:Su25K` | `Vietnam_Su-25K` | **Irq_Su25k** | CB **`irq_t72a`** | **0.9** | Fab-250 + KH-25ML + S-8 | `Command_ConstructVietnam_Su-25K` | `3rdGenCloseAirSupportFighterCommandSet` | **UNLOCKED** at airfield | **YES** — 10 other Su-25K clones. **Vietnam operates Su-22, not Su-25.** |
| 4 | `OBJECT:Mi-8` | `Vietnam_Mi-8T` | **Irq_Mi8T** | CB **`irq_t72a`** | default | (helo) | `Command_ConstructVietnam_Mi-8T` | `AmericaVehicleChinookCommandSet` | SupplyCenter required | **YES** — 37 objects (Patch assault helos + Iraq-kit Mi-8s). Role is plausible (Mi-17/8 family). |
| 5 | `OBJECT:IL-76` | `Vietnam_IL-76` | **Iraq_IL-76** | CB **`irq_t72a`** | **0.9** | transport | `Command_ConstructVietnam_IL-76` | `Command_ScriptedTransportDrops` | **UNLOCKED** (also CC/MHQ slot 12) | **YES** — 8 other IL-76 clones |
| 13–14 | Rally / Sell | — | — | — | — | — | — | — | n/a | n/a |

**Off-airfield:** `Vietnam_ReconDrone` (War Factory, US_MQ9, Rank3 + `SCIENCE_NatoStealthJet`). `Patch_Vietnam_*` class aircraft **unwired**. Science menu still sells `Upgrade_Vietnam_Su30Doctrine` with **no Su-30 object**.

**Vietnam vs intended fighters:** intended AAB was **Su-30 / MiG-21 / Su-22**. Live is **MiG-29 / Mirage F1 / Su-25**. MiG-29 is the only live fighter that is historically plausible. Donor meshes that **do** exist elsewhere in live INI and are unused by Vietnam:

- Su-30 class: `Arb_Su30MKA` (`India_Su30MKI`)
- Su-22 class: `Irq_SU22M3` (Iraq/Turkey), `Irn_SU22M2` (Iran)
- MiG-21: **no distinct W3D** in the live air-model catalog (historical Patch object used F-16 mesh)

INI file map:

- `…/Vietnam People's Army/Airforce/Vietnam_Mig-29A.ini`
- `…/Vietnam_MirageF1-Bq.ini` → object `Vietnam_MirageF1_Bq`
- `…/Vietnam_Su-25K.ini`
- `…/Vietnam_Mi-8.ini` → `Vietnam_Mi-8T`
- `…/ScienceObjects/IL-76.ini` → `Vietnam_IL-76`

---

## 5. Cross-country fighter visual clusters (the reported bug)

These are the live W3D collisions that make Japan / South Korea / Vietnam fighters look interchangeable.

| W3D | Japan | South Korea | Vietnam | Other live users (count) |
|-----|-------|-------------|---------|--------------------------|
| **US_F35A** | JetF35C | JetF35C | — | NATO clones + USA F-35C + Turkey Anka3 (~12) |
| **NAT_EF2000T4** | EF2000 + CAS | EF2000 + CAS | — | Britain/France/Germany/Italy/UN Typhoon (~20) |
| **US_F16D_B52** | F16DBlk52 | F16DBlk52 | — | NATO F-16s, Taiwan, Turkey Blk70, JF-17 (~17) |
| **Arb_F15SA** | — | **F15K** | — | SaudiArabia_F15SA (1) |
| **Irq_Mig29A** | — | — | Mig-29A | 9 Iraq-kit countries |
| **Irq_MirageF1_Bq** | — | — | MirageF1 | 9 Iraq-kit countries |
| **Irq_Su25k** | — | — | Su-25K | 10 Iraq-kit countries |
| **US_CH47F** | CH47F | CH47F | — | NATO CH-47 clones |
| **US_E3G** | E3A | E3A | — | NATO AWACS + Patch E-2C |
| **Irq_Mi8T** | Patch assault helo (unwired) | Patch assault helo (unwired) | **Mi-8T (live)** | 37 |
| **US_F16CMB50** | Patch light bomber / combat drone (unwired) | same unwired | same unwired | **73** objects (historical AAB fighter default) |

Japan slot 1–4 and South Korea slot 1–4 are **pairwise identical meshes**. Vietnam fighters do not share those NATO meshes; they share the **Iraq army kit** instead, so they look like Egypt/Syria/Libya rather than a VPA roster.

---

## 6. CommandButton / CommandSet wiring notes

| Topic | State |
|-------|--------|
| Live producers | Country `*_AirfieldCommandSet` only. Worker builds `Japan_Airfield` / `SouthKorea_Airfield` / `Vietnam_Airfield_T`. **No** `Command_Construct*_AdvancedAirBase` on live worker sets. |
| AAB CommandSets | Live `CommandSet_AdvancedAirBase.ini` is a stub (dozer/strategy restore only). Historical JP/KR/VN AAB menus are not loaded. |
| Air Force Final CommandSets | `CommandSet_AirForceFinal.ini` comment: “REMOVED AdvancedAirBaseCommandSet block”. |
| Button art | Japan/SK air units almost all use **`SACRaptor`**. Vietnam air units use **`irq_t72a`** (tank icon). SK F-15K uses **`us_airfield`**. Object-level portraits are better (`Nat_f35a`, `Nat_ef2000t4`, `us_f16c`, `arb_f15sa`, `pla_ch5`) but the CommandButton often ignores them. |
| Unit CommandSets | Shared generics (`GenericTacticalBomberCommandSet`, `GenericMultiRoleFighter_AG_CommandSet`, `AmericaVehicleChinookCommandSet`, `E3G_CommandSet`). Not country-unique. |
| Duplicate CommandButton IDs | Not re-audited as broken; prior duplicate-button repair stands. New issue is **shared ButtonImage**, not duplicate button names. |

---

## 7. Packaging / art inventory (repair later, not now)

Live air INI already references distinct Specter meshes that **could** differentiate rosters without new vendor archives (overlay Draw remap only). Not applied:

| Role | Existing live Model= elsewhere | Current JP/KR/VN user |
|------|--------------------------------|------------------------|
| F-15 class | `Arb_F15SA`, `US_F15C` | SK F-15K already `Arb_F15SA`; Japan F-15J missing |
| F-35 class | `US_F35A` | Japan + SK already, shared |
| F-16 / F-2 stand-in | `US_F16D_B52`, `US_F16CMB50`, `US_F16CJ_blk52`, `Arb_F16C_B60`, `Egy_F16C` | JP+SK share `US_F16D_B52` |
| Eurofighter (should not be JP/KR) | `NAT_EF2000T4`, `Arb_EF2000` | JP+SK both `NAT_EF2000T4` |
| Su-30 | `Arb_Su30MKA` (India) | Vietnam intended, unused |
| Su-22 | `Irq_SU22M3`, `Irn_SU22M2` | Vietnam intended, unused |
| MiG-21 | **none unique** | Vietnam intended |
| MiG-29 | `Irq_Mig29A` | Vietnam live (plausible) |
| KF-21 / FA-50 / F-2 unique | **none in live air Model catalog** | not present |

True unique F-2 / KF-21 / MiG-21 W3D would require ART (DONOR_Art / art_data / `_SPEC_ART_ONE`), which this audit did not unpack. Policy remains overlay-only; `mod.z23`/`mod.z24` still missing per `MOD_CONTENT_AUDIT.md`.

---

## 8. What this audit did **not** do

- No INI, string, CommandSet, CommandButton, weapon, or art edits.
- No USA / Russia / China / Turkey / India file changes.
- No re-enable of Advanced Air Base.
- No packaging rebuild.
- No in-game launch (Linux environment; static INI parse only).

---

## 9. Repair backlog (documented only)

Priority if a later pass is authorized, without touching USA/Russia/China:

1. **Japan fighters:** replace Eurofighter + F-16 slots with F-15J / F-2 identity; keep F-35 but unique name (`F-35J`) and preferably a non-shared Draw if an F-35 mesh can be reserved. Fix `SCIENCE_NatoStealthJet` vs `SCIENCE_Japan_StealthJet`.
2. **South Korea fighters:** remove Eurofighter; keep F-15K / F-35A / F-16; fix DisplayName `OBJECT:F15SA` → F-15K; fix F-35 science ID; consider KF-21 only if art exists.
3. **Vietnam fighters:** replace Mirage F1 + Su-25 with Su-30 / Su-22 (donors `Arb_Su30MKA` / `Irq_SU22M3` exist); keep or add MiG-29; MiG-21 only if a mesh exists.
4. **Do not blindly restore** historical `Patch_*` AAB objects — they all used `US_F16CMB50` and would **not** fix the duplicate-visual bug.
5. **Do not re-enable AAB** as a side effect of fighter identity work unless explicitly requested (USA B-2 path is currently airfield-only).

**END AUDIT — NO GAME FILES CHANGED**
