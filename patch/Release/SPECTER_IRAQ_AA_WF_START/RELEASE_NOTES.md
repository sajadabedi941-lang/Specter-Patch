# Iraq Arabic Alliance War Factory available at match start

Iraq dozer/worker slot 6 still uses `Command_ConstructArabicArmy_WarFactory`
(`Object = ArabicArmy_WarFactory`).

`ArabicArmy_WarFactory` Prerequisites are now `GLASupplyStash` **or**
`Iraq_CommandCenter`. FactionIraq starts with `Iraq_CommandCenter`, so
the replacement is constructible immediately. Arabic Alliance still
requires `GLASupplyStash`.

ART_ONE and ART_TWO are byte-identical to PR #659.
RUNTIME_TEST=NOT RUN
