# SS2 Data folder audit (engine load map)

Source: `/tmp/ss2/SPECTER FINAL (GeneralsMode.com)/Data`
Engine: stock ZH `game.dat` (6,483,968 bytes). Existence of a Loose file is not a load proof.

## Engine-opened INI paths

ControlBar (exact files only):
- `Data\INI\Default\CommandButton.ini`
- `Data\INI\CommandButton.ini`  ← Loose wins over every BIG
- `Data\INI\CommandSet.ini`  ← Loose wins over every BIG

ThingFactory directory glob: `Data\INI\Object` (recursive `.ini`).
MappedImages glob: `Data\INI\MappedImages\*.ini`.
ParticleSystem directory glob: `Data\INI\ParticleSystem`.
Weapons: exact `Data\INI\Weapon.ini` only.

Not opened by ControlBar: `CommandSet_*.ini`, `CommandButton_*.ini`.
Not opened by ThingFactory: `Data\INI\Object_ZZZZ_*.ini` (INI **root**, outside Object/).
Not opened as a weapon glob: `Data\INI\Weapon\*.ini` and `Weapon_*.ini`.
Duplicate CommandSet names throw `INI_INVALID_DATA` (no last-win).

## Data tree

- `Data/Cursors`, `Data/English/Movies`, `Data/Movies`, `Data/Scripts`, `Data/WaterPlane`
- `Data/INI` — 211 Loose INI at root + Default, GameData, MappedImages, Object, Weapon
- Object glob: 2818 `.ini` files
- CommandSet.ini sets: 1154
- CommandButton.ini buttons: 3625
- Extra CommandSet_*.ini files: 59 (not ControlBar-loaded)
- Extra CommandButton_*.ini files: 46 (not ControlBar-loaded)

## Live Command Center bars (26 + Turkey)

| Country | Object file | Live CommandSet (CommandSet.ini) | Slot 1 |
|---|---|---|---|
| Iraq | `Iraq_CommandCenter` | `Iraq_CommandCenterCommandSet` | `Command_ConstructIraq_VT72B` |
| NorthKorea | `NorthKorea_CommandCenter` | `NorthKorea_CommandCenterCommandSet` | `Command_ConstructNorthKorea_VT72B` |
| America | `AmericaCommandCenter` | `AmericaCommandCenterCommandSet` | `Command_ConstructAmericaDozer` |
| Russia | `RussiaCommandCenter` | `RussiaCommandCenterCommandSet` | `Command_ConstructRussiaVehicleDozer` |
| China | `ChinaCommandCenter` | `ChinaCommandCenterCommandSet` | `Command_ConstructChinaDozer` |
| GLA | `GLACommandCenter` | `GLACommandCenterCommandSet` | `Command_ConstructGLAWorker` |
| Boss | `Boss_CommandCenter` | `Boss_ChinaCommandCenterCommandSet` | `Boss_Command_ConstructChinaDozer` |
| AmericaAirForceGeneral | `AirF_AmericaCommandCenter` | `AirF_AmericaCommandCenterCommandSet` | `AirF_Command_ConstructAmericaDozer` |
| Nato | `NatoCommandCenter` | `NatoCommandCenterCommandSet` | `Command_ConstructNatoVehicleDozer` |
| Iran | `IranCommandCenter` | `IranExpandedHQCommandSet` | `Command_ConstructIranVehicleDozer` |
| Pakistan | `Pakistan_CommandCenter` | `Pakistan_CommandCenterCommandSet` | `Command_ConstructPakistan_Dozer` |
| SaudiArabia | `SaudiArabia_CommandCenter` | `SaudiArabia_CommandCenterCommandSet` | `Command_ConstructSaudiArabia_Dozer` |
| UAE | `UAE_CommandCenter` | `UAE_CommandCenterCommandSet` | `Command_ConstructUAE_Dozer` |
| India | `India_CommandCenter` | `India_CommandCenterCommandSet` | `Command_ConstructIndia_Dozer` |
| Syria | `Syria_CommandCenter` | `Syria_CommandCenterCommandSet` | `Command_ConstructSyria_Dozer` |
| Germany | `GermanyCommandCenter` | `GermanyCommandCenterCommandSet` | `Command_ConstructGermanyVehicleDozer` |
| France | `FranceCommandCenter` | `FranceCommandCenterCommandSet` | `Command_ConstructFranceVehicleDozer` |
| Britain | `BritainCommandCenter` | `BritainCommandCenterCommandSet` | `Command_ConstructBritainVehicleDozer` |
| Italy | `ItalyCommandCenter` | `ItalyCommandCenterCommandSet` | `Command_ConstructItalyVehicleDozer` |
| Sweden | `SwedenCommandCenter` | `SwedenCommandCenterCommandSet` | `Command_ConstructSwedenVehicleDozer` |
| Ukraine | `UkraineCommandCenter` | `UkraineCommandCenterCommandSet` | `Command_ConstructUkraineVehicleDozer` |
| Libya | `Libya_CommandCenter` | `Libya_CommandCenterCommandSet` | `Command_ConstructLibya_Dozer` |
| SouthAfrica | `SouthAfrica_CommandCenter` | `SouthAfrica_CommandCenterCommandSet` | `Command_ConstructSouthAfrica_Dozer` |
| SouthKorea | `SouthKorea_CommandCenter` | `SouthKorea_CommandCenterCommandSet` | `Command_ConstructSouthKorea_VT72B` |
| Japan | `Japan_CommandCenter` | `Japan_CommandCenterCommandSet` | `Command_ConstructJapan_VT72B` |
| Vietnam | `Vietnam_CommandCenter` | `Vietnam_CommandCenterCommandSet` | `Command_ConstructVietnam_VT72B` |
| Turkey | `TurkeyCommandCenter` | `TurkeyCommandCenterCommandSet` | `Command_ConstructTurkeyVehicleDozer` |

Iran factory (untouched): `Iran_MissileFactoryCommandSet` in CommandSet.ini, button `CB_IRAN_MISSILE_G` → `Iran_Khorram` in CommandButton.ini, object `Object/Specter/Iranian Army/Wheeled/Iran_Khorram.ini`.
Turkey loader already live in CommandSet.ini slot 4 + CommandButton.ini + `Turkish Armed Forces/Wheleed/Dozer.ini`.
Country extras such as `CommandSet_Pakistan.ini` redefine CC sets but are **not** loaded; live Pakistan CC is Dozer from CommandSet.ini.

## Where this patch writes

| Piece | File | Why |
|---|---|---|
| CC buttons | `Data/INI/CommandSet.ini` | Only CommandSet file ControlBar opens |
| Unique loader CommandSets | appended to `Data/INI/CommandSet.ini` | New names only |
| Unique construct buttons | appended to `Data/INI/CommandButton.ini` | Only CommandButton file ControlBar opens |
| Loader/tunnel Objects | new files under `Data/INI/Object/Specter/<country>/` | ThingFactory glob |

No BIG members are created or replaced.
