# 25-country Spy Satellite packed last-wins matrix

RUNTIME_TEST=NOT RUN

Country | Faction | Radar object | CommandSet | Radar cmd | Fee cmd | SP module | OCL ping | CREATE_AT_LOCATION | One module | ProductionUpdate | Reload 60s | SPECIAL_POWER | NEED_UPGRADE | OBJECT_UPGRADE | Upgrade $5000 | Original ping | Fee stripper | ROW
--- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---
Iran | FactionIran | IranRadarStation | IranExpandedRadarCommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
Iraq | FactionIraq | Iraq_RadarStation | Iraq_RadarStationCommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
North Korea | FactionNorthKorea | NorthKorea_RadarStation | NorthKorea_RadarStationCommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
South Korea | FactionSouthKorea | SouthKorea_RadarStation | SouthKorea_RadarStationCommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
Japan | FactionJapan | Japan_RadarStation | Japan_RadarStationCommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
Vietnam | FactionVietnam | Vietnam_RadarStation | Vietnam_RadarStationCommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
China | FactionChina | ChinaRadarYj26 | ChinaRadarStationCommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
Russia | FactionRussia | Russia91N6E | RussiaRadarStationCommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
Israel | FactionIsrael | IsraelBuildingRadarStation | IsraelRadarStationCommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
USA | FactionAmerica | AmericaRadarStation | AmericaRadarStationCommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
NATO | FactionNato | NatoRadarGM406 | NatoGM406CommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
France | FactionFrance | FranceRadarGM406 | FranceGM406CommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
Britain | FactionBritain | BritainRadarGM406 | BritainGM406CommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
Italy | FactionItaly | ItalyRadarGM406 | ItalyGM406CommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
Turkey | FactionTurkey | TurkeyRadarGM406 | TurkeyGM406CommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
Sweden | FactionSweden | SwedenRadarGM406 | SwedenGM406CommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
Ukraine | FactionUkraine | UkraineRadarGM406 | UkraineGM406CommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
Germany | FactionGermany | GermanyRadarGM406 | GermanyGM406CommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
India | FactionIndia | India_RadarStation | India_RadarCommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
Pakistan | FactionPakistan | Pakistan_RadarStation | Pakistan_RadarCommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
South Africa | FactionSouthAfrica | SouthAfrica_RadarStation | SouthAfrica_RadarCommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
Libya | FactionLibya | Libya_RadarStation | Libya_RadarCommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
Syria | FactionSyria | Syria_RadarStation | Syria_RadarCommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
UAE | FactionUAE | UAE_RadarStation | UAE_RadarCommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS
Saudi Arabia | FactionSaudiArabia | SaudiArabia_RadarStation | SaudiArabia_RadarCommandSet | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS

Cost mechanism: Command_SpecterSpySatelliteFee is OBJECT_UPGRADE of
Upgrade_SpecterSpySatelliteScan (Type=OBJECT, BuildCost=5000, BuildTime=0).
Command_SpySatelliteScan remains SPECIAL_POWER + NEED_TARGET_POS + NEED_UPGRADE.
Successful scans create SpecterSpySatelliteFeeStrip which UpgradeDie-removes the fee.
ReloadTime=60000 ms on SpecialPowerSpySatellite.
RUNTIME_TEST=NOT RUN — packed last-wins only.
