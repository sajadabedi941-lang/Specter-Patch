# China Air Force asset report (mod.z extended audit)

Date: 2026-08-24  
Type: read-only scan. No INI, ART, CommandSet, or gameplay files were created or modified.

## What `mod.z` actually is

`mod.z` is a **29-volume zip** (`mod.z01`–`mod.z28` + `mod.zip`), 561.5 MB, 1991 files.

| Expected | Found |
|---|---|
| mod.z DATA BIG files | **None.** Zero `.big` files. |
| mod.z ART BIG files | **None.** Zero aircraft W3D. 39 W3D files are World Builder molds only (`Data/Editor/Molds/`). |
| Patch form | Loose `Data/INI/*.ini` overlay (295 INI files), audio, UI textures, China campaign movies. |

China-related INI inside mod.z:

- `Data/INI/Object/ChinaAir.ini`
- `Data/INI/Object/China Rogue General.ini`
- `Data/INI/Object/NukeGeneral.ini`
- `Data/INI/Object/InfantryGeneral.ini`
- `Data/INI/Object/ArtilleryGeneral.ini`
- `Data/INI/Object/EMPNapalmGeneral.INI`
- `Data/INI/Object/SpecPlane.ini`
- `Data/INI/CommandButton.ini` / `CommandSet.ini`

There are **no** J-11B, J-15, J-31, JF-17, J-8F, J-7, Y-20, KJ-500, KJ-2000, H-6K, WZ-8, BZK-005, or CH-5 object names in any mod.z INI.

## Other sources used

| Label | Archive | Role |
|---|---|---|
| Base game | `SPECTER FINAL (GeneralsMode.com).zip` → `INIZH.big` + `W3DZH.big` | Stock Zero Hour China air |
| `_SPEC_DATA_ONE.big` | `/tmp/russia_four_fighters/_SPEC_DATA_ONE.big` | Current Specter DATA pack |
| `_SPEC_ART_ONE.big` | `/tmp/russia_four_fighters/_SPEC_ART_ONE.big` | Current Specter ART pack |
| Donor ART | `/workspace/DONOR_Art.part001.rar` … `part069.rar` (23126 files) | Extra China W3D/textures |
| Donor INI | `/workspace/DONOR_INI.rar` | No PLA aircraft Object INI |
| art_data RAR | older copies of `_SPEC_*_ONE.big` only | No extra unique China meshes |
| Workspace overlay | `patch/Data/INI/.../Pakistan_JF17*.ini` | Not packed; uses F-16 mesh |

“Can be converted using donor ART + existing aircraft skeleton?” means a dedicated W3D+texture already exists **and** a working packed jet/heli/bomber/drone Object (for example `ChinaJetJ10C`, `ChinaJetJ20B_AG`, `ChinaHelicopterWZ10ME`, `ChinaBomberH6M`, `ChinaDroneCH5`) can be used as the INI skeleton. This report does not create that overlay.

---

## Fighters

| Aircraft | Base game? | `_SPEC_DATA_ONE.big`? | `_SPEC_ART_ONE.big`? | Donor ART? | mod.z? | Exact source location | INI object | ART / model | Convert donor ART + skeleton? |
|---|---|---|---|---|---|---|---|---|---|
| J-20 Mighty Dragon | NO | **YES** | **YES** | YES (extra) | NO | DATA `PLA\Airforce\J20B.ini` (+ `_AA`, `_AA_AI`). ART `CHI_J20B*.W3D` | `ChinaJetJ20B_AG`, `ChinaJetJ20B_AA`, `ChinaJetJ20B_AA_AI` | `CHI_J20B` / `_D` / `_R`. Packed tex `PLA_J20.dds`. Donor extra `LSFJ20.W3D` | YES (already unique in packed game) |
| J-35 / FC-31 | NO | NO unique. Placeholder `ChinaJetJ50` reuses J-20 | NO J-35 mesh | NO J-35/FC-31 W3D | NO | DATA `PLA\China_System.ini` placeholder only | `ChinaJetJ50` (J-20 clone) | `CHI_J20B` | **NO** unique J-35. J-31 donor mesh is the only family stand-in |
| J-16 | NO | **YES** as J-16D | **YES** `Chi_J16D.W3D` | NO extra J-16 mesh | NO | DATA `PLA\Airforce\J16D.ini` | `ChinaJetJ16D` | `Chi_J16D` | YES (J-16D already present). Unique strike J-16: **NO** |
| J-10C | NO (mod.z has a fake J-10) | **YES** | **YES** | NO extra J-10C mesh (packed already has it) | Partial: `ChinaJetJ-10` exists but is **not** J-10C | Packed: `PLA\Airforce\J10C.ini`. mod.z: `Data/INI/Object/ChinaAir.ini` | Packed `ChinaJetJ10C`. mod.z `ChinaJetJ-10` | Packed `CHI_J10C`. mod.z model `NVSU-37;NVTejas` (Su-37/Tejas, not J-10) | YES (packed J-10C already unique). Do not convert from mod.z `ChinaJetJ-10` |
| J-11B | NO | NO | NO | **YES** | **NO** | Donor `Art/w3d/LSFJ11B.W3D` (+ d/k), `CHJ11_r.W3D`. Tex `LSFJ11B.dds`, `J11B.tga` | none | `LSFJ11B` | **YES** (donor W3D + `ChinaJetJ10C` / `ChinaJetJ20B_AG` skeleton) |
| J-15 Flying Shark | NO | NO | NO | **YES** | **NO** | Donor `Art/w3d/J15JZ.W3D`. Tex `AGMZJ15.dds`, `CHNJ15A.tga`, `CHNJ15ATB.tga` | none | `J15JZ` | **YES** |
| J-10B | NO unique | NO unique (other factions clone J-10C) | NO unique | **YES** | NO | Donor `Art/w3d/ChJ10B.W3D`. Tex `CHJ10B.dds` | none unique | `ChJ10B` | **YES** |
| JH-7A Flying Leopard | NO | **YES** as JH-7A2 | **YES** | YES extra `CHJH7A.W3D` | NO | DATA `PLA\Airforce\JH7A2.ini` | `ChinaJetJH7A2` | `CHI_JH7A2` | YES (already present) |
| J-8F | NO | NO | NO | **YES** as J-8II, not named J-8F | **NO** | Donor `Art/w3d/CHJ8_2.W3D`, `LSFChinaJ8B.W3D` | none | `CHJ8_2` / `LSFChinaJ8B` | **YES** as J-8II stand-in |
| JF-17 Block 3 / FC-1 | NO | NO (not packed) | NO | **YES** | **NO** | Donor `Art/w3d/CHJF17.W3D`, `LSFPKJF17.W3D`. Workspace overlay `Pakistan_JF17` uses `US_F16D_B52` and is not in DATA BIG | Overlay only: `Pakistan_JF17` (do not use) | `CHJF17` / `LSFPKJF17` | **YES** with donor JF-17 mesh + fighter skeleton. Current overlay INI is an F-16 fake |
| J-31 | NO | NO | NO | **YES** | **NO** | Donor `Art/w3d/LSFJ31.W3D` (+ d/k), `CHAJ31HXNew.W3D`. Tex `LSFJ31.dds`, `J31TB.tga` | none | `LSFJ31` | **YES** |
| Su-35 Chinese version | NO | NO PLA object. Old China airfield still constructs Russian Su-35 | Russian `RUS_SU35S.W3D` only | Russian/Egypt Su-35 only | NO PLA Su-35. Has `ChinaJetSu-34` instead | Packed CommandSet leftover `Command_ConstructRussian_Su35`. mod.z `ChinaJetSu-34` → `NVSu-34` | none Chinese Su-35 | Russian `LSFSU35` / `RUS_SU35S` | **NO** (no Chinese Su-35 texture/object) |
| H-20 | NO | NO | NO | NO real bomber mesh | NO | `PTBush20.W3D` is a bush. `LSFzh2000.W3D` is PzH 2000 artillery | none | none | **NO** |
| J-7 | NO | NO | NO | **YES** | **NO** | Donor `Art/w3d/LSFJ7.W3D` (+ d/k/R). Tex `CHJ7.dds` | none | `LSFJ7` | **YES** |
| J-10A | NO | NO | NO | **YES** | NO | Donor `Art/w3d/chj10a.W3D`, `BJSTJ10A.W3D`. Tex `CHJ10A.dds` | none | `chj10a` | **YES** |

### Stock / mod.z China air that is **not** on the modern PLA list

These exist in base game and/or mod.z. They are not J-20/J-11/J-15-class assets.

| Object | Where | Model | Notes |
|---|---|---|---|
| `ChinaJetMIG` | Base `INIZH.big` `ChinaAir.ini`; mod.z `ChinaAir.ini`; packed DATA keeps `Infa_ChinaJetMIG` | Base `NVMIG`. mod.z main object uses `NVEnvoy` | Stock ZH MiG. Base W3D `NVMigN.w3d` in `W3DZH.big`. **Not** in packed ART BIG |
| `ChinaVehicleHelix` | Base + mod.z + packed infantry-general clone | `NVHELIX` | Stock ZH Helix. Base W3D in `W3DZH.big`. **Not** in packed ART BIG |
| `ChinaJetCargoPlane` | Base + mod.z | `NVCargoPln` | Stock cargo |
| `ChinaJetCarpetBomber` | Base `SpecialPowerObjects.ini` | `NVCBomber` | Science carpet bomber |
| `ChinaJetJ-10` | **mod.z only** | `NVSU-37;NVTejas` (also `Su-33;J-10` on some generals) | Fake J-10. No J-10 W3D in mod.z. Commented out of default `ChinaAirfieldCommandSet` slot 3 |
| `ChinaJetSu-34` | mod.z | `NVSu-34` / `Su-34` | Russian Su-34, not a PLA unique type in Specter DATA |
| `Art_ChinaJetTu-160` | mod.z Artillery General | `NVTu-160` | Russian bomber on a China general |
| `EMPNapalm_ChinaJetSu-47` | mod.z | `NVSu-47` | Russian Su-47 |
| `Nuke_ChinaMig-25` | mod.z | `NVSU-37A` | Placeholder |

mod.z `ChinaAirfieldCommandSet` default slots: MIG, Helix, Su-34. `Command_ConstructChinaJetJ-10` is commented out except on Nuke/Infa/EMP/Art generals.

---

## Large aircraft

| Aircraft | Base game? | `_SPEC_DATA_ONE.big`? | `_SPEC_ART_ONE.big`? | Donor ART? | mod.z? | Exact source location | INI object | ART / model | Convert donor ART + skeleton? |
|---|---|---|---|---|---|---|---|---|---|
| H-20 Bomber | NO | NO | NO | NO | NO | none | none | none | **NO** |
| H-6K / H-6N | NO | **YES** as H-6M science bomber | **YES** `CHI_H6M` | **YES** H-6K `h6k.W3D`, `LSFCHNH6k.W3D` | **NO** | Packed `PLA\Science Objects\H6M.ini`. Donor `Art/w3d/h6k.W3D` | `ChinaBomberH6M` | Packed `CHI_H6M`. Donor `h6k` | H-6M already present. H-6K: **YES**. H-6N: **NO** (no N mesh) |
| Y-20 Transport | NO | NO | NO | **YES** | **NO** | Donor `Art/w3d/HXYun20HXNew.W3D`. Tex `CHNY20.tga` | none | `HXYun20HXNew` | **YES** (Y-20 W3D + large transport/cargo skeleton) |
| Y-9 Transport | NO | NO | NO | NO | NO | none | none | none | **NO** |
| KJ-500 AWACS | NO | Placeholder object only | NO KJ-500 mesh (uses A-50) | NO KJ-500 W3D | **NO** | DATA `PLA\China_System.ini` | `ChinaAircraftKJ500` | `RUS_A50` | **NO** (no KJ-500 mesh; already an A-50 stand-in) |
| KJ-2000 AWACS | NO | NO | NO | Icons only `CHNKJ2000.tga` | **NO** | Donor textures only | none | no W3D | **NO** |
| WZ-10 Helicopter | NO | **YES** as WZ-10ME | **YES** | YES extra `LSFWZ10.W3D` | **NO** | DATA `PLA\Airforce\WZ10ME.ini` | `ChinaHelicopterWZ10ME` | `CHI_WZ10ME` | YES (already present) |
| Z-19 Helicopter | NO | NO (Z-18 exists instead) | Z-18 `CHI_Z18A` only | NO Z-19 | **NO** | Packed `PLA\Airforce\Z18A.ini` is Z-18, not Z-19 | `ChinaHelicopterZ18A` is Z-18 | `CHI_Z18A` | **NO** for Z-19 |
| GJ-11 UCAV | NO | **YES** | **YES** | Packed already has it | **NO** | DATA `PLA\Drones\GJ11.ini` | `ChinaDroneGJ11` | `CHI_GJ11` | YES (already present) |
| WZ-8 Recon Drone | NO | Placeholder object only | NO WZ-8 mesh | NO | **NO** | DATA `PLA\China_System.ini` | `ChinaDroneWZ8` | `CHI_GJ11` | **NO** |
| CH-5 Drone | NO | **YES** | **YES** | Packed already has it | **NO** | DATA `PLA\Drones\CH5.ini` | `ChinaDroneCH5` | `CHI_CH5` | YES (already present) |
| Other CH drones | NO | Placeholders `ChinaDroneCH7`, `ChinaDroneFH97` | NO unique CH-7 mesh | NO | **NO** | DATA `PLA\China_System.ini` | `ChinaDroneCH7` / `FH97` | clones (`pla_gj11` / `pla_ch5` icons) | **NO** unique CH-7. CH-5 is the only real CH drone mesh |
| BZK-005 Drone | NO | NO | NO | NO (Type-92 vehicle `China92BZk.W3D` is not BZK-005) | **NO** | none | none | none | **NO** |
| Y-20 Tanker | NO | NO | NO | Possible `HXYun20YJ.W3D` | **NO** | Donor only; YJ identity not proven in INI | none | `HXYun20YJ` (unconfirmed) | **YES** only if that YJ mesh is accepted as tanker |
| MA60 Utility | NO | NO | NO | NO | NO | none | none | none | **NO** |

---

## Hidden Chinese assets in mod.z (complete)

mod.z does **not** hide J-11B, J-15, J-31, JF-17, J-8F, J-7, Y-20, KJ-500, KJ-2000, H-6, WZ-8, BZK-005, or CH drones.

What mod.z *does* contain for China air:

1. Stock ZH Helix + MiG (INI overlay; models live in base `W3DZH.big`, not in mod.z ART).
2. A fake `ChinaJetJ-10` using Su-37 / Tejas / Su-33 meshes.
3. `ChinaJetSu-34` (Russian Su-34).
4. General clones: Nuke/Infa/Art/EMP/CR MiG, J-10, Su-34, Helix.
5. `Art_ChinaJetTu-160`, `EMPNapalm_ChinaJetSu-47`, `Nuke_ChinaMig-25`.
6. China campaign movies `MD_China01_0.bik` … `05`.
7. China music tracks `CHI_01.mp3` … `CHI_10.mp3`.

No mod.z DATA BIG. No mod.z ART BIG. No aircraft W3D inside mod.z.

---

## Convert shortlist (donor ART + packed skeleton)

These are the requested missing types that **can** be converted later without inventing a mesh:

| Type | Donor W3D | Suggested existing skeleton (do not create now) |
|---|---|---|
| J-11B | `LSFJ11B.W3D` | `ChinaJetJ10C` or `ChinaJetJ20B_AG` |
| J-15 | `J15JZ.W3D` | same fighter skeleton |
| J-31 | `LSFJ31.W3D` | same (also the only FC-31/J-35 stand-in) |
| JF-17 | `CHJF17.W3D` / `LSFPKJF17.W3D` | same; discard F-16 overlay INI |
| J-8II | `CHJ8_2.W3D` / `LSFChinaJ8B.W3D` | same |
| J-7 | `LSFJ7.W3D` | same |
| J-10A / J-10B | `chj10a.W3D` / `ChJ10B.W3D` | `ChinaJetJ10C` |
| H-6K | `h6k.W3D` / `LSFCHNH6k.W3D` | `ChinaBomberH6M` |
| Y-20 | `HXYun20HXNew.W3D` | large transport/cargo jet skeleton |

Cannot convert from existing assets: unique J-35, Chinese Su-35, H-20, Y-9, unique KJ-500, KJ-2000 mesh, Z-19, unique WZ-8, BZK-005, MA60, unique CH-7.

## Not done

- No CommandSet created or edited
- No INI created or edited
- No ART packed
- No in-game click test
