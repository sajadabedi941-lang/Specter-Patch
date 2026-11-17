# SPECTER Multiplayer OOS diagnostic

**Zero Hour was not run. A 4-player match was not reproduced.**
This is a static diagnosis of live `_SPEC_DATA_ONE.big` (combo-hide / vietnam-radar lineage) plus EA Zero Hour source. It is **not** a fix and does not claim the mismatch is resolved.

Dialog text **"Game has detected a mismatch"** is `GameLogic` CRC compare (`TheNetwork->setSawCRCMismatch()`). It is not a map/version lobby check. The engine checksums, every validation frame:

1. every Object snapshot
2. GameLogic random seed
3. PartitionManager
4. ModuleFactory
5. PlayerList
6. AI

Any extra, missing, or differently updated object changes the CRC. That is why the failure appears only after the battlefield fills up: CRC surface grows with object count.

---

## Static vs real 4-player test

| Kind | Done? | Result |
| --- | --- | --- |
| Static scan of live DATA BIG (3580 files, 3062 INI) | Yes | Candidates below |
| EA ZH source (`GameLogic.cpp`, `GUIUtil.cpp`) | Yes | CRC + combo mechanisms confirmed |
| Compare SPECTER volume vs stock ZH patterns | Yes | SPECTER adds far more logic projectiles / FireOCL / FireWeaponUpdate |
| 4-player in-game OOS | **No** | Not run on this machine |
| Network CRC dump / `Generals.dbg` from a failed match | **No** | Not provided |

Do not treat this report as a patched multiplayer build.

---

## What the previous SPECTER “sync” audit actually checked

`patch/tools/economy/sync_audit.py` and `SYNC_FINAL_REPORT.md` (2026-07-23, PASS) only check overlay `patch/Data/INI` for duplicate IDs, dual costs, `Random*` **assignments**, and `MinLifetime != MaxLifetime`.

That is **not** a multiplayer CRC test. It does not load `_SPEC_DATA_ONE.big`, does not simulate weapons, and treats GameLogic RNG ranges as errors even when the engine consumes them from the synced seed. A PASS there does not predict 4-player OOS.

---

## How Zero Hour decides “mismatch”

Source: `GeneralsMD/Code/GameEngine/Source/GameLogic/System/GameLogic.cpp`.

Clients are lockstep. Each player sends a CRC. If any CRC differs, the dialog appears. Scatter / lifetime ranges use `GameLogicRandomValue` and stay in sync **only if every client creates the same objects in the same order and draws the same number of random values**.

OOS at high unit count therefore means: some client created, skipped, or updated an object differently once the object table got large — not that `PlayableSide` or CSF is wrong.

---

## Candidates (ranked, with evidence)

### 1. Install / load-order skew (highest practical risk)

`ThingFactory` loads `Data\INI\Object` as a **directory**. `FileSystem::openFile` reads loose files first, then the first BIG that owns the path.

Live DATA contains **283 duplicate Object names** (5437 unique names). Examples: infantry and radars defined both under `Data\INI\Object\Specter\...` and later `Object_ZZZZ_*` / `zzzzz_*` files. Same BIG → same last-write. A leftover **loose** `Data\INI\Object\...` on one PC only → that unit’s modules differ the moment many of those units exist.

SPECTER also requires loose `Data\INI\CommandSet.ini` and `CommandButton.ini` (INIZH first-wins those paths). `PlayerTemplate.ini` is also loose. If any of the four PCs has an older loose file or an extra `0_` / `zz_` BIG, versions can “look the same” in the lobby and still CRC-diverge in combat.

**Evidence:** load path in EA source + 283 in-BIG duplicates + SPECTER’s documented loose CS/CB/PT install. **Not proven** for this report’s match, because the four game folders were not hashed.

### 2. SPECTER logic-projectile density (best match for “soldiers and tanks past a threshold”)

Stock ZH uses many hitscan / simple shots. Live SPECTER `Weapon.ini` has **2050** `ProjectileObject` lines and **597** unique projectile objects. **122** weapons use `30mm_API-T_Projectile`.

That object (Iraq `Expermental_Objects.ini`, reused globally) is a full GameLogic projectile:

- `DumbProjectileBehavior` + `PhysicsBehavior`
- `FireWeaponUpdate` → weapon `30mm_API-T` (`PrimaryDamage = 0`)
- `FireWeaponWhenDeadBehavior` → `30mm_API-T_Impact`

Every cannon burst creates real objects that tick updates and enter the CRC. **416** projectile templates also have `FireWeaponUpdate` (path jitter, boosters, RCS, GLMMC). There are **822** `FireWeaponUpdate` behaviors and **390** `FireOCL` lines in `Weapon.ini`.

SPECTER-only `FireOCL` examples that run during heavy fire (not stock bike-death debris):

| OCL | Used from | Effect |
| --- | --- | --- |
| `OCL_GenericAAMissilePathChanging` | weapon `GenericAAMissilePathChanging` | `ApplyRandomForce` |
| `OCL_RocketWindEffect` | Weapon.ini | `ApplyRandomForce` |
| `OCL_ArtillaryShellWindEffect1/2/3` | artillery path | `ApplyRandomForce` |
| `OCL_JSOW_*` / `OCL_155mm_*` / `OCL_9M528_*` / `OCL_MGM140_*` bomblet waves | cluster weapons | `ApplyRandomForce` + extra objects |

`ApplyRandomForce` is GameLogic RNG (synced **if** the same OCL runs). It is still extra objects + extra seed draws per shot. A 4-player tank / AAA / MLRS fight multiplies this far beyond stock ZH.

**Not proven as the CRC bit.** It is the SPECTER-specific system that scales exactly with “lots of soldiers and tanks shooting.”

### 3. Drone / hulk lifetime windows (secondary)

`LifetimeUpdate` / `DeletionUpdate` with `MinLifetime != MaxLifetime`: **83** (513 pinned equal).

SPECTER-added large windows (stock hulks are ~9500–9600):

| Object | Module | Min | Max |
| --- | --- | --- | --- |
| `RussiaDroneFPV` | DeletionUpdate | 20000 | 40000 |
| `RussiaDroneLancet3` | DeletionUpdate | 50000 | 70000 |
| `Iraq_Sarab3` / copies (JP/SK/VN/NK light drones) | DeletionUpdate | 50000 | 70000 |

Hulk `LifetimeUpdate` 9500–9600 appears on many SPECTER wrecks. That pattern exists in stock ZH wrecks too. RNG is synced if the same hulks spawn.

**Do not call this the cause** just because Min ≠ Max. It only matters if one client skips creating some drones/hulks (cap, first-win, or a failed create).

### 4. Aircraft `FireWeaponWhenDamaged` / `RadarWaveEmitter` (weak for this repro)

**822** SPECTER aircraft use `FireWeaponWhenDamagedBehavior ModuleTag_RS` with `RadarWaveEmitter` (`FireOCL = OCL_GenericRadarCrossSection`) on `+MICROWAVE` only. A ground-only infantry/tank fight should not hit this unless EW/microwave weapons are in play. **Not the primary suspect** for the stated repro.

### 5. Engine / hardware (not a SPECTER INI line)

- Sleepy-update heap orders by wake frame only (`isLowerPriority`). Equal-frame ties follow insertion order (object create order). That stays synced if creates match; it becomes fragile when they do not.
- Different CPU families (AMD vs Intel) have a long-standing Generals FPU OOS reputation. More objects → more float ops → more chance. **Not proven here.**

### 6. What was checked and is unlikely

| Item | Why it is not the smoking gun |
| --- | --- |
| `PlayableSide` / Arabic Alliance combo | Combo filter only; not in CRC |
| `ScatterRadiusVsInfantry` | Stock field; GameLogic RNG |
| `Animation2D RandomizeStartFrame` | Client animation |
| `RandomOffsetForHowitzer` | Commented unused on SPECTER AWACS |
| `DelayBetweenShots` min–max ranges | **0** in live Weapon.ini |
| `SharedSyncedTimer` | Teammate cooldown share, not CRC |
| `MaxParticleCount` (DATA=4000) | Particles are not GameLogic objects |
| Scripts / `.scb` | **0** script files in DATA BIG |
| Object ID 32-bit wrap | Needs billions of creates; not a skirmish |

---

## Stock ZH vs SPECTER (why countries “work” until the field fills)

Countries being playable only means `PlayerTemplate` + starting building work. The CRC does not care about faction count. It cares how many **logic objects** those factions spawn when they shoot.

Stock ZH: a tank MG is often instant or a cheap tracer. SPECTER: the same visual role is frequently a `PROJECTILE` object with physics, `FireWeaponUpdate`, death weapons, and `FireOCL` path noise. Four full armies crossing that threshold is a different simulation than one-player skirmish.

---

## What is required to name the actual CRC bit

Without these, any “fix” would be a guess.

1. **Install identity from all four PCs** (run `hash_game_folder.py` below, send the four texts):
   - `_SPEC_DATA_ONE.big` SHA-256
   - every `0_*.big` / `zz*.big` SHA-256
   - loose `Data\INI\CommandSet.ini`, `CommandButton.ini`, `PlayerTemplate.ini`, `Weapon.ini` if present
   - count of loose files under `Data\INI\Object`
2. **One failed match:** map name, four countries, roughly when the dialog appeared (time + “lots of tanks/infantry” vs “after MLRS/AD/air”).
3. If anyone still has **Generals.dbg / Network log / CRC mismatch dump** from that session, send it. Retail ZH often only shows the dialog; a debug binary would print `CRC from player N = ...` per `GameLogic.cpp`.
4. Two isolation games, same map/mod:
   - Ground only (no AD fire, no MLRS/cluster, no drones/Shahed)
   - Same unit count with AD + artillery allowed  
   If only (b) OOS, suspect FireOCL / missile objects. If both OOS, suspect install skew or generic projectile flood.
5. Note CPU vendors (all Intel / mixed AMD+Intel).

---

## What this pack does **not** change

No Gameplay INI, no `_SPEC_DATA_ONE.big`, no ART, no `0_` overlays, no Shahed/Vietnam/AA combo edits. A gameplay patch without a CRC dump would be an untested guess.

If later evidence points at a specific object (for example one projectile `FireWeaponUpdate` that one client skips), that fix should be a **separate** PR.
