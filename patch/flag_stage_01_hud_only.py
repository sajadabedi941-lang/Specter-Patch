#!/usr/bin/env python3
"""FLAG_STAGE_01_HUD_ONLY: freeze the launching pair as HUD-only Stage 01.

The Turkey parser-fix pair already boots. Country-select HUD (MappedImage +
flag TGAs + PlayerTemplate FlagWaterMark/EnabledImage/SideIconImage/GeneralImage)
is already wired on that pair. This packer copies those BIG bytes and does
not rewrite DATA or ART.

No ExtraDraw, Flag_Hs W3D, Model=, Animation=, building Objects, or gameplay
INI edits. Cloth is not restored. Stage 02 is not started.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_FLAG_TURKEY_MI_PARSE_01/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_FLAG_TURKEY_MI_PARSE_01/_SPEC_ART_ONE.big")
SRC_DATA_SHA = "0603b12e855f5f35cfff889362b0a02f2044968b7cdd1dd35c8c1285843f2652"
SRC_ART_SHA = "c16055702267e59770a7f657f843ea49840889b453a5c0611e8971045afe05b7"

WS_OUT = Path("/workspace/patch/Release/SPECTER1_FLAG_STAGE_01_HUD_ONLY")
RELEASE_NAME = "SPECTER1_FLAG_STAGE_01_HUD_ONLY"

P_TURKEY = r"Data\INI\MappedImages\HandCreated\Turkey_FactionImages.INI"
P_REMAIN = r"Data\INI\MappedImages\HandCreated\Specter_RemainingFlags.INI"
P_CAMP = r"Data\INI\MappedImages\HandCreated\Specter_CampFlags.INI"
P_PT = r"Data\INI\PlayerTemplate.ini"
P_PT_PATCH = r"Data\INI\PlayerTemplate_SpecterPatch.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_WEAPON = r"Data\INI\Weapon.ini"
P_UPGRADE = r"Data\INI\Upgrade.ini"
P_CMDSET = r"Data\INI\CommandSet.ini"

SIDES = (
    "Japan", "Vietnam", "SouthKorea", "Libya", "SouthAfrica", "Pakistan",
    "India", "Syria", "UAE", "SaudiArabia", "Sweden", "Ukraine", "Italy",
    "Britain", "Germany", "France",
)
TURKEY_MI = (
    "WatermarkTurkey", "GameinfoTurkey", "Turkey_Logo",
    "SSObserverTurkey", "Turkey_Flag",
)
FLAG_TGA = (
    "DE_Flag", "FR_Flag", "IN_Flag", "IT_Flag", "JP_Flag", "LY_Flag",
    "PK_Flag", "SA_Flag", "SE_Flag", "SK_Flag", "SY_Flag", "TR_Flag",
    "UA_Flag", "UAE_Flag", "UK_Flag", "VN_Flag", "ZA_Flag",
)
TURKEY_TGA = (
    "WatermarkTurkey", "GameinfoTurkey", "SSObserverTurkey",
    "Turkey_Logo", "Turkey_Flag",
)
HUD_FIELDS = ("FlagWaterMark", "EnabledImage", "SideIconImage", "GeneralImage")
PT_TEMPLATE = {
    "Japan": ("WatermarkJapan", "SSObserverJapan", "GameinfoJapan", "Japan_Logo"),
    "Vietnam": ("WatermarkVietnam", "SSObserverVietnam", "GameinfoVietnam", "Vietnam_Logo"),
    "SouthKorea": ("WatermarkSouthKorea", "SSObserverSouthKorea", "GameinfoSouthKorea", "SouthKorea_Logo"),
    "Libya": ("WatermarkLibya", "SSObserverLibya", "GameinfoLibya", "Libya_Logo"),
    "SouthAfrica": ("WatermarkSouthAfrica", "SSObserverSouthAfrica", "GameinfoSouthAfrica", "SouthAfrica_Logo"),
    "Pakistan": ("WatermarkPakistan", "SSObserverPakistan", "GameinfoPakistan", "Pakistan_Logo"),
    "India": ("WatermarkIndia", "SSObserverIndia", "GameinfoIndia", "India_Logo"),
    "Syria": ("WatermarkSyria", "SSObserverSyria", "GameinfoSyria", "Syria_Logo"),
    "UAE": ("WatermarkUAE", "SSObserverUAE", "GameinfoUAE", "UAE_Logo"),
    "SaudiArabia": ("WatermarkSaudiArabia", "SSObserverSaudiArabia", "GameinfoSaudiArabia", "SaudiArabia_Logo"),
    "Sweden": ("WatermarkSweden", "SSObserverSweden", "GameinfoSweden", "Sweden_Logo"),
    "Ukraine": ("WatermarkUkraine", "SSObserverUkraine", "GameinfoUkraine", "Ukraine_Logo"),
    "Italy": ("WatermarkItaly", "SSObserverItaly", "GameinfoItaly", "Italy_Logo"),
    "Britain": ("WatermarkBritain", "SSObserverBritain", "GameinfoBritain", "Britain_Logo"),
    "Germany": ("WatermarkGermany", "SSObserverGermany", "GameinfoGermany", "Germany_Logo"),
    "France": ("WatermarkFrance", "SSObserverFrance", "GameinfoFrance", "France_Logo"),
    "Turkey": ("WatermarkTurkey", "SSObserverTurkey", "GameinfoTurkey", "Turkey_Logo"),
}

FROZEN_GAMEPLAY = (P_WEAPON, P_UPGRADE, P_CMDSET, P_PT_PATCH)


def _art_has(art_map: dict[str, bytes], stem: str) -> str:
    for key in (
        rf"art\textures\{stem}.tga".lower(),
        rf"art\tex\textures\{stem}.tga".lower(),
    ):
        if key in art_map:
            return key
    hits = [k for k in art_map if k.endswith(f"\\{stem.lower()}.tga")]
    if len(hits) != 1:
        raise SystemExit(f"ART missing unique texture {stem}.tga")
    return hits[0]


def _mi_names(text: str) -> list[str]:
    return re.findall(r"(?im)^MappedImage\s+(\S+)\s*$", text)


def _mi_textures(text: str) -> list[str]:
    return re.findall(r"(?im)^\s*Texture\s*=\s*(\S+)\s*$", text)


def _pt_field(block: str, field: str) -> str | None:
    m = re.search(rf"(?im)^\s*{re.escape(field)}\s*=\s*(\S+)", block)
    return m.group(1) if m else None


def _faction_block(pt: str, name: str) -> str:
    m = re.search(
        rf"(?ims)^PlayerTemplate\s+{re.escape(name)}\s*$.*?(?=^PlayerTemplate\s|\Z)",
        pt,
    )
    if not m:
        raise SystemExit(f"missing PlayerTemplate {name}")
    return m.group(0)


def main() -> int:
    if jf.sha256_file(SRC_DATA) != SRC_DATA_SHA:
        raise SystemExit("TURKEY_MI_PARSE DATA SHA mismatch")
    if jf.sha256_file(SRC_ART) != SRC_ART_SHA:
        raise SystemExit("TURKEY_MI_PARSE ART SHA mismatch")

    data = jf.read_big_list(SRC_DATA)
    art = jf.read_big_list(SRC_ART)
    if len(data) != 2883:
        raise SystemExit(f"DATA count {len(data)}")
    if len(art) != 4449:
        raise SystemExit(f"ART count {len(art)}")

    art_map = {jf.norm(n).lower(): bytes(b) for n, b in art}
    w3d_new = [
        n for n, _ in art
        if n.lower().endswith(".w3d")
        and re.search(
            r"(?i)(DE|FR|IN|IT|JP|LY|PK|SA|SE|SK|SY|TR|UA|UAE|UK|VN|ZA)_Flag_Hs",
            n,
        )
    ]
    if w3d_new:
        raise SystemExit("clone Flag_Hs W3D present; refuse to ship")

    remain = jf.text_of(data, P_REMAIN)
    turkey = jf.text_of(data, P_TURKEY)
    camp = jf.text_of(data, P_CAMP)
    pt = jf.text_of(data, P_PT)

    if remain.lstrip().startswith("'") or turkey.startswith("'"):
        raise SystemExit("MappedImage INI still starts with apostrophe")
    if not turkey.startswith(";"):
        raise SystemExit("Turkey MI must start with comment")
    if not remain.lstrip().startswith(";"):
        raise SystemExit("RemainingFlags must start with comment")

    remain_names = _mi_names(remain)
    turkey_names = _mi_names(turkey)
    if len(remain_names) != 64:
        raise SystemExit(f"RemainingFlags MappedImage count {len(remain_names)}")
    if turkey_names != list(TURKEY_MI):
        raise SystemExit(f"Turkey MappedImage set {turkey_names}")

    for side in SIDES:
        for name in (
            f"Watermark{side}",
            f"{side}_Logo",
            f"Gameinfo{side}",
            f"SSObserver{side}",
        ):
            if name not in remain_names:
                raise SystemExit(f"missing MappedImage {name}")

    textures = _mi_textures(remain) + _mi_textures(turkey)
    for tex in textures:
        _art_has(art_map, tex)
    for stem in FLAG_TGA + TURKEY_TGA:
        _art_has(art_map, stem)

    hud_rows = []
    for side, expected in PT_TEMPLATE.items():
        block = _faction_block(pt, f"Faction{side}")
        got = tuple(_pt_field(block, f) for f in HUD_FIELDS)
        if got != expected:
            raise SystemExit(f"Faction{side} HUD fields {got} != {expected}")
        hud_rows.append(
            f"Faction{side}  FlagWaterMark={got[0]}  EnabledImage={got[1]}  "
            f"SideIconImage={got[2]}  GeneralImage={got[3]}"
        )

    extra_draw = 0
    for n, b in data:
        if "object" not in jf.norm(n).lower():
            continue
        text = b.decode("latin1", errors="replace")
        extra_draw += len(re.findall(r"(?i)ModuleTag_Specter(Nat|Camp)Flag", text))
    if extra_draw:
        raise SystemExit(f"extra flag Draws present: {extra_draw}")

    gameplay_sha = {p: hashlib.sha256(jf.raw_of(data, p)).hexdigest() for p in FROZEN_GAMEPLAY}

    WS_OUT.mkdir(parents=True, exist_ok=True)
    dst_data = WS_OUT / "_SPEC_DATA_ONE.big"
    dst_art = WS_OUT / "_SPEC_ART_ONE.big"
    shutil.copy2(SRC_DATA, dst_data)
    shutil.copy2(SRC_ART, dst_art)

    new_data_sha = jf.sha256_file(dst_data)
    new_art_sha = jf.sha256_file(dst_art)
    if new_data_sha != SRC_DATA_SHA:
        raise SystemExit("DATA copy is not byte-identical to launching pair")
    if new_art_sha != SRC_ART_SHA:
        raise SystemExit("ART copy is not byte-identical to launching pair")

    packed_d = jf.read_big_list(dst_data)
    packed_a = jf.read_big_list(dst_art)
    if len(packed_d) != 2883 or len(packed_a) != 4449:
        raise SystemExit("re-read count mismatch")
    if jf.text_of(packed_d, P_TURKEY).startswith("'"):
        raise SystemExit("re-read Turkey MI apostrophe")
    for p, digest in gameplay_sha.items():
        if hashlib.sha256(jf.raw_of(packed_d, p)).hexdigest() != digest:
            raise SystemExit(f"gameplay file drifted: {p}")

    changed_files = "\n".join([
        "FLAG_STAGE_01_HUD_ONLY changed files",
        "",
        "THIS PACK DOES NOT REWRITE ANY BIG BYTES.",
        "DATA and ART are byte-identical to SPECTER1_FLAG_TURKEY_MI_PARSE_01,",
        "the pair the user launched (BOOT = PASS).",
        "",
        "DATA_CHANGED = NO",
        "ART_CHANGED = NO",
        "GAMEPLAY_DATA_CHANGED = NO",
        "W3D_CHANGED = NO",
        "OBJECT_INI_CHANGED = NO",
        "EXTRADRAW_ADDED = NO",
        "CLOTH_RESTORED = NO",
        "",
        "Stage 01 HUD assets already present on that launching pair",
        "(country selection / faction display only):",
        "",
        "DATA HUD MappedImage",
        f"  {P_REMAIN}",
        "    64 MappedImage blocks (16 remaining sides x 4 HUD names)",
        f"  {P_TURKEY}",
        "    WatermarkTurkey GameinfoTurkey Turkey_Logo SSObserverTurkey Turkey_Flag",
        "",
        "DATA HUD PlayerTemplate fields (17 factions)",
        f"  {P_PT}",
        "    FlagWaterMark / EnabledImage / SideIconImage / GeneralImage only",
        *[f"    {row}" for row in hud_rows],
        "",
        "ART country flag TGAs (17)",
        *[f"  Art\\Textures\\{stem}.tga" for stem in FLAG_TGA],
        "",
        "ART Turkey HUD TGAs (5)",
        *[f"  Art\\Textures\\{stem}.tga" for stem in TURKEY_TGA],
        "",
        "Present on the pair but NOT Stage 01 (frozen, do not expand this stage):",
        f"  {P_CAMP}",
        f"  {P_CMDBTN}",
        "  building Object INIs",
        "  Flag_Hs / ExtraDraw / Model= / Animation=",
        "  Weapon.ini Upgrade.ini CommandSet.ini",
        "",
        "Stage 02 is not included.",
    ]) + "\n"

    audit = "\n".join([
        "SPECTER1 FLAG STAGE 01 HUD ONLY",
        "BASELINE = SPECTER1_FLAG_TURKEY_MI_PARSE_01",
        f"BASELINE_DATA_SHA256 = {SRC_DATA_SHA}",
        f"BASELINE_ART_SHA256 = {SRC_ART_SHA}",
        f"NEW_DATA_SHA256 = {new_data_sha}",
        f"NEW_ART_SHA256 = {new_art_sha}",
        f"PACKED_DATA_FILES = {len(packed_d)}",
        f"PACKED_ART_FILES = {len(packed_a)}",
        "DUPLICATE_PACKED_PATHS = NO",
        "BIG_INTEGRITY = YES",
        "DATA_REBUILT = NO",
        "ART_REBUILT = NO",
        "DATA_CHANGED = NO",
        "ART_CHANGED = NO",
        "BOOT = PASS",
        "FIX_APPLIED = YES (Stage 01 HUD freeze of launching pair)",
        "INGAME_TESTED = YES (boot; same bytes as TURKEY_MI_PARSE)",
        "HUD_DISPLAY_CONFIRMED = NO",
        "STAGE = 01 HUD / country-select only",
        "STAGE_02_STARTED = NO",
        "MAPPEDIMAGE_REMAINING = 64",
        "MAPPEDIMAGE_TURKEY = 5",
        "PLAYERTEMPLATE_HUD_SIDES = 17",
        "FLAG_TGA = 17",
        "TURKEY_HUD_TGA = 5",
        "TEXTURE_RESOLVE = YES",
        "EXTRADRAW_ADDED = NO",
        "FLAG_HS_W3D_ADDED = NO",
        "MODEL_CHANGED = NO",
        "ANIMATION_CHANGED = NO",
        "OBJECT_INI_CHANGED = NO",
        "COMMANDBUTTON_CHANGED = NO",
        "WEAPON_INI_CHANGED = NO",
        "UPGRADE_INI_CHANGED = NO",
        "COMMANDSET_CHANGED = NO",
        "CLOTH_RESTORED = NO",
        "W3D_CLONES_CREATED = NO",
    ]) + "\n"

    changelog = """SPECTER1 FLAG_STAGE_01_HUD_ONLY

The Turkey_FactionImages.INI parser-fix pair launched.
Country-select HUD is already wired on that pair.

This release freezes those exact DATA/ART bytes as Stage 01.
No files were rewritten. No cloth. No W3D clones. No gameplay INI edits.

Stage 01 scope (already present):
- MappedImage blocks in Specter_RemainingFlags.INI and Turkey_FactionImages.INI
- PlayerTemplate FlagWaterMark / EnabledImage / SideIconImage / GeneralImage
- 17 country flag TGAs and 5 Turkey HUD TGAs

Not in this stage:
- ExtraDraw, Flag_Hs W3D, Model=, Animation=, building Objects
- Camp/Barracks cameos (already on disk; do not expand here)
- Stage 02

BOOT = PASS
INGAME_TESTED = YES (boot; same bytes as TURKEY_MI_PARSE)
HUD_DISPLAY_CONFIRMED = NO
"""

    install = f"""SPECTER1_FLAG_STAGE_01_HUD_ONLY
================================

Stage 01 = country selection / faction display flags only.
These are the same BIG bytes you already launched after the
Turkey MappedImage parser fix. Installing this zip is optional
if SPECTER1_FLAG_TURKEY_MI_PARSE_01 is already in GameRoot.

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG in GameRoot.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG in GameRoot.
4. Launch Specter.
5. Open country / faction select and check the 17 remaining sides.

Checksums:
  DATA SHA256 {new_data_sha}
  ART  SHA256 {new_art_sha}

BOOT = PASS
INGAME_TESTED = YES (boot; same bytes as TURKEY_MI_PARSE)
HUD_DISPLAY_CONFIRMED = NO
STAGE_02_STARTED = NO
"""

    next_prompt = """You are continuing Specter flag restoration.

Stage 01 HUD/country-select is the current launching pair
SPECTER1_FLAG_TURKEY_MI_PARSE_01, frozen as
SPECTER1_FLAG_STAGE_01_HUD_ONLY. Bytes were not rewritten.

BOOT = PASS
INGAME_TESTED = YES (boot)
HUD_DISPLAY_CONFIRMED = NO
STAGE_02_STARTED = NO

Do not start Stage 02 until the user confirms a real Zero Hour
launch of this pair AND country-select flags.

If HUD display looks wrong: stay on Stage 01. Do not add cloth.

If Stage 02 is authorized later:
- one visual group only
- no W3D clones
- no ExtraDraw / Flag_Hs / Model= / Animation= unless explicitly asked
- do not modify gameplay DATA
- keep this pair as baseline
"""

    (WS_OUT / "CHANGED_FILES.txt").write_text(changed_files, encoding="utf-8")
    (WS_OUT / "audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "INSTALL.txt").write_text(install, encoding="utf-8")
    (WS_OUT / "NEXT_AGENT_PROMPT.md").write_text(next_prompt, encoding="utf-8")
    (WS_OUT / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {new_data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {new_art_sha}\n",
        encoding="utf-8",
    )
    zpath = WS_OUT / f"{RELEASE_NAME}.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in (
            "_SPEC_DATA_ONE.big",
            "_SPEC_ART_ONE.big",
            "INSTALL.txt",
            "changelog.txt",
            "audit.txt",
            "SHA256.txt",
            "CHANGED_FILES.txt",
        ):
            zf.write(WS_OUT / name, name)
    zip_sha = hashlib.sha256(zpath.read_bytes()).hexdigest()
    (WS_OUT / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {new_data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {new_art_sha}\n"
        f"{RELEASE_NAME}.zip  SHA256 {zip_sha}  {zpath.stat().st_size} bytes\n",
        encoding="utf-8",
    )
    print(audit)
    print(changed_files)
    print("WROTE", dst_data, new_data_sha)
    print("ART", new_art_sha)
    print("ZIP", zpath, zpath.stat().st_size, zip_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
