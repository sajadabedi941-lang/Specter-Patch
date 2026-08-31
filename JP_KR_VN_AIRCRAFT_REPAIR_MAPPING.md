# Japan / South Korea / Vietnam aircraft repair mapping

Unique W3D meshes only. Donor ART from New folder (TEOD) and existing `_SPEC_ART_ONE` where already in-game.
USA / Russia / China files were not modified. Packaging scripts were not modified.

| Country | Object name | Old W3D | New W3D | Donor source | Weapon | CommandButton | CommandSet (unit) | Airfield CommandSet |
|---|---|---|---|---|---|---|---|---|
| Japan | `Japan_F15JKai` | `NAT_EF2000T4` | `AVF-15` | New folder / TEOD AVF-15 | `Japan_Weapon_AAM_Medium` | `Command_ConstructJapan_F15JKai` | `GenericMultiRoleFighterCommandSet` | `Japan_AirfieldCommandSet` |
| Japan | `Japan_F2A` | `US_F16D_B52` | `AVF16` | New folder / TEOD AVF16 (F-2 analog, not US_F16 SPEC mesh) | `Japan_Weapon_ATGM` | `Command_ConstructJapan_F2A` | `GenericTacticalBomberCommandSet` | `Japan_AirfieldCommandSet` |
| Japan | `Japan_F35A` | `US_F35A` | `AVF-35` | New folder / TEOD AVF-35 | `Japan_Weapon_AAM4B_F35J` | `Command_ConstructJapan_F35A` | `GenericMultiRoleFighter_AG_CommandSet` | `Japan_AirfieldCommandSet` |
| Japan | `Japan_F35B` | `NAT_EF2000T4` | `AVF-35_NFZ` | New folder / TEOD AVF-35_NFZ | `Japan_Weapon_AAM4B_F35J` | `Command_ConstructJapan_F35B` | `GenericMultiRoleFighter_AG_CommandSet` | `Japan_AirfieldCommandSet` |
| Japan | `Japan_X2Shinshin` | `(none)` | `RUSU-47` | New folder / TEOD RUSU-47 (experimental stand-in for X-2) | `Japan_Weapon_AAM_Medium` | `Command_ConstructJapan_X2Shinshin` | `GenericMultiRoleFighterCommandSet` | `Japan_AirfieldCommandSet` |
| Japan | `Japan_F3GCAP` | `(none)` | `AVRaptor` | New folder / TEOD AVRaptor | `Japan_Weapon_AAM4B_F35J` | `Command_ConstructJapan_F3GCAP` | `GenericMultiRoleFighter_AA_CommandSet` | `Japan_AirfieldCommandSet` |
| SouthKorea | `SouthKorea_F15K` | `Arb_F15SA` | `Arb_F15SA` | _SPEC_ART_ONE Arb_F15SA (kept, unique vs Japan TEOD AVF-15) | `GBU_31V2_JDAM_F15SA` | `Command_ConstructSouthKorea_F15K` | `GenericTacticalBomberCommandSet` | `SouthKorea_AirfieldCommandSet` |
| SouthKorea | `SouthKorea_F16C` | `NAT_EF2000T4` | `US_F16CMB50` | _SPEC_ART_ONE US_F16CMB50 | `SouthKorea_Weapon_AAM_Medium` | `Command_ConstructSouthKorea_F16C` | `GenericMultiRoleFighterCommandSet` | `SouthKorea_AirfieldCommandSet` |
| SouthKorea | `SouthKorea_KF16` | `US_F16D_B52` | `US_F16D_B52` | _SPEC_ART_ONE US_F16D_B52 (two-seat KF-16, distinct from F-16C mesh) | `SouthKorea_Weapon_ATGM` | `Command_ConstructSouthKorea_KF16` | `GenericTacticalBomberCommandSet` | `SouthKorea_AirfieldCommandSet` |
| SouthKorea | `SouthKorea_F35A` | `US_F35A` | `US_F35A` | _SPEC_ART_ONE US_F35A (Japan uses TEOD AVF-35 instead) | `SouthKorea_Weapon_AAM_Medium` | `Command_ConstructSouthKorea_F35A` | `GenericMultiRoleFighter_AG_CommandSet` | `SouthKorea_AirfieldCommandSet` |
| SouthKorea | `SouthKorea_KF21` | `NAT_EF2000T4` | `AVStealth` | New folder / TEOD AVStealth (unique KF-21 mesh) | `SouthKorea_Weapon_AAM_Medium` | `Command_ConstructSouthKorea_KF21` | `GenericMultiRoleFighter_AG_CommandSet` | `SouthKorea_AirfieldCommandSet` |
| SouthKorea | `SouthKorea_FA50` | `(none)` | `AVF-18` | New folder / TEOD AVF-18 (twin-tail, not F-16) | `SouthKorea_Weapon_ATGM` | `Command_ConstructSouthKorea_FA50` | `GenericTacticalBomberCommandSet` | `SouthKorea_AirfieldCommandSet` |
| SouthKorea | `SouthKorea_T50` | `(none)` | `AVGHawk` | New folder / TEOD AVGHawk (trainer silhouette, not F-16) | `SouthKorea_Weapon_AAM_Short` | `Command_ConstructSouthKorea_T50` | `GenericMultiRoleFighterCommandSet` | `SouthKorea_AirfieldCommandSet` |
| Vietnam | `Vietnam_Su30MK2` | `Irq_Mig29A` | `SU-37` | New folder / TEOD SU-37 | `Vietnam_Weapon_AAM_Medium` | `Command_ConstructVietnam_Su30MK2` | `GenericMultiRoleFighterCommandSet` | `Vietnam_AirfieldCommandSet` |
| Vietnam | `Vietnam_Su27SK` | `Irq_MirageF1_Bq` | `Arb_SU35` | _SPEC_ART_ONE Arb_SU35 (Flanker, distinct from TEOD SU-37) | `Vietnam_Weapon_AAM_Medium` | `Command_ConstructVietnam_Su27SK` | `GenericMultiRoleFighterCommandSet` | `Vietnam_AirfieldCommandSet` |
| Vietnam | `Vietnam_Su30MK2V` | `Irq_Su25k` | `RUSU-34` | New folder / TEOD RUSU-34 (two-seat Flanker family) | `Vietnam_Weapon_ATGM` | `Command_ConstructVietnam_Su30MK2V` | `GenericTacticalBomberCommandSet` | `Vietnam_AirfieldCommandSet` |
| Vietnam | `Vietnam_Mig21bis` | `(none)` | `UVMig-21` | New folder / TEOD UVMig-21 | `Vietnam_Weapon_AAM_Short` | `Command_ConstructVietnam_Mig21bis` | `GenericMultiRoleFighterCommandSet` | `Vietnam_AirfieldCommandSet` |
| Vietnam | `Vietnam_Mig21MF` | `(none)` | `UVMig21_SP` | New folder / TEOD UVMig21_SP (distinct MiG-21 mesh vs UVMig-21) | `Vietnam_Weapon_AAM_Short` | `Command_ConstructVietnam_Mig21MF` | `GenericMultiRoleFighterCommandSet` | `Vietnam_AirfieldCommandSet` |
| Vietnam | `Vietnam_Su22M3` | `(none on VN)` | `Irq_SU22M3` | _SPEC_ART_ONE Irq_SU22M3 | `5x_Fab500_SU22M3_CenterRack` | `Command_ConstructVietnam_Su22M3` | `GenericTacticalBomberCommandSet` | `Vietnam_AirfieldCommandSet` |
| Vietnam | `Vietnam_Su22M4` | `(none)` | `Irn_SU22M2` | _SPEC_ART_ONE Irn_SU22M2 (distinct swing-wing vs Irq_SU22M3) | `Vietnam_Weapon_ATGM` | `Command_ConstructVietnam_Su22M4` | `GenericTacticalBomberCommandSet` | `Vietnam_AirfieldCommandSet` |
| Vietnam | `Vietnam_Yak130` | `(none)` | `RUMIG_35` | New folder / TEOD RUMIG_35 (twin-engine stand-in; no Yak-130 W3D in approved donors) | `Vietnam_Weapon_AAM_Short` | `Command_ConstructVietnam_Yak130` | `GenericMultiRoleFighterCommandSet` | `Vietnam_AirfieldCommandSet` |
| Vietnam | `Vietnam_L39` | `(none)` | `RUSU75` | New folder / TEOD RUSU75 (single-engine light-jet stand-in; no L-39 W3D in approved donors) | `Vietnam_Weapon_AAM_Short` | `Command_ConstructVietnam_L39` | `GenericMultiRoleFighterCommandSet` | `Vietnam_AirfieldCommandSet` |
| Vietnam | `Vietnam_F5E` | `(none)` | `NVJ31` | New folder / TEOD NVJ31 (unique twin-engine stand-in; no F-5E W3D in approved donors) | `Vietnam_Weapon_AAM_Short` | `Command_ConstructVietnam_F5E` | `GenericMultiRoleFighterCommandSet` | `Vietnam_AirfieldCommandSet` |

## Notes

- Japan no longer uses `NAT_EF2000T4` or `US_F16D_B52`.
- Japan F-35A/B unlock with `SCIENCE_Japan_StealthJet` (national menu), not `SCIENCE_NatoStealthJet`.
- South Korea F-35A unlocks with `SCIENCE_SouthKorea_StealthJet`.
- FA-50 uses TEOD Hornet-class `AVF-18`; T-50 uses TEOD trainer `AVGHawk` — neither is an F-16 mesh.
- KF-21 uses TEOD `AVStealth`, not shared with Japan.
- Vietnam Mirage F1 and Su-25 are unwired from all airfield CommandSets.
- Approved donors have no dedicated Yak-130, L-39, or F-5E W3D; those three use unique TEOD stand-ins listed above.
- Old clone objects (`Japan_JetEF2000T4`, `Vietnam_MirageF1_Bq`, etc.) remain defined but are not on airfield CommandSets.

## INI validation (this repair)

Scoped to the new/rewired JP / KR / VN aircraft (full-tree duplicate Object/CommandButton noise from pre-existing USA B-2 overlays was not introduced here).

- Missing Object: none of the 23 roster objects
- Missing Weapon: none (`Japan_Weapon_*`, `SouthKorea_Weapon_*`, `Vietnam_Weapon_*`, `GBU_31V2_JDAM_F15SA`, Su-22 FAB/S-8 templates all resolve)
- Duplicate CommandButton among new IDs: none
- Duplicate CommandSet among airfield sets: none (`Japan_AirfieldCommandSet`, `SouthKorea_AirfieldCommandSet`, `Vietnam_AirfieldCommandSet` 1/2/3)
- Shared W3D among JP/KR/VN roster: none (23 distinct Model names)
- Eurofighter / US F-16 Japan clones and VN Mirage F1 / Su-25: unwired from airfields
- Overlay TEOD W3D present under `patch/Art/W3D` for every imported mesh
- Global `apply_country_balance.py` was **not** left applied to USA/Russia/China (reverted); JP/KR/VN costs use existing country multipliers only on the new files


