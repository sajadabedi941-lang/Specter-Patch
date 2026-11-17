SPECTER radar Shahed-136 Fire
=============================

Gives the 18-country radar "Shahed_136 Mobile Launcher" the same Fire
path as the working Iranian launcher. Zero Hour was not run. Static
checks are not in-game proof.

What changed
------------
Object SpecterRadar_ShahedLauncher (shared by 18 radar menus, slot 12):
  CommandSet  AmericaTankCrusaderCommandSet
           -> IranShahed136FireCommandSet  (existing; not duplicated)
  PRIMARY     5x_Shahed136DroneSwarm
           -> Weapon_Iran_Shahed136Launcher
  BuildCost   8000 (unchanged)

IranVehicleShahedLauncher is not edited. Iran BuildCost stays 1500.
Radar country lists, slot 12, and other radar/missile buttons are not
edited. CommandSet.ini and CommandButton.ini are byte-identical to the
#722 / specter-unified pack.

Fire path (same as Iran)
------------------------
1. Radar slot 12 builds SpecterRadar_ShahedLauncher
2. Unit CommandSet IranShahed136FireCommandSet
3. Slot 1 Command_FireMainWeapon = FIRE_WEAPON PRIMARY NEED_TARGET_POS
4. Weapon Weapon_Iran_Shahed136Launcher in Data\INI\Weapon.ini
   (AntiGround=Yes, AttackRange=3000, projectile Iran_Shahed136_FireProjectile)
5. Projectile uses DumbProjectileBehavior (not Shahed136_AI_Object)

Install
-------
1. Close Zero Hour.
2. Unzip RADAR_SHAHED_FIRE_INSTALL.zip
3. Run Install_RadarShahedFire.bat from the game folder or a folder beside it.
4. Keep 0_SPECTER_GlobalStoreCameos.big and 0_SPECTER_MissileJLMNCameos.big.
5. Do not replace _SPEC_ART_ONE.big / _SPEC_ART_TWO.big.

This DATA replaces _SPEC_DATA_ONE.big from specter-unified / #722. It
already contains those DATA changes. Do not install an older DATA BIG
after this pack.

SHA-256
-------
See SHA256SUMS.txt.
