SPECTER — hide Arabic Alliance in the country combo
===================================================

Why remove-arabic-alliance failed in-game
-----------------------------------------
That pack set PlayableSide = No and OldFaction = No on
PlayerTemplate FactionGLA. The skirmish / multiplayer country
dropdown does not read those fields.

Zero Hour source (GeneralsMD GUIUtil.cpp,
PopulatePlayerTemplateComboBox):
  * skip if StartingBuilding is empty
  * skip locked Challenge generals
  * skip non-OldFaction only when the original-factions filter is on
  * label the row with CSF SIDE:<Side>, not DisplayName / INI:FactionGLA

FactionGLA still had StartingBuilding = GLACommandCenter, so it stayed
in the list. CSF SIDE:GLA in Data\English\generals.csf is the string
"Arabic Alliance". Changing PlayableSide or CSF alone cannot hide it.

What this pack changes
----------------------
PlayerTemplate FactionGLA:
  PlayableSide     = No
  OldFaction       = No
  StartingBuilding commented out  (empty — same hide Civilian/Observer use)

The FactionGLA block itself is kept so maps/scripts that name it do
not fail. Iraq / Saudi Arabia / UAE / Syria / Libya are unchanged.

CommandSet.ini, CommandButton.ini, Shahed Fire, cost 8000, Vietnam
radar, ART, 0_ overlays, and generals.csf are not modified.

Install (required)
------------------
Copying only _SPEC_DATA_ONE.big will NOT hide the country if
Data\INI\PlayerTemplate.ini already exists (SPECTER Full Release
installs that loose file). FileSystem::openFile opens the loose
file first, then BIGs.

1. Close Zero Hour.
2. Unzip AA_COMBO_HIDE_INSTALL.zip into the game folder
   (the folder that has generals.exe) or next to it.
3. Run Install_AAComboHide.bat.
4. Confirm the script printed SPECTER_PATCH AA_COMBO_HIDE hashes.
5. Keep 0_SPECTER_GlobalStoreCameos.big and
   0_SPECTER_MissileJLMNCameos.big.
6. Do not replace _SPEC_ART_ONE.big / _SPEC_ART_TWO.big.

This DATA still contains vietnam-radar-minimap + Shahed Fire 8000.

Zero Hour was not run. Engine-source evidence is not an in-game screenshot.

SHA-256: SHA256SUMS.txt
