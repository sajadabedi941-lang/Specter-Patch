# Vietnam missile A-H fire-button fix

- Root cause: Vietnam A-H weapons were only in a satellite Weapon file, so `Command_FireMainWeapon` (FIRE_WEAPON / PRIMARY) stayed inactive. Same class of bug as Al-Fahd before it was spliced into `Weapon.ini`.
- Satellite `SecondaryDamage = 62.5.0` / `87.5.0` (VCM-02 / Cửu Long) was also illegal.
- Fix: sanitize those floats and append the 16 weapon/warhead blocks to `Weapon.ini`.
- Factory menu, production buttons, 9P117, Iraq A-M, ART, names, colors, dorsal flags, range, damage, cost, and build time are unchanged.
- Static validation only. The game was not launched.
