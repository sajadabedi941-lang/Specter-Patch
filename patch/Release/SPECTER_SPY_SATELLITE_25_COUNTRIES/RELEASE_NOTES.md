# SPECTER Spy Satellite — real $5,000 activation cost

Original targeted Spy Satellite remains on all 25 country radars.
ReloadTime stays 60000 ms.

Engine-compatible cost path (not a tooltip-only value):
1. `Command_SpecterSpySatelliteFee` = `OBJECT_UPGRADE` of
   `Upgrade_SpecterSpySatelliteScan` (`BuildCost = 5000`, `BuildTime = 0`).
   SAGE withdraws $5,000 through ProductionUpdate. Less than $5,000
   cannot purchase the upgrade.
2. `Command_SpySatelliteScan` stays `SPECIAL_POWER` + `NEED_TARGET_POS`
   + `RadiusCursorType = SPYSATELLITE`, now gated with `NEED_UPGRADE`.
3. A successful scan still creates `SpySatellitePing` via
   `SUPERWEAPON_SpySatellite`, and also creates `SpecterSpySatelliteFeeStrip`
   whose `UpgradeDie` removes the object upgrade so the next scan is paid again.

Trade-off: SAGE has no native money field on SPECIAL_POWER, so the player
authorizes ($5,000) then targets. Targeting, reveal, and 60s cooldown are unchanged.

ART_ONE and ART_TWO are byte-identical to PR #656.
RUNTIME_TEST=NOT RUN
