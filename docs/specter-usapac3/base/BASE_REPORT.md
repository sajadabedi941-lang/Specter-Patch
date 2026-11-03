# USAPAC3 stage 1 — THAAD-clone base unit

Zero Hour was **not** run. In-game spawn is **not** verified here.
New Donor art was **not** imported. Previous GitHub Releases were **not**
deleted or rewritten.

## What was built

New `Object USAPAC3` cloned from the packed live winner of `Object US_THAAD`
in `Data\INI\Object\Specter\United States Of America\AirDefense\US_M1120.ini`.

Last-wins duplicate in `Object_ZZZZ_ZzGlobalStoreFivePrereq.ini` differs only
in Prerequisites (`America_GlobalStore` vs `AmericaStrategyCenter_T`). Both
Prerequisites blocks were dropped on USAPAC3 (locked spec: no Prerequisite).
Draw, modules, locomotor, geometry, and deploy OCL match `US_M1120.ini`.

| Field | Value |
|---|---|
| Object | `USAPAC3` |
| Side | America |
| Cost / time | 3876 / 18.6 |
| Draw | `W3DTruckDraw` — `US_M1120` / `US_M1120D` / `US_M1120_A` / `US_M1120_AD` |
| Locomotor | `Generic8x8Locomotor` |
| AI | `DeployStyleAIUpdate` |
| Unit CommandSet | `S400ECommandSet` (existing; not a new set) |
| Weapons | `USAPAC3_Weapon` + `USAPAC3_Weapon_ABM` |
| Projectile | none — packed `S400R_Deploy` has no `ProjectileObject` |
| Build | `AmericaCommandCenterCommandSet` slot 6 |
| Science / Rank / Upgrade / Prerequisite | none on object or construct button |

`USAPAC3_Weapon_ABM` exists because live THAAD WeaponSet has SECONDARY and
TERTIARY dummy deploy weapons (`SPLATTED` → `OCL_THAAD_Deployed`, `EXTRA_8` →
`OCL_THAAD_Deployed_ABM`). Sharing those names was unnecessary; cloning both
keeps the spawn/fire path independent without a new projectile.

## Files changed

| Path | Role |
|---|---|
| `docs/specter-usapac3/base/USAPAC3.ini` | source Object |
| `docs/specter-usapac3/base/Weapon_USAPAC3.ini` | source weapons |
| `patch/Data/INI/Object/Specter/United States Of America/AirDefense/USAPAC3.ini` | overlay copy of Object |
| `patch/Data/INI/Weapon_USAPAC3.ini` | overlay copy of weapons |
| packed `Data\INI\Object\...\AirDefense\USAPAC3.ini` | DATA winner |
| packed `Data\INI\Weapon_USAPAC3.ini` | DATA weapons |
| `CommandButton.ini` (packed + loose + installer) | append `Command_ConstructUSAPAC3` |
| `CommandSet.ini` (packed + loose + installer + patch Data) | slot 6 only |
| `_SPEC_DATA_ONE.big` | repack (3583 entries) |

## Files not changed

- `Object US_THAAD` / `US_M1120.ini` (sha `b56d62cd…`)
- Patriot `AmericaMobileSamSiteMIM104F`
- NASAMS / HQ overlay slot 6 still `Command_ConstructAmerica_AD_NASAMS`
- F-117 / B-21
- `_SPEC_ART_ONE.big` / `_SPEC_ART_TWO.big`
- archive `docs/specter-usapac3/archive/failed-impl/` and abtest docs

## Static validation

`python3 docs/specter-usapac3/base/validate_base_thaad.py` → `STATIC_OK`

INGAME_ZH: not executed. Do not treat this stage as crash-fixed until the unit
builds in Zero Hour.
