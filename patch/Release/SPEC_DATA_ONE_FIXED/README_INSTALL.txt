SPEC DATA ONE FIXED
===================

File: _SPEC_DATA_ONE_FIXED.big
SHA256: c15b5d58ee2b764e611faa19f09beae022b8ecc9732eb5497c1ef020f365e0fd
Egypt_CommandCenter.ini SHA256: 81dd3fcd672bf68d3d7a965e1d8b30195301b7ac198582fc8d28bbc5d963e00c
Validation: PASS

This is a COMPLETE replacement for vendor _SPEC_DATA_ONE.big.
It is NOT an overlay.

What changed:
  ONLY Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_CommandCenter.ini
  (broken Iraq-donor → USA AmericaCommandCenter donor, Side=Egypt)

INSTALL (mandatory):
1. Backup Data\_SPEC_DATA_ONE.big
2. Copy _SPEC_DATA_ONE_FIXED.big → Data\_SPEC_DATA_ONE.big
   (overwrite using the SPEC Data filename)
3. Keep Data\_SPEC_ART_ONE.big
4. DELETE every Specter overlay BIG (_SPECTER_*.big, old patch BIGs)
5. Do not leave the original broken vendor SPEC Data BIG installed

Inside this BIG: Egypt_CommandCenter copies = 1 only.
