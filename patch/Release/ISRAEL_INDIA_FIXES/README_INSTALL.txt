SPECTER — Israel Global Store + India drone removal
===================================================

One installer. Two static INI/BIG patches. Zero Hour was not run;
neither fix is in-game confirmed.

Israel (PR #728)
----------------
Starting dozer CommandSet AirF_AmericaDozerCommandSet slot 2 =
Command_ConstructIsrael_GlobalStore (not Strategy Center).
Object Israel_GlobalStore, ButtonImage Button_GlobalMarket.

India (PR #729)
---------------
India_CombatDrone, India_LoiteringDrone, India_HeavyUAV are not
producible. Shared radar UAVs (Heron / MQ-4 / Orlan-10 / Shahed),
infantry, and other countries' drones are unchanged.

Install
-------
1. Close Zero Hour.
2. Unzip SPECTER_ISRAEL_INDIA_FIXES_INSTALL.zip into the folder that has generals.exe
   (or into a folder next to it).
3. Run Install_IsraelIndiaFixes.bat once.
4. Do not replace _SPEC_ART_ONE.big / _SPEC_ART_TWO.big.
5. Keep 0_SPECTER_GlobalStoreCameos.big and other 0_ overlays.

The BAT copies only DATA + three INI files. It never copies ART or 0_.

SHA-256
-------
  DATA  52b1186bc552b02237751f3faabd2b3c24c67f2a3ffe69d312db8dfd9a5bc58e
  CS    ba1c8175abc717aac5bb67d23abf249f24ebe24fe63ce00ffcbe250c40ae1e57
  CB    60f904c668a5602258972b996911d129b13bc69facfcf36dc9af40094b9624ba
  PT    d82dc19204f68e6289d60c1989383623f91b130fa29cd529df75f08f4106be8e
  ZIP   72e59762ca086c54bc57294e46d042cefeb8773859f25ba5e81ab5bc349b962b
