# Unified pack: GS S-300 + 19-country Radar drones

**Zero Hour was not run.**

Merged lineage (not nested ZIPs):

`radar-sarab-lamina-19` (`bb42e2c1e96c7c41660540cb8cfd93f1633a41557dde1af349984ac9242b787e`) → `gs-s300` (`aa40e6d1e68058becbe8d197a94c9ba05a5ef1af6bda25a14f5e82e9ea4ece53`)

gs-s300 changed only five MIC shop files. Spain Radar from
radar-sarab-lamina-19 is unchanged.

## Global Store

| Check | Result |
| --- | --- |
| Slot 5 | `Command_ConstructIraq_MIC_S300` |
| Object | `Iraq_MIC_S300` BuildCost **4500** |
| Pantsir on GS slot 5 | gone (CS.ini + last-win overlay) |
| `Iraq_MIC_PantsirS1M` / other-country Pantsir | kept |
| `Arabic_S300PMU2` cost | still 2000 |
| Other GS slots 1–4, 6–15 | unchanged |
| Israel GS shop | still `Iraq_MICCommandSet` |

## 19-country Radar

| Country | CommandSet | Sarab_3 | Lamina |
| --- | --- | --- | --- |
| عربستان | `SaudiArabia_RadarCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |
| امارات | `UAE_RadarCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |
| سوریه | `Syria_RadarCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |
| هند | `India_RadarCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |
| پاکستان | `Pakistan_RadarCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |
| آفریقای جنوبی | `SouthAfrica_RadarCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |
| لیبی | `Libya_RadarCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |
| ترکیه | `TurkeyGM406CommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |
| سوئد | `SwedenGM406CommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |
| اوکراین | `UkraineGM406CommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |
| ایتالیا | `ItalyGM406CommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |
| بریتانیا | `BritainGM406CommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |
| آلمان | `GermanyGM406CommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |
| فرانسه | `FranceGM406CommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |
| اسپانیا | `Spain_RadarCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |
| ویتنام | `Vietnam_RadarStationCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |
| کره جنوبی | `SouthKorea_RadarStationCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |
| ژاپن | `Japan_RadarStationCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |
| کره شمالی | `NorthKorea_RadarStationCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` **$500** | slot 8 `Command_ConstructSpecterRadarLamina` **$5000** |

Spain uses `SpainRadarGM406` + `Spain_RadarCommandSet` from
radar-sarab-lamina-19. India CombatDrone stays commented. Shared
Heron/MQ-4/Orlan-10/Shahed and Spy Satellite removal stay.

## SHA-256

| File | SHA-256 |
| --- | --- |
| `_SPEC_DATA_ONE.big` | `aa40e6d1e68058becbe8d197a94c9ba05a5ef1af6bda25a14f5e82e9ea4ece53` |
| `CommandSet.ini` | `13264095c91e610458e92bbc324aaa4d82d11bfdba597cd26cdf31d42e771213` |
| `CommandButton.ini` | `1264aef1606ca9e6d1d68db0c211a793403d385417bc66238175c757f7350250` |
| `PlayerTemplate.ini` | `d82dc19204f68e6289d60c1989383623f91b130fa29cd529df75f08f4106be8e` |
| `SPECTER_S300_RADAR_DRONES_INSTALL.zip` | `818f6f554565379e241a783bd9c1f308fc2aaded1d944d95059e47fe120c3474` |
