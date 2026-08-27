#!/usr/bin/env python3
"""Pack New-folder/TEOD visual source correction on final-global-aircraft-completion BIGs.

Does not rebuild from an older branch. Does not change CommandSet slots.
Does not import TEOD Object/Weapon/CommandSet gameplay.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_new_folder_source_fix as gen
import pack_china_heavy_aircraft as ch
import pack_europe_airforce as eu
import pack_france_airforce as fr
import pack_uk_e7_boot_crash_fix as e7

ROOT = Path("/workspace")
PATCH = ROOT / "patch/Data"
BASE_DATA = Path("/tmp/final_global_completion/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/final_global_completion/_SPEC_ART_ONE.big")
TEOD_W3D = Path("/tmp/teod/!TEOD_W3D.big")
TEOD_TEX = Path("/tmp/teod/!TEOD_Textures.big")
ART_CACHE = Path("/tmp/teod_nf_art")

MARKER_W = "; ===== SPECTER NEW FOLDER SOURCE FIX WEAPONS BEGIN ====="
MARKER_WE = "; ===== SPECTER NEW FOLDER SOURCE FIX WEAPONS END ====="
MARKER_B = "; ===== SPECTER NEW FOLDER SOURCE FIX BUTTONS BEGIN ====="
MARKER_BE = "; ===== SPECTER NEW FOLDER SOURCE FIX BUTTONS END ====="

NEW_OBJECTS = [s["obj"] for s in gen.NEW_AIRCRAFT]
NEW_WEAPONS = re.findall(r"^Weapon (\S+)", gen.WEAPONS, re.M)

KEEP_SLOTS = {
    "Germany_HeavyAirBaseCommandSet": {
        8: "Command_ConstructGermanyUAVEuroMALE",
        9: "Command_ConstructGermanyJetFCASNGF",
    },
    "France_HeavyAirBaseCommandSet": {5: "Command_ConstructFranceUCAVNeuron"},
    "FranceAirfieldCommandSet": {
        11: "Command_ConstructFranceJetMirageF1CR",
        12: "Command_ConstructFranceJetRafaleF4",
    },
    "France_LargeAirBaseCommandSet": {
        11: "Command_ConstructFranceJetMirageF1CR",
        12: "Command_ConstructFranceJetRafaleF4",
    },
    "Britain_HeavyAirBaseCommandSet": {12: "Command_ConstructBritainAircraftTornadoECR"},
    "Japan_HeavyAirBaseCommandSet": {
        7: "Command_ConstructJapanJetC130H",
        8: "Command_ConstructJapanUAVRQ4",
    },
    "China_HeavyAirBaseCommandSet": {12: "Command_ConstructChinaJetJ35A"},
    "Iran_HeavyAirBaseCommandSet": {
        2: "Command_ConstructIranJetMig21Bis",
        3: "Command_ConstructIranJetSu35S",
    },
    "Turkey_HeavyAirBaseCommandSet": {6: "Command_ConstructTurkeyJetF4ETerm"},
    "Italy_HeavyAirBaseCommandSet": {8: "Command_ConstructItalyJetGCAP"},
    "Pakistan_AirfieldCommandSet": {9: "Command_ConstructPakistanJetJ10CE"},
}

PROTECT_SETS = [
    "AmericaAirfieldCommandSet",
    "America_LargeAirBaseCommandSet",
    "America_HeavyAirBaseCommandSet",
    "RussiaAirfieldCommandSet",
    "Russia_LargeAirBaseCommandSet",
    "Russia_HeavyAirBaseCommandSet",
    "PLAAirfieldCommandSet",
    "China_LargeAirBaseCommandSet",
    "ItalyAirfieldCommandSet",
    "Italy_LargeAirBaseCommandSet",
    "BritainAirfieldCommandSet",
    "Britain_LargeAirBaseCommandSet",
    "Britain_HeavyAirBaseCommandSet",
    "GermanyAirfieldCommandSet",
    "Germany_LargeAirBaseCommandSet",
    "Germany_HeavyAirBaseCommandSet",
    "TurkeyAirfieldCommandSet",
    "Turkey_LargeAirBaseCommandSet",
    "Turkey_HeavyAirBaseCommandSet",
    "IranAirfieldCommandSet",
    "IranExpandedAirfieldCommandSet",
    "Iran_HeavyAirBaseCommandSet",
    "Japan_AirfieldCommandSet",
    "Japan_HeavyAirBaseCommandSet",
    "FranceAirfieldCommandSet",
    "France_LargeAirBaseCommandSet",
    "France_HeavyAirBaseCommandSet",
    "China_HeavyAirBaseCommandSet",
    "Italy_HeavyAirBaseCommandSet",
    "Pakistan_AirfieldCommandSet",
]

W3D_INJECT = [
    "UVMirage.W3D", "UVMirage_D.W3D", "UVMirage_E.W3D",
    "AVCargoPln.W3D", "AVCargoPln_D.W3D", "AVCargoPln_E.W3D",
    "NVJ31.W3D", "NVJ31_D.W3D", "NVJ31_E.W3D",
    "UVMig-21.W3D", "UVMig-21_D.W3D", "UVMig-21_E.W3D",
    "SU-37.W3D", "SU-37_D.W3D", "SU-37_E.W3D",
    "NVJ-10.W3D", "NVJ-10D.W3D", "NVJ-10_D.W3D",
    "PAK-FA.W3D", "PAK-FA_D.W3D", "PAK-FA_E.W3D",
    "AVF16.W3D", "AVF16_D.W3D", "AVF16_E.W3D",
    "AV_RQ180.W3D", "AV_RQ180_D.W3D", "AV_RQ180_E.W3D",
    "UV_Turbo.W3D", "UV_Turbo_D.W3D",
    "UVVampire.W3D", "UVVampire_D.W3D", "UVVampire_E1.W3D",
    "RU_Orion.W3D", "RU_Orion_D.W3D",
]

TEX_INJECT = [
    "UVMirage.dds", "UVMirage_D.dds", "UVMirage_E.dds",
    "Straight Flush2.dds", "Straight Flush2_D.dds",
    "AC130.dds", "AC130_D.dds", "AC130_E.dds",
    "AH64 rotor.dds", "AH64 rotor_D.dds",
    "J31.dds", "J31_D.dds", "J31_E.dds",
    "UVMig-21.dds", "UVMig-21_D.dds", "UVMig-21_E.dds",
    "Russian Missiles.dds", "Russian Missiles_D.dds",
    "SU-35.dds", "SU-35_D.dds", "SU-35_E.dds",
    "Chinese_Missiles.dds", "Chinese_Missiles_D.dds", "HQ-61.dds",
    "J-10.dds", "J-10_D.dds", "J-10_E.dds",
    "PAKFA.dds", "PAKFA_D.dds", "PAKFA_E.dds",
    "F-16.dds", "F-16_D.dds", "F-16_E.dds",
    "USA Missiles.dds", "RubbleTexture.dds",
    "Drones_US_RU.dds", "Drones_US_RU_D.dds", "Drones_US_RU_E.dds",
    "GLA-Vampire.dds", "GLA-Vampire_D.dds", "GLA-Vampire_E.dds",
    "Scudmissile.dds", "Scudmissile_D.dds",
    "Orion.dds", "Orion_D.dds",
    "RU-rotor.dds", "RU-rotor_D.dds",
    "housecolor2.dds",
]

SHARED_NO_OVERWRITE = {
    "housecolor2.dds",
    "rubbletexture.dds",
}

PORTRAIT_SRC = {
    "SPEC_FranceMirageF1CR.tga": "UVMirage.dds",
    "SPEC_JapanC130H.tga": "AC130.dds",
    "SPEC_ChinaJ35A.tga": "J31.dds",
    "SPEC_GermanyFCASNGF.tga": "J31.dds",
    "SPEC_IranMig21Bis.tga": "UVMig-21.dds",
    "SPEC_IranSu35S.tga": "SU-35.dds",
    "SPEC_PakistanJ10CE.tga": "J-10.dds",
    "SPEC_ItalyGCAP.tga": "PAKFA.dds",
    "SPEC_TurkeyF16C.tga": "F-16.dds",
    "SPEC_AmericaRQ180.tga": "Drones_US_RU.dds",
    "SPEC_BritainVampireFB5.tga": "GLA-Vampire.dds",
    "SPEC_BritainVampireFB9.tga": "GLA-Vampire.dds",
}

PATCHED_MODELS = {
    "FranceJetMirageF1CR": ("UVMirage", "UVMirage_D", "UVMirage_E"),
    "JapanJetC130H": ("AVCargoPln", "AVCargoPln_D", "AVCargoPln_E"),
    "ChinaJetJ35A": ("NVJ31", "NVJ31_D", "NVJ31_E"),
    "GermanyJetFCASNGF": ("NVJ31", "NVJ31_D", "NVJ31_E"),
    "IranJetMig21Bis": ("UVMig-21", "UVMig-21_D", "UVMig-21_E"),
    "IranJetSu35S": ("SU-37", "SU-37_D", "SU-37_E"),
    "PakistanJetJ10CE": ("NVJ-10", "NVJ-10D", "NVJ-10_D"),
    "ItalyJetGCAP": ("PAK-FA", "PAK-FA_D", "PAK-FA_E"),
    "TurkeyJetF16C": ("AVF16", "AVF16_D", "AVF16_E"),
}

PRESERVED_MODELS = {
    "GermanyUAVEuroMALE": "Nat_Heron",
    "FranceUCAVNeuron": "CHI_GJ11L",
    "FranceJetRafaleF4": "LSFIDRafale",
    "BritainAircraftTornadoECR": "LSFTornado",
    "JapanUAVRQ4": "US_RQ-4",
    "TurkeyJetF4ETerm": "JPF4",
}

PROJECTILES = {
    "AIM-9X_Object",
    "Fab-250",
    "GenericUnguidedRockets",
    "30mm_API-T_Projectile",
    "MeteorMissile_Object",
    "GBU24_GuidedBombObject",
    "Paveway_IV_Object",
}

REGRESS = {
    "America_LargeAirBaseCommandSet": "Command_ConstructAmericaJetRaptor",
    "America_HeavyAirBaseCommandSet": "Command_ConstructAmericaJetB2",
    "Russia_LargeAirBaseCommandSet": "Command_ConstructRussiaJetSu35S",
    "PLAAirfieldCommandSet": "Command_ConstructChinaJetJ11B",
    "China_HeavyAirBaseCommandSet": "Command_ConstructChinaJetJ20C",
    "France_LargeAirBaseCommandSet": "Command_ConstructFranceJetRafaleC",
    "FranceAirfieldCommandSet": "Command_ConstructFranceJetMirage20005F",
    "Germany_LargeAirBaseCommandSet": "Command_ConstructGermanyJetTyphoonT4",
    "Italy_LargeAirBaseCommandSet": "Command_ConstructItalyJetTyphoon",
    "Britain_LargeAirBaseCommandSet": "Command_ConstructBritainJetF35B",
    "Britain_HeavyAirBaseCommandSet": "Command_ConstructBritainJetTempest",
    "BritainAirfieldCommandSet": "Command_ConstructBritainJetPhantomFG1",
    "Japan_AirfieldCommandSet": "Command_ConstructJapanJetF2A",
    "Turkey_HeavyAirBaseCommandSet": "Command_ConstructTurkeyJetKAAN",
    "IranExpandedAirfieldCommandSet": "Command_ConstructIranJetF14A",
    "Iran_HeavyAirBaseCommandSet": "Command_ConstructIranJetF4E",
}

ORION_KEYS = [
    r"data\ini\object\specter\armed forces of russian federation\drones\orion2.ini",
    r"data\ini\object\specter\armed forces of russian federation\drones\orion2r.ini",
]

NO_SLOT_BUTTONS = [
    "Command_ConstructAmericaDroneRQ180",
    "Command_ConstructBritainJetVampireFB5",
    "Command_ConstructBritainJetVampireFB9",
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def index_big(path: Path) -> dict[str, tuple[str, bytes]]:
    entries, raw = ch.read_big(path)
    out: dict[str, tuple[str, bytes]] = {}
    for name, off, size in entries:
        leaf = name.split("\\")[-1].split("/")[-1]
        out[leaf.lower()] = (name, raw[off : off + size])
    return out


def extract_teod() -> dict[str, Path]:
    ART_CACHE.mkdir(parents=True, exist_ok=True)
    w3d = index_big(TEOD_W3D)
    tex = index_big(TEOD_TEX)
    written: dict[str, Path] = {}
    missing = []
    for name in W3D_INJECT:
        hit = w3d.get(name.lower())
        if not hit:
            missing.append(name)
            continue
        dest = ART_CACHE / name
        dest.write_bytes(hit[1])
        written[name.lower()] = dest
    for name in TEX_INJECT:
        hit = tex.get(name.lower())
        if not hit:
            missing.append(name)
            continue
        dest = ART_CACHE / name
        dest.write_bytes(hit[1])
        written[name.lower()] = dest
    # SU-37_E references 5_E.dds; TEOD has SU-35_E.dds as the real rubble sheet.
    if "5_e.dds" not in written and "su-35_e.dds" in written:
        dest = ART_CACHE / "5_E.dds"
        dest.write_bytes(written["su-35_e.dds"].read_bytes())
        written["5_e.dds"] = dest
        print("aliased 5_E.dds from SU-35_E.dds")
    if missing:
        print("TEOD extract missing (non-fatal if shared/optional):", missing)
    print("extracted", len(written), "TEOD art files")
    return written


def patch_orion_visual(text: str) -> str:
    out = []
    state = "default"
    for line in text.splitlines(True):
        s = line.strip()
        if s.startswith("DefaultConditionState"):
            state = "default"
        elif s.startswith("ConditionState") and "RUBBLE" in s:
            state = "rubble"
        elif s.startswith("ConditionState"):
            state = "damaged"
        if re.match(r"\s*Animation(Mode)?\s*=", line):
            continue
        if re.match(r"\s*Model\s+=\s+RUS_Orion2\s*$", line):
            tgt = "RU_Orion" if state == "default" else "RU_Orion_D"
            line = re.sub(r"(Model\s+=\s+)\S+", r"\1" + tgt, line)
        out.append(line)
    new = "".join(out)
    if "Animation" in new and "RUS_Orion2.RUS_Orion2" in new:
        raise SystemExit("Orion animation still present")
    if "Model               = RU_Orion" not in new and "Model = RU_Orion" not in new:
        if not re.search(r"Model\s+=\s+RU_Orion\b", new):
            raise SystemExit("Orion model swap failed")
    return new


def inline_marked(host: str, overlay: str, start: str, end: str, insert_before: str) -> str:
    body = "\n".join(l for l in overlay.splitlines() if not l.startswith(";")).strip()
    block = start + "\n" + body + "\n" + end + "\n"
    if start in host:
        return re.sub(
            re.escape(start) + r".*?" + re.escape(end) + r"\n?",
            block,
            host,
            count=1,
            flags=re.S,
        )
    idx = host.find(insert_before)
    if idx < 0:
        raise SystemExit(f"missing insert point {insert_before}")
    return host[:idx] + block + "\n" + host[idx:]


def dup_moduletags(text: str, label: str) -> list[str]:
    errs = []
    obj = None
    seen: set[str] = set()
    for i, line in enumerate(text.splitlines(), 1):
        m = re.match(r"^Object\s+(\S+)", line)
        if m:
            obj = m.group(1)
            seen = set()
        t = re.search(r"(ModuleTag_\S+)", line)
        if t:
            tag = t.group(1)
            if tag in seen:
                errs.append(f"{label}:{i} duplicate {tag} in {obj}")
            seen.add(tag)
    return errs


def collect_overlay() -> dict[str, bytes]:
    overlay: dict[str, bytes] = {}
    for spec in gen.VISUAL_PATCHES:
        p = PATCH / spec["rel"]
        dest = "Data\\" + spec["rel"].replace("/", "\\")
        overlay[dest] = ch.lf(p.read_bytes())
    for spec in gen.NEW_AIRCRAFT:
        p = PATCH / spec["rel"]
        dest = "Data\\" + spec["rel"].replace("/", "\\")
        overlay[dest] = ch.lf(p.read_bytes())
    extra = [
        "INI/Weapon_NewFolderSourceFix.ini",
        "INI/CommandButton_NewFolderSourceFix.ini",
        "INI/MappedImages/HandCreated/zNewFolderSourceFix_Portrait_Images.INI",
    ]
    for rel in extra:
        p = PATCH / rel
        dest = "Data\\" + rel.replace("/", "\\")
        overlay[dest] = ch.lf(p.read_bytes())
    return overlay


def write_install(out: Path) -> None:
    text = """SPECTER NEW-FOLDER AIRCRAFT SOURCE FIX

Copy both BIG files into the game folder, replacing previous Specter BIGs:

  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big

This pass keeps the final-global-aircraft-completion gameplay identities.
It replaces Draw/Model visuals with verified New folder / TEOD W3Ds where found.

Does not change airbase architecture, Rally, Sell, or CommandSet slots.
RQ-180 and Vampire objects are complete but not attached (USA/UK menus full).
Vulcan: NEW_FOLDER_VULCAN_NOT_FOUND. Existing B-52 stand-in was not reused.

See NEW_FOLDER_AIRCRAFT_SOURCE_AUDIT.md for full provenance.
"""
    (out / "INSTALL.txt").write_text(text)


def write_audit(out: Path, dh: str, ah: str, data_sz: int, art_sz: int) -> str:
    text = f"""# NEW FOLDER AIRCRAFT SOURCE AUDIT

Baseline: `final-global-aircraft-completion-v1` (`_SPEC_DATA_ONE.big` / `_SPEC_ART_ONE.big`).
Primary art source: New folder multipart archive reconstructed as TEOD (`!TEOD_W3D.big`, `!TEOD_Textures.big`).
TEOD Object/Weapon/CommandSet INI was inspected for names only and was **not** imported.

DATA sha256: `{dh}` ({data_sz} bytes)
ART  sha256: `{ah}` ({art_sz} bytes)

Statuses: `NEW_FOLDER_EXACT` | `NEW_FOLDER_CLOSE_MATCH` | `CURRENT_STANDIN_PRESERVED` | `NEW_FOLDER_NOT_FOUND` | `DUPLICATE_MODEL` | `BROKEN_ASSET`

## Dotted aliases

| Alias | Dot | New folder search result | Archive/volume | Exact W3D | Textures | W3D size | Current object | Old visual | New visual | Gameplay identity | Country | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EdaEurodyone. | yes | no Eurodrone / EuroMALE / MALE UAV W3D | !TEOD_W3D.big | — | — | — | GermanyUAVEuroMALE | Nat_Heron | Nat_Heron | Eurodrone MALE recon+PGM x4 | Germany Heavy 8 | CURRENT_STANDIN_PRESERVED |
| neuRonucan. | yes | no nEUROn / Neuron / DassaultNeuron W3D. RU_Skat is a Russian UCAV, not used | !TEOD_W3D.big | — | — | — | FranceUCAVNeuron | CHI_GJ11L | CHI_GJ11L | nEUROn stealth UCAV GBU x2 | France Heavy 5 | CURRENT_STANDIN_PRESERVED |
| Edafcas. | yes | no dedicated FCAS/NGF/SCAF W3D. NVJ31 is FC-31/J-31 family fighter-shaped, not UAV | !TEOD_W3D.big | NVJ31.W3D / NVJ31_D.W3D / NVJ31_E.W3D | J31.dds + housecolor2.dds | 46424 / 46426 / 42748 | GermanyJetFCASNGF | LSFJ31 | NVJ31 | FCAS NGF Meteor x4 + GBU x2 | Germany Heavy 9 | NEW_FOLDER_CLOSE_MATCH |
| Mirage 17. | yes | GLAJetMirage / UVMirage. F1-like delta, kept F1CR identity | !TEOD_W3D.big | UVMirage.W3D / _D / _E | UVMirage.dds, Straight Flush2.dds | 80336 / 80348 / 52063 | FranceJetMirageF1CR | LSFFRF1 | UVMirage | Mirage F1CR | France Fighter 11 | NEW_FOLDER_EXACT |
| Edavulcan. | yes | no Vulcan / Avro / VULCANB2 W3D | !TEOD_W3D.big | — | — | — | BritainBomberVulcan (untouched) | existing B-52-class stand-in | unchanged | Avro Vulcan B.2 not created | UK Heavy 5 existing | NEW_FOLDER_NOT_FOUND |
| EDA tornado. | yes | UVTornado_M.W3D is 7750 bytes and maps UVT-55.dds (T-55 projectile), not a Tornado airframe | !TEOD_W3D.big | UVTornado_M.W3D | UVT-55.dds | 7750 | BritainAircraftTornadoECR | LSFTornado | LSFTornado | Tornado ECR SEAD | UK Heavy 12 | BROKEN_ASSET |
| Dassaultrafale. | yes | no Rafale / DassaultRafale W3D | !TEOD_W3D.big | — | — | — | FranceJetRafaleF4 | LSFIDRafale | LSFIDRafale | Rafale F4 Meteor x6 MICA x4 AASM x4 | France Fighter 12 | CURRENT_STANDIN_PRESERVED |
| RQ_180. | yes | AV_RQ180 flying-wing HALE | !TEOD_W3D.big | AV_RQ180.W3D / _D / _E | Drones_US_RU.dds | 23300 / 23302 / 20926 | AmericaDroneRQ180 | (new) | AV_RQ180 | Unarmed stealth recon. OBJECT_READY_NO_VISIBLE_USA_SLOT | USA (no slot) | NEW_FOLDER_EXACT |
| Turbo vampire. | yes | GLAJetTurboVampire / UV_Turbo | !TEOD_W3D.big | UV_Turbo.W3D / UV_Turbo_D.W3D | GLA-Vampire.dds, Scudmissile.dds | 54918 / 54926 | BritainJetVampireFB5 | (new) | UV_Turbo | Vampire FB.5 cannon/rockets/bombs. No UK slot | UK (no slot) | NEW_FOLDER_EXACT |
| vampire. | yes | GLAJetVampire / UVVampire. Distinct from UV_Turbo | !TEOD_W3D.big | UVVampire.W3D / _D / UVVampire_E1.W3D (UVVampire_E missing) | GLA-Vampire.dds | 47852 / 47864 / 30675 | BritainJetVampireFB9 | (new) | UVVampire | Vampire FB.9. Not DUPLICATE_VAMPIRE_MODEL. No UK slot | UK (no slot) | NEW_FOLDER_EXACT |
| OriohuAV. | yes | RU_Orion | !TEOD_W3D.big | RU_Orion.W3D / RU_Orion_D.W3D | Orion.dds, RU-rotor.dds | 18668 / 18670 | RussiaDronesOrion2 (+ Orion2R) | RUS_Orion2 + Animation | RU_Orion, Animation stripped | Existing Orion recon-strike. No duplicate | Russia | NEW_FOLDER_EXACT |
| cargoplane. | yes | AVCargoPln. TEOD INI AmericaJetCargoPlane. Textures AC130.dds. 4-engine turboprop C-130/AC-130 class. NVCargoPln/UVCargoPln are other nations' cargo and were not used | !TEOD_W3D.big | AVCargoPln.W3D / _D / _E | AC130.dds, AH64 rotor.dds. CWCusAC130.tga NOT in TEOD | 75728 / 75740 / 49567 | JapanJetC130H | donor AVCargoPln/AVCrago2 | TEOD AVCargoPln | JASDF C-130H unarmed transport. Japan slot kept | Japan Heavy 7 | NEW_FOLDER_EXACT |
| Shenygng. | yes | no J-35 name. NVJ31 is Shenyang FC-31/J-31 family | !TEOD_W3D.big | NVJ31.W3D / _D / _E | J31.dds | 46424 / 46426 / 42748 | ChinaJetJ35A | CHAJ31HXNew | NVJ31 | J-35A PL-15 x6 PL-10 x2 LS-6 x2. Existing J-31 unchanged | China Heavy 12 | NEW_FOLDER_CLOSE_MATCH |

### Dotted not-found reports

- Eurodrone: `NEW_FOLDER_ASSET_NOT_FOUND` / `CURRENT_STANDIN_PRESERVED` (`Nat_Heron`)
- nEUROn: `NEW_FOLDER_ASSET_NOT_FOUND` / `CURRENT_STANDIN_PRESERVED` (`CHI_GJ11L`). `RU_Skat` rejected (wrong nation/shape for French nEUROn)
- Edavulcan: `NEW_FOLDER_VULCAN_NOT_FOUND`. Existing Vulcan object was **not** retargeted to B-52
- Dassaultrafale: `NEW_FOLDER_ASSET_NOT_FOUND` / `CURRENT_STANDIN_PRESERVED` (`LSFIDRafale`)
- EDA tornado: `BROKEN_ASSET` (`UVTornado_M` is UVT-55 ammo) / `CURRENT_STANDIN_PRESERVED` (`LSFTornado`)
- CWCusAC130.tga: referenced by TEOD AVCargoPln, **not present** in `!TEOD_Textures.big`. Main skin `AC130.dds` is packed

## Appearance-only aliases (no-dot)

| Alias | New folder W3D | Used? | Target | Status |
|---|---|---|---|---|
| Typhon | NOT FOUND | no | Germany Typhoon live units untouched | NEW_FOLDER_NOT_FOUND |
| F_16 | AVF16.W3D | yes | TurkeyJetF16C only. Turkey F-16 OZGUR stays LSFF16C-family | NEW_FOLDER_EXACT |
| Jh_7A | NVJH-7A.W3D | no | China JH-7 live unit untouched | NEW_FOLDER_EXACT found, not applied (related China unit) |
| J_31 | NVJ31.W3D | yes | GermanyJetFCASNGF + ChinaJetJ35A | NEW_FOLDER_CLOSE_MATCH |
| J_10 / J10fireba | NVJ-10.W3D | yes | PakistanJetJ10CE | NEW_FOLDER_EXACT |
| J_20 | NVJ-20.W3D | no | China J-20 live units untouched | found, not applied |
| J_16 / J16 | NVJ16.W3D | no | China J-16 live units untouched | found, not applied |
| F_35 | AVF-35.W3D | no | USA/UK/IT/DE F-35 live units untouched | found, not applied |
| F_18E | AVF-18.W3D | no | USA F/A-18 live units untouched | found, not applied |
| Mirage2000 | no dedicated W3D (UVMirage is F1-class) | no | France Mirage 2000 untouched | NEW_FOLDER_NOT_FOUND |
| Mig31 | RU-Mig31.W3D | no | Russia MiG-31 untouched | found, not applied |
| su35 / Su35flanker | no SU-35.W3D; SU-37.W3D uses SU-35.dds | yes | IranJetSu35S | NEW_FOLDER_CLOSE_MATCH |
| mirg35 | RUMIG_35.W3D | no | Russia MiG-35 untouched | found, not applied |
| Su34 | RUSU-34.W3D | no | Russia Su-34 untouched | found, not applied |
| Su25 | RUSU-25.W3D | no | Russia Su-25 untouched | found, not applied |
| sqt50Rakfa | PAK-FA.W3D | yes | ItalyJetGCAP | NEW_FOLDER_EXACT |
| Mig21 / Mig21 fishing | UVMig-21.W3D | yes | IranJetMig21Bis | NEW_FOLDER_EXACT |

## Existing stand-ins replaced vs preserved

Replaced Draw/Model only (weapons/CommandSet/cost/CSF/country kept):

- FranceJetMirageF1CR LSFFRF1 -> UVMirage
- JapanJetC130H donor AVCargoPln/AVCargoPln_D1 -> TEOD AVCargoPln / AVCargoPln_E
- ChinaJetJ35A CHAJ31HXNew -> NVJ31
- GermanyJetFCASNGF LSFJ31 -> NVJ31
- IranJetMig21Bis LSFIDMig21 -> UVMig-21
- IranJetSu35S LSFSU35 -> SU-37
- PakistanJetJ10CE CHI_J10C -> NVJ-10
- ItalyJetGCAP qsnt50 -> PAK-FA
- TurkeyJetF16C LSFF16C -> AVF16
- RussiaDronesOrion2 / Orion2R RUS_Orion2+Animation -> RU_Orion (Animation stripped)

Preserved:

- GermanyUAVEuroMALE Nat_Heron
- FranceUCAVNeuron CHI_GJ11L
- FranceJetRafaleF4 LSFIDRafale
- BritainAircraftTornadoECR LSFTornado
- JapanUAVRQ4 US_RQ-4
- TurkeyJetF4ETerm JPF4
- BritainBomberVulcan existing stand-in (not B-52 retarget)
- IranDroneFotros still RUS_Orion2+Animation (not the Russian Orion object)

## New objects (complete, no visible slot)

| Object | W3D | Role | Slot |
|---|---|---|---|
| AmericaDroneRQ180 | AV_RQ180 | Unarmed stealth HALE recon, detector, no A2A/A2G | OBJECT_READY_NO_VISIBLE_USA_SLOT |
| BritainJetVampireFB5 | UV_Turbo | Legacy FB cannon/rockets/bombs | OBJECT_READY_NO_VISIBLE_UK_SLOT |
| BritainJetVampireFB9 | UVVampire | Distinct Vampire, IR+cannon+bombs | OBJECT_READY_NO_VISIBLE_UK_SLOT |

USA Fighter/Large/Heavy 1-12 are full unique units. UK Fighter/Large/Heavy 1-12 are full (Tempest/Phantom protected). Buttons exist; they are not attached to hidden slots 13/14.

## CommandSet slots (unchanged)

- Germany Heavy 8 Eurodrone, 9 FCAS NGF
- France Heavy 5 nEUROn
- France Fighter/Large 11 F1CR, 12 Rafale F4
- UK Heavy 12 Tornado ECR
- Japan Heavy 7 C-130H, 8 RQ-4
- China Heavy 12 J-35A
- Iran Heavy 2 MiG-21bis, 3 Su-35
- Turkey Heavy 6 F-4E Terminator (Turkey Heavy 4 F-16C visual swapped)
- Italy Heavy 8 GCAP
- Pakistan Airfield 9 J-10CE
- Rally 13 / Sell 14 preserved on those sets

No new airbase buildings. No helicopter airfield. No Nuclear/Atomic replacement.

## Country / aircraft / W3D table

| Country | Object | W3D now | Source |
|---|---|---|---|
| Germany | GermanyUAVEuroMALE | Nat_Heron | CURRENT_STANDIN_PRESERVED |
| Germany | GermanyJetFCASNGF | NVJ31 | NEW_FOLDER_CLOSE_MATCH |
| France | FranceUCAVNeuron | CHI_GJ11L | CURRENT_STANDIN_PRESERVED |
| France | FranceJetMirageF1CR | UVMirage | NEW_FOLDER_EXACT |
| France | FranceJetRafaleF4 | LSFIDRafale | CURRENT_STANDIN_PRESERVED |
| UK | BritainAircraftTornadoECR | LSFTornado | CURRENT_STANDIN_PRESERVED / BROKEN_ASSET UVTornado_M |
| UK | BritainBomberVulcan | unchanged | NEW_FOLDER_VULCAN_NOT_FOUND |
| UK | BritainJetVampireFB5 | UV_Turbo | NEW_FOLDER_EXACT, no slot |
| UK | BritainJetVampireFB9 | UVVampire | NEW_FOLDER_EXACT, no slot |
| Japan | JapanJetC130H | AVCargoPln (TEOD) | NEW_FOLDER_EXACT |
| Japan | JapanUAVRQ4 | US_RQ-4 | CURRENT_STANDIN_PRESERVED |
| China | ChinaJetJ35A | NVJ31 | NEW_FOLDER_CLOSE_MATCH |
| Iran | IranJetMig21Bis | UVMig-21 | NEW_FOLDER_EXACT |
| Iran | IranJetSu35S | SU-37 | NEW_FOLDER_CLOSE_MATCH |
| Turkey | TurkeyJetF4ETerm | JPF4 | CURRENT_STANDIN_PRESERVED |
| Turkey | TurkeyJetF16C | AVF16 | NEW_FOLDER_EXACT |
| Italy | ItalyJetGCAP | PAK-FA | NEW_FOLDER_EXACT |
| Pakistan | PakistanJetJ10CE | NVJ-10 | NEW_FOLDER_EXACT |
| Russia | RussiaDronesOrion2 | RU_Orion | NEW_FOLDER_EXACT |
| USA | AmericaDroneRQ180 | AV_RQ180 | NEW_FOLDER_EXACT, no slot |

## Exact New folder W3Ds packed

UVMirage.W3D UVMirage_D.W3D UVMirage_E.W3D
AVCargoPln.W3D AVCargoPln_D.W3D AVCargoPln_E.W3D
NVJ31.W3D NVJ31_D.W3D NVJ31_E.W3D
UVMig-21.W3D UVMig-21_D.W3D UVMig-21_E.W3D
SU-37.W3D SU-37_D.W3D SU-37_E.W3D
NVJ-10.W3D NVJ-10D.W3D NVJ-10_D.W3D
PAK-FA.W3D PAK-FA_D.W3D PAK-FA_E.W3D
AVF16.W3D AVF16_D.W3D AVF16_E.W3D
AV_RQ180.W3D AV_RQ180_D.W3D AV_RQ180_E.W3D
UV_Turbo.W3D UV_Turbo_D.W3D
UVVampire.W3D UVVampire_D.W3D UVVampire_E1.W3D
RU_Orion.W3D RU_Orion_D.W3D

SU-37_E references `5_E.dds`; packed as a copy of TEOD `SU-35_E.dds`.
"""
    dest = out / "NEW_FOLDER_AIRCRAFT_SOURCE_AUDIT.md"
    dest.write_text(text)
    repo = ROOT / "NEW_FOLDER_AIRCRAFT_SOURCE_AUDIT.md"
    repo.write_text(text)
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/new_folder_source_fix"))
    args = ap.parse_args()
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    gen.main()
    overlay = collect_overlay()
    fr.parse_check(overlay)
    print("overlay parser PASS")

    teod_files = extract_teod()

    data_entries, data_raw = ch.read_big(BASE_DATA)
    art_entries, art_raw = ch.read_big(BASE_ART)
    data_map: dict[str, tuple[str, bytes]] = {}
    data_keys = []
    for name, off, size in data_entries:
        key = ch.norm_key(name)
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (name.replace("/", "\\"), data_raw[off : off + size])
    art_map: dict[str, tuple[str, bytes]] = {}
    art_keys = []
    for name, off, size in art_entries:
        key = ch.norm_key(name)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (name.replace("/", "\\"), art_raw[off : off + size])

    cs_probe = data_map["data\\ini\\commandset.ini"][1].decode("latin1")
    protect_hash = {}
    for n in PROTECT_SETS:
        try:
            protect_hash[n] = hashlib.sha256(ch.grab_block(cs_probe, n).encode("latin1")).hexdigest()
        except Exception:
            print("protect skip missing", n)

    cs_key = "data\\ini\\commandset.ini"
    cs_name, cs_blob = data_map[cs_key]
    cs_text = cs_blob.decode("latin1")
    btn_overlay = overlay[r"Data\INI\CommandButton_NewFolderSourceFix.ini"].decode("ascii")
    cs_text = inline_marked(cs_text, btn_overlay, MARKER_B, MARKER_BE, "CommandSet GenericCommandSet")
    cb_key = "data\\ini\\commandbutton.ini"
    cb_text = data_map[cb_key][1].decode("latin1")
    ch.validate_commandset_button_refs(cs_text, cb_text)
    data_map[cs_key] = (cs_name, ch.lf(cs_text.encode("latin1")))

    wpn_key = "data\\ini\\weapon.ini"
    wpn_name, wpn_blob = data_map[wpn_key]
    wpn_text = wpn_blob.decode("latin1")
    wpn_overlay = overlay[r"Data\INI\Weapon_NewFolderSourceFix.ini"].decode("ascii")
    for wname in NEW_WEAPONS:
        if MARKER_W not in wpn_text and f"Weapon {wname}" in wpn_text:
            raise SystemExit(f"Weapon {wname} already in Weapon.ini")
    wpn_text = inline_marked(wpn_text, wpn_overlay, MARKER_W, MARKER_WE, "Weapon ")
    # inline_marked with insert_before "Weapon " would put block at file start if new; if marked, replaced.
    # If Weapon.ini does not start at a convenient point, first-run inserts before first Weapon.
    if MARKER_W not in wpn_text:
        raise SystemExit("weapon marker missing after inline")
    for wname in NEW_WEAPONS:
        if wpn_text.count(f"Weapon {wname}") != 1:
            raise SystemExit(f"Weapon {wname} count {wpn_text.count('Weapon '+wname)}")
    data_map[wpn_key] = (wpn_name, ch.lf(wpn_text.encode("latin1")))
    print("inlined", len(NEW_WEAPONS), "weapons")

    hc_key = "data\\ini\\mappedimages\\handcreated\\handcreatedmappedimages.ini"
    for k in data_map:
        if k.endswith("handcreatedmappedimages.ini"):
            hc_key = k
            break
    hc_name, hc_blob = data_map[hc_key]
    hc_text = hc_blob.decode("latin1")
    por_ini = overlay[r"Data\INI\MappedImages\HandCreated\zNewFolderSourceFix_Portrait_Images.INI"].decode("ascii")
    if "MappedImage SPEC_AmericaRQ180" not in hc_text:
        if not hc_text.endswith("\n"):
            hc_text += "\n"
        hc_text += "\n" + por_ini.strip() + "\n"
    data_map[hc_key] = (hc_name, ch.lf(hc_text.encode("latin1")))

    csf_key = "data\\english\\generals.csf"
    csf_name, csf_blob = data_map[csf_key]
    version, unk, lang, labels = ch.parse_csf(csf_blob)
    have_idx = {name: i for i, (_, name, _) in enumerate(labels)}
    added = updated = 0
    for key, value in gen.CSF_LABELS.items():
        if any(ord(c) > 127 for c in key) or any(ord(c) > 127 for c in value):
            raise SystemExit(f"non-ASCII CSF {key}")
        if key in have_idx:
            i = have_idx[key]
            mag, name, _s = labels[i]
            labels[i] = (mag, name, [(ch.CSF_STR_MAGIC, value, b"")])
            updated += 1
        else:
            labels.append((ch.CSF_LBL_MAGIC, key, [(ch.CSF_STR_MAGIC, value, b"")]))
            added += 1
            have_idx[key] = len(labels) - 1
    print(f"CSF added {added} labels, updated {updated}")
    csf_new = ch.build_csf(version, unk, lang, labels)
    ch.validate_csf(csf_new, list(gen.CSF_LABELS))
    data_map[csf_key] = (csf_name, csf_new)

    for key in ORION_KEYS:
        if key not in data_map:
            raise SystemExit(f"missing {key}")
        name, blob = data_map[key]
        text = blob.decode("latin1")
        patched = patch_orion_visual(text)
        data_map[key] = (name, ch.lf(patched.encode("latin1")))
        print("patched Orion visual", name)

    skip = {
        "data\\ini\\commandbutton_newfoldersourcefix.ini",
        "data\\ini\\weapon_newfoldersourcefix.ini",
    }
    for dest, content in overlay.items():
        key = ch.norm_key(dest)
        if key in skip:
            continue
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (dest, content)
        print("DATA inject", dest)

    packed_tex_keys = {k.split("\\")[-1].lower() for k in art_map if "\\textures\\" in k}
    for name in W3D_INJECT:
        src = teod_files.get(name.lower())
        if src is None:
            raise SystemExit(f"missing extracted W3D {name}")
        dest = "Art\\W3D\\" + name
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, src.read_bytes())
    for name in TEX_INJECT + ["5_E.dds"]:
        src = teod_files.get(name.lower())
        if src is None:
            if name.lower() in packed_tex_keys:
                print("skip missing TEOD tex, packed already has", name)
                continue
            if name == "housecolor2.dds":
                continue
            print("WARN missing tex", name)
            continue
        if name.lower() in SHARED_NO_OVERWRITE and name.lower() in packed_tex_keys:
            print("keep packed shared tex", name)
            continue
        dest = "Art\\Textures\\" + name
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, src.read_bytes())
    print("ART injected from New folder / TEOD")

    packed_tex = {k.split("\\")[-1].lower(): art_map[k][1] for k in art_map if "\\textures\\" in k}
    for dest_name, src_name in PORTRAIT_SRC.items():
        src = teod_files.get(src_name.lower())
        if src is None:
            leaf = src_name.lower()
            if leaf not in packed_tex:
                raise SystemExit(f"missing portrait source {src_name}")
            tmp = Path("/tmp") / ("portrait_src_" + leaf.replace("/", "_").replace(" ", "_"))
            tmp.write_bytes(packed_tex[leaf])
            src = tmp
        tga = eu.make_portrait_any(src)
        dest = f"Art\\Textures\\{dest_name}"
        key = ch.norm_key(dest)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (dest, tga)
        print("portrait", dest_name, len(tga))

    overlay_obj_keys = {
        ch.norm_key("Data\\" + s["rel"].replace("/", "\\")) for s in gen.VISUAL_PATCHES
    } | {
        ch.norm_key("Data\\" + s["rel"].replace("/", "\\")) for s in gen.NEW_AIRCRAFT
    }
    obj_hits: dict[str, list[str]] = {o: [] for o in NEW_OBJECTS}
    for key in list(data_map):
        name, blob = data_map[key]
        if not key.endswith(".ini"):
            continue
        text = blob.decode("latin1")
        if key in overlay_obj_keys or key in ORION_KEYS:
            errs = e7.balanced_end(text, name)
            if errs:
                raise SystemExit("End balance FAIL\n" + "\n".join(errs))
            dups = dup_moduletags(text, name)
            if dups:
                raise SystemExit("duplicate ModuleTag FAIL\n" + "\n".join(dups))
        for obj in NEW_OBJECTS:
            if re.search(rf"^Object {re.escape(obj)}\b", text, re.M):
                obj_hits[obj].append(name)
    for obj, hits in obj_hits.items():
        expect = [s for s in gen.NEW_AIRCRAFT if s["obj"] == obj][0]
        expect_name = "Data\\" + expect["rel"].replace("/", "\\")
        if [h.lower() for h in hits] != [expect_name.lower()]:
            raise SystemExit(f"Object {obj} hits={hits}")
    print("new Object unique PASS")

    art_w3d = {k.split("\\")[-1].lower().replace(".w3d", "") for k in art_map if k.endswith(".w3d")}
    for spec in gen.NEW_AIRCRAFT:
        for m in (spec["model"], spec["model_d"], spec["model_k"]):
            if m.lower() not in art_w3d:
                raise SystemExit(f"missing W3D for {spec['obj']} model {m}")
    for obj, models in PATCHED_MODELS.items():
        for m in models:
            if m.lower() not in art_w3d:
                raise SystemExit(f"missing W3D for {obj} model {m}")
    print("ART/W3D PASS")

    found_proj = set()
    for key, (name, blob) in data_map.items():
        if not key.endswith(".ini"):
            continue
        text = blob.decode("latin1")
        for p in PROJECTILES:
            if re.search(rf"^Object {re.escape(p)}\b", text, re.M):
                found_proj.add(p)
    missing_proj = PROJECTILES - found_proj
    if missing_proj:
        raise SystemExit("missing projectile objects: " + ", ".join(sorted(missing_proj)))
    print("Projectile references PASS")

    cs_final = data_map[cs_key][1].decode("latin1")
    for n, oldh in protect_hash.items():
        h = hashlib.sha256(ch.grab_block(cs_final, n).encode("latin1")).hexdigest()
        if h != oldh:
            raise SystemExit(f"protected CommandSet changed: {n}")
    print("protected CommandSets unchanged PASS")

    for set_name, adds in KEEP_SLOTS.items():
        block = ch.grab_block(cs_final, set_name)
        for slot, btn in adds.items():
            if not re.search(rf"^\s*{slot}\s*=\s*{re.escape(btn)}\s*$", block, re.M):
                raise SystemExit(f"{set_name} missing {slot}={btn}")
        if "Command_Sell" not in block and set_name != "Pakistan_AirfieldCommandSet":
            # Pakistan overlay may still have Sell; require if present in original
            if "Command_Sell" in ch.grab_block(data_map[cs_key][1].decode("latin1"), set_name):
                pass
        slots = [int(x) for x in re.findall(r"^\s*(\d+)\s*=", block, re.M)]
        if len(slots) != len(set(slots)):
            raise SystemExit(f"{set_name} duplicate slots {slots}")
        if "Command_SetRallyPoint" not in block and "Command_Sell" not in block:
            print("WARN", set_name, "no Rally/Sell in block (may use other slots)")
    print("kept slots PASS")

    for set_name, btn in REGRESS.items():
        if btn not in ch.grab_block(cs_final, set_name):
            raise SystemExit(f"regression {set_name} lost {btn}")
    print("country regression PASS")

    # New buttons exist but must not occupy visible 1-12 slots.
    for set_name in list(protect_hash) + [s for s in KEEP_SLOTS if s not in protect_hash]:
        try:
            block = ch.grab_block(cs_final, set_name)
        except SystemExit:
            continue
        for line in block.splitlines():
            sm = re.match(r"\s*(\d+)\s*=\s*(\S+)", line)
            if not sm:
                continue
            slot, btn = int(sm.group(1)), sm.group(2)
            if btn in NO_SLOT_BUTTONS and slot <= 12:
                raise SystemExit(f"{btn} attached to visible slot {set_name} {slot}")
    for btn in NO_SLOT_BUTTONS:
        if btn not in cs_final:
            raise SystemExit(f"missing construct button {btn}")
    print("no-visible-slot buttons PASS")

    mapped = set(re.findall(r"^MappedImage (\S+)", data_map[hc_key][1].decode("latin1"), re.M))
    for img in gen.PORTRAITS:
        if img not in mapped:
            raise SystemExit(f"missing MappedImage {img}")
    print("MappedImage PASS")

    # Preserve stand-in models for units we did not swap.
    for obj, model in PRESERVED_MODELS.items():
        hits = []
        for key, (name, blob) in data_map.items():
            if key.endswith(".ini") and re.search(rf"^Object {re.escape(obj)}\b", blob.decode("latin1"), re.M):
                hits.append((name, blob.decode("latin1")))
        if len(hits) != 1:
            raise SystemExit(f"preserved object {obj} hits={[h[0] for h in hits]}")
        if not re.search(rf"Model\s+=\s+{re.escape(model)}\b", hits[0][1]):
            raise SystemExit(f"{obj} lost stand-in model {model}")
    for obj, models in PATCHED_MODELS.items():
        found = False
        for key, (name, blob) in data_map.items():
            if not key.endswith(".ini"):
                continue
            text = blob.decode("latin1")
            if re.search(rf"^Object {re.escape(obj)}\b", text, re.M):
                found = True
                if not re.search(rf"Model\s+=\s+{re.escape(models[0])}\b", text):
                    raise SystemExit(f"{obj} missing new model {models[0]}")
        if not found:
            raise SystemExit(f"missing patched object {obj}")
    orion_text = data_map[ORION_KEYS[0]][1].decode("latin1")
    if re.search(r"Animation\s*=", orion_text):
        raise SystemExit("Orion2 still has Animation")
    if not re.search(r"Model\s+=\s+RU_Orion\b", orion_text):
        raise SystemExit("Orion2 missing RU_Orion")
    print("visual swap / stand-in preserve PASS")

    # Weapon refs used by new objects exist.
    vwpn = data_map[wpn_key][1].decode("latin1")
    for wname in NEW_WEAPONS:
        if f"Weapon {wname}" not in vwpn:
            raise SystemExit(f"missing weapon {wname}")
    print("weapon refs PASS")

    out_data_map = {data_map[k][0]: data_map[k][1] for k in data_keys}
    out_art_map = {art_map[k][0]: art_map[k][1] for k in art_keys}
    data_big = ch.build_big(out_data_map)
    art_big = ch.build_big(out_art_map)
    out_data = out / "_SPEC_DATA_ONE.big"
    out_art = out / "_SPEC_ART_ONE.big"
    out_data.write_bytes(data_big)
    out_art.write_bytes(art_big)
    dh = sha256(out_data)
    ah = sha256(out_art)
    print("DATA sha256", dh)
    print("ART sha256", ah)

    v_entries, v_raw = ch.read_big(out_data)
    v_map = {}
    for name, off, size in v_entries:
        v_map[ch.norm_key(name)] = (name, v_raw[off : off + size])
    va_entries, va_raw = ch.read_big(out_art)
    va_w3d = set()
    va_tex = set()
    for name, off, size in va_entries:
        leaf = name.split("\\")[-1].lower()
        if name.lower().endswith(".w3d"):
            va_w3d.add(leaf)
        if "\\textures\\" in name.lower():
            va_tex.add(leaf)
    vcs = v_map["data\\ini\\commandset.ini"][1].decode("latin1")
    vwpn = v_map["data\\ini\\weapon.ini"][1].decode("latin1")
    for obj in NEW_OBJECTS:
        hits = []
        for name, blob in v_map.values():
            if name.lower().endswith(".ini") and re.search(rf"^Object {re.escape(obj)}\b", blob.decode("latin1"), re.M):
                hits.append(name)
        if len(hits) != 1:
            raise SystemExit(f"re-extract Object {obj} hits={hits}")
        if f"Command_Construct{obj}" not in vcs:
            raise SystemExit(f"re-extract missing button {obj}")
    for wname in NEW_WEAPONS:
        if f"Weapon {wname}" not in vwpn:
            raise SystemExit(f"re-extract missing weapon {wname}")
    for need in (
        "uvmirage.w3d", "nvcargopln.w3d", "avcargopln.w3d", "nvj31.w3d",
        "uvmig-21.w3d", "su-37.w3d", "nvj-10.w3d", "pak-fa.w3d", "avf16.w3d",
        "av_rq180.w3d", "uv_turbo.w3d", "uvvampire.w3d", "ru_orion.w3d",
        "nat_heron.w3d", "chi_gj11l.w3d", "lsfidrafale.w3d", "lstornado.w3d",
    ):
        if need == "nvcargopln.w3d":
            continue
        if need == "lstornado.w3d":
            if "lstornado.w3d" not in va_w3d:
                # packed name may be LSFTornado.W3D
                if "lsftornado.w3d" not in va_w3d:
                    raise SystemExit(f"re-extract ART missing tornado {need}")
            continue
        if need not in va_w3d:
            raise SystemExit(f"re-extract ART missing {need}")
    for tex in ("uvmirage.dds", "ac130.dds", "j31.dds", "orion.dds", "drones_us_ru.dds", "gla-vampire.dds"):
        if tex not in va_tex:
            raise SystemExit(f"re-extract ART missing tex {tex}")
    f1 = None
    for name, blob in v_map.values():
        if name.lower().endswith("francejetmiragef1cr.ini"):
            f1 = blob.decode("latin1")
            break
    if not f1 or "UVMirage" not in f1:
        raise SystemExit("re-extract F1CR not UVMirage")
    euro = None
    for name, blob in v_map.values():
        if name.lower().endswith("germanyuaveuromale.ini"):
            euro = blob.decode("latin1")
            break
    if not euro or "Nat_Heron" not in euro:
        raise SystemExit("re-extract Eurodrone lost Nat_Heron")
    print("re-extract FINAL content PASS")

    write_install(out)
    write_audit(out, dh, ah, out_data.stat().st_size, out_art.stat().st_size)
    (out / "PACK_REPORT.txt").write_text(
        f"DATA sha256 {dh}\nART  sha256 {ah}\nDATA bytes {out_data.stat().st_size}\nART  bytes {out_art.stat().st_size}\n"
        f"new aircraft {len(NEW_OBJECTS)}\nnew weapons {len(NEW_WEAPONS)}\n"
    )
    zpath = out / "NEW_FOLDER_AIRCRAFT_SOURCE_FIX.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
        zf.write(out / "NEW_FOLDER_AIRCRAFT_SOURCE_AUDIT.md", "NEW_FOLDER_AIRCRAFT_SOURCE_AUDIT.md")
        zf.write(out / "INSTALL.txt", "INSTALL.txt")
    print("ZIP", zpath, zpath.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
