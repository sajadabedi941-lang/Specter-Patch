# USAPAC3 appearance stage (PAC-3 TEL Draw)

Zero Hour was **not** run for this Draw attach. In-game proof that PAC-3
**buttons appear** belongs to Release `specter-usapac3-commandset-fix`
(#749), which still used THAAD `US_M1120` Draw. This stage only changes
how `Object USAPAC3` and `USAPAC3_CombatMode` look.

Gameplay, CommandSets, CommandButtons, OCLs, dummy weapons, FireControlSystem
modules, Deploy/Pack, Anti-Air / Anti-Missile, THAAD, Patriot, NASAMS,
ART ONE, failed-impl, and abtest were not rewritten. Previous GitHub
Releases were not deleted.

## Current object before this stage

Packed `Object USAPAC3` spawned with live THAAD Draw (`W3DTruckDraw`,
`US_M1120` / `_D` / `_A` / `_AD`). CommandSets were already on live
`CommandSet.ini`. FCS still uses shared `THAAD_FCS` (left unchanged:
FireControlSystem is out of scope).

## Archive W3D evidence (ZH-safe attach)

| File | Mesh ver | Bones | ANIMATION | Channels | Use |
|---|---|---:|---|---:|---|
| `UsaPac3Car.W3D` | 0x40002 | 53 incl. TIRE01–08, CORE, TURRET01, FIREPOINT01–04 | 101 frames | 2 real (Z on YYG08, PLANE01) | packed TEL |
| `UsaPac3Car_d.W3D` | 0x40002 | same | 101 frames | 2 real | damaged packed |
| `UsaPac3F.W3D` | 0x40002 | same | **none** (spawnfix3 already stripped) | 0 | deployed TEL |
| `UsaPac3F_d.W3D` | 0x40002 | same | **none** | 0 | damaged deployed |
| `UsaPac3Car_w.W3D` | 0x40002 | 3 (TIRE09/10) | 101 empty | 0 | **not used** |
| `pac3mis_m.W3D` | 0x40002 | 4 | empty 101-frame header | 0 | packed after strip; **not** wired to weapons |
| live `US_M1120.W3D` | 0x50000 | 30 | 151 frames | 7 real | THAAD, untouched |
| live `US_M1120_A.W3D` | 0x50000 | 30 | **none** | 0 | THAAD deployed |
| live `ABPatriot.W3D` | 0x40002 | 30 | none | 0 | proves 0x40002 is a live SPECTER mesh |

Textures referenced by the TEL W3Ds: `usaPAC3TRUCKmap.tga`, `ampac3map.tga`,
`ampac3mapBaCK.tga` (and `_d` variants). Archive supplies matching `.dds`
files. `pac3missilemap.dds` is packed for `pac3mis_m` only.

`UsaPac3Car_w` is a 3-bone axle fragment with an empty animation header.
Previous spawnfix already disproved attach-on-`_w` as the crash cause, and
there is no proven need to parent it to the truck. It stays in
`docs/specter-usapac3/archive/failed-impl/` only.

`UsaPac3F` backup copies still contain the empty 101-frame clip that
preloaded at object create and crashed construction. The **archive** F
files already match live deployed TELs: hierarchy + meshes + HLOD, no
ANIMATION chunk. Draw therefore names `Model = UsaPac3F` and does **not**
set `Animation =`.

## What changed

- `Object USAPAC3` Draw: `UsaPac3Car` packed / `UsaPac3F` deployed.
- `Object USAPAC3_CombatMode` Draw: `UsaPac3F` (deployed pose). Car’s two
  Z channels are not a full TEL unpack, so CombatMode does not freeze
  `UsaPac3Car` at last frame.
- ART TWO: **add** 11 unique PAC-3 W3D/texture entries. Existing THAAD /
  Patriot / `pac3_sudarb` / `ABNPatriot02` bytes are identical.
- `pac3mis_m.W3D` empty ANIMATION chunk stripped before packing. Weapons
  still fire `8x_LRSAM_THAAD` / `THAADMissile_ABM` (no weapon-art swap).

## What did not change

CommandSet.ini, CommandButton.ini, Weapon.ini, Weapon_USAPAC3.ini,
ObjectCreationList.ini, ObjectCreationList_USAPAC3.ini, US_M1120.ini,
FCS Draw (`THAAD_FCS`), ART ONE, `UsaPac3Car_w`, archive, abtest.

## Output SHA-256

| Artifact | SHA-256 | Bytes |
|---|---|---|
| `_SPEC_DATA_ONE.big` | `6a07d03bb1f45d9fa7a943274f105066be9fc60df93effabd193bbe4fc4185ff` | 374101196 |
| `_SPEC_ART_TWO.big` | `d9011cf80192f9b5ee8806de732ea1b02f55d9a7e6c1abcf09910dad3f65ee67` | 310396813 |

ZIP hash: `docs/specter-usapac3/draw/SHA256SUMS.txt` after the archive is built.

Protected (unchanged): `US_M1120.ini` `b56d62cd…`, `Weapon.ini` `a8eb8340…`,
`CommandSet.ini` `87af44ff…`, `CommandButton.ini` `1870f111…`,
`US_M1120.W3D` `44ddcc62…`, `ABPatriot.W3D` `ded239d0…`.

## Static validation

`python3 docs/specter-usapac3/draw/validate_draw.py` → `STATIC_OK`

INGAME_ZH: not executed for this Draw stage.
Button visibility in-game was reported on `specter-usapac3-commandset-fix` only.
