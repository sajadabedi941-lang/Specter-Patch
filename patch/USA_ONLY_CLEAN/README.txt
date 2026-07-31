SPECTER - USA STRING RUNTIME FIX
================================
ROOT CAUSE of "***FATAL*** String Manager failed to initialize properly":

Corrupt Data/English/generals.csf in USA packs.
Turkey string entries used invalid magic "RTSW" instead of "WRTS"/"STR ".
String Manager aborts while parsing CSF.

FIX:
- Replace with known-good generals.csf
- Append USA OBJECT:/CONTROLBAR: keys into CSF
- Remove Data/English/*.txt overlays (not CSF; working packs use CSF only)

USA aircraft / AdvancedAirBase / heliborne content is preserved.
CommandSet.ini untouched. No new factions.
