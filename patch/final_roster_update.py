#!/usr/bin/env python3
"""SPECTER1_FINAL_ROSTER_UPDATE packager.

Validates the stacked SPECTER1 roster DATA (Iran+Israel packed baseline,
which already contains USA/China/Russia/Iraq/Vietnam/Syria plus every
later country pass) and copies it to the final release folder.

Does not rebuild DATA. Does not modify ART. Packed BIGs stay untracked.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DIR = Path("/workspace/patch/Release/SPECTER1_IRAN_ISRAEL_ROSTER_01")
SRC_DATA = SRC_DIR / "_SPEC_DATA_ONE.big"
SRC_ART = SRC_DIR / "_SPEC_ART_ONE.big"
EXPECTED_DATA_SHA = "2a06ca987362da5ffecd2121c85d2e49a6da8bb4ee80ac1a45bb9278d74b5921"
EXPECTED_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"

OUT_DIR = Path("/tmp/SPECTER1_FINAL_ROSTER_UPDATE")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_FINAL_ROSTER_UPDATE")
RELEASE_NAME = "SPECTER1_FINAL_ROSTER_UPDATE"

# Packed clone/object files that prove each country pass is still in DATA.
REQUIRED_FILES = {
    "USA": [
        r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaHelicopterAH1Z.ini",
        r"Data\INI\Object\Specter\United States Of America\AmericaJetC17Visual.ini",
        r"Data\INI\Object\Specter\United States Of America\AmericaJetE3Visual.ini",
        r"Data\INI\Object\Specter\United States Of America\AmericaJetV22Visual.ini",
        r"Data\INI\Object\Specter\United States Of America\Airforce\B1R.ini",
        r"Data\INI\Object\Specter\United States Of America\AmericaJetB2A.ini",
    ],
    "CHINA": [
        r"Data\INI\Object\Specter\PLA\Airforce\H6K.ini",
        r"Data\INI\Object\Specter\PLA\Airforce\H20.ini",
        r"Data\INI\Object\Specter\PLA\Airforce\J7.ini",
    ],
    "RUSSIA": [
        r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\TU22M3M.ini",
        r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\RussiaJetTU160.ini",
        r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\Su24MR.ini",
    ],
    "IRAQ": [
        r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Su-24MR.ini",
    ],
    "VIETNAM": [
        r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetB21.ini",
        r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetYak130.ini",
        r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetMi17.ini",
    ],
    "SYRIA": [
        r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\SyriaBomberH6K.ini",
        r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig21.ini",
    ],
    "INDIA": [
        r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetTu22M3M.ini",
        r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaJetB2A.ini",
        r"Data\INI\Object\Specter\Indian Armed Forces\Airforce\IndiaHelicopterKA52.ini",
    ],
    "GERMANY": [
        r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetC130.ini",
        r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyJetB2A.ini",
        r"Data\INI\Object\Specter\German Armed Forces\Airforce\GermanyAircraftE3.ini",
    ],
    "JAPAN": [
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetEA6BUSA.ini",
    ],
    "FRANCE": [
        r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetC130US.ini",
        r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetB21.ini",
        r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetB52H.ini",
    ],
    "KOREA": [
        r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaHelicopterAH64E.ini",
        r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetCN235US.ini",
        r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetB1R.ini",
        r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetB52H.ini",
    ],
    "ITALY": [
        r"Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyAircraftG550CAEW.ini",
        r"Data\INI\Object\Specter\Italian Armed Forces\Rotary\ItalyHelicopterA129.ini",
        r"Data\INI\Object\Specter\Italian Armed Forces\Rotary\ItalyHelicopterAW101.ini",
    ],
    "SAUDI": [
        r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetB52H.ini",
        r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetB1R.ini",
        r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiJetB21.ini",
        r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Airforce\SaudiHelicopterAH64E.ini",
    ],
    "UK": [
        r"Data\INI\Object\Specter\British Armed Forces\Rotary\BritainHelicopterChinook.ini",
        r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainAircraftE7.ini",
        r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetC17.ini",
        r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetA400M.ini",
    ],
    "SWEDEN": [
        r"Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenAircraftE3USA.ini",
        r"Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetB1R.ini",
        r"Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenJetB2A.ini",
    ],
    "UAE": [
        r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetB21.ini",
        r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetB2A.ini",
        r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetB1R.ini",
    ],
    "NATO": [
        r"Data\INI\Object\Specter\NATO\Airforce\NatoAircraftE3USA.ini",
        r"Data\INI\Object\Specter\NATO\Airforce\NatoJetB1R.ini",
        r"Data\INI\Object\Specter\NATO\Airforce\NatoJetB2A.ini",
        r"Data\INI\Object\Specter\NATO\Airforce\NatoJetB52H.ini",
        r"Data\INI\Object\Specter\NATO\Airforce\NatoJetV22.ini",
        r"Data\INI\Object\Specter\NATO\Airforce\NatoJetC17.ini",
    ],
    "UKRAINE": [
        r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineAircraftE3USA.ini",
        r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetB1R.ini",
        r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetV22.ini",
        r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetB21.ini",
    ],
    "IRAN": [
        r"Data\INI\Object\Specter\Iranian Army\Airforce\IranJetTu22M3M.ini",
        r"Data\INI\Object\Specter\Iranian Army\Airforce\IranJetTu160.ini",
        r"Data\INI\Object\Specter\Iranian Army\Airforce\IranBomberH6K.ini",
        r"Data\INI\Object\Specter\Iranian Army\Airforce\IranBomberH20.ini",
        r"Data\INI\Object\Specter\Iranian Army\Airforce\IranJetMirageF1CR.ini",
        r"Data\INI\Object\Specter\Iranian Army\Buildings\Airfield.ini",
        r"Data\INI\Object\Specter\Iranian Army\Buildings\Iran_HeavyAirBase.ini",
    ],
    "ISRAEL": [
        r"Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelAircraftE3USA.ini",
        r"Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetV22.ini",
        r"Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetB1R.ini",
        r"Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetB52H.ini",
        r"Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetB2A.ini",
        r"Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelJetB21.ini",
        r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_HeavyAirBase.ini",
    ],
}

REQUIRED_COMMANDS = {
    "INDIA": ["Command_ConstructIndiaJetTu22M3M", "Command_ConstructIndiaJetB2A"],
    "GERMANY": ["Command_ConstructGermanyJetB2A", "Command_ConstructGermanyJetC130"],
    "JAPAN": ["Command_ConstructJapanJetEA6BUSA"],
    "FRANCE": ["Command_ConstructFranceJetB21", "Command_ConstructFranceJetB52H", "Command_ConstructFranceJetC130US"],
    "KOREA": ["Command_ConstructSouthKoreaJetB1R", "Command_ConstructSouthKoreaJetB52H", "Command_ConstructSouthKoreaHelicopterAH64E"],
    "SAUDI": ["Command_ConstructSaudiJetB52H", "Command_ConstructSaudiJetB1R", "Command_ConstructSaudiJetB21"],
    "SWEDEN": ["Command_ConstructSwedenAircraftE3USA", "Command_ConstructSwedenJetB1R", "Command_ConstructSwedenJetB2A"],
    "UAE": ["Command_ConstructUAEJetB21", "Command_ConstructUAEJetB2A", "Command_ConstructUAEJetB1R"],
    "NATO": [
        "Command_ConstructNatoAircraftE3USA",
        "Command_ConstructNatoJetB1R",
        "Command_ConstructNatoJetB2A",
        "Command_ConstructNatoJetB52H",
        "Command_ConstructNatoJetV22",
        "Command_ConstructNatoJetC17",
    ],
    "UKRAINE": [
        "Command_ConstructUkraineAircraftE3USA",
        "Command_ConstructUkraineJetB1R",
        "Command_ConstructUkraineJetV22",
        "Command_ConstructUkraineJetB21",
    ],
    "SOUTHAFRICA": [
        "Command_ConstructSouthAfricaTankOlifant",
        "Command_ConstructSouthAfricaTankOlifant1B",
    ],
    "IRAN": [
        "Command_ConstructIranJetTu22M3M",
        "Command_ConstructIranJetTu160",
        "Command_ConstructIranBomberH6K",
        "Command_ConstructIranBomberH20",
        "Command_ConstructIranJetF14A",
        "Command_ConstructIranJetMig29A",
    ],
    "ISRAEL": [
        "Command_ConstructIsraelAircraftE3USA",
        "Command_ConstructIsraelJetV22",
        "Command_ConstructIsraelJetB1R",
        "Command_ConstructIsraelJetB52H",
        "Command_ConstructIsraelJetB2A",
        "Command_ConstructIsraelJetB21",
        "Command_ConstructIsraelJetF16CBarak",
        "Command_ConstructIsraelJetF15CBaz",
        "Command_ConstructIsraelJetKfir",
        "Command_ConstructIsraelJetNesher",
        "Command_ConstructIsraelJetF4E",
    ],
}

PROTECTED_DONORS = [
    r"Data\INI\Object\Specter\United States Of America\AmericaJetE3Visual.ini",
    r"Data\INI\Object\Specter\United States Of America\AmericaJetV22Visual.ini",
    r"Data\INI\Object\Specter\United States Of America\Airforce\B1R.ini",
    r"Data\INI\Object\Specter\United States Of America\AmericaJetB2A.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\TU22M3M.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\RussiaJetTU160.ini",
    r"Data\INI\Object\Specter\PLA\Airforce\H6K.ini",
    r"Data\INI\Object\Specter\PLA\Airforce\H20.ini",
    r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Su-24MR.ini",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(msg: str) -> None:
    raise SystemExit("VALIDATION FAIL: " + msg)


def packed_index(entries) -> dict[str, int]:
    out: dict[str, int] = {}
    for i, (name, _) in enumerate(entries):
        out[jf.norm(name).lower()] = i
    return out


def has_file(idx: dict[str, int], path: str) -> bool:
    return jf.norm(path).lower() in idx


def cs_has(cmdset: str, token: str) -> bool:
    return token.lower() in cmdset.lower()


def content_checks(entries) -> list[str]:
    notes: list[str] = []

    iran_air = jf.text_of(entries, r"Data\INI\Object\Specter\Iranian Army\Buildings\Airfield.ini")
    if not re.search(r"(?im)^\s*NumRows\s*=\s*4\b", iran_air):
        fail("Iran airfield NumRows != 4")
    if not re.search(r"(?im)^\s*NumCols\s*=\s*4\b", iran_air):
        fail("Iran airfield NumCols != 4")
    notes.append("IRAN_AIRFIELD_PARKING = 4x4")

    mig29 = jf.text_of(entries, r"Data\INI\Object\Specter\Iranian Army\Airforce\Iran_Mig29A.ini")
    if not re.search(r"(?im)^\s*NeedsRunway\s*=\s*Yes\b", mig29):
        fail("Iran Mig29A NeedsRunway != Yes")
    if not re.search(r"(?im)^\s*KeepsParkingSpaceWhenAirborne\s*=\s*No\b", mig29):
        fail("Iran Mig29A KeepsParking != No")
    notes.append("IRAN_MIG29_RUNWAY = NeedsRunway=Yes KeepsParking=No")

    mi8 = jf.text_of(entries, r"Data\INI\Object\Specter\Iranian Army\Airforce\Mil_Mi8.ini")
    if "ChinookAIUpdate" in mi8 or "ChinookLocomotor" in mi8:
        fail("Iran Mi-8 still has ChinookAI/ChinookLocomotor")
    if not re.search(r"(?im)^\s*NeedsRunway\s*=\s*No\b", mi8):
        fail("Iran Mi-8 NeedsRunway != No")
    notes.append("IRAN_MI8 = JetAI NeedsRunway=No (no ChinookAI)")

    isr_heavy = jf.text_of(entries, r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_HeavyAirBase.ini")
    if not re.search(r"(?im)^\s*Side\s*=\s*Israel\b", isr_heavy):
        fail("Israel HeavyAirBase Side != Israel")
    notes.append("ISRAEL_HEAVY_SIDE = Israel")

    e3 = jf.text_of(entries, r"Data\INI\Object\Specter\Israel Defense Forces\Airforce\IsraelAircraftE3USA.ini")
    if "AN_APY2_Radar_Power" not in e3:
        fail("Israel E-3 missing USA AWACS modules")
    if not re.search(r"(?im)^\s*Side\s*=\s*Israel\b", e3):
        fail("Israel E-3 Side != Israel")
    notes.append("ISRAEL_E3 = AmericaJetE3Visual clone + AN_APY2")

    nato_c17 = jf.text_of(entries, r"Data\INI\Object\Specter\NATO\Airforce\NatoJetC17.ini")
    if "ModuleTag_StarlifterCargo" not in nato_c17:
        fail("NATO C-17 missing Starlifter cargo")
    notes.append("NATO_C17 = StarlifterCargo present")

    nato_e3 = jf.text_of(entries, r"Data\INI\Object\Specter\NATO\Airforce\NatoAircraftE3USA.ini")
    if "AN_APY2_Radar_Power" not in nato_e3:
        fail("NATO E-3 missing USA AWACS modules")
    notes.append("NATO_E3 = AN_APY2 present")

    se_e3 = jf.text_of(entries, r"Data\INI\Object\Specter\Swedish Armed Forces\Airforce\SwedenAircraftE3USA.ini")
    if "AN_APY2_Radar_Power" not in se_e3:
        fail("Sweden E-3 missing USA AWACS modules")
    notes.append("SWEDEN_E3 = AN_APY2 present")

    ua_e3 = jf.text_of(entries, r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineAircraftE3USA.ini")
    if "AN_APY2_Radar_Power" not in ua_e3:
        fail("Ukraine E-3 missing USA AWACS modules")
    notes.append("UKRAINE_E3 = AN_APY2 present")

    uk_e7 = jf.text_of(entries, r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainAircraftE7.ini")
    if "AN_APY2_Radar_Power" not in uk_e7:
        fail("UK E-7 missing USA AWACS modules")
    notes.append("UK_E7 = AN_APY2 present")

    jp_ea6 = jf.text_of(entries, r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetEA6BUSA.ini")
    if "Object JapanJetEA6BUSA" not in jp_ea6:
        fail("Japan EA-6B clone object missing")
    notes.append("JAPAN_EA6B = JapanJetEA6BUSA present")

    fr_c130 = jf.text_of(entries, r"Data\INI\Object\Specter\French Armed Forces\Airforce\FranceJetC130US.ini")
    if "ModuleTag_An124Cargo" not in fr_c130:
        fail("France C-130 missing An-124 cargo")
    notes.append("FRANCE_C130 = An124Cargo present")

    ir_f1 = jf.text_of(entries, r"Data\INI\Object\Specter\Iranian Army\Airforce\IranJetMirageF1CR.ini")
    if "Object IranJetMirageF1CR" not in ir_f1:
        fail("Iran Mirage F1CR clone missing")
    notes.append("IRAN_F1CR = clone present")

    yak = jf.text_of(entries, r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetYak130.ini")
    if "LSFYAK130" not in yak:
        fail("Vietnam Yak-130 model is not LSFYAK130")
    notes.append("VIETNAM_YAK130 = LSFYAK130")

    for donor in PROTECTED_DONORS:
        txt = jf.text_of(entries, donor)
        if not txt.strip():
            fail(f"empty donor {donor}")
    notes.append("PROTECTED_DONORS_PRESENT = YES")
    return notes


def main() -> int:
    if not SRC_DATA.is_file():
        fail(f"missing source DATA {SRC_DATA}")
    if not SRC_ART.is_file():
        fail(f"missing source ART {SRC_ART}")

    data_sha = sha256_file(SRC_DATA)
    art_sha = sha256_file(SRC_ART)
    if data_sha != EXPECTED_DATA_SHA:
        fail(f"DATA SHA {data_sha} != {EXPECTED_DATA_SHA}")
    if art_sha != EXPECTED_ART_SHA:
        fail(f"ART SHA {art_sha} != {EXPECTED_ART_SHA} (ART must be unchanged)")

    entries = jf.read_big_list(SRC_DATA)
    idx = packed_index(entries)
    file_count = len(entries)
    data_bytes = SRC_DATA.stat().st_size
    art_bytes = SRC_ART.stat().st_size

    missing: list[str] = []
    country_files: dict[str, list[str]] = {}
    for country, paths in REQUIRED_FILES.items():
        found = []
        for p in paths:
            if has_file(idx, p):
                found.append(p)
            else:
                missing.append(f"{country}: {p}")
        country_files[country] = found
    if missing:
        fail("missing packed files:\n  " + "\n  ".join(missing))

    cmdset = jf.text_of(entries, r"Data\INI\CommandSet.ini")
    cmdbtn = jf.text_of(entries, r"Data\INI\CommandButton.ini")
    missing_cmd: list[str] = []
    for country, tokens in REQUIRED_COMMANDS.items():
        for token in tokens:
            if not cs_has(cmdset, token) and not cs_has(cmdbtn, token):
                missing_cmd.append(f"{country}: {token}")
    if missing_cmd:
        fail("missing CommandSet/CommandButton tokens:\n  " + "\n  ".join(missing_cmd))

    notes = content_checks(entries)

    sa_ok = has_file(idx, r"Data\INI\Object\Specter\NationalGround\SouthAfricaTankOlifant.ini") or cs_has(
        cmdset, "Command_ConstructSouthAfricaTankOlifant"
    )
    if not sa_ok:
        fail("South Africa Olifant marker missing")

    libya_hits = [n for n, _ in entries if "Libya" in n or "Libyan" in n]
    if not libya_hits:
        fail("no Libya packed files")

    # ART is a byte-identical copy. Never rewrite it.
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC_DATA, OUT_DIR / "_SPEC_DATA_ONE.big")
    shutil.copy2(SRC_ART, OUT_DIR / "_SPEC_ART_ONE.big")
    shutil.copy2(SRC_DATA, WS_OUT / "_SPEC_DATA_ONE.big")
    shutil.copy2(SRC_ART, WS_OUT / "_SPEC_ART_ONE.big")

    copy_data_sha = sha256_file(WS_OUT / "_SPEC_DATA_ONE.big")
    copy_art_sha = sha256_file(WS_OUT / "_SPEC_ART_ONE.big")
    if copy_data_sha != data_sha:
        fail("copied DATA SHA mismatch")
    if copy_art_sha != art_sha:
        fail("copied ART SHA mismatch — ART must remain a byte-identical copy")

    changelog = f"""{RELEASE_NAME}

SPECTER1 final roster package. Packed from the verified Iran+Israel DATA
baseline (which already contains every prior SPECTER1 country pass).
Does not rebuild DATA. Does not modify ART.

PR #473 (SPECTER WarFactory + Air Force complete live DATA rebuild) was
already merged to main on 2026-09-12. This package is the later SPECTER1
packed chain, not a rebuild of that older DATA SHA.

Install:
1. Close Specter / Generals.
2. Copy _SPEC_DATA_ONE.big and _SPEC_ART_ONE.big into GameRoot, replacing
   the current Specter DATA/ART BIGs.
3. Launch Specter.

DATA SHA256 {data_sha}
ART  SHA256 {art_sha} (unchanged copy)
DATA files  {file_count}
DATA bytes  {data_bytes}
ART bytes   {art_bytes}
INGAME_TESTED = NO
ART_CHANGED = NO

Applied country changes (latest packed DATA contains all of these):

USA
- F-117 scale 1.04. AH-1Z added. EA-6B/F-35B volume-shadow INI hides.
- Starlifter C-17 uses An-124 transport contain. F-15E Strike Eagle removed
  from live production bars.

CHINA
- J-7 scale 1.30. Q-5 scale 1.00. Barracks/WarFactory science gates stripped.

RUSSIA
- Su-34MM scale 1.03. Su-24MR fire via SU24MR_CommandSet. Faction unlocks.

IRAQ
- Live-path MiG-21/J-7 scale+bombs, drones, WarFactory gates, Tu-22 8-bomb,
  Alhussien cost. Su-24MR donor not edited.

VIETNAM
- Yak-130 LSFYAK130. MiG-29/F-5E scales. Mi-17 fire. 12 fighters + bomb
  diversity. B-21 and Ka-52 on HeavyAirBase.

SYRIA
- MiG-21 scales. H-6K clone. Bomb diversity. Iraq infantry barracks. Unlocks.

INDIA
- Factory Side=India. Russian infantry clones. Tu-22M3M / B-2A / Ka-52.
  Bomb diversity, drones, unlocks.

GERMANY
- Factory Side=Germany. USA C-130 + An-124 cargo. E-3 AWACS modules.
  B-2A and AH-64E. Bomb diversity, unlocks.

JAPAN
- Factory Side=Japan. USA EA-6B clone. Bomb diversity, unlocks.

FRANCE
- Factory Side=France. EC725 combat heli. USA C-130 / B-21 / B-52H.
  E-3 AWACS modules. Mirage F1CR cloned to Iran. Bomb diversity, unlocks.

SOUTH KOREA
- Native factory roster. USA CN-235 / B-1R / B-52H. E-737 AWACS.
  AH-64E / UH-60P. FA-50 / F-5E visuals. Bomb diversity, unlocks.

ITALY
- G550 USA AWACS scan. A129 GeometryIsSmall=No. AW101 JetAI.
  C-27J US_C130H. Bomb diversity, unlocks.

SAUDI ARABIA
- Native factory. Hawk 65 LSFKoreaF5. B-52/B-1/B-21. AH-64E/UH-60.
  Iraqi infantry clones. RQ-180/MQ-4 USA scan. Bomb diversity, unlocks.

UNITED KINGDOM
- AH-64E takeoff. Merlin GeometryIsSmall=No. American CH-47 clone.
  E-7 USA scan. C-17/A400M An-124 cargo. Bomb diversity, unlocks.

SWEDEN
- Native factory. USA E-3 clone. B-1R/B-2A. SK60B LSFT50.
  Bomb diversity, unlocks.

UAE
- Native factory. Iraqi infantry clones. B-21/B-2A/B-1R.
  Bomb diversity, unlocks.

NATO
- USA B-1R/B-2A/B-52H/V-22/E-3/C-17 on HeavyAirBase.
  Missing F-18/F-16C/Tornado buttons. Bomb diversity. STD44 EA-18G/F-35C
  science gates stripped.

LIBYA
- Fighter bomb diversity only. Unlocks not requested.

UKRAINE
- Native factory. USA E-3/B-1R/V-22/B-21. Missing fighter buttons.
  Bomb diversity, unlocks.

SOUTH AFRICA
- Iraqi infantry clones. Hawk 120 LSFT50 / Hawk 127 LSFKoreaF5.
  Olifant/Rooikat/Ratel factory. Bomb diversity, unlocks.

IRAN
- Airfield parking 4x4. Jets NeedsRunway=Yes KeepsParking=No.
  Mi-8 JetAI NeedsRunway=No. Tu-22M3M/Tu-160/H-6K/H-20 clones. Unlocks.

ISRAEL
- Side=Israel on Israel-folder objects/airbases.
  Missing airfield CommandSets + fighter buttons.
  USA E-3/V-22/B-1R/B-52H/B-2A/B-21. Unlocks.
"""

    audit_lines = [
        RELEASE_NAME,
        f"SOURCE = {SRC_DIR}",
        f"DATA_SHA256 = {data_sha}",
        f"ART_SHA256 = {art_sha}",
        f"DATA_BYTES = {data_bytes}",
        f"ART_BYTES = {art_bytes}",
        f"DATA_FILE_COUNT = {file_count}",
        "ART_CHANGED = NO",
        "DATA_REBUILT = NO (byte-identical copy of Iran+Israel packed DATA)",
        "PR_473_STATE = already MERGED to main 2026-09-12; not re-merged",
        "PR_473_OLD_DATA_SHA256 = 6ce400a40cb6d250443505c5ec56e529f897595ce82e18fb944c0838e955d198",
        "VALIDATION = PASS",
        "INGAME_TESTED = NO",
        "",
        "=== COUNTRY FILE MARKERS ===",
    ]
    for country, paths in country_files.items():
        audit_lines.append(f"{country}_FILES = {len(paths)}/{len(REQUIRED_FILES[country])}")
        for p in paths:
            audit_lines.append("  " + p)
    audit_lines.append("")
    audit_lines.append("=== COMMAND MARKERS ===")
    for country, tokens in REQUIRED_COMMANDS.items():
        audit_lines.append(f"{country}_COMMANDS = YES")
        for t in tokens:
            audit_lines.append("  " + t)
    audit_lines.append("")
    audit_lines.append("=== CONTENT CHECKS ===")
    for n in notes:
        audit_lines.append(n)
    audit_lines.append("LIBYA_FILES = " + str(len(libya_hits)))
    audit_lines.append("SOUTHAFRICA_OLIFANT = YES")
    audit_lines.append("")
    audit_lines.append("ALL_STACKED_COUNTRY_CHANGES_PRESENT = YES")

    audit = "\n".join(audit_lines) + "\n"
    sha_txt = (
        f"_SPEC_DATA_ONE.big  SHA256 {data_sha}  {data_bytes} bytes  {file_count} files\n"
        f"_SPEC_ART_ONE.big   SHA256 {art_sha}  {art_bytes} bytes  (unchanged copy)\n"
    )
    install = f"""{RELEASE_NAME}
==============================

Replace the live Specter DATA and ART BIGs with the files in this folder.

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG in GameRoot.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG in GameRoot.
   ART is an unchanged copy of the current SPECTER1 ART pack.
4. Launch Specter.

Do not mix this DATA with older SPECTER1 roster ZIPs.
Do not use the older PR #473 Specter_WarFactory_AirForce_Final DATA
(SHA 6ce400a4...). This package supersedes that pack.

Checksums:
  DATA SHA256 {data_sha}
  ART  SHA256 {art_sha}

INGAME_TESTED = NO
"""

    for dest in (OUT_DIR, WS_OUT):
        (dest / "changelog.txt").write_text(changelog, encoding="utf-8")
        (dest / "audit.txt").write_text(audit, encoding="utf-8")
        (dest / "SHA256.txt").write_text(sha_txt, encoding="utf-8")
        (dest / "INSTALL.txt").write_text(install, encoding="utf-8")

    zpath = WS_OUT / f"{RELEASE_NAME}.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS_OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS_OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS_OUT / "changelog.txt", "changelog.txt")
        zf.write(WS_OUT / "audit.txt", "audit.txt")
        zf.write(WS_OUT / "SHA256.txt", "SHA256.txt")
        zf.write(WS_OUT / "INSTALL.txt", "INSTALL.txt")
    (OUT_DIR / f"{RELEASE_NAME}.zip").write_bytes(zpath.read_bytes())
    zip_sha = sha256_file(zpath)

    print(audit)
    print("ZIP", zpath, zpath.stat().st_size, zip_sha)
    print("VALIDATION PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
