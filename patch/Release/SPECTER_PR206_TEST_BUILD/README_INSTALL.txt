SPECTER PR #206 TEST BUILD
==========================

Baseline: PR #206 Turkey WeaponObjects full rebuild BIG
Plus: current PR #206 branch Turkey Armed Forces INI fixes embedded.
Plus: UAE_MilitaryHQ AmericaCommandCenter donor remap (v2).

NOT included: PR #207 / #208 faction reset work.
No faction rebuild was performed for this package.

UAE_MilitaryHQ fix (v2):
- Object name unchanged: UAE_MilitaryHQ
- ASCII-only INI (removed UTF-8 Phase comments that can crash Generals parse)
- CommandSet = AmericaCommandCenterCommandSet (CommandSet.ini)
- SpecialPower/Behavior set mirrored from AmericaCommandCenter / Turkey_MilitaryHQ
- Removed FOAB / Tu22 / IraqiCruise leftover modules and oil AutoDeposit
- Draw: US_Command + US_COM_Strb (ART unchanged)

Install:
1. Backup your current Data\_SPEC_DATA_ONE.big
2. Replace Data\_SPEC_DATA_ONE.big with this package file
3. Keep Data\_SPEC_ART_ONE.big unchanged
4. Launch skirmish and smoke-test UAE Military HQ / Turkey worker path

After successful test: merge PR #206 and cut final release.
