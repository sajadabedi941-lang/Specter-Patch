# USAPAC3 unlocked without Rank 3

Zero Hour was not run.

## Cause

`Object USAPAC3` already matched overlay `America_AD_THAAD`:

```
  Prerequisites
    Science = SCIENCE_Rank3
  End
```

after WeaponSet, before ArmorSet/BuildCost. `America_AD_THAAD` is **not**
in live DATA, so that Object gate was never the live CC path.

Live `Command_ConstructUSAPAC3` (only in `CommandButton.ini`) was:

```
Command = UNIT_BUILD
Object  = USAPAC3
```

No `Science` field. ControlBar enables UNIT_BUILD from the CommandButton.
Object Prerequisites Science is not what disables this CC button.

Working rank-gate in this Specter CommandButton.ini is `Science = SCIENCE_Rank3`
on the button (see `Command_US_Tier3`). Overlay UNIT_BUILD buttons use the
same field (`Command_ConstructChinaDroneFH97`).

One CommandButton definition. CommandSet.ini slot 6 unchanged.

## Fix

Added only:

```
  Science            = SCIENCE_Rank3
```

to `Command_ConstructUSAPAC3`. Object stats, slot 6, THAAD/Patriot/NASAMS
untouched.
