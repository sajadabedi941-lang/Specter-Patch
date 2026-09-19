#!/usr/bin/env python3
"""Fix remaining-faction infantry Camp/Barracks flag images.

Baseline: SPECTER1_FACTION_FLAGS_REMAINING_01 (PR #516).
3D camp cloth is already native on that baseline. This pass replaces the
leftover USA/Iraq camp portraits and construct cameos with the same
national flag TGAs, and re-checks Camp/Barracks flag attachments.

Does not touch protected factions: USA, Iran, Israel, China, Russia, NATO,
Egypt, North Korea, Iraq.

Weapon.ini / Upgrade.ini / CommandSet.ini unchanged. CommandButton.ini
changes are ButtonImage flag refs on the 17 camp construct buttons only.
Object names and Country IDs unchanged. Same two BIG names. No loose files.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_FACTION_FLAGS_REMAINING_01/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_FACTION_FLAGS_REMAINING_01/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "c29a14b27609c7e87ceba5df0edbf69ca3d67222a5ef03a030986c228e07d622"
EXPECTED_ART_SHA = "e1f603a06c3ccb18601e046d0fef212c56888425db3e77fcd5a69be3c612c8c9"
OUT_DIR = Path("/tmp/SPECTER1_FACTION_CAMP_FLAGS_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_FACTION_CAMP_FLAGS_01")
RELEASE_NAME = "SPECTER1_FACTION_CAMP_FLAGS_01"

P_PT = r"Data\INI\PlayerTemplate.ini"
P_PT_PATCH = r"Data\INI\PlayerTemplate_SpecterPatch.ini"
P_MI = r"Data\INI\MappedImages\HandCreated\Specter_CampFlags.INI"
P_WEAPON = r"Data\INI\Weapon.ini"
P_UPGRADE = r"Data\INI\Upgrade.ini"
P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"

PROTECTED_TEMPLATES = {
    "FactionAmerica", "FactionIsrael", "FactionChina", "FactionRussia",
    "FactionIran", "FactionIraq", "FactionNorthKorea", "FactionNato",
    "FactionEgypt",
}
PROTECTED_FOLDER = (
    "united states of america", "israel defense forces", "pla",
    "armed forces of russian federation", "iranian army", "iraq army",
    "north korea", "nato", "egyptian armed forces",
)

SIDES = {
    "Japan": "JP_Flag.tga",
    "Vietnam": "VN_Flag.tga",
    "SouthKorea": "SK_Flag.tga",
    "Libya": "LY_Flag.tga",
    "SouthAfrica": "ZA_Flag.tga",
    "Pakistan": "PK_Flag.tga",
    "India": "IN_Flag.tga",
    "Syria": "SY_Flag.tga",
    "UAE": "UAE_Flag.tga",
    "SaudiArabia": "SA_Flag.tga",
    "Turkey": "TR_Flag.tga",
    "Sweden": "SE_Flag.tga",
    "Ukraine": "UA_Flag.tga",
    "Italy": "IT_Flag.tga",
    "Britain": "UK_Flag.tga",
    "Germany": "DE_Flag.tga",
    "France": "FR_Flag.tga",
}

FOLDER_SIDE = {
    "japan self-defense forces": "Japan",
    "vietnam people's armed forces": "Vietnam",
    "south korean armed forces": "SouthKorea",
    "libyan armed forces": "Libya",
    "south african national defence force": "SouthAfrica",
    "pakistan armed forces": "Pakistan",
    "indian armed forces": "India",
    "syrian armed forces": "Syria",
    "united arab emirates armed forces": "UAE",
    "saudi arabia armed forces": "SaudiArabia",
    "turkish armed forces": "Turkey",
    "swedish armed forces": "Sweden",
    "ukrainian armed forces": "Ukraine",
    "italian armed forces": "Italy",
    "british armed forces": "Britain",
    "german armed forces": "Germany",
    "french armed forces": "France",
}

CAMP_OBJECTS = {
    "Japan_Barracks": "Japan",
    "Vietnam_Barracks": "Vietnam",
    "SouthKorea_Barracks": "SouthKorea",
    "Libya_Barracks": "Libya",
    "SouthAfrica_Barracks": "SouthAfrica",
    "Pakistan_Barracks": "Pakistan",
    "India_Barracks": "India",
    "Syria_Barracks": "Syria",
    "UAE_Barracks": "UAE",
    "SaudiArabia_Barracks": "SaudiArabia",
    "TurkeyBootCamp": "Turkey",
    "SwedenBootCamp": "Sweden",
    "UkraineBootCamp": "Ukraine",
    "ItalyBootCamp": "Italy",
    "BritainBootCamp": "Britain",
    "GermanyBootCamp": "Germany",
    "FranceBootCamp": "France",
}

WRONG_CAMEOS = {"us_camp", "irq_barracks", "SUBarracks", "SUBarracks_L", "SABarracks"}
DONOR_MODELS = (
    "irq_camp", "Irq__IqFlag_Hs", "NKr__NKFlag_Hs",
)
HS_OF = {
    "Japan": "JP_Flag_Hs", "Vietnam": "VN_Flag_Hs", "SouthKorea": "SK_Flag_Hs",
    "Libya": "LY_Flag_Hs", "SouthAfrica": "ZA_Flag_Hs", "Pakistan": "PK_Flag_Hs",
    "India": "IN_Flag_Hs", "Syria": "SY_Flag_Hs", "UAE": "UAE_Flag_Hs",
    "SaudiArabia": "SA_Flag_Hs", "Turkey": "TR_Flag_Hs", "Sweden": "SE_Flag_Hs",
    "Ukraine": "UA_Flag_Hs", "Italy": "IT_Flag_Hs", "Britain": "UK_Flag_Hs",
    "Germany": "DE_Flag_Hs", "France": "FR_Flag_Hs",
}


def folder_side(path: str) -> str | None:
    low = jf.norm(path).lower()
    for folder, side in FOLDER_SIDE.items():
        if f"\\{folder}\\" in low:
            return side
    return None


def in_protected(path: str) -> bool:
    low = jf.norm(path).lower()
    return any(f"\\{p}\\" in low for p in PROTECTED_FOLDER)


def is_camp_ini(path: str) -> bool:
    low = jf.norm(path).lower()
    if not low.endswith(".ini") or "\\object\\specter\\" not in low:
        return False
    if "\\buildings\\" not in low:
        return False
    fname = low.split("\\")[-1]
    return fname in ("camp.ini",) or "barracks" in fname


def camp_image(side: str) -> str:
    return f"CampFlag{side}"


def mi_block(name: str, tex: str) -> str:
    return (
        f"MappedImage {name}\r\n"
        f"  Texture = {tex}\r\n"
        f"  TextureWidth = 128\r\n"
        f"  TextureHeight = 64\r\n"
        f"  Coords = Left:0 Top:0 Right:128 Bottom:64\r\n"
        f"  Status = NONE\r\n"
        f"End\r\n"
    )


def parse_buttons(text: str) -> list[tuple[str, int, int]]:
    out = []
    for m in re.finditer(r"(?im)^CommandButton\s+(\S+)\s*$", text):
        m2 = re.search(r"(?im)^CommandButton\s+\S+", text[m.end():])
        end = m.end() + m2.start() if m2 else len(text)
        out.append((m.group(1), m.start(), end))
    return out


def extra_flag_draw(mesh: str, nl: str) -> str:
    return (
        "  Draw = W3DModelDraw ModuleTag_SpecterCampFlag" + nl
        + "    OkToChangeModelColor = No" + nl
        + "    DefaultConditionState" + nl
        + f"      Model = {mesh}" + nl
        + "      Animation = Irq__IqFlag_Hs.Irq__IqFlag_Hs" + nl
        + "      AnimationMode = LOOP" + nl
        + "    End" + nl
        + "  End" + nl
    )


def insert_flag_draw(text: str, mesh: str) -> str:
    if "ModuleTag_SpecterCampFlag" in text or "ModuleTag_SpecterNatFlag" in text:
        return text
    draw = extra_flag_draw(mesh, jf.file_nl(text))
    m = re.search(r"(?im)^[ \t]*Draw\s*=", text)
    if not m:
        raise SystemExit("cannot find camp Draw insertion point")
    return text[:m.start()] + draw + text[m.start():]


def main() -> int:
    if jf.sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("source DATA SHA mismatch")
    if jf.sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("source ART SHA mismatch")

    data = jf.read_big_list(SRC_DATA)
    art = jf.read_big_list(SRC_ART)
    if len(data) != 2882 or len(art) != 4509:
        raise SystemExit(f"packed count {len(data)}/{len(art)}")

    src_weapon = jf.raw_of(data, P_WEAPON)
    src_upgrade = jf.raw_of(data, P_UPGRADE)
    src_cmdset = jf.raw_of(data, P_CMDSET)
    src_pt = jf.raw_of(data, P_PT)
    src_pt_patch = jf.raw_of(data, P_PT_PATCH)
    src_cmdbtn = jf.text_of(data, P_CMDBTN)
    protected_files = {
        jf.norm(n).lower(): bytes(b)
        for n, b in data
        if in_protected(n)
    }

    art_map = {jf.norm(n).lower() for n, _ in art}
    for stem in SIDES.values():
        if f"art\\textures\\{stem}".lower() not in art_map:
            raise SystemExit(f"ART missing {stem}")
        side = next(s for s, st in SIDES.items() if st == stem)
        if f"art\\w3d\\{HS_OF[side]}.w3d".lower() not in art_map:
            raise SystemExit(f"ART missing {HS_OF[side]}")

    # ---- DATA: camp flag MappedImages (reuse packed national TGAs) ----
    chunks = [
        "; SPECTER - infantry Camp/Barracks flag images (select / HUD cameo)\r\n"
        "; Texture paths are the packed Art\\Textures\\<stem> national flags.\r\n"
    ]
    for side, stem in SIDES.items():
        chunks.append(mi_block(camp_image(side), stem[:-4]))
    jf.add_file(data, P_MI, "".join(chunks))

    # ---- DATA: camp Object SelectPortrait / ButtonImage ----
    portrait_swaps = 0
    extra_draws = 0
    camp_files = 0
    for idx, (fname, blob) in enumerate(data):
        if not is_camp_ini(fname) or in_protected(fname):
            continue
        side = folder_side(fname)
        if side not in SIDES:
            continue
        text = blob.decode("latin-1", errors="replace")
        orig = text
        img = camp_image(side)
        for key in ("SelectPortrait", "ButtonImage"):
            text, n = re.subn(
                rf"(?im)^(\s*{key}\s*=\s*)\S+",
                rf"\1{img}",
                text,
            )
            portrait_swaps += n
        models = set(re.findall(r"(?im)^\s*Model\s*=\s*(\S+)", text))
        has_native_cloth = any(
            m.startswith("irq_camp_") or m == HS_OF[side] for m in models
        )
        has_extra = (
            "ModuleTag_SpecterNatFlag" in text
            or "ModuleTag_SpecterCampFlag" in text
        )
        if not has_native_cloth and not has_extra:
            text = insert_flag_draw(text, HS_OF[side])
            extra_draws += 1
        leftover = [d for d in DONOR_MODELS if re.search(
            rf"(?im)^\s*Model\s*=\s*{re.escape(d)}\s*$", text
        )]
        if leftover:
            raise SystemExit(f"{fname} leftover donor models {leftover}")
        if text != orig:
            data[idx] = (fname, text.encode("latin-1", errors="replace"))
        camp_files += 1
    if camp_files != 17:
        raise SystemExit(f"expected 17 target camps, got {camp_files}")

    # ---- DATA: construct-button cameos (ButtonImage only) ----
    btn = src_cmdbtn
    btn_swaps = 0
    seen_objects: set[str] = set()
    rebuilt = []
    last = 0
    for name, start, end in parse_buttons(btn):
        rebuilt.append(btn[last:start])
        blk = btn[start:end]
        om = re.search(r"(?im)^\s*Object\s*=\s*(\S+)", blk)
        obj = om.group(1) if om else ""
        if obj in CAMP_OBJECTS:
            side = CAMP_OBJECTS[obj]
            img = camp_image(side)
            if re.search(r"(?im)^\s*ButtonImage\s*=", blk) is None:
                raise SystemExit(f"{name} missing ButtonImage")
            blk, n = re.subn(
                r"(?im)^(\s*ButtonImage\s*=\s*)\S+",
                rf"\1{img}",
                blk,
                count=1,
            )
            if n != 1:
                raise SystemExit(f"{name} ButtonImage replace failed")
            btn_swaps += 1
            seen_objects.add(obj)
        rebuilt.append(blk)
        last = end
    rebuilt.append(btn[last:])
    missing = set(CAMP_OBJECTS) - seen_objects
    if missing:
        raise SystemExit(f"construct buttons missing for {sorted(missing)}")
    jf.set_text(data, P_CMDBTN, "".join(rebuilt))

    # ---- validation ----
    if jf.raw_of(data, P_WEAPON) != src_weapon:
        raise SystemExit("Weapon.ini changed")
    if jf.raw_of(data, P_UPGRADE) != src_upgrade:
        raise SystemExit("Upgrade.ini changed")
    if jf.raw_of(data, P_CMDSET) != src_cmdset:
        raise SystemExit("CommandSet.ini changed")
    if jf.raw_of(data, P_PT) != src_pt:
        raise SystemExit("PlayerTemplate.ini changed")
    if jf.raw_of(data, P_PT_PATCH) != src_pt_patch:
        raise SystemExit("PlayerTemplate_SpecterPatch.ini changed")
    for n, b in data:
        if in_protected(n) and bytes(b) != protected_files.get(jf.norm(n).lower()):
            raise SystemExit(f"protected DATA changed: {n}")

    # CommandButton: only ButtonImage lines on the 17 camp construct buttons
    new_btn = jf.text_of(data, P_CMDBTN)
    old_parts = parse_buttons(src_cmdbtn)
    new_parts = parse_buttons(new_btn)
    if [n for n, _, _ in old_parts] != [n for n, _, _ in new_parts]:
        raise SystemExit("CommandButton names reordered/added")
    for (oname, os, oe), (nname, ns, ne) in zip(old_parts, new_parts):
        old_blk = src_cmdbtn[os:oe]
        new_blk = new_btn[ns:ne]
        if oname != nname:
            raise SystemExit("CommandButton name mismatch")
        om = re.search(r"(?im)^\s*Object\s*=\s*(\S+)", old_blk)
        obj = om.group(1) if om else ""
        if obj in CAMP_OBJECTS:
            old_no_img = re.sub(r"(?im)^(\s*ButtonImage\s*=\s*)\S+", r"\1", old_blk)
            new_no_img = re.sub(r"(?im)^(\s*ButtonImage\s*=\s*)\S+", r"\1", new_blk)
            if old_no_img != new_no_img:
                raise SystemExit(f"{oname} non-image fields changed")
        elif old_blk != new_blk:
            raise SystemExit(f"untouched CommandButton changed: {oname}")

    dnames = [jf.norm(n).lower() for n, _ in data]
    if len(dnames) != len(set(dnames)):
        raise SystemExit("duplicate packed DATA paths")
    if any(n.startswith("art\\") for n in dnames):
        raise SystemExit("ART leaked into DATA")

    mi_text = jf.text_of(data, P_MI)
    for side in SIDES:
        if f"MappedImage {camp_image(side)}" not in mi_text:
            raise SystemExit(f"missing MI {camp_image(side)}")

    leftover_cameo = []
    coverage = []
    for n, b in data:
        if not is_camp_ini(n) or in_protected(n) or folder_side(n) not in SIDES:
            continue
        t = b.decode("latin-1", errors="replace")
        side = folder_side(n)
        img = camp_image(side)
        portraits = re.findall(r"(?im)^\s*SelectPortrait\s*=\s*(\S+)", t)
        buttons = re.findall(r"(?im)^\s*ButtonImage\s*=\s*(\S+)", t)
        if any(p.lower() in WRONG_CAMEOS for p in portraits + buttons):
            leftover_cameo.append(f"{n} still {portraits}/{buttons}")
        if img not in portraits or img not in buttons:
            leftover_cameo.append(f"{n} missing {img}: {portraits}/{buttons}")
        models = sorted(set(re.findall(r"(?im)^\s*Model\s*=\s*(\S+)", t)))
        for dnr in DONOR_MODELS:
            if re.search(rf"(?im)^\s*Model\s*=\s*{re.escape(dnr)}\s*$", t):
                leftover_cameo.append(f"{n} still Model={dnr}")
        coverage.append((side, jf.norm(n).split("\\")[-1], portraits, buttons, models))
    if leftover_cameo:
        raise SystemExit("leftover camp flags:\n  " + "\n  ".join(leftover_cameo[:20]))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(jf.build_big_ordered(data))
    shutil.copy2(SRC_ART, OUT_DIR / "_SPEC_ART_ONE.big")
    shutil.copy2(OUT_DIR / "_SPEC_DATA_ONE.big", WS_OUT / "_SPEC_DATA_ONE.big")
    shutil.copy2(OUT_DIR / "_SPEC_ART_ONE.big", WS_OUT / "_SPEC_ART_ONE.big")
    new_data_sha = jf.sha256_file(WS_OUT / "_SPEC_DATA_ONE.big")
    new_art_sha = jf.sha256_file(WS_OUT / "_SPEC_ART_ONE.big")
    if new_art_sha != EXPECTED_ART_SHA:
        raise SystemExit("ART should be unchanged from PR #516")
    packed_d = jf.read_big_list(WS_OUT / "_SPEC_DATA_ONE.big")
    packed_a = jf.read_big_list(WS_OUT / "_SPEC_ART_ONE.big")
    if packed_d[0][0] is None or packed_a[0][0] is None:
        raise SystemExit("re-read BIG failed")

    country = ["", "===== CAMP AUDIT =====", ""]
    for side, fname, portraits, buttons, models in coverage:
        country += [
            side.upper(),
            f"  FILE = {fname}",
            f"  SELECT = {', '.join(portraits)}",
            f"  HUD_CAMEO = {', '.join(buttons)}",
            f"  MODELS = {', '.join(models)}",
            "  PROTECTED = NO",
            "",
        ]

    audit = "\n".join([
        "SPECTER1 INFANTRY CAMP / BARRACKS FLAGS",
        "BASELINE = SPECTER1_FACTION_FLAGS_REMAINING_01",
        f"BASELINE_DATA_SHA256 = {EXPECTED_DATA_SHA}",
        f"BASELINE_ART_SHA256 = {EXPECTED_ART_SHA}",
        f"NEW_DATA_SHA256 = {new_data_sha}",
        f"NEW_ART_SHA256 = {new_art_sha}",
        f"PACKED_DATA_FILES = {len(packed_d)} (was 2882, +CampFlags MappedImages)",
        f"PACKED_ART_FILES = {len(packed_a)} (unchanged from PR #516)",
        "DUPLICATE_PACKED_PATHS = NO",
        "BIG_INTEGRITY = YES",
        "DATA_LAYOUT = Data\\INI\\... inside _SPEC_DATA_ONE.big",
        "ART_LAYOUT = Art\\... inside _SPEC_ART_ONE.big",
        "NEW_DATA_OR_ART_FOLDERS = NO",
        "NEW_BIG_FILES = NO",
        "WEAPON_INI_CHANGED = NO",
        "UPGRADE_INI_CHANGED = NO",
        "COMMANDSET_CHANGED = NO",
        "COMMANDBUTTON_GAMEPLAY_CHANGED = NO",
        f"COMMANDBUTTON_CAMP_IMAGE_SWAPS = {btn_swaps}",
        f"CAMP_PORTRAIT_SWAPS = {portrait_swaps}",
        f"CAMP_EXTRA_FLAG_DRAWS = {extra_draws}",
        "PROTECTED_FACTIONS_UNCHANGED = YES",
        "PROTECTED = USA, Iran, Israel, China, Russia, NATO, Egypt, North Korea, Iraq",
        "SELECT_CAMP = CampFlag<Side> MappedImage + packed national TGA",
        "HUD_CAMP = same cameo on Object ButtonImage + construct ButtonImage",
        "BUILDING_CAMP_FLAG = PR #516 irq_camp_* clones / extra IqFlag Draw (verified)",
        "GAMEPLAY_CHANGED = NO",
        "INGAME_TESTED = NO",
        "DATA_CHANGED = YES",
        "ART_CHANGED = NO",
    ] + country) + "\n"

    changelog = """SPECTER1 infantry Camp/Barracks flags

Continues from SPECTER1_FACTION_FLAGS_REMAINING_01. Weapons, upgrades,
CommandSets, PlayerTemplates, protected factions, and ART are unchanged.

Replaces leftover USA / Iraq camp portraits and construct cameos for
Japan, Vietnam, South Korea, Libya, South Africa, Pakistan, India, Syria,
UAE, Saudi Arabia, Turkey, Sweden, Ukraine, Italy, United Kingdom,
Germany, and France.

1. Pre-game / build-menu camp preview: construct ButtonImage and
   Object ButtonImage now use CampFlag<Side> (real national TGA).
2. In-game HUD camp cameo: Object SelectPortrait uses the same image.
3. Physical Camp/Barracks cloth: already native from PR #516
   (irq_camp_* texture clones or extra national IqFlag Draw). Re-checked;
   no leftover IraqiFlag/DPRK donor models.

Object names and Country IDs unchanged. CommandButton gameplay fields
other than those 17 ButtonImage lines are unchanged.

INGAME_TESTED = NO
"""

    install = f"""SPECTER1_FACTION_CAMP_FLAGS_01
==============================

Infantry Camp/Barracks national flags on the remaining-flags baseline.
Protected factions (USA, Iran, Israel, China, Russia, NATO, Egypt,
North Korea, Iraq) are unchanged. Gameplay data unchanged.
Same GameRoot layout: two BIG files, no loose Data/Art.

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG in GameRoot.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG in GameRoot.
4. Launch Specter.

Checksums:
  DATA SHA256 {new_data_sha}
  ART  SHA256 {new_art_sha}

CAMP_FLAGS_FIXED = YES
INGAME_TESTED = NO
"""

    for dest in (OUT_DIR, WS_OUT):
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "audit.txt").write_text(audit, encoding="utf-8")
        (dest / "changelog.txt").write_text(changelog, encoding="utf-8")
        (dest / "INSTALL.txt").write_text(install, encoding="utf-8")

    zpath = WS_OUT / f"{RELEASE_NAME}.zip"
    (WS_OUT / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {new_data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {new_art_sha}\n",
        encoding="utf-8",
    )
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in (
            "_SPEC_DATA_ONE.big",
            "_SPEC_ART_ONE.big",
            "INSTALL.txt",
            "changelog.txt",
            "audit.txt",
            "SHA256.txt",
        ):
            zf.write(WS_OUT / name, name)
    zip_sha = hashlib.sha256(zpath.read_bytes()).hexdigest()
    sha_txt = (
        f"_SPEC_DATA_ONE.big  SHA256 {new_data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {new_art_sha}\n"
        f"{RELEASE_NAME}.zip  SHA256 {zip_sha}  {zpath.stat().st_size} bytes\n"
    )
    for dest in (OUT_DIR, WS_OUT):
        (dest / "SHA256.txt").write_text(sha_txt, encoding="utf-8")
    shutil.copy2(zpath, OUT_DIR / zpath.name)
    print(audit)
    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", new_data_sha)
    print("ART unchanged", new_art_sha)
    print("ZIP", zpath, zpath.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
