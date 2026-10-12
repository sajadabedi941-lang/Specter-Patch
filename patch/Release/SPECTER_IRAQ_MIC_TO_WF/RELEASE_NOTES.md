# Iraq: move B_340Radar, karrar_2, fahad_3 from M.I.C. to War Factory

Removed from `Iraq_MICCommandSet` (and unused copies 2/3):
- `Command_ConstructIraqVehicleB340` (`IraqVehicleB340`, `irq_b340`)
- `Command_ConstructIraq_Karrar2` (`Iraq_Karrar2`, `irq_karrar`)
- `Command_ConstructIraqVehicleFahad3` (`IraqVehicleFahad3`, `irq_fahad3`)

Added to `Iraq_WarFactoryCommandSet_T3` slots 9 / 10 / 12.
Object definitions, buttons, and ART are unchanged.
`Iraq_Karrar2` still requires `Iraq_MIC` (existing object prerequisite).
M.I.C. remains constructible at match start (PR #661).

RUNTIME_TEST=NOT RUN
