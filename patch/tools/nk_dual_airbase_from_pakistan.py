#!/usr/bin/env python3
"""North Korea dual-airbase upgrade from proven Pakistan Large/Heavy airbases.

ONLY changes North Korea builder slots:
  slot 5 Airfield  -> NorthKorea_LargeAirBase  (TheAirPort, 16)
  slot 9 Sam2      -> NorthKorea_HeavyAirBase  (HXUSABigAirPort, 6)

Pakistan and all other factions frozen. DATA-only.
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
ZIP_PATH = ROOT / "Release/SPECTER_MASTER_DATA_NK_DUAL_AIRBASE.zip"
NOTE = OUT_DIR / "DATA_NK_DUAL_AIRBASE_HASHES.txt"
DL = OUT_DIR / "DATA_NK_DUAL_AIRBASE_DOWNLOAD.txt"

BASE_DATA = "0413e349f1cabe322f8da425f2665c74940c0178dd87010c32b20a424b53e99e"
BASE_ART = "74a411b72c19fafaafcd48a45d2aa76731d8dbd13e919e4f73f8b989e90d4822"

# NK aircraft: keep fighters/helis on Large; move verified large fixed-wing to Heavy.
LARGE_AIRCRAFT_BUTTONS = [
    "Command_ConstructNorthKoreaAir_WZ10ME",
    "Command_ConstructNorthKoreaAir_Mig29S",
    "Command_ConstructNorthKoreaAir_J10B",
    "Command_ConstructNorthKoreaAir_Mig31K",
    "Command_ConstructNorthKoreaAir_Su25T",
    "Command_ConstructNorthKoreaAir_J20B",
    "Command_ConstructNorthKoreaAir_Mi28N",
    "Command_ConstructNorthKoreaAir_Ka52M",
]
HEAVY_AIRCRAFT_BUTTONS = [
    "Command_ConstructNorthKoreaAir_Su24M2",
    "Command_ConstructNorthKoreaAir_JH7A",
    "Command_ConstructNorthKoreaAir_Tu22M3M",
]


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


def csf_label_set(csf: bytes) -> set[str]:
    nlabels = struct.unpack_from("<I", csf, 8)[0]
    pos = 24
    labels: set[str] = set()
    for _ in range(nlabels):
        if pos + 12 > len(csf) or csf[pos : pos + 4] != b" LBL":
            break
        namelen = struct.unpack_from("<I", csf, pos + 8)[0]
        numvals = struct.unpack_from("<I", csf, pos + 4)[0]
        pos += 12
        label = csf[pos : pos + namelen].decode("ascii", errors="replace")
        pos += namelen
        labels.add(label)
        for _v in range(numvals):
            vtag = csf[pos : pos + 4]
            pos += 4
            strlen = struct.unpack_from("<I", csf, pos)[0]
            pos += 4 + strlen * 2
            if vtag == b"WRTS":
                elen = struct.unpack_from("<I", csf, pos)[0]
                pos += 4 + elen
    return labels


def append_csf_label(csf: bytes, label: str, value: str) -> bytes:
    if label in csf_label_set(csf):
        return csf
    assert value.isascii(), value
    utf16 = value.encode("utf-16-le")
    char_count = len(utf16) // 2
    xored = bytes(b ^ 0xFF for b in utf16)
    label_b = label.encode("ascii")
    entry = bytearray()
    entry += b" LBL"
    entry += struct.pack("<I", 1)
    entry += struct.pack("<I", len(label_b))
    entry += label_b
    entry += b" RTS"
    entry += struct.pack("<I", char_count)
    entry += xored
    data = bytearray(csf)
    nlabels = struct.unpack_from("<I", data, 8)[0]
    nstrings = struct.unpack_from("<I", data, 12)[0]
    struct.pack_into("<I", data, 8, nlabels + 1)
    struct.pack_into("<I", data, 12, nstrings + 1)
    return bytes(data) + bytes(entry)


def parse_csf_ok(csf: bytes) -> tuple[int, int, list[str]]:
    nlabels = struct.unpack_from("<I", csf, 8)[0]
    pos = 24
    labels = []
    errors = []
    for i in range(nlabels):
        if pos + 12 > len(csf) or csf[pos : pos + 4] != b" LBL":
            errors.append(f"bad at {i}")
            break
        numvals = struct.unpack_from("<I", csf, pos + 4)[0]
        namelen = struct.unpack_from("<I", csf, pos + 8)[0]
        pos += 12
        lab = csf[pos : pos + namelen].decode("ascii", errors="replace")
        pos += namelen
        labels.append(lab)
        for _ in range(numvals):
            vtag = csf[pos : pos + 4]
            pos += 4
            strlen = struct.unpack_from("<I", csf, pos)[0]
            pos += 4 + strlen * 2
            if vtag == b"WRTS":
                elen = struct.unpack_from("<I", csf, pos)[0]
                pos += 4 + elen
    return nlabels, len(labels), errors


def clone_pak_airbase(pak_text: str, new_obj: str, command_set: str) -> str:
    """Clone Pakistan airbase Object block to North Korea identity."""
    out = pak_text
    out = out.replace("Object Pakistan_LargeAirBase", f"Object {new_obj}")
    out = out.replace("Object Pakistan_HeavyAirBase", f"Object {new_obj}")
    out = re.sub(r"(Side\s*=\s*)Pakistan\b", r"\1NorthKorea", out)
    out = re.sub(
        r"(Object\s*=\s*)Pakistan_SupplyCenter\b",
        r"\1NorthKorea_SupplyCenter",
        out,
    )
    out = re.sub(r"(CommandSet\s*=\s*)\S+", rf"\1{command_set}", out, count=1)
    # Comments
    out = out.replace("Pakistan LARGE", "North Korea LARGE")
    out = out.replace("Pakistan HEAVY", "North Korea HEAVY")
    out = out.replace("Pakistan_AirfieldCommandSet", command_set)
    out = out.replace("Pakistan_HeavyAirBaseCommandSet", command_set)
    out = out.replace("Pakistan_LargeAirBase", new_obj)
    out = out.replace("Pakistan_HeavyAirBase", new_obj)
    # Ensure no Pakistan Side leak
    assert "Side             = Pakistan" not in out
    assert f"Side             = NorthKorea" in out or re.search(r"Side\s*=\s*NorthKorea", out)
    assert "Pakistan_SupplyCenter" not in out
    return out


def replace_commandset_block(cs_text: str, name: str, new_block: str) -> str:
    m = re.search(rf"^CommandSet\s+{re.escape(name)}\b.*?^End\s*$", cs_text, re.M | re.S)
    assert m, name
    return cs_text[: m.start()] + new_block.rstrip() + "\n" + cs_text[m.end() :]


def upsert_commandbutton(cb_text: str, name: str, block: str) -> str:
    m = re.search(rf"^CommandButton\s+{re.escape(name)}\b.*?^End\s*$", cb_text, re.M | re.S)
    if m:
        return cb_text[: m.start()] + block.rstrip() + "\n" + cb_text[m.end() :]
    return cb_text.rstrip() + "\n\n" + block.rstrip() + "\n"


def upsert_commandset(cs_text: str, name: str, block: str) -> str:
    m = re.search(rf"^CommandSet\s+{re.escape(name)}\b.*?^End\s*$", cs_text, re.M | re.S)
    if m:
        return cs_text[: m.start()] + block.rstrip() + "\n" + cs_text[m.end() :]
    return cs_text.rstrip() + "\n\n" + block.rstrip() + "\n"


def main() -> None:
    assert sha256(DATA_BIG) == BASE_DATA, sha256(DATA_BIG)
    assert sha256(ART_BIG) == BASE_ART

    # ART must already contain airbase W3Ds
    art_entries, art_raw = read_big(ART_BIG)
    art_names = {n.replace("/", "\\").lower() for n, _, _ in art_entries}
    assert any("theairport.w3d" in n for n in art_names), "TheAirPort.W3D missing from ART"
    assert any("hxusabigairport.w3d" in n for n in art_names), "HXUSABigAirPort.W3D missing from ART"

    entries, raw = read_big(DATA_BIG)
    fmap: dict[str, bytes] = {}
    disp: dict[str, str] = {}
    for name, off, size in entries:
        k = norm(name)
        if k not in fmap:
            disp[k] = name.replace("/", "\\")
        fmap[k] = raw[off : off + size]

    freeze_paths = {
        "pak_lab": r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_LargeAirBase.ini",
        "pak_hab": r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_HeavyAirBase.ini",
        "saudi_lab": r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_LargeAirBase.ini",
        "nato_lab": r"Data\INI\Object\Specter\NATO\Buildings\Nato_LargeAirBase.ini",
        "libya_lab": r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_LargeAirBase.ini",
    }
    freeze = {k: fmap[norm(p)] for k, p in freeze_paths.items()}

    pak_lab = fmap[norm(freeze_paths["pak_lab"])].decode("latin1")
    pak_hab = fmap[norm(freeze_paths["pak_hab"])].decode("latin1")
    assert "Model              = TheAirPort" in pak_lab
    assert "NumRows                 = 4" in pak_lab and "NumCols                 = 4" in pak_lab
    assert "Model              = HXUSABigAirPort" in pak_hab
    assert "NumRows                 = 2" in pak_hab and "NumCols                 = 3" in pak_hab

    pt_path = norm(r"Data\INI\PlayerTemplate.ini")
    cs_path = norm(r"Data\INI\CommandSet.ini")
    cb_path = norm(r"Data\INI\CommandButton.ini")
    csf_path = norm(r"Data\English\generals.csf")

    pt_before = fmap[pt_path]
    cs_text = fmap[cs_path].decode("latin1")
    cb_text = fmap[cb_path].decode("latin1")
    csf = fmap[csf_path]

    # Freeze non-NK PlayerTemplates
    freeze_pts = {}
    for name in (
        "FactionPakistan",
        "FactionSaudiArabia",
        "FactionNato",
        "FactionLibya",
        "FactionSouthAfrica",
        "FactionSweden",
        "FactionEgypt",
    ):
        m = re.search(rf"^PlayerTemplate\s+{name}\b.*?^End\s*$", pt_before.decode("latin1"), re.M | re.S)
        if m:
            freeze_pts[name] = m.group(0)

    # Verify current builder slots
    vt72 = re.search(r"^CommandSet\s+NorthKorea_VT72BCommandSet\b.*?^End\s*$", cs_text, re.M | re.S)
    assert vt72
    assert "5  = Command_ConstructNorthKorea_Airfield" in vt72.group(0) or re.search(
        r"5\s*=\s*Command_ConstructNorthKorea_Airfield", vt72.group(0)
    )
    assert re.search(r"9\s*=\s*Command_ConstructNorthKorea_Sam2_SAFE", vt72.group(0))

    old_air_btn = re.search(
        r"^CommandButton\s+Command_ConstructNorthKorea_Airfield\b.*?^End\s*$", cb_text, re.M | re.S
    )
    assert old_air_btn and "Object        = NorthKorea_Airfield" in old_air_btn.group(0)
    old_sam_btn = re.search(
        r"^CommandButton\s+Command_ConstructNorthKorea_Sam2_SAFE\b.*?^End\s*$", cb_text, re.M | re.S
    )
    assert old_sam_btn and "Object           = NorthKorea_Sam2" in old_sam_btn.group(0)

    # --- Create Large / Heavy Object INIs ---
    lab_obj = clone_pak_airbase(pak_lab, "NorthKorea_LargeAirBase", "NorthKorea_AirfieldCommandSet")
    hab_obj = clone_pak_airbase(pak_hab, "NorthKorea_HeavyAirBase", "NorthKorea_HeavyAirBaseCommandSet")
    assert "TheAirPort" in lab_obj and "HXUSABigAirPort" in hab_obj
    assert "Side             = NorthKorea" in lab_obj
    assert "Side             = NorthKorea" in hab_obj
    assert "NorthKorea_SupplyCenter" in lab_obj and "NorthKorea_SupplyCenter" in hab_obj
    # No Sam2 / science prereqs
    assert "Sam2" not in lab_obj and "Sam2" not in hab_obj
    assert "Science" not in lab_obj.split("Prerequisites")[1].split("End")[0]
    assert "Science" not in hab_obj.split("Prerequisites")[1].split("End")[0]

    lab_path = r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_LargeAirBase.ini"
    hab_path = r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_HeavyAirBase.ini"
    assert norm(lab_path) not in fmap
    assert norm(hab_path) not in fmap
    fmap[norm(lab_path)] = lab_obj.encode("latin1")
    disp[norm(lab_path)] = lab_path
    fmap[norm(hab_path)] = hab_obj.encode("latin1")
    disp[norm(hab_path)] = hab_path

    # --- CommandSets: Large keeps fighter roster; Heavy gets verified bombers ---
    large_cs_lines = ["CommandSet NorthKorea_AirfieldCommandSet"]
    for i, btn in enumerate(LARGE_AIRCRAFT_BUTTONS, 1):
        large_cs_lines.append(f"  {i}  = {btn}")
    large_cs_lines += [
        "  12 = Command_UpgradeAmericaCountermeasures",
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
        "End",
    ]
    large_cs = "\n".join(large_cs_lines) + "\n"

    heavy_cs_lines = ["CommandSet NorthKorea_HeavyAirBaseCommandSet"]
    for i, btn in enumerate(HEAVY_AIRCRAFT_BUTTONS, 1):
        heavy_cs_lines.append(f"  {i}  = {btn}")
    heavy_cs_lines += [
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
        "End",
    ]
    heavy_cs = "\n".join(heavy_cs_lines) + "\n"

    cs_text = upsert_commandset(cs_text, "NorthKorea_AirfieldCommandSet", large_cs)
    cs_text = upsert_commandset(cs_text, "NorthKorea_HeavyAirBaseCommandSet", heavy_cs)

    # --- Construct buttons ---
    large_btn = """CommandButton Command_ConstructNorthKorea_LargeAirBase
  Command       = DOZER_CONSTRUCT
  Object        = NorthKorea_LargeAirBase
  TextLabel     = CONTROLBAR:ConstructNorthKoreaAirfield
  ButtonImage   = irq_airfld
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipNorthKoreaBuildAirfield
End
"""
    heavy_btn = """CommandButton Command_ConstructNorthKorea_HeavyAirBase
  Command       = DOZER_CONSTRUCT
  Object        = NorthKorea_HeavyAirBase
  TextLabel     = CONTROLBAR:ConstructNorthKorea_HeavyAirBase
  ButtonImage   = us_airfield
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipConstructNorthKorea_HeavyAirBase
End
"""
    cb_text = upsert_commandbutton(cb_text, "Command_ConstructNorthKorea_LargeAirBase", large_btn)
    cb_text = upsert_commandbutton(cb_text, "Command_ConstructNorthKorea_HeavyAirBase", heavy_btn)

    # Ensure no Sam2 prereqs leaked onto Heavy button
    heavy_m = re.search(
        r"^CommandButton\s+Command_ConstructNorthKorea_HeavyAirBase\b.*?^End\s*$",
        cb_text,
        re.M | re.S,
    )
    assert heavy_m and "Sam2" not in heavy_m.group(0)
    assert "Science" not in heavy_m.group(0)
    assert "Object        = NorthKorea_HeavyAirBase" in heavy_m.group(0)

    # --- Builder palette: only slots 5 and 9 ---
    def repl_vt72(m: re.Match) -> str:
        block = m.group(0)
        block = re.sub(
            r"(5\s*=\s*)Command_ConstructNorthKorea_Airfield\b",
            r"\1Command_ConstructNorthKorea_LargeAirBase",
            block,
        )
        block = re.sub(
            r"(9\s*=\s*)Command_ConstructNorthKorea_Sam2_SAFE\b",
            r"\1Command_ConstructNorthKorea_HeavyAirBase",
            block,
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
    vt72b = re.search(r"^CommandSet\s+NorthKorea_VT72BCommandSet\b.*?^End\s*$", cs_text2, re.M | re.S)
    assert "Command_ConstructNorthKorea_LargeAirBase" in vt72b.group(0)
    assert "Command_ConstructNorthKorea_HeavyAirBase" in vt72b.group(0)
    assert "Command_ConstructNorthKorea_Airfield" not in vt72b.group(0)
    assert "Command_ConstructNorthKorea_Sam2_SAFE" not in vt72b.group(0)
    # Unrelated slots unchanged
    assert "Command_ConstructNorthKorea_PowerPlant" in vt72b.group(0)
    assert "Command_ConstructNorthKorea_WarFactory" in vt72b.group(0)
    assert "Command_ConstructNorthKorea_MIC_SAFE" in vt72b.group(0)
    assert "Command_ConstructNorthKorea_NuclearCenter" in vt72b.group(0)

    fmap[cs_path] = cs_text2.encode("latin1")
    fmap[cb_path] = cb_text.encode("latin1")

    # CSF strings for HeavyAirBase UI
    csf = append_csf_label(csf, "CONTROLBAR:ConstructNorthKorea_HeavyAirBase", "Heavy Air Base")
    csf = append_csf_label(
        csf,
        "CONTROLBAR:ToolTipConstructNorthKorea_HeavyAirBase",
        "Builds the North Korea heavy airbase for large aircraft.",
    )
    nlab, parsed, errs = parse_csf_ok(csf)
    assert not errs and nlab == parsed
    fmap[csf_path] = csf

    # Freeze asserts
    for k, p in freeze_paths.items():
        assert fmap[norm(p)] == freeze[k], k
    assert fmap[pt_path] == pt_before  # PT untouched

    # Sam2 object still exists (not globally deleted)
    sam_still = False
    for _n, b in fmap.items():
        if re.search(r"^Object\s+NorthKorea_Sam2\b", b.decode("latin1", errors="replace"), re.M):
            sam_still = True
            break
    assert sam_still

    DATA_BIG.write_bytes(build_big({disp[k]: v for k, v in fmap.items()}))
    data_sha = sha256(DATA_BIG)
    art_sha = sha256(ART_BIG)
    assert art_sha == BASE_ART

    # -------- Validation from rebuilt BIG --------
    e2, r2 = read_big(DATA_BIG)
    f2 = {norm(n): r2[o : o + s] for n, o, s in e2}
    cs2 = f2[cs_path].decode("latin1")
    cb2 = f2[cb_path].decode("latin1")
    cs_names = set(re.findall(r"^CommandSet\s+(\S+)", cs2, re.M))
    cb_names = set(re.findall(r"^CommandButton\s+(\S+)", cb2, re.M))

    def object_exists(obj: str) -> bool:
        for b in f2.values():
            if re.search(rf"^Object\s+{re.escape(obj)}\b", b.decode("latin1", errors="replace"), re.M):
                return True
        return False

    assert object_exists("NorthKorea_LargeAirBase")
    assert object_exists("NorthKorea_HeavyAirBase")
    assert object_exists("NorthKorea_Sam2")  # not deleted
    assert object_exists("NorthKorea_Airfield")  # old object kept

    # duplicates
    assert re.findall(r"^Object\s+NorthKorea_LargeAirBase\b", "\n".join(
        b.decode("latin1", errors="replace") for b in f2.values()
    ), re.M).count("Object NorthKorea_LargeAirBase") == 1 or sum(
        1 for b in f2.values() if re.search(r"^Object\s+NorthKorea_LargeAirBase\b", b.decode("latin1", errors="replace"), re.M)
    ) == 1
    assert sum(
        1 for b in f2.values() if re.search(r"^Object\s+NorthKorea_HeavyAirBase\b", b.decode("latin1", errors="replace"), re.M)
    ) == 1
    assert cs_names.count if False else list(re.findall(r"^CommandSet\s+NorthKorea_HeavyAirBaseCommandSet\b", cs2, re.M)) == [
        "CommandSet NorthKorea_HeavyAirBaseCommandSet"
    ] or re.findall(r"^CommandSet\s+(NorthKorea_HeavyAirBaseCommandSet)\b", cs2, re.M) == [
        "NorthKorea_HeavyAirBaseCommandSet"
    ]

    vt = re.search(r"^CommandSet\s+NorthKorea_VT72BCommandSet\b.*?^End\s*$", cs2, re.M | re.S).group(0)
    assert re.search(r"5\s*=\s*Command_ConstructNorthKorea_LargeAirBase", vt)
    assert re.search(r"9\s*=\s*Command_ConstructNorthKorea_HeavyAirBase", vt)
    assert "Command_ConstructNorthKorea_Airfield" not in vt
    assert "Sam2" not in vt

    # Full chains
    for btn_name, obj_name, cs_name, aircraft in [
        (
            "Command_ConstructNorthKorea_LargeAirBase",
            "NorthKorea_LargeAirBase",
            "NorthKorea_AirfieldCommandSet",
            LARGE_AIRCRAFT_BUTTONS,
        ),
        (
            "Command_ConstructNorthKorea_HeavyAirBase",
            "NorthKorea_HeavyAirBase",
            "NorthKorea_HeavyAirBaseCommandSet",
            HEAVY_AIRCRAFT_BUTTONS,
        ),
    ]:
        assert btn_name in cb_names
        bb = re.search(rf"^CommandButton\s+{re.escape(btn_name)}\b.*?^End\s*$", cb2, re.M | re.S).group(0)
        assert f"Object        = {obj_name}" in bb or re.search(rf"Object\s*=\s*{obj_name}", bb)
        assert cs_name in cs_names
        # Object CommandSet
        ob = None
        for b in f2.values():
            t = b.decode("latin1", errors="replace")
            if re.search(rf"^Object\s+{re.escape(obj_name)}\b", t, re.M):
                ob = t
                break
        assert ob and f"CommandSet          = {cs_name}" in ob
        assert "Side             = NorthKorea" in ob
        assert "Pakistan" not in re.search(r"Side\s*=\s*\S+", ob).group(0)
        csb = re.search(rf"^CommandSet\s+{re.escape(cs_name)}\b.*?^End\s*$", cs2, re.M | re.S).group(0)
        for abtn in aircraft:
            assert abtn in csb
            assert abtn in cb_names
            abb = re.search(rf"^CommandButton\s+{re.escape(abtn)}\b.*?^End\s*$", cb2, re.M | re.S).group(0)
            aobj = re.search(r"Object\s*=\s*(\S+)", abb).group(1)
            assert object_exists(aobj), aobj

    # Capacity / W3D
    lab = next(
        b.decode("latin1", errors="replace")
        for b in f2.values()
        if re.search(r"^Object\s+NorthKorea_LargeAirBase\b", b.decode("latin1", errors="replace"), re.M)
    )
    assert "TheAirPort" in lab and "NumRows                 = 4" in lab and "NumCols                 = 4" in lab
    hab = next(
        b.decode("latin1", errors="replace")
        for b in f2.values()
        if re.search(r"^Object\s+NorthKorea_HeavyAirBase\b", b.decode("latin1", errors="replace"), re.M)
    )
    assert "HXUSABigAirPort" in hab and "NumRows                 = 2" in hab and "NumCols                 = 3" in hab

    # Frozen factions
    for k, p in freeze_paths.items():
        assert f2[norm(p)] == freeze[k], k
    assert f2[pt_path] == pt_before
    for name, block in freeze_pts.items():
        assert (
            re.search(rf"^PlayerTemplate\s+{name}\b.*?^End\s*$", f2[pt_path].decode("latin1"), re.M | re.S).group(0)
            == block
        )

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")

    report = f"""NORTH KOREA TWO-AIRBASE CONVERSION = PASS

North Korea Side identifier = NorthKorea

OLD AIRFIELD:
Object = NorthKorea_Airfield
ConstructButton = Command_ConstructNorthKorea_Airfield
Builder slot = 5 (NorthKorea_VT72BCommandSet)

NEW LARGE AIRBASE:
Object = NorthKorea_LargeAirBase
ConstructButton = Command_ConstructNorthKorea_LargeAirBase
CommandSet = NorthKorea_AirfieldCommandSet
W3D = TheAirPort.W3D
Capacity = 16 (NumRows=4 x NumCols=4)
Aircraft roster = {', '.join(LARGE_AIRCRAFT_BUTTONS)}

OLD SAM2:
Object = NorthKorea_Sam2
ConstructButton = Command_ConstructNorthKorea_Sam2_SAFE
Builder slot = 9 (NorthKorea_VT72BCommandSet)

NEW HEAVY AIRBASE:
Object = NorthKorea_HeavyAirBase
ConstructButton = Command_ConstructNorthKorea_HeavyAirBase
CommandSet = NorthKorea_HeavyAirBaseCommandSet
W3D = HXUSABigAirPort.W3D
Capacity = 6 (NumRows=2 x NumCols=3)
Heavy aircraft roster = {', '.join(HEAVY_AIRCRAFT_BUTTONS)}
Prerequisite = NorthKorea_SupplyCenter (mirrors Pakistan_HeavyAirBase)

NorthKoreaSam2 removed from builder palette = YES
NorthKoreaSam2 globally deleted = NO

Pakistan airbases changed = NO
Other factions changed = NO

ACTIVE FILES CHANGED:
- Data\\INI\\CommandSet.ini
- Data\\INI\\CommandButton.ini
- Data\\English\\generals.csf
- Data\\INI\\Object\\Specter\\North Korea\\Buildings\\NorthKorea_LargeAirBase.ini (NEW)
- Data\\INI\\Object\\Specter\\North Korea\\Buildings\\NorthKorea_HeavyAirBase.ini (NEW)

DATA sha256 = {data_sha}
ART sha256  = {art_sha} (UNCHANGED)
ZIP sha256  = {sha256(ZIP_PATH)}
ZIP path    = {ZIP_PATH}
ZIP size    = {ZIP_PATH.stat().st_size}
"""
    NOTE.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
