SPECTER USA Patriot PAC-3 — ballistic intercept damage fix
==========================================================

Baseline: tested pack specter-usa-patriot-new-donor-thaad-test
(ss1 New Donor Patriot + THAAD missiles). PAC-3 v1–v8 is not used.

Install
-------
1. Extract this ZIP into SPECTER FINAL (the folder with generals.exe).
2. Replace only:
     _SPEC_DATA_ONE.big
3. Do not replace _SPEC_ART_TWO.big or _SPEC_ART_ONE.big.
   Loose Data\INI is not in this ZIP.

What changed
------------
_SPEC_DATA_ONE.big — one entry:
  Data\INI\Object\Specter\PatchSystems\AirDefense\USAPAC3.ini

Patriot-local ABM weapon / projectile / CRUSH fuze so the interceptor
actually damages ballistic missiles. Stock THAADMissile_ABM,
THAAD_ABM_OBJECT, Object US_THAAD, Weapon.ini, CommandSet.ini, and
other countries are not edited. PRIMARY 8x_LRSAM_THAAD (aircraft) is
unchanged. New Donor Draw / DeployStyle / locomotor / CommandSet /
FIREPOINT bones are unchanged. No Deploy/Pack buttons.

How to use in game
------------------
1. America Command Center slot 6 builds Object USAPAC3 (already in ss1).
2. Attack aircraft: same AA intercept as the previous pack.
3. Attack a ballistic missile: Patriot still detects and fires; the
   interceptor must now apply CRUSH damage and kill the missile.

This pack does not write files under Data\.

In-game test
------------
Not run on this machine. Archive/hash/INI checks only.
