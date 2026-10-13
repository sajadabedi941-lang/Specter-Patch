# Iraq M.I.C. live-catalog menu fix

PR #664 wrote the 14 radar/AD copies only into ZZZZ sidecar INIs.
The live `CommandSet.ini` catalog still showed the old Iraqi MIC
menu. This release writes slots 1-14 + Sell 15 into CommandSet.ini
and the UNIT_BUILD buttons into CommandButton.ini.

War Factory T3 live catalog now also carries B340 / Karrar-2 /
Fahad-3 so they are not lost when removed from the MIC catalog.

ART_ONE and ART_TWO are byte-identical to PR #664.
RUNTIME_TEST=NOT RUN
