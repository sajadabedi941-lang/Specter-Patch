SPECTER — Multiplayer OOS diagnostic (no gameplay patch)
========================================================

This zip is a report and a folder-hash tool. It does NOT replace
_SPEC_DATA_ONE.big, ART, or 0_ overlays. It does NOT claim the
"Game has detected a mismatch" dialog is fixed.

Zero Hour / a 4-player match was not run for this pack.

Read MP_OOS_DIAGNOSTIC_REPORT.md first.

To compare the four PCs
-----------------------
1. Copy hash_game_folder.py onto each game folder (next to generals.exe)
   or run:  python hash_game_folder.py --root "C:\path\to\Zero Hour"
2. Save the printed text from each PC.
3. Diff the four texts. Any BIG or loose INI hash that differs is enough
   to cause CRC OOS once those objects appear in numbers.

If all four hashes match, send the four texts plus map name, countries,
and whether the dialog appeared in a ground-only fight or after
MLRS / AD / air fire. That is what is needed to name the CRC bit.
