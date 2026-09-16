#!/usr/bin/env python3
"""SPECTER1 WarFactory construction/use fix.

Baseline: SPECTER1_FINAL_ROSTER_UPDATE DATA+ART.
Does not modify working factions: USA, Iran, Israel, NATO, Iraq, Italy,
UK, Vietnam, Egypt, Russia, China.
Does not modify aircraft, weapons, upgrades, or ART.
Only WarFactory Draw animation hybrids and wrong-Side WF CommandSets.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_FINAL_ROSTER_UPDATE/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_FINAL_ROSTER_UPDATE/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "2a06ca987362da5ffecd2121c85d2e49a6da8bb4ee80ac1a45bb9278d74b5921"
EXPECTED_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"
OUT_DIR = Path("/tmp/SPECTER1_WARFACTORY_BUILD_FIX")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_WARFACTORY_BUILD_FIX")

P_CMDSET = r"Data\INI\CommandSet.ini"

# Dest WF objects with hybrid Model.WrongAnimation that prevent placement.
# Map packed path -> (dest_model, working_donor_model)
DRAW_FIXES = {
    r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_WarFactory.ini":
        ("IN_WarFactory", "Irq_WarFactory"),
    r"Data\INI\Object\Specter\German Armed Forces\Buildings\Warfactory.ini":
        ("DE_WarFactory", "US_WarFactory"),
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_WarFactory.ini":
        ("JP_WarFactory", "NKr_WarFactory"),
    r"Data\INI\Object\Specter\French Armed Forces\Buildings\Warfactory.ini":
        ("FR_WarFactory", "US_WarFactory"),
    r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\SouthKorea_WarFactory.ini":
        ("SK_WarFactory", "NKr_WarFactory"),
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_WarFactory.ini":
        ("SA_WarFactory", "Irq_WarFactory"),
    r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\Warfactory.ini":
        ("SE_WarFactory", "US_WarFactory"),
    r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_WarFactory.ini":
        ("AE_WarFactory", "Irq_WarFactory"),
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Buildings\Warfactory.ini":
        ("UA_WarFactory", "US_WarFactory"),
    r"Data\INI\Object\Specter\Turkish Armed Forces\Buildings\Warfactory.ini":
        ("TR_WarFactory", "US_WarFactory"),
}

PROTECTED_WF_PATHS = {
    r"Data\INI\Object\Specter\United States Of America\Buildings\Warfactory.ini",
    r"Data\INI\Object\Specter\United States Of America\Buildings\Warfactory_AI.ini",
    r"Data\INI\Object\Specter\Iranian Army\Buildings\Warfactory.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_WarFactory.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_WarFactory_AI.ini",
    r"Data\INI\Object\Specter\Iraq Army\AI\Iraq_WarFactory.ini",
    r"Data\INI\Object\Specter\NATO\Buildings\Warfactory.ini",
    r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\Warfactory.ini",
    r"Data\INI\Object\Specter\British Armed Forces\Buildings\Warfactory.ini",
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_WarFactory.ini",
    r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_WarFactory.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\Warfactory.ini",
    r"Data\INI\Object\Specter\PLA\Buildings\Warfactory.ini",
    r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Warfactory.ini",
}

LIBYA_WF = [
    "  1  = Command_ConstructLibyaTankT72",
    "  2  = Command_ConstructLibyaTankT62",
    "  3  = Command_ConstructLibyaVehicleBMP1",
    "  4  = Command_ConstructLibyaVehicleM113",
    "  5  = Command_ConstructLibyaVehicle2S1",
    "  6  = Command_ConstructLibyaVehicleShilka",
    "  7  = Command_ConstructLibyaVehicleSA6",
    "  8  = Command_ConstructLibyaVehicleRadar",
    "  9  = Command_ConstructLibyaVehicleBM21",
    "  10 = Command_ConstructLibyaVehicleScudB",
    "  11 = Command_ConstructLibya_Alhussaien",
    "  12 = Command_ConstructLibyaVehicleATGM",
    "  13 = Command_ConstructLibyaVehicleBREM",
    "  14 = Command_Sell",
]
SYRIA_WF = [
    "  1  = Command_ConstructSyriaTankT72",
    "  2  = Command_ConstructSyriaTankT62",
    "  3  = Command_ConstructSyriaVehicleBMP1",
    "  4  = Command_ConstructSyriaVehicleBTR",
    "  5  = Command_ConstructSyriaVehicle2S1",
    "  6  = Command_ConstructSyriaVehicleShilka",
    "  7  = Command_ConstructSyriaVehicleBuk",
    "  8  = Command_ConstructSyriaVehicleP18",
    "  9  = Command_ConstructSyriaVehicleBM21",
    "  10 = Command_ConstructSyriaVehicleScud",
    "  11 = Command_ConstructSyriaVehicleTOS1A",
    "  12 = Command_ConstructSyriaVehicleKornet",
    "  13 = Command_ConstructSyriaVehicleBREM",
    "  14 = Command_Sell",
]
PAKISTAN_WF = [
    "  1  = Command_ConstructPakistanTankAlKhalid",
    "  2  = Command_ConstructPakistanTankAlZarrar",
    "  3  = Command_ConstructPakistanVehicleTalhaIFV",
    "  4  = Command_ConstructPakistanVehicleTalhaAPC",
    "  5  = Command_ConstructPakistanVehicleM109",
    "  6  = Command_ConstructPakistanVehicleLY80",
    "  7  = Command_ConstructPakistanVehicleHQ9P",
    "  8  = Command_ConstructPakistanVehicleRadar",
    "  9  = Command_ConstructPakistanVehicleA100",
    "  10 = Command_ConstructPakistanVehicleShaheen",
    "  11 = Command_ConstructPakistanVehicleNasr",
    "  12 = Command_ConstructPakistanVehicleBaktar",
    "  13 = Command_ConstructPakistanVehicleARV",
    "  14 = Command_Sell",
]
TURKEY_WF = [
    "  1  = Command_ConstructTurkeyTankLeopard2A7Plus",
    "  2  = Command_ConstructTurkeyTankPuma",
    "  3  = Command_ConstructTurkeyVehicleCortaleMK3",
    "  4  = Command_ConstructTurkeyVehicleVBCI",
    "  5  = Command_ConstructTurkeyVehicleM142",
    "  6  = Command_ConstructTurkeyVehicleCaesar",
    "  7  = Command_ConstructTurkeyVehicleCentauroB2",
    "  8  = Command_ConstructTurkeyVehicleIRIST",
    "  9  = Command_ConstructTurkeyVehicleTRML4D",
    "  10 = Command_ConstructTurkeyVehicleAltay",
    "  11 = Command_ConstructTurkeyVehicleFirtina",
    "  12 = Command_ConstructTurkeyVehicleHisar",
    "  13 = Command_ConstructTurkeyVehicleM88",
    "  14 = Command_Sell",
]

CS_FIXES = {
    "Libya_WarFactoryCommandSet": LIBYA_WF,
    "Libya_WarFactoryCommandSet1": LIBYA_WF,
    "Libya_WarFactoryCommandSet2": LIBYA_WF,
    "Libya_WarFactoryCommandSet3": LIBYA_WF,
    "Syria_WarFactoryCommandSet": SYRIA_WF,
    "Syria_WarFactoryCommandSet1": SYRIA_WF,
    "Syria_WarFactoryCommandSet2": SYRIA_WF,
    "Syria_WarFactoryCommandSet3": SYRIA_WF,
    "Pakistan_WarFactoryCommandSet": PAKISTAN_WF,
    "TurkeyWarfactoryCommandSet": TURKEY_WF,
}

WORKING = [
    "USA", "Iran", "Israel", "NATO", "Iraq", "Italy", "UK", "Vietnam",
    "Egypt", "Russia", "China",
]


def fix_hybrid_draw(text: str, dest_model: str, donor_model: str, label: str) -> str:
    nl = jf.file_nl(text)
    anim_pat = rf"(?im)^(\s*Animation\s*=\s*){re.escape(dest_model)}\.{re.escape(donor_model)}\b"
    model_pat = rf"(?im)^(\s*Model\s*=\s*){re.escape(dest_model)}\b"
    text2, n_anim = re.subn(anim_pat, rf"\1{donor_model}.{donor_model}", text)
    text3, n_model = re.subn(model_pat, rf"\1{donor_model}", text2)
    if n_anim < 1:
        raise SystemExit(f"{label}: no hybrid Animation {dest_model}.{donor_model} replaced")
    if n_model < 1:
        raise SystemExit(f"{label}: no Model {dest_model} replaced")
    if re.search(rf"(?im)^\s*Animation\s*=\s*{re.escape(dest_model)}\.{re.escape(donor_model)}\b", text3):
        raise SystemExit(f"{label}: hybrid animation still present")
    # Keep construction scaffolding models.
    if "UBArmDeal_DNS" in text and "UBArmDeal_DNS" not in text3:
        raise SystemExit(f"{label}: scaffolding model lost")
    return jf.to_nl(text3, nl) if False else text3


def cs_buttons(block: str) -> list[str]:
    return re.findall(r"(?im)^\s*\d+\s*=\s*(\S+)", block)


def parse_objects(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r"(?im)^Object\s+(\S+)\s*$", text):
        m2 = re.search(r"(?im)^Object\s+\S+", text[m.end() :])
        out[m.group(1)] = text[m.start() : m.end() + m2.start() if m2 else len(text)]
    return out


def field(block: str, key: str) -> str | None:
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block)
    return m.group(1).strip() if m else None


def main() -> int:
    if jf.sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("unexpected DATA SHA")
    if jf.sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("unexpected ART SHA")

    entries = jf.read_big_list(SRC_DATA)
    # Snapshot protected WF files for later equality check.
    protected_before = {p: jf.raw_of(entries, p) for p in PROTECTED_WF_PATHS}

    draw_changed = []
    for path, (dest_model, donor_model) in DRAW_FIXES.items():
        if path in PROTECTED_WF_PATHS:
            raise SystemExit(f"refusing to edit protected {path}")
        old = jf.text_of(entries, path)
        new = fix_hybrid_draw(old, dest_model, donor_model, path)
        if new == old:
            raise SystemExit(f"no change {path}")
        jf.set_text(entries, path, new)
        draw_changed.append((path, dest_model, donor_model))

    cs = jf.text_of(entries, P_CMDSET)
    for name, lines in CS_FIXES.items():
        cs = jf.replace_commandset(cs, name, lines)
    jf.set_text(entries, P_CMDSET, cs)

    # Safety: protected WF objects byte-identical.
    for p, raw in protected_before.items():
        if jf.raw_of(entries, p) != raw:
            raise SystemExit(f"protected WF mutated {p}")

    # Weapon.ini / ART untouched by construction.
    blob = jf.build_big_ordered(entries)
    new_sha = hashlib.sha256(blob).hexdigest()
    if new_sha == EXPECTED_DATA_SHA:
        raise SystemExit("DATA SHA unchanged")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(blob)
    (WS_OUT / "_SPEC_DATA_ONE.big").write_bytes(blob)
    shutil.copy2(SRC_ART, OUT_DIR / "_SPEC_ART_ONE.big")
    shutil.copy2(SRC_ART, WS_OUT / "_SPEC_ART_ONE.big")
    if jf.sha256_file(WS_OUT / "_SPEC_ART_ONE.big") != EXPECTED_ART_SHA:
        raise SystemExit("ART copy changed")

    # Validate packed result.
    packed = jf.read_big_list(WS_OUT / "_SPEC_DATA_ONE.big")
    cmdset = jf.parse_commandsets(jf.text_of(packed, P_CMDSET))
    cmdbtn = jf.parse_buttons(jf.text_of(packed, r"Data\INI\CommandButton.ini"))
    objs: dict[str, str] = {}
    for n, b in packed:
        if n.lower().endswith(".ini"):
            objs.update(parse_objects(b.decode("latin1", errors="replace")))

    def assert_cs_side(csname: str, side: str, label: str) -> list[str]:
        if csname not in cmdset:
            raise SystemExit(f"{label}: missing CS {csname}")
        ok = []
        for btn in cs_buttons(cmdset[csname]):
            if btn in ("Command_Sell", "Command_SetRallyPoint"):
                continue
            if btn not in cmdbtn:
                raise SystemExit(f"{label}: missing button {btn}")
            obj = field(cmdbtn[btn], "Object") or ""
            if obj not in objs:
                raise SystemExit(f"{label}: missing unit {obj}")
            uside = field(objs[obj], "Side")
            if uside != side:
                raise SystemExit(f"{label}: {obj} Side={uside} != {side}")
            ok.append(obj)
        if len(ok) < 8:
            raise SystemExit(f"{label}: too few same-Side units {len(ok)}")
        return ok

    libya_units = assert_cs_side("Libya_WarFactoryCommandSet", "Libya", "Libya")
    syria_units = assert_cs_side("Syria_WarFactoryCommandSet", "Syria", "Syria")
    pak_units = assert_cs_side("Pakistan_WarFactoryCommandSet", "Pakistan", "Pakistan")
    tur_units = assert_cs_side("TurkeyWarfactoryCommandSet", "Turkey", "Turkey")

    # Draw hybrids gone; donor animation present.
    for path, dest_model, donor_model in draw_changed:
        txt = jf.text_of(packed, path)
        if f"{dest_model}.{donor_model}" in txt:
            raise SystemExit(f"hybrid still in {path}")
        if f"Model              = {donor_model}" not in txt and f"Model           = {donor_model}" not in txt:
            if not re.search(rf"(?im)^\s*Model\s*=\s*{re.escape(donor_model)}\b", txt):
                raise SystemExit(f"{path}: donor Model missing")
        if not re.search(rf"(?im)^\s*Animation\s*=\s*{re.escape(donor_model)}\.{re.escape(donor_model)}\b", txt):
            raise SystemExit(f"{path}: donor Animation missing")

    # Working-faction construct buttons still present.
    for btn in (
        "Command_ConstructAmericaWarFactory",
        "Command_ConstructIranWarFactory",
        "Command_ConstructNatoWarFactory",
        "Command_ConstructIraq_WarFactory_T",
        "Command_ConstructItalyWarFactory",
        "Command_ConstructBritainWarFactory",
        "Command_ConstructVietnam_WarFactory",
        "Command_ConstructEgypt_WarFactory_T",
        "Command_ConstructRussiaWarFactory",
        "Command_ConstructChinaWarFactory",
    ):
        if btn not in cmdbtn:
            raise SystemExit(f"working construct button missing {btn}")

    repaired = [
        "India", "Germany", "Japan", "France", "SouthKorea", "SaudiArabia",
        "Sweden", "UAE", "Ukraine", "Turkey", "Libya", "Syria", "Pakistan",
    ]

    lines = [
        "SPECTER1 WARFACTORY BUILD FIX",
        f"BASELINE_DATA_SHA256 = {EXPECTED_DATA_SHA}",
        f"NEW_DATA_SHA256 = {new_sha}",
        f"ART_SHA256 = {EXPECTED_ART_SHA} (unchanged copy)",
        "ART_CHANGED = NO",
        "WEAPON_INI_CHANGED = NO",
        "AIRCRAFT_CHANGED = NO",
        "WORKING_FACTIONS_UNCHANGED = YES",
        "WORKING = " + ", ".join(WORKING),
        "WARFACTORY_FIXED = YES",
        "REPAIRED = " + ", ".join(repaired),
        "SOUTH_AFRICA = already native Side + matching Irq_WarFactory animation; not modified",
        "NORTH_KOREA = already native Side + matching NKr_WarFactory animation; not modified",
        "",
        "BUG = hybrid Model/Animation on dest WarFactory Draw (e.g. JP_WarFactory.NKr_WarFactory)",
        "FIX_DRAW = retarget Draw Model+Animation onto working donor W3D already in ART",
        "BUG2 = Libya/Syria/Pakistan/Turkey WF CommandSets produced wrong-Side units",
        "FIX_CS = retarget those CommandSets onto existing same-Side NationalGround/native vehicles",
        "",
        "DRAW_FIXES =",
    ]
    for path, dest, donor in draw_changed:
        lines.append(f"  {path}: {dest}.{donor} -> {donor}.{donor}")
    lines.append("")
    lines.append("LIBYA_UNITS = " + ", ".join(libya_units))
    lines.append("SYRIA_UNITS = " + ", ".join(syria_units))
    lines.append("PAKISTAN_UNITS = " + ", ".join(pak_units))
    lines.append("TURKEY_UNITS = " + ", ".join(tur_units))
    lines.append("")
    lines.append("INGAME_TESTED = NO")
    lines.append("DATA_CHANGED = YES")
    lines.append("ART_CHANGED = NO")
    audit = "\n".join(lines) + "\n"

    changelog = """SPECTER1 WarFactory build fix

Continues from SPECTER1_FINAL_ROSTER_UPDATE. Does not revert country roster work.
Does not modify USA / Iran / Israel / NATO / Iraq / Italy / UK / Vietnam / Egypt /
Russia / China WarFactory objects or CommandSets. Does not modify ART, aircraft,
weapons, or upgrades.

Bug: dest WarFactory Draw used hybrid animations (Model=JP_WarFactory with
Animation=JP_WarFactory.NKr_WarFactory, and the same pattern for India/Germany/
France/SK/Saudi/Sweden/UAE/Ukraine/Turkey). That is the known construction break.

Fix: WarFactory Draw Model+Animation retargeted onto working donor W3D already
packed in ART (US_WarFactory, Irq_WarFactory, or NKr_WarFactory).

Libya / Syria / Pakistan / Turkey WF CommandSets produced Iraq/GLA/Russia/Nato
units (Side mismatch, UNIT_BUILD fails). Retargeted onto existing same-Side
native vehicles. Buttons already existed.

South Africa and North Korea already had matching Draw + same-Side production
bars; left unchanged.

INGAME_TESTED = NO
"""

    install = f"""SPECTER1_WARFACTORY_FIX_UPDATE
==============================

WarFactory construction/use repair on the SPECTER1_FINAL_ROSTER_UPDATE baseline.
Repaired: India, Germany, Japan, France, South Korea, Saudi Arabia, Sweden, UAE,
Ukraine, Turkey, Libya, Syria, Pakistan.
Working factions unchanged: USA, Iran, Israel, NATO, Iraq, Italy, UK, Vietnam,
Egypt, Russia, China. ART, aircraft, weapons, and upgrades unchanged.

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG in GameRoot.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG in GameRoot.
   ART is an unchanged copy of the current SPECTER1 ART pack.
4. Launch Specter.

Do not mix this DATA with older SPECTER1 roster ZIPs.

Checksums:
  DATA SHA256 {new_sha}
  ART  SHA256 {EXPECTED_ART_SHA}

WARFACTORY_FIXED = YES
INGAME_TESTED = NO
"""
    for dest in (OUT_DIR, WS_OUT):
        (dest / "audit.txt").write_text(audit, encoding="utf-8")
        (dest / "changelog.txt").write_text(changelog, encoding="utf-8")
        (dest / "INSTALL.txt").write_text(install, encoding="utf-8")

    zpath = WS_OUT / "SPECTER1_WarFactory_Build_Fix.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS_OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS_OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS_OUT / "audit.txt", "audit.txt")
        zf.write(WS_OUT / "changelog.txt", "changelog.txt")
        zf.write(WS_OUT / "INSTALL.txt", "INSTALL.txt")
    (OUT_DIR / zpath.name).write_bytes(zpath.read_bytes())
    zip_sha = hashlib.sha256(zpath.read_bytes()).hexdigest()
    sha_txt = (
        f"_SPEC_DATA_ONE.big  SHA256 {new_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {EXPECTED_ART_SHA} (unchanged copy)\n"
        f"SPECTER1_WarFactory_Build_Fix.zip  SHA256 {zip_sha}  {zpath.stat().st_size} bytes\n"
    )
    for dest in (OUT_DIR, WS_OUT):
        (dest / "SHA256.txt").write_text(sha_txt, encoding="utf-8")
    print(audit)
    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", new_sha)
    print("ZIP", zpath, zpath.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
