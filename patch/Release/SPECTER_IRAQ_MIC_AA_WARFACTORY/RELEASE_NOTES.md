# Iraq M.I.C. replaced by Arabic Alliance War Factory

Iraq dozer (`Iraq_VT72BCommandSet`) and worker (`Iraq_WorkerCommandSet`)
slot 6 now use `Command_ConstructArabicArmy_WarFactory`
(`Object = ArabicArmy_WarFactory`, model `Arb_warfactory`,
button `arb_warfactory`).

`ArabicArmy_WarFactory` Prerequisites now accept `GLASupplyStash` **or**
`Iraq_SupplyCenter`. Arabic Alliance worker construction is unchanged.
`Iraq_MIC` remains in DATA but is no longer on Iraq build menus.

ART_ONE and ART_TWO are byte-identical to PR #658.
RUNTIME_TEST=NOT RUN
