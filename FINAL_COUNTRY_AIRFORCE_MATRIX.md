# FINAL_COUNTRY_AIRFORCE_MATRIX

New and edited aircraft from this completion pass only. Existing protected rosters were not rewritten.

A2A / A2G lists are Specter wrappers over packed projectiles (Meteor, AIM-9X, R-77, GBU-24, Fab-250, Kh-31P, Paveway IV, 30mm).

| Country | Aircraft | Visual W3D | Role | A2A | A2G | Special | Ammo | Scale | Price | BuildTime | Airbase | Slot |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Germany | GermanyUAVEuroMALE | Nat_Heron | MALE recon / light strike UAV | none | Paveway-style x4 | detector 520, no A2A, NeedsRunway No | 4 | 0.78 | 1600 | 14 | Heavy | 8 |
| Germany | GermanyJetFCASNGF | LSFJ31 | FCAS NGF demonstrator | Meteor x4 | GBU x2 | stealth, detector 720 | 4/2 | 1.00 | 2600 | 17 | Heavy | 9 |
| France | FranceUCAVNeuron | CHI_GJ11L | stealth UCAV | none | AASM/GBU x2 | stealth, detector 420, NeedsRunway No | 2 | 0.72 | 2200 | 16 | Heavy | 5 |
| France | FranceJetMirageF1CR | LSFFRF1 | recon / strike fighter | MICA-style x2, IR x2 | Fab-250 x4 | detector 400 | 2/2/4 | 0.85 | 1200 | 11 | Fighter+Large | 11 |
| France | FranceJetRafaleF4 | LSFIDRafale | modern multirole | Meteor x6, MICA x4 | AASM x4 | none | 6/4/4 | 0.95 | 2400 | 16 | Fighter+Large | 12 |
| UK | BritainAircraftTornadoECR | LSFTornado | SEAD / strike | IR x2 | Kh-31P x4, GBU x4 | detector 900 | 4/2/4 | 0.92 | 2100 | 15 | Heavy | 12 |
| Japan | JapanJetC130H | AVCargoPln | transport | none | none | TransportContain 24, NeedsRunway Yes | - | 1.05 | 2200 | 26 | Heavy | 7 |
| Japan | JapanUAVRQ4 | US_RQ-4 | unarmed HALE recon | none | none | detector 2200, no CAN_ATTACK | - | 0.88 | 2000 | 18 | Heavy | 8 |
| China | ChinaJetJ35A | CHAJ31HXNew | stealth air superiority | PL-15/R-77 x6, PL-10 x2 | LS-6 x2 | stealth | 6/2/2 | 1.05 | 2800 | 17 | Heavy | 12 |
| Iran | IranJetMig21Bis | LSFIDMig21 | cheap interceptor | R-60/AIM-9 x2, cannon | Fab-250 x2 | legacy | 2/20/2 | 0.82 | 700 | 8 | Heavy | 2 |
| Iran | IranJetSu35S | LSFSU35 | air superiority | R-77 x8, R-73 x2 | Kh-31 x2 | Flanker family | 8/2/2 | 1.05 | 2400 | 16 | Heavy | 3 |
| Turkey | TurkeyJetF4ETerm | JPF4 | legacy strike | Sparrow-style x4, IR x2 | Fab-250 x6 | independent of Iran/Japan F-4 | 4/2/6 | 1.00 | 1400 | 12 | Heavy | 6 |
| Pakistan | PakistanJetJ10CE | CHI_J10C | canard-delta multirole | PL-15 x6, PL-10 x2 | LS-6 x4 | distinct from China J-10B | 6/2/4 | 1.10 | 1900 | 14 | Airfield | 9 |
| Italy | ItalyJetGCAP | qsnt50 | stealth demonstrator | Meteor x4, IR x2 | GBU x2 | visual stand-in T-50 class | 4/2/2 | 1.00 | 2700 | 17 | Heavy | 8 |

## Exact CommandSet slots after this pass

### Germany_HeavyAirBaseCommandSet
8 = Command_ConstructGermanyUAVEuroMALE
9 = Command_ConstructGermanyJetFCASNGF
13 Rally / 14 Sell unchanged. 1-7 previous units unchanged.

### France_HeavyAirBaseCommandSet
5 = Command_ConstructFranceUCAVNeuron
Synced into CommandSet.ini and CommandSet_France.ini.

### FranceAirfieldCommandSet / France_LargeAirBaseCommandSet
11 = Command_ConstructFranceJetMirageF1CR
12 = Command_ConstructFranceJetRafaleF4

### Britain_HeavyAirBaseCommandSet
12 = Command_ConstructBritainAircraftTornadoECR
CommandSet_Britain.ini synced to the live Heavy block (keeps Phantom FGR2 slot 10 and Tempest slot 11).

### Japan_HeavyAirBaseCommandSet
7 = Command_ConstructJapanJetC130H
8 = Command_ConstructJapanUAVRQ4

### China_HeavyAirBaseCommandSet
12 = Command_ConstructChinaJetJ35A

### Iran_HeavyAirBaseCommandSet
2 = Command_ConstructIranJetMig21Bis
3 = Command_ConstructIranJetSu35S
1 remains IranJetF4E.

### Turkey_HeavyAirBaseCommandSet
6 = Command_ConstructTurkeyJetF4ETerm
3-5 remain KAAN / F-16C / OZGUR.

### Italy_HeavyAirBaseCommandSet
8 = Command_ConstructItalyJetGCAP

### Pakistan_AirfieldCommandSet
9 = Command_ConstructPakistanJetJ10CE
Patched in CommandSet.ini and CommandSet_Pakistan.ini.

## UAVs added per country
- Germany: Eurodrone MALE
- France: nEUROn
- Japan: RQ-4 (unarmed)
- FCAS NGF is a manned demonstrator, not a UAV
