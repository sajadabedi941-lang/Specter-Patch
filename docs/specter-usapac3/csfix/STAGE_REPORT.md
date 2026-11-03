# USAPAC3 CommandSet load-path fix (Release 748 buttons)

Zero Hour was **not** run. This is a static DATA + `CommandSet.ini` change.
Appearance is still live THAAD Draw (`US_M1120`). New Donor art was not
attached. Previous GitHub Releases, including `specter-usapac3-independent`
(PR #748), were not deleted or rewritten.

THAAD originals, `S400ECommandSet*`, `OCL_THAAD_*`, `Weapon.ini`,
`S400R_Deploy`, Patriot, NASAMS, `ABPatriot.W3D`, `ABNPatriot02*`,
`pac3_sudarb.W3D`, ART ONE, ART TWO, `failed-impl`, and `abtest` were
not rewritten. Unique PAC-3 source files were not deleted.

## Cause of the missing buttons

Release 748 gave `Object USAPAC3` unique CommandSet names:

- `USAPAC3CommandSet` (initial: MultiTarget / Anti Air / Anti Missile)
- `USAPAC3CommandSet_AA` (Deploy)
- `USAPAC3CommandSet_ABM` (Deploy)
- `USAPAC3CommandSet_Deployed` (Pack)

Those four blocks lived only in packed `Data\INI\CommandSet_USAPAC3.ini`.
They were **not** in live `CommandSet.ini`.

Zero Hour ControlBar first-wins loose `Data\INI\CommandSet.ini`.
`Launch_Specter.bat` copies the installer `CommandSet.ini` to that path
before every launch. Live THAAD menus work because `S400ECommandSet*`
are inside that file (packed `CommandSet.ini` around the `S400ECommandSet`
block). SPECTER unique `CommandSet_*.ini` files are not the ControlBar
winner: `Japan_AirfieldCommandSet` is in packed `CommandSet.ini`, and
`CommandSet_Japan.ini` is not packed.

Release 748 therefore shipped:

| Path | `USAPAC3CommandSet*` |
|---|---|
| installer / loose `CommandSet.ini` | missing |
| packed `Data\INI\CommandSet.ini` | missing |
| packed `Data\INI\CommandSet_USAPAC3.ini` | present, not on the ControlBar path |

`Object USAPAC3` still named `USAPAC3CommandSet`. At parse time that
lookup is NULL if the set is absent from the first-win file, so the
unit command bar is empty. The CommandButtons themselves (`Command_ADS_MTS_SWITCH`,
`Command_AADS_AA_Mode`, `Command_AADS_ABM_Mode`, `Command_ADSCombatMode`,
`Command_ADS_ABM_CombatMode`, `Command_FireControlPack`, `Command_Stop`,
`Command_ConstructUSAPAC3`) were already defined in `CommandButton.ini`
and were not the failure.

CommandSetUpgrade was not replacing the initial set incorrectly. Load
order / duplicate `CommandSet` names were not wiping a working bar;
the names were never on the live file. Installer and packed
`CommandSet.ini` were byte-identical to each other, and both lacked
the PAC-3 sets.

## Fix

Append the four unique PAC-3 CommandSets to live `CommandSet.ini`
(packed DATA, installer, merged, overlay). Remove
`Data\INI\CommandSet_USAPAC3.ini` from packed DATA so the same names
cannot be defined twice if a unique `CommandSet_*.ini` is ever parsed.
Keep `patch/Data/INI/CommandSet_USAPAC3.ini` and the independent source
copy as archive. Keep `ObjectCreationList_USAPAC3.ini` packed.

The 748 `CommandSet.ini` is a byte prefix of the new file
(SHA-256 `f6d9616febbf4eeb2720f6029a7089e7ce1f3d31a576d4f097c738348be9d223`
for the first 450860 bytes). `S400ECommandSet*` blocks are unchanged.

Initial menu is still:

1. `Command_ADS_MTS_SWITCH` (disabled; no `TriggeredBy = Upgrade_AIM-120C`)
3. `Command_AADS_AA_Mode`
5. `Command_AADS_ABM_Mode`
14. `Command_Stop`

AA then shows Deploy (`Command_ADSCombatMode`). ABM then shows Deploy
(`Command_ADS_ABM_CombatMode`). CombatMode shows Pack
(`Command_FireControlPack`).

## Protected hashes (unchanged)

| File | SHA-256 |
|---|---|
| `US_M1120.ini` | `b56d62cdb44d0d3e582df51aeee56fcb25a447397983e8ced5788a4520dae92f` |
| `Weapon.ini` | `a8eb8340aecd1bd04147e97b4b5ce218f91233464178c34c66ff2cc003c5d6b8` |
| `CommandButton.ini` | `1870f1118e20e64b9f4186c49dd561884296ddda9fb7b2caa90bd9f26e8eb65c` |
| `ObjectCreationList.ini` | `e284d55c2b96fcb8c6aa585d155ba94b9f6fbbe1810f30cde96e3ef6bc16cff5` |
| `ObjectCreationList_ZZZZ_ZZGmAdAbm.ini` | `ee88eb90ee1ac12d1127daaf19529f1477b21987582f1102ffbb2a60b3ad79ad` |
| `_SPEC_ART_TWO.big` | `2a65d89d60db9696a2b3a69df5a1c7cb173e10de027e7be6aedb6ba3cb47ae38` |

## Output SHA-256

| Artifact | SHA-256 | Bytes |
|---|---|---|
| `_SPEC_DATA_ONE.big` | `a8a4eb2f31976a9aacc1b9a716de876b349a69a9bce8859daae301c454a4f7a8` | 374101634 |
| `CommandSet.ini` | `87af44ffbbf33cf6fb1a7c1b15c0fcce52b6826891ae40e736cad669453d6404` | 451529 |
| `_SPEC_ART_TWO.big` (unchanged, not in ZIP) | `2a65d89d60db9696a2b3a69df5a1c7cb173e10de027e7be6aedb6ba3cb47ae38` | 308844919 |

ZIP hash: `docs/specter-usapac3/csfix/SHA256SUMS.txt` after the archive is built.

Packed DATA entries: 3584 (was 3585; removed `CommandSet_USAPAC3.ini`).

## Static validation

`python3 docs/specter-usapac3/csfix/validate_csfix.py` → `STATIC_OK`

INGAME_ZH: not executed.
