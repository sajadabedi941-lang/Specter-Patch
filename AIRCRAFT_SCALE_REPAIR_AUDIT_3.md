# AIRCRAFT SCALE REPAIR AUDIT 3

Per-aircraft geometry Scale values. Not a single arbitrary constant.

| Country | Aircraft | Object | W3D | Old Geometry Scale | New Geometry Scale | Reference aircraft | Reason |
|---|---|---|---|---|---|---|---|
| Syria | SyriaJetMig21 | SyriaJetMig21 | UVMig-21 | 0.82 | 0.94 | Ukraine MiG-21bis 0.94 / F-16 0.90 | MiG-21bis was miniature vs F-5/Mirage F1/MiG-29 class |
| Syria | SyriaJetMig21MF | SyriaJetMig21MF | UVMig-21 | 0.80 | 0.96 | Libya MiG-21MF 0.96; offset from Syria bis 0.94 | Independent MF scale; same W3D family but not identical value |
| India | IndiaJetMig21Bison | IndiaJetMig21Bison | LSFIDMig21 | 0.84 | 0.90 | F-16 0.90; below India Su-30MKI 0.92 | Bison remains smaller than Su-30MKI |
| India | IndiaJetTejas | IndiaJetTejas | NVJ31 | 0.86 | 0.90 | F-16/Gripen class; below Su-30MKI 0.92 | Lightweight fighter, not miniature |
| Saudi Arabia | SaudiJetLightning | SaudiJetLightning | AVLightn | 0.86 | 1.02 | F-4 Phantom ~1.00 / Mirage F1 / MiG-23 | English Electric Lightning F.53 full-size interceptor |
| Saudi Arabia | SaudiJetHawk65 | SaudiJetHawk65 | AVHawk | 0.80 | 0.82 | Alpha Jet / M339 / L-159 trainer class | Keep trainer; do not enlarge to F-15 |
| Saudi Arabia | SaudiJetF5E | SaudiJetF5E | AVHawk | 0.78 | 0.88 | Light fighter; larger than trainer, smaller than F-15 | F-5E Tiger II light-fighter scale |
| Pakistan | PakistanJetMirageROSE | PakistanJetMirageROSE | UVMirage | 0.90 | 1.06 | SA Mirage III 1.08 / Mirage 2000 | ROSE III Mirage III/V family |
| Pakistan | PakistanJetF7PG | PakistanJetF7PG | LSFPKJ7 | 0.86 | 0.96 | MiG-21 / J-7 class fighter | F-7PG full-size J-7 |
| Pakistan | PakistanJetF7P | PakistanJetF7P | LSFJ7 | 0.84 | 0.94 | Independent of F-7PG; different W3D LSFJ7 | F-7P Skybolt calculated separately |

SCALE_AUDIT = PASS
Cursor cannot launch Zero Hour. Visual size is STATIC vs reference scales.
