# WEAPON PARSE CRASH CONTEXT

Packed file: `Data\INI\Weapon.ini` from `_SPEC_DATA_ONE.big` (airforce-repair-pass-3-v1).

REPORTED_CRASH_FILE = Data\INI\Weapon.ini
REPORTED_CRASH_LINE = Weapon VietnamJetMig29S_WpnGun
REPORTED_WEAPON_OCCURRENCES_BEFORE = 1 declaration(s) at lines [55730]
All substring hits (including object refs in this file): [55730]

PREVIOUS_WEAPON_NAME = VietnamJetMig29S_WpnIR (L55704-L55729)
REPORTED_WEAPON = VietnamJetMig29S_WpnGun (L55730-L55750)
NEXT_WEAPON_NAME = Japan_Weapon_AAM4B_F15JStd (L55751-L55776)

REPORTED_LINE = VietnamJetMig29S_WpnGun
ACTUAL_BAD_BLOCK = VietnamJetMig29S_WpnGun
ROOT_CAUSE = Invalid Zero Hour DamageType GUN inside VietnamJetMig29S_WpnGun (plus tank FireFX/FireSound and AutoReloadsClip=YES). Previous weapon VietnamJetMig29S_WpnIR has a matching End at L55729. The engine reports the Weapon header of the block that fails field validation.

SOURCE_FILE_THAT_INTRODUCED_BUG = patch/tools/big/generate_jp_kr_vn_objects.py function cannon(), inlined into packed Weapon.ini by pack_jp_kr_vn_airforce_fix.py (JP/KR/VN pass). A second copy of the same broken template is IraqJetMig25RB_WpnGun.

FIX_APPLIED = Replaced both GUN cannons with VietnamJetMig21_WpnGun structural syntax (DamageType=COMANCHE_VULCAN, ProjectileObject=30mm_API-T_Projectile). Kept intended balance (damage/clip/delay/range). Fixed cannon() generator so a future pack cannot reintroduce GUN.

## 40 lines before / after reported declaration

```
   55690|  ProjectileObject = R77_Object
   55691|  ProjectileDetonationFX = FX_LightAAMImpact
   55692|  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
   55693|  FireSound = RaptorJetMissileWeapon
   55694|  DelayBetweenShots = 900
   55695|  ClipSize = 6
   55696|  ClipReloadTime = 16000
   55697|  AutoReloadsClip = RETURN_TO_BASE
   55698|  ProjectileCollidesWith = ALLIES ENEMIES STRUCTURES WALLS SHRUBBERY
   55699|  AntiAirborneVehicle = Yes
   55700|  AntiGround = No
   55701|  AntiAirborneInfantry = Yes
   55702|  ShowsAmmoPips = Yes
   55703|End
   55704|Weapon VietnamJetMig29S_WpnIR
   55705|  PrimaryDamage = 70.0
   55706|  PrimaryDamageRadius = 12.0
   55707|  SecondaryDamage = 12.0
   55708|  SecondaryDamageRadius = 22.0
   55709|  AttackRange = 420.0
   55710|  MinimumAttackRange = 80.0
   55711|  AcceptableAimDelta = 360
   55712|  DamageType = PENALTY
   55713|  DeathType = EXPLODED
   55714|  WeaponSpeed = 8600
   55715|  FireFX = None
   55716|  ProjectileObject = AIM-9X_Object
   55717|  ProjectileDetonationFX = FX_LightAAMImpact
   55718|  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
   55719|  FireSound = RaptorJetMissileWeapon
   55720|  DelayBetweenShots = 600
   55721|  ClipSize = 4
   55722|  ClipReloadTime = 12000
   55723|  AutoReloadsClip = RETURN_TO_BASE
   55724|  ProjectileCollidesWith = ALLIES ENEMIES STRUCTURES WALLS SHRUBBERY
   55725|  AntiAirborneVehicle = Yes
   55726|  AntiGround = No
   55727|  AntiAirborneInfantry = Yes
   55728|  ShowsAmmoPips = Yes
   55729|End
>> 55730|Weapon VietnamJetMig29S_WpnGun
   55731|  PrimaryDamage = 42.0
   55732|  PrimaryDamageRadius = 8.0
   55733|  ScatterRadiusVsInfantry = 40.0
   55734|  ScatterRadius = 12.0
   55735|  AttackRange = 360.0
   55736|  MinimumAttackRange = 20.0
   55737|  DamageType = GUN
   55738|  DeathType = NORMAL
   55739|  WeaponSpeed = 99999
   55740|  FireFX = WeaponFX_GenericTankCannonFire
   55741|  FireSound = M1A2_TankCannonFire
   55742|  DelayBetweenShots = 180
   55743|  ClipSize = 40
   55744|  ClipReloadTime = 8000
   55745|  AutoReloadsClip = YES
   55746|  AntiAirborneVehicle = Yes
   55747|  AntiGround = Yes
   55748|  AntiAirborneInfantry = Yes
   55749|  ShowsAmmoPips = Yes
   55750|End
   55751|Weapon Japan_Weapon_AAM4B_F15JStd
   55752|  PrimaryDamage = 88.0
   55753|  PrimaryDamageRadius = 12.0
   55754|  SecondaryDamage = 12.0
   55755|  SecondaryDamageRadius = 22.0
   55756|  AttackRange = 680.0
   55757|  MinimumAttackRange = 80.0
   55758|  AcceptableAimDelta = 360
   55759|  DamageType = PENALTY
   55760|  DeathType = EXPLODED
   55761|  WeaponSpeed = 8600
   55762|  FireFX = None
   55763|  ProjectileObject = MeteorMissile_Object
   55764|  ProjectileDetonationFX = FX_LightAAMImpact
   55765|  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
   55766|  FireSound = RaptorJetMissileWeapon
   55767|  DelayBetweenShots = 1100
   55768|  ClipSize = 4
   55769|  ClipReloadTime = 15000
   55770|  AutoReloadsClip = RETURN_TO_BASE
```

## Pre-fix sequential parse (Weapon.ini)

- Weapon blocks: 2477
- duplicate Weapon names: 0
- unfinished Weapon blocks: 0
- Weapon-inside-Weapon: 0
- empty Weapon name: 0
- unindented End with no open Weapon (includes `Weapon = Name` false positives if any): 0

Same-country VietnamJetMig29S_* declarations (unique):
- VietnamJetMig29S_WpnRadar L55678-L55703
- VietnamJetMig29S_WpnIR L55704-L55729
- VietnamJetMig29S_WpnGun L55730-L55750
