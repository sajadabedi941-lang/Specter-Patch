SPECTER PR #206 UAE_CommandCenter AmericaCommandCenter donor fix
================================================================

Fixes startup crash on UAE_CommandCenter.ini by aligning special-power
modules to the working AmericaCommandCenter donor (same method as UAE_MilitaryHQ).

Preserved:
- Object UAE_CommandCenter
- Side=UAE
- CommandSet=UAE_CommandCenterCommandSet
- BuildCost/BuildTime/HP/geometry

Install:
1. Backup Data\_SPEC_DATA_ONE.big
2. Replace with this package BIG
3. Keep _SPEC_ART_ONE.big unchanged
