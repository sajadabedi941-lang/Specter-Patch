#!/usr/bin/env python3
"""North Korea builder palette: Clear Mines → China HQ-9 Site, Stop → C-RAM.

Preserves LargeAirBase / HeavyAirBase. Stop moved to slot 15 (engine STOP kept).
DATA-only. China / Pakistan / other factions frozen.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace/patch")
DATA_BIG = ROOT / "Release/SPECTER_MASTER/_SPEC_DATA_ONE.big"
ART_BIG = ROOT / "Release/SPECTER_MASTER/_SPEC_ART_ONE.big"
OUT_DIR = ROOT / "Release/SPECTER_MASTER"
ZIP_PATH = ROOT / "Release/SPECTER_MASTER_DATA_NK_PALETTE_AD_CRAM.zip"
NOTE = OUT_DIR / "DATA_NK_PALETTE_AD_CRAM_HASHES.txt"
DL = OUT_DIR / "DATA_NK_PALETTE_AD_CRAM_DOWNLOAD.txt"

BASE_DATA = "fada163a72c44b95f742aa660886c2633506194ada0700955b910927e9ea256b"
BASE_ART = "74a411b72c19fafaafcd48a45d2aa76731d8dbd13e919e4f73f8b989e90d4822"


def sha256(p: Path | bytes) -> str:
    b = p if isinstance(p, bytes) else Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        entries.append((name, off, size))
    return entries, data


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16 + sum(8 + len(n.encode("latin1")) + 1 for n, _ in items)
    offset = header_size
    index, blobs = [], []
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">III", offset, len(items), header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for b in blobs:
        out += b
    return bytes(out)


def norm(n: str) -> str:
    return n.replace("/", "\\").lower()


def upsert_commandbutton(cb_text: str, name: str, block: str) -> str:
    m = re.search(rf"^CommandButton\s+{re.escape(name)}\b.*?^End\s*$", cb_text, re.M | re.S)
    if m:
        return cb_text[: m.start()] + block.rstrip() + "\n" + cb_text[m.end() :]
    return cb_text.rstrip() + "\n\n" + block.rstrip() + "\n"


def main() -> None:
    assert sha256(DATA_BIG) == BASE_DATA, sha256(DATA_BIG)
    assert sha256(ART_BIG) == BASE_ART

    entries, raw = read_big(DATA_BIG)
    fmap: dict[str, bytes] = {}
    disp: dict[str, str] = {}
    for name, off, size in entries:
        k = norm(name)
        if k not in fmap:
            disp[k] = name.replace("/", "\\")
        fmap[k] = raw[off : off + size]

    freeze_paths = {
        "china_hq9": r"Data\INI\Object\Specter\PLA\AirDefense Sites\Hq9_AI_Site.ini",
        "pak_cram": r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_CRAM.ini",
        "nk_lab": r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_LargeAirBase.ini",
        "nk_hab": r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_HeavyAirBase.ini",
        "saudi_cram": r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_CRAM.ini",
    }
    freeze = {k: fmap[norm(p)] for k, p in freeze_paths.items()}

    china_site = fmap[norm(freeze_paths["china_hq9"])].decode("latin1")
    pak_cram = fmap[norm(freeze_paths["pak_cram"])].decode("latin1")
    assert "Object China_Hq9_Site" in china_site
    assert "Object Pakistan_CRAM" in pak_cram
    assert "Model             = Spec_SamRusCnfg" in china_site
    assert "Model             = US_CRAM" in pak_cram

    # --- NorthKorea_Hq9_Site (clone China_Hq9_Site) ---
    hq9 = china_site
    hq9 = hq9.replace("Object China_Hq9_Site", "Object NorthKorea_Hq9_Site")
    hq9 = re.sub(r"(Side\s*=\s*)China\b", r"\1NorthKorea", hq9)
    hq9 = re.sub(r"(Object\s*=\s*)ChinaPowerPlant\b", r"\1NorthKorea_PowerPlant", hq9)
    # Keep spawn templates / weapons shared (proven China AI launchers)
    assert "Side                  = NorthKorea" in hq9 or re.search(r"Side\s*=\s*NorthKorea", hq9)
    assert "ChinaPowerPlant" not in hq9
    assert "Spec_SamRusCnfg" in hq9
    assert "ChinaVehicleHq9_AAM_AI" in hq9  # shared spawn templates OK
    hq9_path = r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_Hq9_Site.ini"
    assert norm(hq9_path) not in fmap
    fmap[norm(hq9_path)] = hq9.encode("latin1")
    disp[norm(hq9_path)] = hq9_path

    # --- NorthKorea_CRAM (clone Pakistan_CRAM) ---
    cram = pak_cram
    cram = cram.replace("Object Pakistan_CRAM", "Object NorthKorea_CRAM")
    cram = re.sub(r"(Side\s*=\s*)Pakistan\b", r"\1NorthKorea", cram)
    cram = re.sub(r"(Object\s*=\s*)Pakistan_PowerPlant\b", r"\1NorthKorea_PowerPlant", cram)
    cram = cram.replace("Pakistan wrapper", "North Korea wrapper")
    assert re.search(r"Side\s*=\s*NorthKorea", cram)
    assert "Pakistan_PowerPlant" not in cram
    assert "US_CRAM" in cram
    assert "20mm_HEIT-SD_LPWS_G" in cram
    cram_path = r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_CRAM.ini"
    assert norm(cram_path) not in fmap
    fmap[norm(cram_path)] = cram.encode("latin1")
    disp[norm(cram_path)] = cram_path

    cs_path = norm(r"Data\INI\CommandSet.ini")
    cb_path = norm(r"Data\INI\CommandButton.ini")
    cs_text = fmap[cs_path].decode("latin1")
    cb_text = fmap[cb_path].decode("latin1")

    # Construct buttons
    hq9_btn = """CommandButton Command_ConstructNorthKorea_Hq9_Site
  Command       = DOZER_CONSTRUCT
  Object        = NorthKorea_Hq9_Site
  TextLabel     = CONTROLBAR:China_Hq9_Site
  ButtonImage   = pla_hq9b
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipChina_Hq9_Site
End
"""
    cram_btn = """CommandButton Command_ConstructNorthKorea_CRAM
  Command       = DOZER_CONSTRUCT
  Object        = NorthKorea_CRAM
  TextLabel     = CONTROLBAR:ConstructAmericaPatriotBattery
  ButtonImage   = us_mim90d
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipUSABuildPatriotBattery
End
"""
    cb_text = upsert_commandbutton(cb_text, "Command_ConstructNorthKorea_Hq9_Site", hq9_btn)
    cb_text = upsert_commandbutton(cb_text, "Command_ConstructNorthKorea_CRAM", cram_btn)

    # No China/Saudi/Pakistan science prereqs on buttons
    for name in ("Command_ConstructNorthKorea_Hq9_Site", "Command_ConstructNorthKorea_CRAM"):
        m = re.search(rf"^CommandButton\s+{re.escape(name)}\b.*?^End\s*$", cb_text, re.M | re.S)
        assert m and "Science" not in m.group(0)

    # Update builder CommandSet: only slots 13/14; preserve Stop at 15
    def repl_vt72(m: re.Match) -> str:
        block = m.group(0)
        # Confirm expected old slots
        assert re.search(r"13\s*=\s*Command_Stop\b", block)
        assert re.search(r"14\s*=\s*Command_DisarmMinesAtPosition\b", block)
        assert re.search(r"5\s*=\s*Command_ConstructNorthKorea_LargeAirBase\b", block)
        assert re.search(r"9\s*=\s*Command_ConstructNorthKorea_HeavyAirBase\b", block)
        block = re.sub(
            r"(13\s*=\s*)Command_Stop\b",
            r"\1Command_ConstructNorthKorea_CRAM",
            block,
        )
        block = re.sub(
            r"(14\s*=\s*)Command_DisarmMinesAtPosition\b",
            r"\1Command_ConstructNorthKorea_Hq9_Site",
            block,
        )
        # Preserve engine Stop on slot 15 (overflow / page 2)
        if "Command_Stop" not in block:
            block = re.sub(
                r"(^\s*End\s*$)",
                r"  15 = Command_Stop\n\1",
                block,
                count=1,
                flags=re.M,
            )
        return block

    cs_text2, nsub = re.subn(
        r"^CommandSet\s+NorthKorea_VT72BCommandSet\b.*?^End\s*$",
        repl_vt72,
        cs_text,
        count=1,
        flags=re.M | re.S,
    )
    assert nsub == 1
    vt = re.search(r"^CommandSet\s+NorthKorea_VT72BCommandSet\b.*?^End\s*$", cs_text2, re.M | re.S).group(0)
    assert re.search(r"13\s*=\s*Command_ConstructNorthKorea_CRAM", vt)
    assert re.search(r"14\s*=\s*Command_ConstructNorthKorea_Hq9_Site", vt)
    assert re.search(r"15\s*=\s*Command_Stop", vt)
    assert "Command_DisarmMinesAtPosition" not in vt
    # Airbases preserved in palette
    assert re.search(r"5\s*=\s*Command_ConstructNorthKorea_LargeAirBase", vt)
    assert re.search(r"9\s*=\s*Command_ConstructNorthKorea_HeavyAirBase", vt)

    fmap[cs_path] = cs_text2.encode("latin1")
    fmap[cb_path] = cb_text.encode("latin1")

    # Freeze asserts
    for k, p in freeze_paths.items():
        assert fmap[norm(p)] == freeze[k], k

    DATA_BIG.write_bytes(build_big({disp[k]: v for k, v in fmap.items()}))
    data_sha = sha256(DATA_BIG)
    assert sha256(ART_BIG) == BASE_ART

    # -------- Validation --------
    e2, r2 = read_big(DATA_BIG)
    f2 = {norm(n): r2[o : o + s] for n, o, s in e2}
    cs2 = f2[cs_path].decode("latin1")
    cb2 = f2[cb_path].decode("latin1")
    cb_names = set(re.findall(r"^CommandButton\s+(\S+)", cb2, re.M))

    def object_exists(obj: str) -> bool:
        for b in f2.values():
            if re.search(rf"^Object\s+{re.escape(obj)}\b", b.decode("latin1", errors="replace"), re.M):
                return True
        return False

    vt2 = re.search(r"^CommandSet\s+NorthKorea_VT72BCommandSet\b.*?^End\s*$", cs2, re.M | re.S).group(0)
    slots = {int(s): b for s, b in re.findall(r"(\d+)\s*=\s*(\S+)", vt2)}
    assert slots[5] == "Command_ConstructNorthKorea_LargeAirBase"
    assert slots[9] == "Command_ConstructNorthKorea_HeavyAirBase"
    assert slots[13] == "Command_ConstructNorthKorea_CRAM"
    assert slots[14] == "Command_ConstructNorthKorea_Hq9_Site"
    assert slots[15] == "Command_Stop"
    assert "Command_DisarmMinesAtPosition" not in vt2

    for btn, obj in [
        ("Command_ConstructNorthKorea_CRAM", "NorthKorea_CRAM"),
        ("Command_ConstructNorthKorea_Hq9_Site", "NorthKorea_Hq9_Site"),
    ]:
        assert btn in cb_names
        bb = re.search(rf"^CommandButton\s+{re.escape(btn)}\b.*?^End\s*$", cb2, re.M | re.S).group(0)
        assert re.search(rf"Object\s*=\s*{obj}", bb)
        assert object_exists(obj)

    cram_obj = next(
        b.decode("latin1", errors="replace")
        for b in f2.values()
        if re.search(r"^Object\s+NorthKorea_CRAM\b", b.decode("latin1", errors="replace"), re.M)
    )
    assert "US_CRAM" in cram_obj and "20mm_HEIT-SD_LPWS_G" in cram_obj
    assert re.search(r"Side\s*=\s*NorthKorea", cram_obj)
    assert "NorthKorea_PowerPlant" in cram_obj

    hq9_obj = next(
        b.decode("latin1", errors="replace")
        for b in f2.values()
        if re.search(r"^Object\s+NorthKorea_Hq9_Site\b", b.decode("latin1", errors="replace"), re.M)
    )
    assert "Spec_SamRusCnfg" in hq9_obj
    assert re.search(r"Side\s*=\s*NorthKorea", hq9_obj)
    assert "NorthKorea_PowerPlant" in hq9_obj
    assert "ChinaVehicleHq9_AAM_AI" in hq9_obj

    # Shared spawn objects still exist
    assert object_exists("ChinaVehicleHq9_AAM_AI")
    assert object_exists("ChinaVehicleHq9_ABM_AI")
    assert object_exists("America_BGMM71F_RCWS")

    # Airbases untouched
    assert f2[norm(freeze_paths["nk_lab"])] == freeze["nk_lab"]
    assert f2[norm(freeze_paths["nk_hab"])] == freeze["nk_hab"]
    assert f2[norm(freeze_paths["china_hq9"])] == freeze["china_hq9"]
    assert f2[norm(freeze_paths["pak_cram"])] == freeze["pak_cram"]

    # Full palette report
    palette_lines = []
    for s in sorted(slots):
        btn = slots[s]
        obj = "-"
        if btn in cb_names:
            bb = re.search(rf"^CommandButton\s+{re.escape(btn)}\b.*?^End\s*$", cb2, re.M | re.S)
            if bb:
                om = re.search(r"Object\s*=\s*(\S+)", bb.group(0))
                obj = om.group(1) if om else "-"
        palette_lines.append(f"Slot {s} = {btn} -> {obj}")

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")

    report = f"""NORTH KOREA PALETTE UPDATE = PASS

ACTIVE BUILDER = NorthKorea_VT72B
ACTIVE BUILDER COMMANDSET = NorthKorea_VT72BCommandSet

CLEAR MINES:
Old Command = Command_DisarmMinesAtPosition
Old slot = 14

CHINESE AIR DEFENSE:
Exact donor Object = China_Hq9_Site
Donor faction = China (PLA)
North Korea Object = NorthKorea_Hq9_Site
ConstructButton = Command_ConstructNorthKorea_Hq9_Site
Weapon = SpawnHT233ViaWeapon + spawn ChinaVehicleHq9_AAM_AI / ChinaVehicleHq9_ABM_AI (shared)
W3D = Spec_SamRusCnfg
Prerequisite = NorthKorea_PowerPlant (was ChinaPowerPlant)
New slot = 14

STOP:
Exact old Command = Command_Stop
Old slot = 13
Engine-required Stop = YES
How Stop functionality was preserved = Moved to slot 15 (Command_Stop retained on builder CommandSet)

C-RAM:
Exact donor Object = Pakistan_CRAM
North Korea Object = NorthKorea_CRAM
ConstructButton = Command_ConstructNorthKorea_CRAM
Weapon = 20mm_HEIT-SD_LPWS_G / _AAM / _AA + America_BGMM71F_RCWS payload
W3D = US_CRAM
Prerequisite = NorthKorea_PowerPlant (was Pakistan_PowerPlant)
New slot = 13

Clear Mines removed from North Korea palette = YES
Chinese Air Defense added = YES
C-RAM added = YES
Builder Stop functionality preserved = YES

LargeAirBase preserved = YES
HeavyAirBase preserved = YES

China changed = NO
Other factions changed = NO

FULL PALETTE:
{chr(10).join(palette_lines)}

ACTIVE FILES CHANGED:
- Data\\INI\\CommandSet.ini
- Data\\INI\\CommandButton.ini
- Data\\INI\\Object\\Specter\\North Korea\\Buildings\\NorthKorea_Hq9_Site.ini (NEW)
- Data\\INI\\Object\\Specter\\North Korea\\Buildings\\NorthKorea_CRAM.ini (NEW)

DATA sha256 = {data_sha}
ART sha256  = {BASE_ART} (UNCHANGED)
ZIP sha256  = {sha256(ZIP_PATH)}
ZIP path    = {ZIP_PATH}
ZIP size    = {ZIP_PATH.stat().st_size}
"""
    NOTE.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
