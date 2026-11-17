# SS1 INI load topology (from live `_SPEC_DATA_ONE.big`)

- Source: `/tmp/ss1/SPECTER FINAL (GeneralsMode.com)/_SPEC_DATA_ONE.big`
- DATA members: **3587**
- Data\INI root files: **192**

## First-level Data\INI directories

- `Default/` 25
- `MappedImages/` 39
- `Object/` 2786
- `Weapon/` 26

## Object

- Recursive: **True** (SS1 ships Object\Specter\<faction>\... nested INI that must load.)
- Files: 2786

## Weapon directory

- Recursive: **False**
- Nested subdir files: **0**
- SS1 Data\INI\Weapon\ holds only flat Weapon_*.ini. Extra weapons also live at Data\INI\Weapon_*.ini. No Weapon\<subdir>\ members exist.

## MappedImages

- Subdirs: `{'HandCreated': 35, 'TextureSize_512': 4}`
- Loaded: ['HandCreated', 'TextureSize_512']
- SS1 only contains HandCreated and TextureSize_512 under MappedImages.

## Proven extra root prefixes

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

## Proven root kinds (stock table + extra root loader)

- Extra root INI: **157**
- `Armor`: stock `Armor.ini` is at Data\INI root with 157 extra root INI (including Weapon_/CommandSet_ extras). Same loadDirectory; kind is first-token.
- `Locomotor`: stock `Locomotor.ini` is at Data\INI root with 157 extra root INI (including Weapon_/CommandSet_ extras). Same loadDirectory; kind is first-token.
- `FXList`: stock `FXList.ini` is at Data\INI root with 157 extra root INI (including Weapon_/CommandSet_ extras). Same loadDirectory; kind is first-token.
- `DamageFX`: stock `DamageFX.ini` is at Data\INI root with 157 extra root INI (including Weapon_/CommandSet_ extras). Same loadDirectory; kind is first-token.
- `CrateData`: stock `Crate.ini` is at Data\INI root with 157 extra root INI (including Weapon_/CommandSet_ extras). Same loadDirectory; kind is first-token.
- `CrateTemplate`: stock `Crate.ini` is at Data\INI root with 157 extra root INI (including Weapon_/CommandSet_ extras). Same loadDirectory; kind is first-token.
- `ParticleSystem`: stock `ParticleSystem.ini` is at Data\INI root with 157 extra root INI (including Weapon_/CommandSet_ extras). Same loadDirectory; kind is first-token.
- `AudioEvent`: stock `SoundEffects.ini` is at Data\INI root with 157 extra root INI (including Weapon_/CommandSet_ extras). Same loadDirectory; kind is first-token.
- `Weapon`: stock `Weapon.ini` is at Data\INI root with 157 extra root INI (including Weapon_/CommandSet_ extras). Same loadDirectory; kind is first-token.
- `CommandSet`: stock `CommandSet.ini` is at Data\INI root with 157 extra root INI (including Weapon_/CommandSet_ extras). Same loadDirectory; kind is first-token.
- `CommandButton`: stock `CommandButton.ini` is at Data\INI root with 157 extra root INI (including Weapon_/CommandSet_ extras). Same loadDirectory; kind is first-token.
- `ObjectCreationList`: stock `ObjectCreationList.ini` is at Data\INI root with 157 extra root INI (including Weapon_/CommandSet_ extras). Same loadDirectory; kind is first-token.
- `SpecialPower`: stock `SpecialPower.ini` is at Data\INI root with 157 extra root INI (including Weapon_/CommandSet_ extras). Same loadDirectory; kind is first-token.
- `Upgrade`: stock `Upgrade.ini` is at Data\INI root with 157 extra root INI (including Weapon_/CommandSet_ extras). Same loadDirectory; kind is first-token.
- `Science`: stock `Science.ini` is at Data\INI root with 157 extra root INI (including Weapon_/CommandSet_ extras). Same loadDirectory; kind is first-token.

## Emit paths (SS1-safe)

- Object: `Data\INI\Object\SilentDeath\{Side}\{Name}.ini`
- Weapon: `Data\INI\Weapon_SilentDeath.ini`
- Armor: `Data\INI\Armor_SilentDeath.ini`
- Locomotor: `Data\INI\Locomotor_SilentDeath.ini`
- FXList: `Data\INI\FXList_SilentDeath.ini`
- DamageFX: `Data\INI\DamageFX_SilentDeath.ini`
- CrateData: `Data\INI\Crate_SilentDeath.ini`
- CrateTemplate: `Data\INI\Crate_SilentDeath.ini`
- ObjectCreationList: `Data\INI\ObjectCreationList_SilentDeath.ini`
- ParticleSystem: `Data\INI\ParticleSystem_SilentDeath.ini`
- AudioEvent: `Data\INI\SoundEffects_SilentDeath.ini`
- CommandButton: `Data\INI\CommandButton_SilentDeath.ini`
- CommandSet: `Data\INI\CommandSet_ZZZZ_SilentDeath_{Side}.ini`
- MappedImage: `Data\INI\MappedImages\HandCreated\SilentDeathMappedImages.ini`

Weapons go to **root** `Weapon_SilentDeath.ini`, not `Weapon\SilentDeath\`.
MappedImages go to **HandCreated**, not a new SilentDeath folder.

