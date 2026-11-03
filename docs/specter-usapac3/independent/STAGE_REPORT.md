# USAPAC3 independent functional stage 1

Zero Hour was **not** run. This is a static DATA change only.
Appearance is still live THAAD Draw (`US_M1120`). New Donor art was not
attached. Previous GitHub Releases were not deleted or rewritten.

THAAD originals, `S400ECommandSet`, `OCL_THAAD_*`, `Weapon.ini`,
`S400R_Deploy`, Patriot, NASAMS, `ABPatriot.W3D`, `ABNPatriot02*`,
`pac3_sudarb.W3D`, ART ONE, ART TWO, `failed-impl`, and `abtest` were
not rewritten.

## New names

| Kind | Name |
|---|---|
| CommandSet | `USAPAC3CommandSet` |
| CommandSet | `USAPAC3CommandSet_AA` |
| CommandSet | `USAPAC3CommandSet_ABM` |
| CommandSet | `USAPAC3CommandSet_Deployed` |
| OCL | `OCL_USAPAC3_Deployed` |
| OCL | `OCL_USAPAC3_Deployed_ABM` |
| OCL | `OCL_USAPAC3_Pack` |
| Object | `USAPAC3_CombatMode` |
| Object | `USAPAC3_FireControlSystem` |
| Object | `USAPAC3_FireControlSystem_ABM` |
| Weapon (dummy) | `USAPAC3_Weapon` / `_ABM` / `_Pack` |

`OCL_USAPAC3_Pack` is required so Pack does not spawn `US_THAAD_PackMode`.
It is PAC-3-only and is not a THAAD name.

`AirdefenseLinkRestarter` is spawned by the deploy OCLs. It is existing
SPECTER air-defense glue, not a THAAD TEL/FCS. No new radar system was added.

MultiTarget stays the shared `Command_ADS_MTS_SWITCH` (`Upgrade_AIM-120C`)
with no `TriggeredBy` on `USAPAC3`, so the button stays disabled.

## AA chain

1. `Object USAPAC3` `CommandSet = USAPAC3CommandSet`
2. `Command_AADS_AA_Mode` → `Upgrade_AADS_AA_Mode`
3. `CommandSetUpgrade` → `USAPAC3CommandSet_AA`
4. `Command_ADSCombatMode` `FIRE_WEAPON SECONDARY` → `USAPAC3_Weapon`
5. `SlowDeath` `SPLATTED` → `OCL_USAPAC3_Deployed`
6. Creates `USAPAC3_FireControlSystem` (`PRIMARY 8x_LRSAM_THAAD`) +
   `USAPAC3_CombatMode` + `AirdefenseLinkRestarter`

## ABM chain

1. Same initial set
2. `Command_AADS_ABM_Mode` → `Upgrade_AADS_ABM_Mode`
3. `CommandSetUpgrade` → `USAPAC3CommandSet_ABM`
4. `Command_ADS_ABM_CombatMode` `FIRE_WEAPON TERTIARY` → `USAPAC3_Weapon_ABM`
5. `SlowDeath` `EXTRA_8` → `OCL_USAPAC3_Deployed_ABM`
6. Creates `USAPAC3_FireControlSystem_ABM` (`PRIMARY THAADMissile_ABM`) +
   `USAPAC3_CombatMode` + `AirdefenseLinkRestarter`

Missile stats are referenced, not copied: `8x_LRSAM_THAAD` and
`THAADMissile_ABM` in packed `Weapon.ini` are unchanged.

## Deploy and Pack

Deploy is still `FIRE_WEAPON` suicide (proven THAAD ControlBar pattern;
packed `CommandButton.ini` has no `TOGGLE_DEPLOY`). Only the OCL target
and CommandSet names are PAC-3-specific.

Pack: `USAPAC3CommandSet_Deployed` slot 13 `Command_FireControlPack`
`FIRE_WEAPON SECONDARY` → `USAPAC3_Weapon_Pack` → `OCL_USAPAC3_Pack` →
`Object USAPAC3`. `FireWeaponWhenDeadBehavior` still uses shared
`FCS_POWER_ZERO_Pack` by reference to drop the PAC-3 FCS.

## THAAD before / after (packed hashes, unchanged)

| File | SHA-256 |
|---|---|
| `US_M1120.ini` | `b56d62cdb44d0d3e582df51aeee56fcb25a447397983e8ced5788a4520dae92f` |
| `Weapon.ini` | `a8eb8340aecd1bd04147e97b4b5ce218f91233464178c34c66ff2cc003c5d6b8` |
| `CommandSet.ini` | `f6d9616febbf4eeb2720f6029a7089e7ce1f3d31a576d4f097c738348be9d223` |
| `CommandButton.ini` | `1870f1118e20e64b9f4186c49dd561884296ddda9fb7b2caa90bd9f26e8eb65c` |
| `ObjectCreationList.ini` | `e284d55c2b96fcb8c6aa585d155ba94b9f6fbbe1810f30cde96e3ef6bc16cff5` |
| `ObjectCreationList_ZZZZ_ZZGmAdAbm.ini` | `ee88eb90ee1ac12d1127daaf19529f1477b21987582f1102ffbb2a60b3ad79ad` |
| `_SPEC_ART_TWO.big` | `2a65d89d60db9696a2b3a69df5a1c7cb173e10de027e7be6aedb6ba3cb47ae38` |

## Changed files

- `patch/Data/INI/Object/Specter/United States Of America/AirDefense/USAPAC3.ini`
- `patch/Data/INI/Weapon_USAPAC3.ini`
- `patch/Data/INI/CommandSet_USAPAC3.ini` (new unique path)
- `patch/Data/INI/ObjectCreationList_USAPAC3.ini` (new unique path)
- `docs/specter-usapac3/base/USAPAC3.ini` / `Weapon_USAPAC3.ini`
- packed `Data\INI\...` copies of the four INI above inside `_SPEC_DATA_ONE.big`

`CommandSet.ini` / installer CommandSet / CommandButton were **not** edited.
ART TWO was **not** edited.

## Output SHA-256

| Artifact | SHA-256 | Bytes |
|---|---|---|
| `_SPEC_DATA_ONE.big` | `347f04b919edd733c519740919a48d493700fca6bc2f0ed5a224b64ed2f2ebbe` | 374101537 |
| `_SPEC_ART_TWO.big` (unchanged, not in ZIP) | `2a65d89d60db9696a2b3a69df5a1c7cb173e10de027e7be6aedb6ba3cb47ae38` | 308844919 |

ZIP and installer-file hashes: `docs/specter-usapac3/independent/SHA256SUMS.txt`.

Packed DATA entries: 3585 (was 3583; added `CommandSet_USAPAC3.ini` and `ObjectCreationList_USAPAC3.ini`).

## Static validation

`python3 docs/specter-usapac3/independent/validate_independent.py` → `STATIC_OK`

INGAME_ZH: not executed.
