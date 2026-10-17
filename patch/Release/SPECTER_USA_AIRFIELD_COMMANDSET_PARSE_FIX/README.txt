SPECTER_USA_AIRFIELD_COMMANDSET_PARSE_FIX

FIX ONLY: CommandSet.ini parse crash at AmericaAirfieldCommandSet.

Cause: UTF-8 em-dash (U+2014) in comment immediately before
  CommandSet AmericaAirfieldCommandSet
ZH INI parser cannot read non-ASCII; crash reported at next CommandSet.

Correction: replace em-dash with ASCII hyphen in comments
  (CommandSet.ini + AIRFIELD_RUNTIME_ROSTER.ini comments only).

No gameplay / roster / aircraft / Strategy Center / upgrade changes.

Replace GameRoot Data\_SPEC_ART_ONE.big and Data\_SPEC_DATA_ONE.big.
Zip contains ONLY those two files.
