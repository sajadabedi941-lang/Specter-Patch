# Global 5-minute missile cooldown + warhead damage scale

- Native SAGE reload: `ClipSize=1`, `AutoReloadsClip=Yes`, `ClipReloadTime=300000` on produceable SPECTER missile weapons. Clock starts after the shot.
- Damage formula vs 9P117 400 kg / PrimaryDamage 2000: `PD = 2000 * (kg/400)`, splash `SD = 100 * (kg/400)`.
- Al-Fahd 1600 kg was 4000 in Weapon.ini; now 8000. Iraq B–J splash scaled. Vietnam A–H already matched. Mother 2000/100 not changed.
- Death HACK extras are not added into the AP total (avoids double-count).
- Shared Grad weapons and vanilla GLA Scud guns were not changed.
- Static validation only. The game was not launched.
