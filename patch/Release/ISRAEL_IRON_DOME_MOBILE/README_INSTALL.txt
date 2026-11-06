Israel Iron Dome Mobile
=======================

This overlay is built on the ss1 SPECTER FINAL baseline.

What it adds
------------
- New vehicle object: Israel_VehicleIronDomeMobile
- In-game name: Iron Dome Mobile
- Buy button on AirF_AmericaCommandCenterCommandSet slot 11
  (the Command Center the Israel dozer actually builds)
- Buy button also kept on Israel_CommandCenterCommandSet slot 1
- Model: BONDKS.W3D
- Weapon: existing ss1 weapon IroneDome_AA (1.ini named PatriotMissilemWeapon, which is not in ss1)

Install
-------
1. Extract this folder.
2. Put it inside the SPECTER FINAL game folder (the folder that has generals.exe),
   or put it next to that folder.
3. Run Install_Israel_IronDomeMobile.bat
4. Start the game from the SPECTER launcher.

The installer copies Data\INI\CommandSet.ini (ss1 file with one added slot),
unique INI files, Art\W3D\BONDKS.W3D, textures, and Data\English\generals.csf
(the winning ss1 CSF plus three Iron Dome Mobile labels).

What it does not change
-----------------------
- Israel_AD_IronDome
- Israel_AD_Barak8
- Israel_MilitaryHQ / Israel_MilitaryHQCommandSet
- Israel dozer
- Israel_CommandCenter.ini (building definition)

Notes
-----
In the ss1 baseline, FactionIsrael starts at Israel_MilitaryHQ, and the Israel
dozer builds AirF_AmericaCommandCenter. The buy button is on that Command
Center bar (slot 11) so it is reachable in normal play. The same button remains
on Israel_CommandCenterCommandSet slot 1.

W3D has no bone named Turret, MUZZLEFX01, WEAPONB, or IRFX, and no named tire
bones. The INI uses HERO / CYLINDER12 / MUZZLE / MUZZLE01 which exist in the
model. Wheels will not spin visually.

Build cost 1000 and build time 25.0 seconds come from the delivered 1.ini.
