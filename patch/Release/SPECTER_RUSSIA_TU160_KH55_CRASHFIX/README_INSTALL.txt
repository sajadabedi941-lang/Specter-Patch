SPECTER Russia TU-160 KH55 crash fix

Install: replace _SPEC_ART_ONE.big and _SPEC_DATA_ONE.big

Removed custom Russia_TU160_KH55MS_Projectile (INI parse crash).
TU-160 weapon now uses original TEOD Object KH55MS.
Requires !TEOD_INI.big in load order (provides Object KH55MS).

First test: Russia -> start match.
Do not assume combat PASS.
