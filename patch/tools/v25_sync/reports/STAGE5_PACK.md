# Stage 5 — experimental DATA+ART BIG pack (ChinaCSSA1, ChinaHQ11)

- Generated: 2026-11-11 14:47 Asia/Tehran
- Original SPECTER BIGs unchanged: **True**
- Loose INI written: **False**
- Generals.exe run: **False**

## China build location (extracted from SPECTER Objects, not guessed)

- Building Object: `ChinaWarFactory`
- CommandSet: `PLAWarFactoryCommandSet`
- Source: `_SPEC_DATA_ONE.big:Data\INI\Object\Specter\PLA\Buildings\Warfactory.ini`
- ChinaCSSA1 UNIT_BUILD slot: `4`
- ChinaHQ11 UNIT_BUILD slot: `7`
- SPECTER ChinaWarFactory uses PLAWarFactoryCommandSet, not ChinaWarFactoryCommandSet. ChinaSupplyCenter only builds the supply truck. Dozer places buildings (HQ-9 site), not this TEL.

## Experimental BIGs

- `/tmp/v25_stage5_pack/_SPEC_DATA_ONE.big` SHA256 `2198049d286f7295f9bdd8abfd7cc3f251a105e976672d718370de75112e34c2`
- `/tmp/v25_stage5_pack/_SPEC_ART_TWO.big` SHA256 `bce126e0943ca771bcf5a13cf222c5a41a590b10b244ea6812d2a770a62dacd5`
- Original DATA `7f8c7f63e972652e8d178c2a43b1f0102904096d630538b010dbf2d081881343`
- Original ART TWO `81d9a4aa10550ef8b3f4a58842f159fda3f54a1af32fcef37df185eb9b9995bf`

## Capabilities kept

- ChinaCSSA1 UNIT_BUILD from ChinaWarFactory / PLAWarFactoryCommandSet slot 4
- ChinaHQ11 UNIT_BUILD from ChinaWarFactory / PLAWarFactoryCommandSet slot 7
- HQ11 pack/unpack via stock DeployStyleAIUpdate
- HQ11 fire only when deployed (WeaponSet Conditions = DEPLOYED + TurretsFunctionOnlyWhenDeployed)
- Original W3D/texture/animation filenames (not SD25-prefixed)
- Unique AudioEvent names; wav stems unchanged

## Limitations

- Runtime CommandSet swap (packed vs deployed labels) is not available on stock Generals.exe
- SET_SLUGGISH crawl-while-deployed is not bound; unit packs then moves on SET_NORMAL
- PackTime/UnpackTime = 2000 copied from V25 SDSR5, not measured CWC rider timing
- Shilka CWC voice wavs may be missing if they live only in WYS/Audio.big
- Projectile W3D stems `CWCgenExpTracer` and `CWCruS300_m` are not in the V25 zip or nested BIGs (exact stem only; no substitute)
- CWC Shilka / radio voice wavs are not in `WYS/Audio.big` or loose `Data/Audio/Sounds` (`LSF2C6gun` and `S400Triumf` fire sounds were recovered)
- Generals.exe was not run

## Install ZIP

- `SPECTER_V25_SD25_ChinaCSSA1_ChinaHQ11_experimental.zip` SHA256 `3e4d0e5ffdcff34e74a63e3ad936187912b2760442c67a82e8cd56942e805afb`
- Contents: complete `_SPEC_DATA_ONE.big`, complete `_SPEC_ART_TWO.big`, `INSTALL.txt`, `REVERT.txt`, `SHA256SUMS.txt`
- No loose INI. Rebuild locally with `python3 patch/tools/v25_sync/v25_sync.py pack-sample --out /tmp/v25_stage5_pack`

## Warnings

- ART not recovered (exact stem only): CWCgenExpTracer
- ART not recovered (exact stem only): CWCruS300_m
- audio wav not recovered: CWCgenRadioStart01
- audio wav not recovered: CWCgenRadioStart02
- audio wav not recovered: CWCgenRadioStart03
- audio wav not recovered: CWCgenRadioStart04
- audio wav not recovered: CWCgenRadioStart05
- audio wav not recovered: CWCgenRadioStart06
- audio wav not recovered: CWCruShilka_MA_sel_01
- audio wav not recovered: CWCruShilka_MA_sel_02
- audio wav not recovered: CWCruShilka_MA_sel_03
- audio wav not recovered: CWCruShilka_MA_sel_04
- audio wav not recovered: CWCgenRadioEnd01
- audio wav not recovered: CWCgenRadioEnd02
- audio wav not recovered: CWCgenRadioEnd03
- audio wav not recovered: CWCgenRadioEnd04
- audio wav not recovered: CWCgenRadioEnd05
- audio wav not recovered: CWCgenRadioEnd06
- audio wav not recovered: CWCruShilka_MA_mov_01
- audio wav not recovered: CWCruShilka_MA_mov_02
- audio wav not recovered: CWCruShilka_MA_mov_03
- audio wav not recovered: CWCruShilka_MA_mov_04
- audio wav not recovered: CWCruShilka_MA_gua_01
- audio wav not recovered: CWCruShilka_MA_gua_02
- audio wav not recovered: CWCruShilka_MA_gua_03
- audio wav not recovered: CWCruShilka_MA_gua_04
- audio wav not recovered: CWCruShilka_MA_gro_01
- audio wav not recovered: CWCruShilka_MA_gro_02
- audio wav not recovered: CWCruShilka_MA_gro_03
- audio wav not recovered: CWCruShilka_MA_gro_04
- audio wav not recovered: CWCruShilka_MA_int_01
- audio wav not recovered: CWCruShilka_MA_int_02
- audio wav not recovered: CWCruShilka_MA_int_03
- audio wav not recovered: CWCruShilka_MA_int_04
- audio wav not recovered: CWCruShilka_MA_cre_01
- audio wav not recovered: CWCruShilka_MA_cre_02
- audio wav not recovered: CWCruShilka_MA_cre_03
- audio wav not recovered: CWCruShilka_MA_cre_04

## Added DATA members

- `Data\Audio\Sounds\LSF2C6gun.wav`
- `Data\Audio\Sounds\S400Triumf.wav`
- `Data\INI\Armor_SilentDeath.ini`
- `Data\INI\CommandButton_SilentDeath.ini`
- `Data\INI\CommandSet_ZZZZ_SilentDeath_China.ini`
- `Data\INI\Crate_SilentDeath.ini`
- `Data\INI\DamageFX_SilentDeath.ini`
- `Data\INI\FXList_SilentDeath.ini`
- `Data\INI\Locomotor_SilentDeath.ini`
- `Data\INI\MappedImages\SilentDeath\SilentDeathMappedImages.ini`
- `Data\INI\Object\SilentDeath\China\SD25_ChinaCSSA1.ini`
- `Data\INI\Object\SilentDeath\China\SD25_ChinaHQ11.ini`
- `Data\INI\Object\SilentDeath\China\SD25_ChinaVehicleBattleMasterDeadHull.ini`
- `Data\INI\Object\SilentDeath\China\SD25_CWCgenExplosiveShell.ini`
- `Data\INI\Object\SilentDeath\China\SD25_CWCgenExplosiveShellAir.ini`
- `Data\INI\Object\SilentDeath\China\SD25_CWCgenTreesOnFire.ini`
- `Data\INI\Object\SilentDeath\China\SD25_CWCruS300Missile.ini`
- `Data\INI\ObjectCreationList_SilentDeath.ini`
- `Data\INI\ParticleSystem_SilentDeath.ini`
- `Data\INI\SoundEffects_SilentDeath.ini`
- `Data\INI\Weapon\SilentDeath\SD25_Weapons.ini`

## Added ART members

- `Art\Textures\CHCSSA1B.dds`
- `Art\Textures\CHCSSA1T.dds`
- `Art\Textures\CHHQ11B.dds`
- `Art\Textures\CHHQ11F.dds`
- `Art\Textures\CHHQ11G.dds`
- `Art\Textures\CHHQ11N.dds`
- `Art\Textures\CHHQ11R.dds`
- `Art\Textures\CHHQ11T.dds`
- `Art\Textures\CHHQ11TB.tga`
- `Art\Textures\CSSA1TB.tga`
- `Art\Textures\extiretrack.dds`
- `Art\Textures\Glass1.tga`
- `Art\Textures\nvbtmstr_d1.dds`
- `Art\Textures\pmbarrel01.dds`
- `Art\Textures\pmconsup01.dds`
- `Art\Textures\pmcrates04.dds`
- `Art\Textures\pmcrates04_l.dds`
- `Art\Textures\SDNSM04.dds`
- `Art\W3D\CHCSSA1.W3D`
- `Art\W3D\HQ11.W3D`
- `Art\W3D\HQ11RD.W3D`
- `Art\W3D\NVBtMstr_D1.W3D`
- `Art\W3D\PMJnkCrate.W3D`
