#!/usr/bin/env python3
"""Fix remaining faction flags (select / HUD / building cloth).

Baseline: SPECTER1_CAMP_CLONE_IRAQ_VIETNAM (PR #505 + unlock + WF/Camp clone).
Does not touch protected factions: USA, Iran, Israel, China, Russia, NATO,
Egypt, North Korea, Iraq.

Only flag textures and material/model references. Gameplay INI (CommandSet,
CommandButton, Weapon, Upgrade, costs, production) unchanged.
Same two BIG names. No loose Data/Art folders.
"""
from __future__ import annotations

import hashlib
import io
import re
import shutil
import struct
import urllib.request
import zipfile
from pathlib import Path

from PIL import Image

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_CAMP_CLONE_IRAQ_VIETNAM/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_CAMP_CLONE_IRAQ_VIETNAM/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "e04a7b08a2fc6ae5648611d68b3b026e5cb004a103e92b2926d246a9ad1c6dfd"
EXPECTED_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"
OUT_DIR = Path("/tmp/SPECTER1_FACTION_FLAGS_REMAINING_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_FACTION_FLAGS_REMAINING_01")
RELEASE_NAME = "SPECTER1_FACTION_FLAGS_REMAINING_01"

P_PT = r"Data\INI\PlayerTemplate.ini"
P_PT_PATCH = r"Data\INI\PlayerTemplate_SpecterPatch.ini"
P_MI = r"Data\INI\MappedImages\HandCreated\Specter_RemainingFlags.INI"
P_TURKEY_MI = r"Data\INI\MappedImages\HandCreated\Turkey_FactionImages.INI"
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

# Side -> (flagcdn, 13-char-max texture file, HUD names already exist?)
SIDES = {
    "Japan": ("jp", "JP_Flag.tga", "JP"),
    "Vietnam": ("vn", "VN_Flag.tga", "VN"),
    "SouthKorea": ("kr", "SK_Flag.tga", "SK"),
    "Libya": ("ly", "LY_Flag.tga", "LY"),
    "SouthAfrica": ("za", "ZA_Flag.tga", "ZA"),
    "Pakistan": ("pk", "PK_Flag.tga", "PK"),
    "India": ("in", "IN_Flag.tga", "IN"),
    "Syria": ("sy", "SY_Flag.tga", "SY"),
    "UAE": ("ae", "UAE_Flag.tga", "UAE"),
    "SaudiArabia": ("sa", "SA_Flag.tga", "SA"),
    "Turkey": ("tr", "TR_Flag.tga", "TR"),
    "Sweden": ("se", "SE_Flag.tga", "SE"),
    "Ukraine": ("ua", "UA_Flag.tga", "UA"),
    "Italy": ("it", "IT_Flag.tga", "IT"),
    "Britain": ("gb", "UK_Flag.tga", "UK"),
    "Germany": ("de", "DE_Flag.tga", "DE"),
    "France": ("fr", "FR_Flag.tga", "FR"),
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

# Building W3Ds that already carry a baked national-flag texture.
FLAG_DONORS = {
    "irq_camp": "IraqiFlag.tga",
    "Iraq_Powerplant": "IraqiFlag.tga",
    "Iraq_Supply": "IraqiFlag.tga",
    "Irq_WarFactory": "IraqiFlag.tga",
    "NKor_Powerplant": "DPRK_Flag.tga",
    "NKor_Supply": "DPRK_Flag.tga",
    "NKr_WarFactory": "DPRK_Flag.tga",
    "NKr_Command": "DPRK_Flag.tga",
}
# Only clone donors that a side actually draws.
CLONE_SIDES = {
    "irq_camp": (
        "Japan", "Vietnam", "SouthKorea", "Libya", "SouthAfrica",
        "Pakistan", "India", "Syria", "UAE", "SaudiArabia",
    ),
    "Iraq_Powerplant": (
        "Libya", "SouthAfrica", "Pakistan", "India", "Syria", "UAE", "SaudiArabia",
    ),
    "Iraq_Supply": (
        "Libya", "SouthAfrica", "Pakistan", "India", "Syria", "UAE", "SaudiArabia",
    ),
    "Irq_WarFactory": (
        "Libya", "SouthAfrica", "Syria", "UAE", "SaudiArabia",
    ),
    "NKor_Powerplant": ("Japan", "Vietnam", "SouthKorea"),
    "NKor_Supply": ("Japan", "Vietnam", "SouthKorea"),
    "NKr_WarFactory": ("Japan", "Vietnam", "SouthKorea", "India", "Pakistan"),
    "NKr_Command": ("Japan", "Vietnam", "SouthKorea"),
}
FLAGLESS = {
    "US_Camp", "US_Command", "US_Powerplant", "US_PowerplantU",
    "US_Supply", "US_WarFactory", "Irq_P3", "Nat_RadarSt",
}
ABBAS_DONORS = ("Irq__IqFlag_Hs", "NKr__NKFlag_Hs")
HS_DONOR_TEX = "IraqiFlag.dds"

BUILDING_HINT = (
    "barracks", "camp", "warfactory", "supply", "power", "radar",
    "commandcenter", "command_center", "abbas", "nuclearcenter", "gm406",
)


def fetch_flag(code: str) -> Image.Image:
    url = f"https://flagcdn.com/w320/{code}.png"
    req = urllib.request.Request(url, headers={"User-Agent": "SpecterPatch/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    if im.width < 80 or im.height < 40:
        raise SystemExit(f"flag {code}: implausible size {im.size}")
    return im


def to_tga(im: Image.Image, w: int, h: int) -> bytes:
    im = im.resize((w, h), Image.LANCZOS)
    px = im.tobytes("raw", "RGBA")
    rows = [px[i * w * 4:(i + 1) * w * 4] for i in range(h)]
    out = bytearray()
    for row in reversed(rows):
        for i in range(0, len(row), 4):
            out += bytes((row[i + 2], row[i + 1], row[i], row[i + 3]))
    hdr = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, w, h, 32, 0x08)
    return hdr + bytes(out)


def clone_w3d(donor: bytes, donor_tex: str, new_stem: str) -> bytes:
    dt = donor_tex.encode("ascii")
    field_len = len(dt) + 1
    new_field = new_stem.encode("ascii") + b"\x00"
    if len(new_field) > field_len:
        raise SystemExit(f"texture name too long: {new_stem}")
    new_field += b"\x00" * (field_len - len(new_field))
    out = bytearray(donor)
    count = 0
    start = 0
    while True:
        i = out.find(dt, start)
        if i < 0:
            break
        if i + len(dt) < len(out) and out[i + len(dt)] == 0:
            out[i:i + field_len] = new_field
            count += 1
            start = i + field_len
        else:
            start = i + 1
    if count < 1:
        raise SystemExit(f"no {donor_tex} refs to replace for {new_stem}")
    if len(out) != len(donor):
        raise SystemExit("W3D size changed")
    if donor_tex != new_stem and dt in bytes(out):
        raise SystemExit(f"leftover {donor_tex} after clone {new_stem}")
    return bytes(out)


def split_templates(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"(?im)^PlayerTemplate\s+(\S+)\s*$", text))
    out = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((m.group(1), text[m.start():end]))
    return out


def field(block: str, key: str) -> str | None:
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(\S+)", block)
    return m.group(1) if m else None


def folder_side(path: str) -> str | None:
    low = jf.norm(path).lower()
    for folder, side in FOLDER_SIDE.items():
        if f"\\{folder}\\" in low:
            return side
    return None


def in_protected(path: str) -> bool:
    low = jf.norm(path).lower()
    return any(f"\\{p}\\" in low for p in PROTECTED_FOLDER)


def is_building_ini(path: str) -> bool:
    low = jf.norm(path).lower()
    if not low.endswith(".ini") or "\\object\\" not in low:
        return False
    if "\\buildings\\" not in low:
        return False
    return any(h in low for h in BUILDING_HINT)


def mi_block(name: str, tex: str, tw: int, th: int, box: tuple[int, int, int, int]) -> str:
    l, t, r, b = box
    return (
        f"MappedImage {name}\r\n"
        f"  Texture = {tex}\r\n"
        f"  TextureWidth = {tw}\r\n"
        f"  TextureHeight = {th}\r\n"
        f"  Coords = Left:{l} Top:{t} Right:{r} Bottom:{b}\r\n"
        f"  Status = NONE\r\n"
        f"End\r\n"
    )


def extra_flag_draw(mesh: str, nl: str) -> str:
    return (
        "  Draw = W3DModelDraw ModuleTag_SpecterNatFlag" + nl
        + "    OkToChangeModelColor = No" + nl
        + "    DefaultConditionState" + nl
        + f"      Model = {mesh}" + nl
        + "      Animation = Irq__IqFlag_Hs.Irq__IqFlag_Hs" + nl
        + "      AnimationMode = LOOP" + nl
        + "    End" + nl
        + "  End" + nl
    )


def insert_flag_draw(text: str, mesh: str) -> str:
    if "ModuleTag_SpecterNatFlag" in text:
        return text
    draw = extra_flag_draw(mesh, jf.file_nl(text))
    m = re.search(r"(?im)^[ \t]*Draw\s*=", text)
    if m:
        return text[:m.start()] + draw + text[m.start():]
    raise SystemExit("cannot find insertion point for flag Draw")


def main() -> int:
    if jf.sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("source DATA SHA mismatch")
    if jf.sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("source ART SHA mismatch")

    data = jf.read_big_list(SRC_DATA)
    art = jf.read_big_list(SRC_ART)
    if len(data) != 2880 or len(art) != 4432:
        raise SystemExit(f"packed count {len(data)}/{len(art)}")

    src_weapon = jf.raw_of(data, P_WEAPON)
    src_upgrade = jf.raw_of(data, P_UPGRADE)
    src_cmdset = jf.raw_of(data, P_CMDSET)
    src_cmdbtn = jf.raw_of(data, P_CMDBTN)
    src_pt_patch = jf.raw_of(data, P_PT_PATCH)
    protected_pt = {}
    for name, blk in split_templates(jf.text_of(data, P_PT)):
        if name in PROTECTED_TEMPLATES:
            protected_pt[name] = blk
    protected_files = {
        jf.norm(n).lower(): bytes(b)
        for n, b in data
        if in_protected(n)
    }

    # ---- ART: real flag TGAs ----
    flags: dict[str, Image.Image] = {}
    for side, (code, _stem, _cc) in SIDES.items():
        flags[side] = fetch_flag(code)

    new_art: dict[str, bytes] = {}
    for side, (_code, stem, _cc) in SIDES.items():
        tga = to_tga(flags[side], 128, 64)
        new_art[f"Art\\Textures\\{stem}"] = tga

    # Refresh Turkey HUD textures in-place (same packed paths).
    new_art[r"Art\Textures\WatermarkTurkey.tga"] = to_tga(flags["Turkey"], 128, 64)
    new_art[r"Art\Textures\GameinfoTurkey.tga"] = to_tga(flags["Turkey"], 64, 64)
    new_art[r"Art\Textures\SSObserverTurkey.tga"] = to_tga(flags["Turkey"], 64, 64)
    new_art[r"Art\Textures\Turkey_Logo.tga"] = to_tga(flags["Turkey"], 128, 128)
    new_art[r"Art\Textures\Turkey_Flag.tga"] = to_tga(flags["Turkey"], 256, 128)

    # ---- ART: W3D clones (size-preserving texture-name swap) ----
    clone_of: dict[tuple[str, str], str] = {}
    for donor, dtex in FLAG_DONORS.items():
        donor_bytes = bytes(jf.raw_of(art, f"Art\\W3D\\{donor}.W3D"))
        if clone_w3d(donor_bytes, dtex, dtex) != donor_bytes:
            raise SystemExit(f"W3D self-test failed {donor}")
        for side in CLONE_SIDES[donor]:
            stem = SIDES[side][1]
            cc = SIDES[side][2]
            clone = f"{donor}_{cc}"
            w3d = clone_w3d(donor_bytes, dtex, stem)
            new_art[f"Art\\W3D\\{clone}.W3D"] = w3d
            clone_of[(donor, side)] = clone

    hs_donor = bytes(jf.raw_of(art, r"Art\W3D\Irq__IqFlag_Hs.W3D"))
    hs_of: dict[str, str] = {}
    for side, (_c, stem, cc) in SIDES.items():
        mesh = f"{cc}_Flag_Hs"
        w3d = clone_w3d(hs_donor, HS_DONOR_TEX, stem)
        new_art[f"Art\\W3D\\{mesh}.W3D"] = w3d
        hs_of[side] = mesh

    art_names = {jf.norm(n).lower() for n, _ in art}
    for rel, blob in new_art.items():
        key = jf.norm(rel).lower()
        if key in art_names:
            idx = next(i for i, (n, _) in enumerate(art) if jf.norm(n).lower() == key)
            art[idx] = (art[idx][0], blob)
        else:
            art.append((jf.norm(rel), blob))
            art_names.add(key)

    # ---- DATA: MappedImages ----
    chunks = [
        "; SPECTER - remaining faction flag images (select / HUD)\r\n"
        "; Texture paths are the packed Art\\Textures\\<stem> files.\r\n"
    ]
    for side, (_c, stem, _cc) in SIDES.items():
        tex = stem[:-4]
        if side == "Turkey":
            continue  # existing Turkey_FactionImages names
        chunks.append(mi_block(f"Watermark{side}", tex, 128, 64, (0, 0, 128, 64)))
        chunks.append(mi_block(f"{side}_Logo", tex, 128, 64, (32, 0, 96, 64)))
        chunks.append(mi_block(f"Gameinfo{side}", tex, 128, 64, (32, 0, 96, 64)))
        chunks.append(mi_block(f"SSObserver{side}", tex, 128, 64, (32, 0, 96, 64)))
    jf.add_file(data, P_MI, "".join(chunks))
    turkey_mi = Path("/workspace/patch/Data/INI/MappedImages/HandCreated/Turkey_FactionImages.INI")
    jf.add_file(data, P_TURKEY_MI, turkey_mi.read_text(encoding="utf-8"))

    # ---- DATA: PlayerTemplate image refs (not gameplay) ----
    pt = jf.text_of(data, P_PT)
    parts = split_templates(pt)
    rebuilt = []
    last = 0
    matches = list(re.finditer(r"(?im)^PlayerTemplate\s+(\S+)\s*$", pt))
    hud_repoints = 0
    for i, m in enumerate(matches):
        name = m.group(1)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(pt)
        rebuilt.append(pt[last:m.start()])
        blk = pt[m.start():end]
        side = name[7:] if name.startswith("Faction") else ""
        if name not in PROTECTED_TEMPLATES and side in SIDES:
            if side == "Turkey":
                mapping = {
                    "FlagWaterMark": "WatermarkTurkey",
                    "EnabledImage": "SSObserverTurkey",
                    "SideIconImage": "GameinfoTurkey",
                    "GeneralImage": "Turkey_Logo",
                }
            else:
                mapping = {
                    "FlagWaterMark": f"Watermark{side}",
                    "EnabledImage": f"SSObserver{side}",
                    "SideIconImage": f"Gameinfo{side}",
                    "GeneralImage": f"{side}_Logo",
                }
            for key, img in mapping.items():
                if field(blk, key) is None:
                    raise SystemExit(f"{name} missing {key}")
                blk, n = re.subn(
                    rf"(?im)^(\s*{re.escape(key)}\s*=\s*)\S+",
                    rf"\1{img}",
                    blk,
                    count=1,
                )
                if n != 1:
                    raise SystemExit(f"{name} {key} replace failed")
                hud_repoints += 1
        rebuilt.append(blk)
        last = end
    rebuilt.append(pt[last:])
    jf.set_text(data, P_PT, "".join(rebuilt))

    # ---- DATA: building Model= retarget + extra flag Draw ----
    donors_sorted = sorted(FLAG_DONORS, key=len, reverse=True)
    model_swaps = 0
    extra_draws = 0
    abbas_swaps = 0
    for idx, (fname, blob) in enumerate(data):
        if not is_building_ini(fname):
            continue
        if in_protected(fname):
            continue
        side = folder_side(fname)
        if side not in SIDES:
            continue
        text = blob.decode("latin-1", errors="replace")
        orig = text

        def rep_model(m: re.Match[str]) -> str:
            nonlocal model_swaps
            cur = m.group(2)
            for dnr in donors_sorted:
                if cur == dnr:
                    model_swaps += 1
                    return m.group(1) + clone_of[(dnr, side)]
            if cur in ABBAS_DONORS:
                return m.group(1) + hs_of[side]
            return m.group(0)

        text2 = re.sub(r"(?im)^(\s*Model\s*=\s*)(\S+)", rep_model, text)
        if re.search(r"(?im)^\s*Model\s*=\s*(Irq__IqFlag_Hs|NKr__NKFlag_Hs)\b", text2):
            text2, n = re.subn(
                r"(?im)^(\s*Model\s*=\s*)(Irq__IqFlag_Hs|NKr__NKFlag_Hs)\b",
                rf"\1{hs_of[side]}",
                text2,
            )
            abbas_swaps += n

        models_now = set(re.findall(r"(?im)^\s*Model\s*=\s*(\S+)", text2))
        needs_extra = bool(models_now & FLAGLESS)
        if needs_extra:
            text2 = insert_flag_draw(text2, hs_of[side])
            extra_draws += 1
        if text2 != orig:
            data[idx] = (fname, text2.encode("latin-1", errors="replace"))

    # ---- validation ----
    if jf.raw_of(data, P_WEAPON) != src_weapon:
        raise SystemExit("Weapon.ini changed")
    if jf.raw_of(data, P_UPGRADE) != src_upgrade:
        raise SystemExit("Upgrade.ini changed")
    if jf.raw_of(data, P_CMDSET) != src_cmdset:
        raise SystemExit("CommandSet.ini changed")
    if jf.raw_of(data, P_CMDBTN) != src_cmdbtn:
        raise SystemExit("CommandButton.ini changed")
    if jf.raw_of(data, P_PT_PATCH) != src_pt_patch:
        raise SystemExit("PlayerTemplate_SpecterPatch.ini changed")
    for name, blk in split_templates(jf.text_of(data, P_PT)):
        if name in PROTECTED_TEMPLATES and blk != protected_pt[name]:
            raise SystemExit(f"protected template changed: {name}")
    for n, b in data:
        if in_protected(n) and bytes(b) != protected_files.get(jf.norm(n).lower()):
            raise SystemExit(f"protected DATA changed: {n}")

    dnames = [jf.norm(n).lower() for n, _ in data]
    if len(dnames) != len(set(dnames)):
        raise SystemExit("duplicate packed DATA paths")
    anames = [jf.norm(n).lower() for n, _ in art]
    if len(anames) != len(set(anames)):
        raise SystemExit("duplicate packed ART paths")
    if any(n.startswith("art\\") for n in dnames):
        raise SystemExit("ART leaked into DATA")
    if any(n.startswith("data\\") for n in anames):
        raise SystemExit("DATA leaked into ART")

    art_map = {jf.norm(n).lower() for n, _ in art}
    for side, (_c, stem, _cc) in SIDES.items():
        if f"art\\textures\\{stem}".lower() not in art_map:
            raise SystemExit(f"missing flag texture {stem}")
        if f"art\\w3d\\{hs_of[side]}.w3d".lower() not in art_map:
            raise SystemExit(f"missing HS mesh {hs_of[side]}")
    for (donor, side), clone in clone_of.items():
        if f"art\\w3d\\{clone}.w3d".lower() not in art_map:
            raise SystemExit(f"missing clone {clone}")

    mi_text = jf.text_of(data, P_MI) + "\n" + jf.text_of(data, P_TURKEY_MI)
    for side in SIDES:
        if side == "Turkey":
            for name in ("WatermarkTurkey", "GameinfoTurkey", "SSObserverTurkey", "Turkey_Logo"):
                if f"MappedImage {name}" not in mi_text:
                    raise SystemExit(f"missing MI {name}")
        else:
            for name in (f"Watermark{side}", f"Gameinfo{side}", f"SSObserver{side}", f"{side}_Logo"):
                if f"MappedImage {name}" not in mi_text:
                    raise SystemExit(f"missing MI {name}")

    pt2 = jf.text_of(data, P_PT)
    for side in SIDES:
        tname = f"Faction{side}"
        blk = dict(split_templates(pt2))[tname]
        wm = field(blk, "FlagWaterMark")
        sideicon = field(blk, "SideIconImage")
        if side == "Turkey":
            if wm != "WatermarkTurkey" or sideicon != "GameinfoTurkey":
                raise SystemExit(f"Turkey HUD not wired {wm} {sideicon}")
        else:
            if wm != f"Watermark{side}" or sideicon != f"Gameinfo{side}":
                raise SystemExit(f"{side} HUD not wired {wm} {sideicon}")

    # leftover wrong baked-flag models on target buildings
    leftover = []
    missing_art_model = []
    coverage = {side: {"baked": 0, "extra": 0, "files": []} for side in SIDES}
    art_w3d = {jf.norm(n).lower() for n, _ in art if n.lower().endswith(".w3d")}
    for n, b in data:
        if not is_building_ini(n) or in_protected(n):
            continue
        side = folder_side(n)
        if side not in SIDES:
            continue
        t = b.decode("latin-1", errors="replace")
        for dnr in FLAG_DONORS:
            if re.search(rf"(?im)^\s*Model\s*=\s*{re.escape(dnr)}\s*$", t):
                leftover.append(f"{n} still {dnr}")
        if re.search(r"(?im)^\s*Model\s*=\s*(Irq__IqFlag_Hs|NKr__NKFlag_Hs)\b", t):
            leftover.append(f"{n} still donor HS flag")
        models_now = set(re.findall(r"(?im)^\s*Model\s*=\s*(\S+)", t))
        for mdl in models_now:
            key = f"art\\w3d\\{mdl}.w3d".lower()
            if key not in art_w3d:
                missing_art_model.append(f"{n} Model={mdl}")
        has_extra = "ModuleTag_SpecterNatFlag" in t
        side_clones = {clone_of[k] for k in clone_of if k[1] == side}
        has_clone = bool(models_now & side_clones) or hs_of[side] in models_now
        if models_now & FLAGLESS and not has_extra:
            leftover.append(f"{n} flagless models without extra Draw")
        if has_extra:
            coverage[side]["extra"] += 1
        if has_clone:
            coverage[side]["baked"] += 1
        if has_extra or has_clone:
            coverage[side]["files"].append(jf.norm(n).split("\\")[-1])
    if leftover:
        raise SystemExit("leftover donor models:\n  " + "\n  ".join(leftover[:20]))
    if missing_art_model:
        raise SystemExit("Model= missing from ART:\n  " + "\n  ".join(missing_art_model[:20]))
    for side, info in coverage.items():
        if info["baked"] + info["extra"] < 1:
            raise SystemExit(f"{side}: no building flag coverage")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(jf.build_big_ordered(data))
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(jf.build_big_ordered(art))
    shutil.copy2(OUT_DIR / "_SPEC_DATA_ONE.big", WS_OUT / "_SPEC_DATA_ONE.big")
    shutil.copy2(OUT_DIR / "_SPEC_ART_ONE.big", WS_OUT / "_SPEC_ART_ONE.big")
    new_data_sha = jf.sha256_file(WS_OUT / "_SPEC_DATA_ONE.big")
    new_art_sha = jf.sha256_file(WS_OUT / "_SPEC_ART_ONE.big")
    packed_d = jf.read_big_list(WS_OUT / "_SPEC_DATA_ONE.big")
    packed_a = jf.read_big_list(WS_OUT / "_SPEC_ART_ONE.big")
    if packed_d[0][0] is None or packed_a[0][0] is None:
        raise SystemExit("re-read BIG failed")

    country = ["", "===== COUNTRY AUDIT =====", ""]
    for side, (code, stem, cc) in SIDES.items():
        country += [
            side.upper(),
            f"  FLAGCDN = {code}  TEXTURE = Art\\Textures\\{stem}",
            f"  SELECT = Gameinfo{side if side != 'Turkey' else 'Turkey'} / {(side+'_Logo') if side != 'Turkey' else 'Turkey_Logo'}",
            f"  HUD = Watermark{side if side != 'Turkey' else 'Turkey'} / SSObserver{side if side != 'Turkey' else 'Turkey'}",
            f"  BUILDING_HS = {hs_of[side]}",
            f"  BUILDING_FILES = {coverage[side]['baked']} baked / {coverage[side]['extra']} extra-draw",
            "  PROTECTED = NO",
            "",
        ]

    audit = "\n".join([
        "SPECTER1 REMAINING FACTION FLAGS",
        "BASELINE = SPECTER1_CAMP_CLONE_IRAQ_VIETNAM",
        f"BASELINE_DATA_SHA256 = {EXPECTED_DATA_SHA}",
        f"BASELINE_ART_SHA256 = {EXPECTED_ART_SHA}",
        f"NEW_DATA_SHA256 = {new_data_sha}",
        f"NEW_ART_SHA256 = {new_art_sha}",
        f"PACKED_DATA_FILES = {len(packed_d)} (was 2880, +MappedImages)",
        f"PACKED_ART_FILES = {len(packed_a)} (was 4432, +flag TGA/W3D)",
        "DUPLICATE_PACKED_PATHS = NO",
        "BIG_INTEGRITY = YES",
        "DATA_LAYOUT = Data\\INI\\... inside _SPEC_DATA_ONE.big",
        "ART_LAYOUT = Art\\... inside _SPEC_ART_ONE.big",
        "NEW_DATA_OR_ART_FOLDERS = NO",
        "NEW_BIG_FILES = NO",
        "WEAPON_INI_CHANGED = NO",
        "UPGRADE_INI_CHANGED = NO",
        "COMMANDSET_CHANGED = NO",
        "COMMANDBUTTON_CHANGED = NO",
        "PROTECTED_FACTIONS_UNCHANGED = YES",
        "PROTECTED = USA, Iran, Israel, China, Russia, NATO, Egypt, North Korea, Iraq",
        f"HUD_REPOINTS = {hud_repoints}",
        f"BUILDING_MODEL_SWAPS = {model_swaps}",
        f"ABBAS_FLAG_SWAPS = {abbas_swaps}",
        f"EXTRA_FLAG_DRAWS = {extra_draws}",
        "SELECT_FLAG = native MappedImage + real national TGA",
        "HUD_FLAG = native watermark/observer + real national TGA",
        "BUILDING_FLAG = W3D texture-name clones for baked-flag buildings; extra IqFlag Draw on flagless US/Radar models",
        "GAMEPLAY_CHANGED = NO",
        "INGAME_TESTED = NO",
        "DATA_CHANGED = YES",
        "ART_CHANGED = YES",
    ] + country) + "\n"

    changelog = """SPECTER1 remaining faction flags

Continues from SPECTER1_CAMP_CLONE_IRAQ_VIETNAM. Gameplay, weapons,
upgrades, CommandSets, and protected factions are unchanged.

Replaces incorrect USA / GLA / DPRK flag images for Japan, Vietnam,
South Korea, Libya, South Africa, Pakistan, India, Syria, UAE,
Saudi Arabia, Turkey, Sweden, Ukraine, Italy, United Kingdom,
Germany, and France.

1. Pre-game select: SideIconImage / GeneralImage point at native
   MappedImages backed by real national flag TGAs.
2. In-game HUD: FlagWaterMark / EnabledImage point at the same flags.
3. Building cloth: Power Plant, Camp, Supply, War Factory, and
   Command Center models that baked IraqiFlag/DPRK_Flag now use
   per-country W3D clones. Flagless US-lineage buildings and Radar
   get a small extra national-flag Draw (Iraq IqFlag mesh, native
   texture). Same object names.

INGAME_TESTED = NO
"""

    install = f"""SPECTER1_FACTION_FLAGS_REMAINING_01
===================================

National flags for the remaining factions on the Camp-clone baseline.
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

FLAGS_FIXED = YES
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
    print("ART", new_art_sha, "files", len(packed_a))
    print("ZIP", zpath, zpath.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
