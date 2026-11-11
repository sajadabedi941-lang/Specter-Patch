# SS1 compatibility engine audit

- Generated: 2026-11-11 16:29 Asia/Tehran
- Mode: `ss1-compat-infra`
- Original SPECTER BIGs modified: **False**
- Original hashes unchanged: **True**
- Equipment imported: **False**
- Loose INI written: **False**
- Generals.exe run: **False**

## SPECTER FINAL (SS1) hashes (read-only)

- `_SPEC_DATA_ONE.big`: `7f8c7f63e972652e8d178c2a43b1f0102904096d630538b010dbf2d081881343`
- `_SPEC_ART_TWO.big`: `81d9a4aa10550ef8b3f4a58842f159fda3f54a1af32fcef37df185eb9b9995bf`

## SS1 load topology (from live DATA BIG)

- Data\INI root files: **192**
- Object recursive: **True**
- Weapon\ recursive: **False**
- Weapon\ nested subdir files: **0**
- MappedImages subdirs: `{'HandCreated': 35, 'TextureSize_512': 4}`

Proven extra root prefixes:

- `CommandButton_*`
- `CommandSet_*`
- `Weapon_*`
- `Object_*`
- `ObjectCreationList_*`
- `Science_*`
- `SpecialPower_*`
- `Upgrade_*`
- `PlayerTemplate_*`
- `ControlBarScheme_*`

Unproven extra root kinds (root `loadDirectory` should still parse first-token blocks):

- `Armor_*`
- `FXList_*`
- `DamageFX_*`
- `Crate_*`
- `Locomotor_*`
- `ParticleSystem_*`
- `SoundEffects_*`

## Emit paths (SS1-safe)

- Objects: `Data\INI\Object\SilentDeath\{Side}\{Name}.ini` (recursive, proven)
- Weapons: `Data\INI\Weapon_SilentDeath.ini` (root extra, proven). **Never** `Weapon\SilentDeath\`
- MappedImages: `Data\INI\MappedImages\HandCreated\SilentDeathMappedImages.ini`
- CommandSet overlay: `Data\INI\CommandSet_ZZZZ_SilentDeath_{Side}.ini`

## Catalog (entire V25 Object table)

- Objects: **6207**
- Ready for safe transfer: **4027**
- unique_import_ready: **4027**
- needs_fix: **564**
- needs_rebuild: **689**
- blocked: **218**
- rename_or_reuse: **709**

## Stage 5 crash classes now gated by preflight

- Nested `Weapon\SilentDeath\` unloadable
- Nested `MappedImages\SilentDeath\` unloadable
- Missing `DeathWeapon` / `IgnitionFX` parse-fatal
- Locomotor uncommented `GroupMovementPriority` tail
- FXList missing column-0 `End`
- Tokens after Object `End` (HQ11 DEPLOYED draw)
- Duplicate named Armor/Weapon/FXList
- Object file existence is not readiness

- Preflight rejects nested Weapon: **True**
- Preflight rejects MappedImages\SilentDeath: **True**

## What this engine still is not

- Not a Generals.exe boot test
- Not an install pack and not a bulk transfer
- Unproven root kinds (Armor_/Locomotor_/FXList_ extras) are warnings, not proof they load
- ART/W3D integrity is not a parse-fatal INI check

Do not start grouped equipment transfer until ready_for_safe_transfer rows are packed
only after preflight on the actual added payloads.

