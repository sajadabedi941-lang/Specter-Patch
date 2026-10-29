SPECTER — Israel: Strategy Center -> Global Store
=================================================

What this pack changes
----------------------
Israel's starting dozer (`AirF_AmericaVehicleDozer`, Side=Israel) uses
`AirF_AmericaDozerCommandSet`. Slot 2 was
`AirF_Command_ConstructAmericaStrategyCenter` (Strategy Center /
Industry Planet) with Global Store button art.

Slot 2 is now the already-working
`Command_ConstructIsrael_GlobalStore` button:

  CommandButton -> Object Israel_GlobalStore
  ButtonImage   -> Button_GlobalMarket
  Object        -> CommandSet Iraq_MICCommandSet
  Prerequisites empty, BuildCost 7000

Same pattern as Germany / USA Global Store. No new building, no new
CommandButton, no other-country Global Store edits.

CommandButton.ini and PlayerTemplate.ini are the aa-combo-hide bytes
(Arabic Alliance stays hidden). Shahed Fire 8000 and Vietnam radar
TriggeredBy are unchanged.

Install (required)
------------------
Copying only `_SPEC_DATA_ONE.big` will NOT change the Israel menu if
`Data\INI\CommandSet.ini` already exists. FileSystem::openFile opens
the loose file first, then BIGs.

1. Close Zero Hour.
2. Unzip ISRAEL_GS_INSTALL.zip into the game folder
   (the folder that has generals.exe) or next to it.
3. Run Install_IsraelGS.bat.
4. Confirm the script printed SPECTER_PATCH ISRAEL_GS hashes.
5. Keep 0_SPECTER_GlobalStoreCameos.big and
   0_SPECTER_MissileJLMNCameos.big.
6. Do not replace _SPEC_ART_ONE.big / _SPEC_ART_TWO.big.

Zero Hour was not run. Static validation is not an in-game screenshot.

SHA-256
-------
  DATA  df81c16bfbfc4c1b666056e3e9c2ce0a8237fa68e3d90fa54f0f499c05d95b46
  CS    1fdbc74c096077fa871708d7fe87a2b1a09de6efc8202ccbb502adb59793a85c
  CB    60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba
  PT    d82dc19204f68e6289d60c1989383623f91b130fa29cd529df75f08f4106be8e
  ZIP   90109d9ea4c0e7c2657e939bd4b251045f6b69eeadee9c013709c96c8f21380e
