# Iraq M.I.C. constructible at match start

Iraq dozer/worker slot 6 still uses `Command_ConstructIraq_MIC`
(`Object = Iraq_MIC`, model `Irq_MIC`, `CommandSet = Iraq_MICCommandSet`).

The original three-building AND prerequisites (radar + airfield + war factory)
are removed. No upgrade, science, or tier gate remains on the construct button.
Arabic Alliance and all other Iraq construction slots are unchanged.

ART_ONE and ART_TWO are byte-identical to PR #658.
RUNTIME_TEST=NOT RUN
