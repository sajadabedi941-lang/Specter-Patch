# China aircraft inventory (scan only)

Date: 2026-08-24  
Scope: read-only audit. No INI, ART, CommandSet, or gameplay files were modified.

## Sources scanned

| Source | Path / archive | Result |
|---|---|---|
| Current DATA BIG | `/tmp/russia_four_fighters/_SPEC_DATA_ONE.big` (SHA256 `50d09d4939f87f13a3932b9c8dcc22b98c5bed92768ccb03309a6201cf2b3c7c`) | 2565 files. PLA Airforce/Drones/Science INI present. |
| Current ART BIG | `/tmp/russia_four_fighters/_SPEC_ART_ONE.big` (SHA256 `5acbdb350f2ae2298882ab0463426a53829fb00ab29a952a46f13b95cc319bf8`) | 2915 files. Dedicated `CHI_*` / `PLA_*` aircraft meshes for a subset of PLA air units. |
| Original DATA BIG | `/tmp/russia_su35s_ka52/_SPEC_DATA_ONE.big` | Same PLA aircraft INI set as current DATA (PLA was already in the Specter DATA pack). |
| art_data RAR | `/workspace/art_data.part01.rar` … `part22.rar` | Contains older `_SPEC_ART_ONE.big` + `_SPEC_DATA_ONE.big` only. No extra unique China meshes beyond the DATA/ART BIGs. |
| Donor ART pack | `/workspace/DONOR_Art.part001.rar` … `part069.rar` (23126 files) | Many extra China W3D/textures **not** in the packed ART BIG. |
| Donor INI | `/workspace/DONOR_INI.rar` | No China/PLA aircraft Object INI. Extracted content is CommandButton/CommandSet + `Russia.ini` only. |
| Workspace overlay INI | `/workspace/patch/Data/INI/Object/Specter/PLA/` and `Pakistan Armed Forces/Airforce/` | PLA overlay folder has no extra fighters. Pakistan `Pakistan_JF17.ini` / `Pakistan_JF17BlockIII.ini` exist but are **not packed** into current DATA BIG and use an F-16 mesh. |
| mod.zip | `/workspace/mod.zip` | Audio/sounds split zip. No China aircraft INI or W3D. |
| Base-game remnants inside DATA | `Data\INI\Object\ChinaAir.ini`, `ChinaAirfieldCommandSet` | Helix module objects only. `Command_ConstructChinaJetMIG` is still referenced; **no `ChinaJetMIG` Object definition** was found in packed DATA. |

“Exists in current game” means a unique Object definition is in the packed DATA BIG **and** it uses a dedicated matching W3D that is in the packed ART BIG (not a clone of a different aircraft).

“Can be added easily” means dedicated W3D + textures already exist in packed ART **or** donor ART, so an isolated overlay INI could be written without inventing a mesh. It does **not** mean CommandSet work was done.

---

## Fighters

| Aircraft | Exists in current game? | Found in | Exact INI object name | Exact ART object name (W3D) | Model / texture availability | Can be added easily? |
|---|---|---|---|---|---|---|
| J-20 Mighty Dragon | **YES** | DATA BIG + ART BIG | `ChinaJetJ20B_AG`, `ChinaJetJ20B_AA`, `ChinaJetJ20B_AA_AI` | `CHI_J20B` / `CHI_J20B_D` / `CHI_J20B_R` | Packed textures `PLA_J20.dds` (+ D/R). Icons `pla_j20b`. Extra donor meshes `LSFJ20.W3D`, `AGMZCNJ20X.W3D`. | **YES** (already present) |
| J-35 / FC-31 | **NO** | not found (no unique INI or W3D named J-35/FC-31) | none | none | Placeholder `ChinaJetJ50` exists in `China_System.ini` but reuses `CHI_J20B`. No J-35/FC-31 mesh in packed ART or donor ART. | **NO** (no dedicated mesh; J-31 donor art is the closest family stand-in) |
| J-16 | **YES** (J-16D EW variant) | DATA BIG + ART BIG | `ChinaJetJ16D` | `Chi_J16D` | Packed `Chi_J16D.W3D` + `Chi_J16D.dds`. Icon `pla_j16d`. Strike J-16 is not a separate object. `ChinaJetJ16B_Bunker` is a J-20 clone (`CHI_J20B`). | **YES** (J-16D already present). Unique strike J-16: **NO** (no dedicated mesh) |
| J-10C | **YES** | DATA BIG + ART BIG | `ChinaJetJ10C` | `CHI_J10C` / `CHI_J10C_D` / `CHI_J10C_R` | Packed `PLA_J10C.dds` (+ D/R). Icon `pla_j10c`. | **YES** (already present) |
| J-11B | **NO** | donor ART only | none in packed DATA | Donor: `LSFJ11B.W3D` / `LSFJ11Bd.W3D` / `LSFJ11Bk.W3D`, `CHJ11_r.W3D` | Donor textures `LSFJ11B.dds`, `J11B.tga`, `J11A.tga`. Not in packed ART BIG. | **YES** (donor W3D + textures; needs overlay INI) |
| J-15 Flying Shark | **NO** | donor ART only | none in packed DATA | Donor: `J15JZ.W3D` | Donor textures `AGMZJ15.dds`, `CHNJ15A.tga`, `CHNJ15ATB.tga`. Not in packed ART BIG. | **YES** (donor W3D + textures; needs overlay INI) |
| J-10B | **NO** (no unique PLA object) | donor ART; some non-PLA clones reuse J-10C | none unique. Other factions clone J-10C as `JapanJetJ10B` / `NorthKoreaJetJ10B` / `VietnamJetJ10B` using `CHI_J10C` | Donor unique: `ChJ10B.W3D` | Donor `CHJ10B.dds`, `ChinaJ10BIm.tga`. Packed game uses J-10C mesh for those clones. | **YES** (donor J-10B W3D + textures; needs overlay INI) |
| JH-7A Flying Leopard | **YES** (as JH-7A2) | DATA BIG + ART BIG | `ChinaJetJH7A2` | `CHI_JH7A2` / `CHI_JH7A2D` / `CHI_JH7A2R` | Packed `PLA_JH7A.dds` (+ D/R). Icon `pla_jh7a2`. Donor extra: `CHJH7A.W3D`. `ChinaJetJH7B_HeavyBunker` reuses this mesh. | **YES** (already present) |
| J-8F | **NO** | donor ART only (J-8II family, not named J-8F) | none | Donor: `CHJ8_2.W3D`, `LSFChinaJ8B.W3D` / `LSFChinaJ8Bd.W3D` | Donor textures `chj8_2.dds`, `LSFChinaJ8B.dds`. No packed ART. | **YES** as J-8II stand-in (donor mesh). **NO** as a uniquely named J-8F mesh |
| JF-17 Block 3 / FC-1 | **NO** in packed DATA | donor ART + workspace overlay INI (not packed) | Overlay only (not in DATA BIG): `Pakistan_JF17`, `Pakistan_JF17BlockIII` | Overlay models are **wrong**: `US_F16D_B52`. Donor real meshes: `CHJF17.W3D`, `LSFPKJF17.W3D` (+ d/k/r) | Donor textures `LSFJF17.dds`, `jf17China.tga`, `JF17TB.tga`. Overlay portraits are `us_f16c`. | **YES** (donor JF-17 W3D + textures). Current overlay INI cannot be used as-is (F-16 mesh) |
| J-31 | **NO** | donor ART only | none | Donor: `LSFJ31.W3D` / `LSFJ31d.W3D` / `LSFJ31k.W3D`, `CHAJ31HXNew.W3D` | Donor textures `LSFJ31.dds`, `J31TB.tga`, `CHA_J31A.dds`, `autreJ31.tga`. Not in packed ART. | **YES** (donor W3D + textures; needs overlay INI) |
| Su-35 Chinese version | **NO** | not found | none. Old `ChinaAirfieldCommandSet` still calls `Command_ConstructRussian_Su35` (Russian object, not a PLA Su-35) | Russian/Egypt Su-35 only: packed `RUS_SU35S.W3D`; donor `LSFSU35.W3D`, `AGMZSU35BM.W3D` | No PLA/Chinese Su-35 skin or object. | **NO** as a unique Chinese Su-35. A reskin of existing Russian Su-35 would still need a Chinese texture that was not found |
| H-20 (if classified as aircraft) | **NO** | not found | none | none real. `PTBush20.W3D` is a bush. `LSFzh2000.W3D` is PzH 2000 artillery, not H-20 | No H-20 bomber mesh or texture. | **NO** |
| J-7 / J-10A | **NO** | donor ART only | none | J-7 donor: `LSFJ7.W3D` / `LSFJ7d.W3D` / `LSFJ7k.W3D`. J-10A donor: `chj10a.W3D`, `BJSTJ10A.W3D` | J-7 textures `CHJ7.dds`, `LSFJ7K.dds`. J-10A textures `CHJ10A.dds`, `BJ10A.dds`. Not packed. | **YES** (both have donor W3D + textures; need overlay INI) |

---

## Large aircraft

| Aircraft | Exists in current game? | Found in | Exact INI object name | Exact ART object name (W3D) | Model / texture availability | Can be added easily? |
|---|---|---|---|---|---|---|
| H-20 Bomber | **NO** | not found | none | none | No bomber mesh. Do not treat `LSFzh2000` or `PTBush20` as H-20. | **NO** |
| H-6K / H-6N | **YES** as H-6M science bomber; **NO** as unique H-6K/H-6N objects | DATA BIG + ART BIG (H-6M). Donor ART has H-6K | Packed: `ChinaBomberH6M`. No `H6K`/`H6N` Object | Packed: `CHI_H6M` / `CHI_H6M_D` / `CHI_H6M_R`. Donor H-6K: `h6k.W3D`, `LSFCHNH6k.W3D` | Packed `PLA_H6M.dds`. Donor `CHNH6K.tga`, `h6k.dds`, `LSFCHNH6k.tga`. H-6M is a science object (`Science Objects\H6M.ini`), not a standard airbase jet. | H-6M already present. Unique H-6K: **YES** (donor W3D). Unique H-6N: **NO** (no H-6N mesh) |
| Y-20 Transport | **NO** | donor ART only | none | Donor: `HXYun20HXNew.W3D` | Donor icons/textures `CHNY20.tga`, `CHNY20TB.tga`. Not packed. | **YES** (donor W3D + textures; needs overlay INI) |
| Y-9 Transport | **NO** | not found | none | none | No Y-9 W3D/texture. | **NO** |
| KJ-500 AWACS | **NO** as unique KJ-500 art | DATA BIG object only (placeholder mesh) | `ChinaAircraftKJ500` in `China_System.ini` | Uses **Russian** `RUS_A50` | Button image `rus_a50`. CommandSet `ChinaKJ500CommandSet` exists. No KJ-500 W3D in packed ART or donor ART. | **NO** (object exists, but there is no KJ-500 mesh; it is an A-50 stand-in) |
| KJ-2000 AWACS | **NO** | donor textures only | none | no W3D | Donor icons `CHNKJ2000.tga`, `CHNKJ2000TB.tga`, `chinakj200.tga`. No matching W3D. | **NO** (icon art only) |
| WZ-10 Helicopter | **YES** (WZ-10ME) | DATA BIG + ART BIG | `ChinaHelicopterWZ10ME` | `CHI_WZ10ME` / `CHI_WZ10ME_D` / `CHI_WZ10ME_R` (+ turret `WZ10Turret`) | Packed `PLA_WZ10ME.dds`. Icon `pla_wz10me`. Extra donor `LSFWZ10.W3D`. | **YES** (already present) |
| Z-19 Helicopter | **NO** | not found | none | none | Packed has `ChinaHelicopterZ18A` / `CHI_Z18A` (Z-18, not Z-19). No Z-19 mesh. | **NO** |
| GJ-11 UCAV | **YES** | DATA BIG + ART BIG | `ChinaDroneGJ11` | `CHI_GJ11` / `CHI_GJ11D` / `CHI_GJ11R` | Packed `PLA_GJ11.dds`. Icon `pla_gj11`. Launcher object `ChinaVehicleGJ11Launcher` (`CHI_GJ11L`). | **YES** (already present) |
| WZ-8 Recon Drone | **NO** as unique WZ-8 art | DATA BIG object only (placeholder mesh) | `ChinaDroneWZ8` in `China_System.ini` | Uses `CHI_GJ11` (GJ-11 mesh) | CommandSet `ChinaWZ8ReconCommandSet` exists. Button uses `pla_asn301`. No WZ-8 W3D in packed ART or donor ART. | **NO** (placeholder only; no WZ-8 mesh) |
| CH-5 Drone | **YES** | DATA BIG + ART BIG | `ChinaDroneCH5` | `CHI_CH5` / `CHI_CH5D` / `CHI_CH5R` | Packed `PLA_CH5.dds`. Icon `pla_ch5`. | **YES** (already present) |
| BZK-005 Drone | **NO** | not found | none | none | Donor `China92BZk.W3D` / `LSF92BZk.W3D` are ground Type-92 style objects, not BZK-005. | **NO** |
| Y-20 Tanker | **NO** | possible donor mesh only | none | Donor possible tanker/boom mesh: `HXYun20YJ.W3D` | Same `CHNY20` textures as transport. Not packed. Identity of `YJ` mesh is not proven in INI. | **YES** only if `HXYun20YJ.W3D` is accepted as the tanker mesh; otherwise **NO** |
| MA60 Utility Aircraft | **NO** | not found | none | none | No MA60 W3D/texture. | **NO** |

---

## Already on PLA air menus (for context only; CommandSet was not changed)

Packed `PLAAirfieldCommandSet` / `China_LargeAirBaseCommandSet` / `China_HeavyAirBaseCommandSet` already reference:

- `ChinaJetJ20B_AG`, `ChinaJetJ20B_AA`, `ChinaJetJ20B_AA_AI`
- `ChinaJetJ10C`, `ChinaJetJ16D`
- `ChinaJetJH7A2`
- `ChinaHelicopterWZ10ME`, `ChinaHelicopterZ18A`
- Placeholder clones: `ChinaJetJ50` (J-20 mesh), `ChinaJetJ16B_Bunker` (J-20 mesh), `ChinaJetJH7B_HeavyBunker` (JH-7A2 mesh), `ChinaAircraftKJ500` (A-50 mesh)

Old `ChinaAirfieldCommandSet` still mixes stock Helix / MIG construct commands with Russian aircraft. That is leftover wiring, not a Chinese Su-35.

---

## Extra PLA air objects found (not on the requested list)

| Object | Model | Notes |
|---|---|---|
| `ChinaHelicopterZ18A` | `CHI_Z18A` | Packed unique Z-18 transport helicopter |
| `ChinaDroneAsn301` | `Irn_Shahed136` | Packed; Iranian Shahed mesh |
| `ChinaDroneCH7`, `ChinaDroneJXDS`, `ChinaDroneFH97` | clones in `China_System.ini` | Placeholder drones, not unique meshes |
| `ChinaJetMIGNapalmStriker` | weapon object | Not an aircraft |

---

## Easy-add shortlist (donor ART exists, not currently a unique packed unit)

1. J-11B — `LSFJ11B.W3D`
2. J-15 — `J15JZ.W3D`
3. J-10B — `ChJ10B.W3D`
4. J-10A — `chj10a.W3D`
5. J-7 — `LSFJ7.W3D`
6. J-31 — `LSFJ31.W3D` (also the only practical stand-in for FC-31/J-35)
7. JF-17 — `CHJF17.W3D` / `LSFPKJF17.W3D` (do not use the current F-16 overlay INI)
8. J-8II — `CHJ8_2.W3D` / `LSFChinaJ8B.W3D`
9. H-6K — `h6k.W3D` / `LSFCHNH6k.W3D`
10. Y-20 transport — `HXYun20HXNew.W3D`

Cannot add from existing assets: J-35 unique mesh, Chinese Su-35, H-20, Y-9, KJ-500 unique mesh, KJ-2000 mesh, Z-19, WZ-8 unique mesh, BZK-005, MA60.

## Not done

- No CommandSet edits
- No INI edits
- No ART edits
- No in-game click test
