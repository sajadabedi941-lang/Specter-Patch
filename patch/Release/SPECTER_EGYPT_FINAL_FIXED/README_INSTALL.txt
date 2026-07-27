SPECTER EGYPT FINAL FIXED
========================

File: _SPECTER_EGYPT_FINAL_FIXED.big
SHA256: c1d6dc12801dfa0b908bc060997797a1edf2690c9c3dbf19977f4d4362b317be
Egypt_CommandCenter.ini SHA256: 81dd3fcd672bf68d3d7a965e1d8b30195301b7ac198582fc8d28bbc5d963e00c
Validation: PASS

WHY THE LAST FIX FAILED
-----------------------
The broken Egypt_CommandCenter lives INSIDE vendor _SPEC_DATA_ONE.big
(sha 1b559b9e0d4eb140… irq_comndcntr / Iraq_Adnan1).

Dropping _SPECTER_* beside SPEC does NOT reliably replace that file.
You must REPLACE _SPEC_DATA_ONE.big.

INSTALL
-------
1. Backup your current Data\_SPEC_DATA_ONE.big
2. Copy _SPECTER_EGYPT_FINAL_FIXED.big → Data\_SPEC_DATA_ONE.big
   (same filename as SPEC Data — overwrite)
3. Keep Data\_SPEC_ART_ONE.big
4. DELETE every other Specter Data BIG (_SPECTER_*.big, old patch BIGs)
5. Do NOT leave the original vendor SPEC Data BIG installed

This BIG contains exactly ONE Egypt_CommandCenter.ini
(USA AmericaCommandCenter donor structure, Side=Egypt).
