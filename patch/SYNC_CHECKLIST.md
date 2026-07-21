# Specter Patch — Multiplayer Sync Checklist

**Status:** Required gate before adding more units, weapons, or factions.  
**Last audit:** CountryBalance v2 income + MP sync hardening (Side / LinkKey / Lifetime pin).

SAGE/Zero Hour multiplayer requires every client to simulate the same game state.
This patch is an **overlay**: all clients must ship **identical** `patch/` contents.
Do not rely on runtime randomness or per-machine file differences.

---

## Non-negotiable rules

1. **Deterministic data only**  
   - No gameplay `RandomValue` / `RandomDelay` / seed fields on weapons, damage, production, or economy.  
   - Cosmetic `RandomBone` on particles is allowed (engine FX only).  
   - `LifetimeUpdate` / `DeletionUpdate`: keep `MinLifetime == MaxLifetime` (pinned).  
   - Country Balance bake uses fixed `round()`; keep `; PatchBaseCost` markers so re-bakes do not compound.

2. **Never modify original Specter archives**  
   - Do **not** edit or re-pack: `Data.zip`, `Specter_Data*`, `_SPEC_DATA_ONE*`, `_SPEC_ART_ONE*`, `payload.rar`, or any `.big`.  
   - All content lives under `patch/` as additive/override INI + art.

3. **Identical load for all factions / all clients**  
   - ZH loads the full INI set for every player.  
   - Do not ship client-specific or faction-conditional loose files.  
   - One patch package hash for the whole lobby.

4. **One definition per ID**  
   - Unique: `Object`, `Upgrade`, `Science`, `Weapon`, `CommandSet`, `CommandButton`, `PlayerTemplate`.  
   - No duplicate blocks with different `BuildCost` / `BuildTime`.  
   - No two `BuildCost` lines inside the same Object.

5. **Player production ≠ AI-only variants**  
   - Player CommandSets must not build `*_AI` Objects that have different stats/costs.  
   - AI factories may exist, but if they share a CommandSet reachable by players, use the same Object IDs as players.

6. **Side ownership matches faction tree**  
   - Objects under `Turkey Armed Forces/` (etc.) that are player-buildable must have `Side = <Faction>`.  
   - Wrong `Side` causes wrong Country Balance multipliers if re-baked.

---

## Audit scope (run before every content PR)

| Area | Paths |
|------|--------|
| Objects | `patch/Data/INI/Object/**/*.ini` |
| Weapons / weapon objects | `**/Weapon*.ini`, `**/*WeaponObjects.ini` |
| CommandSet | `patch/Data/INI/CommandSet*.ini` |
| CommandButton | `patch/Data/INI/CommandButton*.ini` |
| Science | `patch/Data/INI/Science*.ini` |
| Upgrade | `patch/Data/INI/Upgrade*.ini` |
| PlayerTemplate | `patch/Data/INI/PlayerTemplate*.ini` |
| Economy bake | `patch/Data/INI/CountryBalance.ini` + `tools/economy/*` |

### Automated check

```bash
python3 patch/tools/economy/sync_audit.py
# expect: PASS, errors=0
# covers: duplicate IDs, dual BuildCost, Random* fields, Min!=Max Lifetime,
#         player CommandSet *_AI / MilitaryWarfactory constructs,
#         Side vs faction folder (BuildCost Objects), LinkKeys, vendor git dirty
```

---

## Pre-merge checklist (tick all)

- [x] `sync_audit.py` exits 0  
- [x] No new gameplay Random* keys  
- [x] LifetimeUpdate/DeletionUpdate MinLifetime == MaxLifetime  
- [x] No edits to Specter zip/big archives in the commit  
- [x] No duplicate Object/Upgrade/Science/CommandSet/CommandButton/PlayerTemplate IDs  
- [x] No Object with two `BuildCost` / `BuildTime` pairs  
- [x] Player CommandSets do not reference `*_AI` construct buttons or MilitaryWarfactory  
- [x] AD / strategic launcher Objects have LinkKeys (`Patch_AirDefense` / `Patch_StrategicLauncher` / `Patch_ArtillerySite` / `Patch_Nuclear`)  
- [x] If costs changed: ran `apply_country_balance.py` and committed baked INIs + `PatchBaseCost` markers  
- [x] Faction-tree BuildCost Objects have correct `Side`  
- [ ] All lobby clients will install the **same** patch build (same commit / package) — host responsibility  
- [ ] CSF/strings overlay identical on all clients (UI only; still ship same file) — host responsibility  

---

## Known-safe patterns

| Pattern | Why OK |
|---------|--------|
| `RandomBone` on smoke/fire | Cosmetic particles |
| `BuildVariations` lists | Engine syncs choice from sim RNG shared across peers |
| `; PatchBaseCost` / `; CountryBalance` comments | Documentation; not simulated |
| AI Object INIs unused by player CommandSets | Not produced in MP by players |
| Scaffold factions starting with Iraq units | Same on every client until faction is fully authored |
| Vendor `Data.zip` present at repo root | Read-only reference; never modify |

---

## Fixes applied in desync audits (reference)

- Removed duplicate `Upgrade_Turkey_BMP-1M3` (conflicting costs).  
- Removed player CommandSet links to `*_AI` / MilitaryWarfactory constructs; fixed CC slot 17 clash.  
- AI `Turkey_WarFactoryCommandSet` now uses player Object IDs.  
- Fixed dual `BuildCost` on `Turkey_Lamiaa`.  
- Fixed `Side` on Ababil200R recon + Ural supply AI → `Turkey`.  
- Renamed duplicated helper Objects from Phase 4 copies (`Turkey_SIPER_FireControl*`, `Turkey_BoraHulk`).  
- CountryBalance v2: income AutoDeposit channels baked; drone/domestic cost mults deterministic.  
- Fixed wrong `Side` (America/GLA leftovers) on Turkey systems / Fab bombs / CombatTrench.  
- `Turkey_HISAR_A_Combat` now shares `Patch_AirDefense` LinkKey (build-limits SKIP no longer drops `*Combat`).  
- Pinned hulk / Bora / AbbasLauncher `LifetimeUpdate` Min==Max.  

---

## Packaging note for hosts

Distribute one zip/folder of `patch/` (and matching `generals.csf` if used).  
If any client has a different bake of `BuildCost` / CommandSets, the match will desync.  
Prefer tagging a release commit and forbidding mid-season local re-bakes without a lobby-wide update.
