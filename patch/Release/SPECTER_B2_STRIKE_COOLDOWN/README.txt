SPECTER_B2_STRIKE_COOLDOWN
=========================

Purpose
-------
Timed recharge for AmericaJetB2 bunker-buster strike ability.

Behavior
--------
- After the full payload is spent (ClipSize 6), strike is disabled
- Automatically reactivates after 5 minutes (ClipReloadTime 300000 ms)
- No money cost
- No return-to-base / manual reload (AutoReloadsClip = Yes)
- OutOfAmmoDamagePerSecond = 0% so the aircraft survives the wait

Unchanged
---------
- Draw / AVB3bmbr / Scale 0.85 / Attachments
- Airfield / Production
- Locomotor / takeoff-idle flight fields (except ammo survival)
- Weapon damage / range / projectile identity
