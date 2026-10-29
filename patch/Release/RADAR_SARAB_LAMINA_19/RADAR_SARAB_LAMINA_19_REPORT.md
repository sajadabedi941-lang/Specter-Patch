# Radar Sarab_3 ($500) + Lamina ($5000) — 19 countries

**Zero Hour was not run.** Static INI/BIG validation only.

Supersedes incomplete GitHub Release `radar-sarab-lamina` (Spain skipped).
That tag is kept. This pack is tag `radar-sarab-lamina-19`.

SAGE construct cost is Object `BuildCost` (CommandButton.ini has no Cost field).
`SpecterRadar_Sarab3` last-win BuildCost = 500.
`SpecterRadar_Lamina` last-win BuildCost = 5000.

## Spain (this pack's structural change)

Live DATA has no `FactionSpain`, no Spain dozer, no Spain Radar. Spain content
is `Spain_MissileFactory` with `Side = Nato`, constructed from
`NatoDozerCommandSet` slot 14. That dozer uses slots 1–18; adding Radar there
would replace an existing NATO button.

Spain-only Radar added:

- Object `SpainRadarGM406` — clone of `NatoRadarGM406` (model `Nat_RadarSt`,
  ProductionUpdate, DefaultProductionExitUpdate, RadarUpgrade).
- CommandSet `Spain_RadarCommandSet` — empty slots 7/8 get Sarab_3 / Lamina.
- Construct button `Command_ConstructSpainRadarGM406` on
  `Spain_MissileFactoryCommandSet` **empty slot 15** (CommandSet.ini and
  last-win `CommandSet_SpainMissiles.ini`).
- Spy Satellite special power omitted on the Spain clone.
- NATO Radar CS, NATO dozer, and other countries unchanged.
- No `FactionSpain` / combo entry created (would be a new playable country).

Access path: play NATO → build Spain Missile Factory (already on NATO dozer)
→ construct Spain Radar from factory slot 15 → produce Sarab_3 / Lamina.

SPECTER already puts `DOZER_CONSTRUCT` on non-dozer CommandSets (VT72B).
Zero Hour was not run, so factory-to-Radar placement is not in-game proven.

## North Korea

Previous pack already put both drones on `NorthKorea_RadarStationCommandSet`
slots 7/8. Kept. Shared Heron/MQ-4/Orlan/Shahed were never on NK radar and
were not added.

## 19-country static table

| Country | Radar CommandSet identified | Sarab_3 $500 | Lamina $5000 | Objects/deps valid | Notes |
| --- | --- | --- | --- | --- | --- |
| عربستان | `SaudiArabia_RadarCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | object SaudiArabia_RadarStation |
| امارات | `UAE_RadarCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | object UAE_RadarStation |
| سوریه | `Syria_RadarCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | object Syria_RadarStation |
| هند | `India_RadarCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | object India_RadarStation |
| پاکستان | `Pakistan_RadarCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | object Pakistan_RadarStation |
| آفریقای جنوبی | `SouthAfrica_RadarCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | object SouthAfrica_RadarStation |
| لیبی | `Libya_RadarCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | object Libya_RadarStation |
| ترکیه | `TurkeyGM406CommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | object TurkeyRadarGM406 |
| سوئد | `SwedenGM406CommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | object SwedenRadarGM406 |
| اوکراین | `UkraineGM406CommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | object UkraineRadarGM406 |
| ایتالیا | `ItalyGM406CommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | object ItalyRadarGM406 |
| بریتانیا | `BritainGM406CommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | object BritainRadarGM406 |
| آلمان | `GermanyGM406CommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | object GermanyRadarGM406 |
| فرانسه | `FranceGM406CommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | object FranceRadarGM406 |
| اسپانیا | `Spain_RadarCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | new object SpainRadarGM406 (clone of NatoRadarGM406); no FactionSpain — NATO builds Spain_MissileFactory then Spain Radar |
| ویتنام | `Vietnam_RadarStationCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | object Vietnam_RadarStation |
| کره جنوبی | `SouthKorea_RadarStationCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | object SouthKorea_RadarStation |
| ژاپن | `Japan_RadarStationCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | object Japan_RadarStation |
| کره شمالی | `NorthKorea_RadarStationCommandSet` | slot 7 `Command_ConstructSpecterRadarSarab3` yes; Object `SpecterRadar_Sarab3` BuildCost **500** | slot 8 `Command_ConstructSpecterRadarLamina` yes; Object `SpecterRadar_Lamina` BuildCost **5000** | yes | object NorthKorea_RadarStation |

## SHA-256

| File | SHA-256 |
| --- | --- |
| `_SPEC_DATA_ONE.big` | `bb42e2c1e96c7c41660540cb8cfd93f1633a41557dde1af349984ac9242b787e` |
| `CommandSet.ini` | `4a280015eea96b167426268616b51f761a2ec67ecd90213121e979b0d0309680` |
| `CommandButton.ini` | `4e987da75ee4ce1a2079aa4a2da1b514b0ccbb43f987d51c67d2d122dd50c54b` |
| `PlayerTemplate.ini` | `d82dc19204f68e6289d60c1989383623f91b130fa29cd529df75f08f4106be8e` |
| `SPECTER_RADAR_SARAB_LAMINA_19_INSTALL.zip` | `465823470f9baa4ec7ed4b20ec4a243e3ec042ce8337c7236601f2d8f69bb834` |
