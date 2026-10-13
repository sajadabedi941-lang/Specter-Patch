# Israel missile factory replaces Clear Mines

Replaces Israel's remaining Clear Mines construction option
(`AirF_AmericaDozerCommandSet` slot 14) with the existing
`Command_ConstructIsrael_MissileFactory` button.

Israel's starting dozer (`IsraelDozerCommandSet`) already had the
missile factory at slot 14 and Global Store at slot 2; those slots
are unchanged. The factory object, A-J roster, Fire commands, and
artwork are reused. Other countries keep Clear Mines.

ART is byte-identical to PR #670. RUNTIME_TEST=NOT RUN
