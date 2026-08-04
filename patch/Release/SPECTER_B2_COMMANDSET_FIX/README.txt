SPECTER_B2_COMMANDSET_FIX

Fixes parse crash:
  Data\INI\CommandSet.ini
  Line: CommandSet AmericaAirfieldCommandSet_T

Cause:
  Bad packaging regex matched a comment containing
  "CommandSet AmericaAirfieldCommandSet_T" and injected
  Object/comment garbage into CommandSet.ini.

Fix:
  All five USA Airfield CommandSet blocks rewritten cleanly.
  Each block has matching End, no duplicates, slot lines only.
  slot 5 = Command_ConstructTEODAmericaJetB2

Does NOT change B-2 object / model / weapon / AI.
