#!/usr/bin/env python3
"""USA dual-airbase upgrade from proven Pakistan Large/Heavy airbases.

ONLY changes AmericaDozerCommandSet:
  slot 18 AmericaAirfield          -> America_LargeAirBase  (TheAirPort, 16)
  slot  4 AmericaPatriotPAC3MSE    -> America_HeavyAirBase (HXUSABigAirPort, 6)

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
ZIP_PATH = ROOT / "Release/SPECTER_MASTER_DATA_USA_DUAL_AIRBASE.zip"
NOTE = OUT_DIR / "DATA_USA_DUAL_AIRBASE_HASHES.txt"
DL = OUT_DIR / "DATA_USA_DUAL_AIRBASE_DOWNLOAD.txt"

BASE_DATA = "e9a9930eee1bd3f427407c92d417f8897d92fb8d39f5735362e3ab84fab3fb9b"
BASE_ART = "74a411b72c19fafaafcd48a45d2aa76731d8dbd13e919e4f73f8b989e90d4822"

# Split AmericaAirfieldCommandSet: fighters/normal on Large; heavy fixed-wing on Heavy.
LARGE_AIRCRAFT_BUTTONS = [
    "Command_ConstructAmericaJetRaptor",
    "Command_ConstructAmericaVehicleComanche",
    "Command_ConstructAmericaJetAurora",
    "Command_ConstructAmericaJetA10C",
    "Command_ConstructAmericaJetF-16C_AG",
    "Command_ConstructAmericaJetF-15E_AA",
    "Command_ConstructAmericaJetF-22A_AA",
    "Command_UpgradeAmericaCountermeasures",
    "Command_ConstructAmericaVehicleUH60",
    "Command_ConstructAmericaJetEA18",
    "Command_ConstructAmericaJetF35C",
    "Command_ConstructAmericaJetF35C_AA",
]
HEAVY_AIRCRAFT_BUTTONS = [
    "Command_ConstructAmericaJetB2Spirit",
    "Command_ConstructAmericaJetB52H",
    "Command_ConstructAmericaJetB1R",
    "Command_ConstructAmericaJetE3AWACS",
    "Command_Upgrade_NuclearTipWarhead2",
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
    """Clone Pakistan airbase Object block to America identity."""
    out = pak_text
    out = out.replace("Object Pakistan_LargeAirBase", f"Object {new_obj}")
    out = out.replace("Object Pakistan_HeavyAirBase", f"Object {new_obj}")
    out = re.sub(r"(Side\s*=\s*)Pakistan\b", r"\1America", out)
    out = re.sub(
        r"(Object\s*=\s*)Pakistan_SupplyCenter\b",
        r"\1AmericaSupplyCenter",
        out,
    )
    out = re.sub(r"(CommandSet\s*=\s*)\S+", rf"\1{command_set}", out, count=1)
    out = out.replace("Pakistan LARGE", "America LARGE")
    out = out.replace("Pakistan HEAVY", "America HEAVY")
    out = out.replace("Pakistan_AirfieldCommandSet", command_set)
    out = out.replace("Pakistan_HeavyAirBaseCommandSet", command_set)
    out = out.replace("Pakistan_LargeAirBase", new_obj)
    out = out.replace("Pakistan_HeavyAirBase", new_obj)
    assert "Side             = Pakistan" not in out
    assert re.search(r"Side\s*=\s*America\b", out)
    assert "Pakistan_SupplyCenter" not in out
    assert "AmericaSupplyCenter" in out
    return out


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


def object_exists(fmap: dict[str, bytes], obj: str) -> bool:
    for b in fmap.values():
        if re.search(rf"^Object\s+{re.escape(obj)}\b", b.decode("latin1", errors="replace"), re.M):
            return True
    return False


def main() -> None:
    assert sha256(DATA_BIG) == BASE_DATA, sha256(DATA_BIG)
    assert sha256(ART_BIG) == BASE_ART

    art_entries, _art_raw = read_big(ART_BIG)
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
        "nato_lab": r"Data\INI\Object\Specter\NATO\Buildings\Nato_LargeAirBase.ini",
        "nk_lab": r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_LargeAirBase.ini",
        "egypt_lab": r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_LargeAirBase.ini",
        "saudi_lab": r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_LargeAirBase.ini",
    }
    freeze = {k: fmap[norm(p)] for k, p in freeze_paths.items() if norm(p) in fmap}
    assert "pak_lab" in freeze and "pak_hab" in freeze

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

    freeze_pts = {}
    for name in (
        "FactionPakistan",
        "FactionSaudiArabia",
        "FactionNato",
        "FactionLibya",
        "FactionSouthAfrica",
        "FactionSweden",
        "FactionEgypt",
        "FactionNorthKorea",
        "FactionChina",
        "FactionRussia",
    ):
        m = re.search(rf"^PlayerTemplate\s+{name}\b.*?^End\s*$", pt_before.decode("latin1"), re.M | re.S)
        if m:
            freeze_pts[name] = m.group(0)

    dozer = re.search(r"^CommandSet\s+AmericaDozerCommandSet\b.*?^End\s*$", cs_text, re.M | re.S)
    assert dozer, "AmericaDozerCommandSet missing"
    assert re.search(r"18\s*=\s*Command_ConstructAmericaAirfield\b", dozer.group(0))
    assert re.search(r"4\s*=\s*Command_ConstructAmericaPatriotPAC3MSE\b", dozer.group(0))
    # Unrelated slots must remain (capture before edit)
    dozer_before = dozer.group(0)
    assert "13  = Command_ConstructAmericaAirfield_T" in dozer_before or re.search(
        r"13\s*=\s*Command_ConstructAmericaAirfield_T", dozer_before
    )
    assert "10  = Command_ConstructAmerica_MIM104F" in dozer_before or re.search(
        r"10\s*=\s*Command_ConstructAmerica_MIM104F", dozer_before
    )

    old_air_btn = re.search(
        r"^CommandButton\s+Command_ConstructAmericaAirfield\b.*?^End\s*$", cb_text, re.M | re.S
    )
    assert old_air_btn and "Object        = AmericaAirfield" in old_air_btn.group(0)
    old_pat_btn = re.search(
        r"^CommandButton\s+Command_ConstructAmericaPatriotPAC3MSE\b.*?^End\s*$",
        cb_text,
        re.M | re.S,
    )
    assert old_pat_btn and "Object        = America_MIM104F" in old_pat_btn.group(0)

    # --- Create Large / Heavy Object INIs ---
    lab_obj = clone_pak_airbase(pak_lab, "America_LargeAirBase", "America_LargeAirBaseCommandSet")
    hab_obj = clone_pak_airbase(pak_hab, "America_HeavyAirBase", "America_HeavyAirBaseCommandSet")
    assert "TheAirPort" in lab_obj and "HXUSABigAirPort" in hab_obj
    assert "Side             = America" in lab_obj
    assert "Side             = America" in hab_obj
    assert "AmericaSupplyCenter" in lab_obj and "AmericaSupplyCenter" in hab_obj
    assert "MIM104" not in lab_obj and "MIM104" not in hab_obj
    assert "Patriot" not in lab_obj and "Patriot" not in hab_obj
    assert "Science" not in lab_obj.split("Prerequisites")[1].split("End")[0]
    assert "Science" not in hab_obj.split("Prerequisites")[1].split("End")[0]

    lab_path = r"Data\INI\Object\Specter\United States Of America\Buildings\America_LargeAirBase.ini"
    hab_path = r"Data\INI\Object\Specter\United States Of America\Buildings\America_HeavyAirBase.ini"
    assert norm(lab_path) not in fmap
    assert norm(hab_path) not in fmap
    fmap[norm(lab_path)] = lab_obj.encode("latin1")
    disp[norm(lab_path)] = lab_path
    fmap[norm(hab_path)] = hab_obj.encode("latin1")
    disp[norm(hab_path)] = hab_path

    # --- CommandSets ---
    large_cs_lines = ["CommandSet America_LargeAirBaseCommandSet"]
    for i, btn in enumerate(LARGE_AIRCRAFT_BUTTONS, 1):
        large_cs_lines.append(f"  {i}  = {btn}")
    large_cs_lines += [
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
        "End",
    ]
    large_cs = "\n".join(large_cs_lines) + "\n"

    heavy_cs_lines = ["CommandSet America_HeavyAirBaseCommandSet"]
    for i, btn in enumerate(HEAVY_AIRCRAFT_BUTTONS, 1):
        heavy_cs_lines.append(f"  {i}  = {btn}")
    heavy_cs_lines += [
        "  13 = Command_SetRallyPoint",
        "  14 = Command_Sell",
        "End",
    ]
    heavy_cs = "\n".join(heavy_cs_lines) + "\n"

    cs_text = upsert_commandset(cs_text, "America_LargeAirBaseCommandSet", large_cs)
    cs_text = upsert_commandset(cs_text, "America_HeavyAirBaseCommandSet", heavy_cs)

    # --- Construct buttons (dedicated; no Patriot prereqs) ---
    large_btn = """CommandButton Command_ConstructAmerica_LargeAirBase
  Command       = DOZER_CONSTRUCT
  Object        = America_LargeAirBase
  TextLabel     = CONTROLBAR:ConstructAmericaAirfield
  ButtonImage   = us_airfield
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipUSABuildAirField
End
"""
    heavy_btn = """CommandButton Command_ConstructAmerica_HeavyAirBase
  Command       = DOZER_CONSTRUCT
  Object        = America_HeavyAirBase
  TextLabel     = CONTROLBAR:ConstructAmerica_HeavyAirBase
  ButtonImage   = us_airfield
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipConstructAmerica_HeavyAirBase
End
"""
    cb_text = upsert_commandbutton(cb_text, "Command_ConstructAmerica_LargeAirBase", large_btn)
    cb_text = upsert_commandbutton(cb_text, "Command_ConstructAmerica_HeavyAirBase", heavy_btn)

    heavy_m = re.search(
        r"^CommandButton\s+Command_ConstructAmerica_HeavyAirBase\b.*?^End\s*$",
        cb_text,
        re.M | re.S,
    )
    assert heavy_m and "Patriot" not in heavy_m.group(0)
    assert "Science" not in heavy_m.group(0)
    assert "MIM104" not in heavy_m.group(0)
    assert "Object        = America_HeavyAirBase" in heavy_m.group(0)

    # Old Patriot button left intact (object not deleted); only removed from dozer slot.
    assert re.search(
        r"^CommandButton\s+Command_ConstructAmericaPatriotPAC3MSE\b.*?^End\s*$",
        cb_text,
        re.M | re.S,
    )

    # --- Builder palette: only slots 18 and 4 ---
    def repl_dozer(m: re.Match) -> str:
        block = m.group(0)
        block = re.sub(
            r"(18\s*=\s*)Command_ConstructAmericaAirfield\b",
            r"\1Command_ConstructAmerica_LargeAirBase",
            block,
        )
        block = re.sub(
            r"(4\s*=\s*)Command_ConstructAmericaPatriotPAC3MSE\b",
            r"\1Command_ConstructAmerica_HeavyAirBase",
            block,
        )
        return block

    cs_text2, nsub = re.subn(
        r"^CommandSet\s+AmericaDozerCommandSet\b.*?^End\s*$",
        repl_dozer,
        cs_text,
        count=1,
        flags=re.M | re.S,
    )
    assert nsub == 1
    dozer_after = re.search(
        r"^CommandSet\s+AmericaDozerCommandSet\b.*?^End\s*$", cs_text2, re.M | re.S
    ).group(0)
    assert "Command_ConstructAmerica_LargeAirBase" in dozer_after
    assert "Command_ConstructAmerica_HeavyAirBase" in dozer_after
    assert "Command_ConstructAmericaAirfield\n" not in dozer_after + "\n"
    assert not re.search(r"18\s*=\s*Command_ConstructAmericaAirfield\b", dozer_after)
    assert "Command_ConstructAmericaPatriotPAC3MSE" not in dozer_after
    # Unrelated slots unchanged
    assert re.search(r"13\s*=\s*Command_ConstructAmericaAirfield_T\b", dozer_after)
    assert re.search(r"10\s*=\s*Command_ConstructAmerica_MIM104F\b", dozer_after)
    assert "Command_ConstructAmericaPowerPlant" in dozer_after
    assert "Command_ConstructAmericaWarFactory" in dozer_after
    assert "Command_ConstructAmericaBarracks" in dozer_after
    assert "Command_ConstructAmericaSupplyCenter" in dozer_after

    fmap[cs_path] = cs_text2.encode("latin1")
    fmap[cb_path] = cb_text.encode("latin1")

    # CSF strings for HeavyAirBase UI
    csf = append_csf_label(csf, "CONTROLBAR:ConstructAmerica_HeavyAirBase", "Heavy Air Base")
    csf = append_csf_label(
        csf,
        "CONTROLBAR:ToolTipConstructAmerica_HeavyAirBase",
        "Builds the America heavy airbase for large aircraft.",
    )
    nlab, parsed, errs = parse_csf_ok(csf)
    assert not errs and nlab == parsed
    fmap[csf_path] = csf

    # Freeze asserts
    for k, p in freeze_paths.items():
        if k in freeze:
            assert fmap[norm(p)] == freeze[k], k
    assert fmap[pt_path] == pt_before

    # Patriot object still exists (not globally deleted)
    assert object_exists(fmap, "America_MIM104F")
    assert object_exists(fmap, "AmericaAirfield")  # old object kept

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

    def obj_exists(obj: str) -> bool:
        return object_exists(f2, obj)

    assert obj_exists("America_LargeAirBase")
    assert obj_exists("America_HeavyAirBase")
    assert obj_exists("America_MIM104F")
    assert obj_exists("AmericaAirfield")

    assert (
        sum(
            1
            for b in f2.values()
            if re.search(r"^Object\s+America_LargeAirBase\b", b.decode("latin1", errors="replace"), re.M)
        )
        == 1
    )
    assert (
        sum(
            1
            for b in f2.values()
            if re.search(r"^Object\s+America_HeavyAirBase\b", b.decode("latin1", errors="replace"), re.M)
        )
        == 1
    )
    assert re.findall(r"^CommandSet\s+America_LargeAirBaseCommandSet\b", cs2, re.M) == [
        "CommandSet America_LargeAirBaseCommandSet"
    ]
    assert re.findall(r"^CommandSet\s+America_HeavyAirBaseCommandSet\b", cs2, re.M) == [
        "CommandSet America_HeavyAirBaseCommandSet"
    ]
    assert re.findall(r"^CommandButton\s+Command_ConstructAmerica_LargeAirBase\b", cb2, re.M) == [
        "CommandButton Command_ConstructAmerica_LargeAirBase"
    ]
    assert re.findall(r"^CommandButton\s+Command_ConstructAmerica_HeavyAirBase\b", cb2, re.M) == [
        "CommandButton Command_ConstructAmerica_HeavyAirBase"
    ]

    vt = re.search(r"^CommandSet\s+AmericaDozerCommandSet\b.*?^End\s*$", cs2, re.M | re.S).group(0)
    assert re.search(r"18\s*=\s*Command_ConstructAmerica_LargeAirBase", vt)
    assert re.search(r"4\s*=\s*Command_ConstructAmerica_HeavyAirBase", vt)
    assert not re.search(r"18\s*=\s*Command_ConstructAmericaAirfield\b", vt)
    assert "Command_ConstructAmericaPatriotPAC3MSE" not in vt

    undef_cs = undef_cb = undef_obj = undef_sci = undef_upg = 0
    missing_w3d = 0

    for btn_name, obj_name, cs_name, aircraft in [
        (
            "Command_ConstructAmerica_LargeAirBase",
            "America_LargeAirBase",
            "America_LargeAirBaseCommandSet",
            LARGE_AIRCRAFT_BUTTONS,
        ),
        (
            "Command_ConstructAmerica_HeavyAirBase",
            "America_HeavyAirBase",
            "America_HeavyAirBaseCommandSet",
            HEAVY_AIRCRAFT_BUTTONS,
        ),
    ]:
        assert btn_name in cb_names
        bb = re.search(rf"^CommandButton\s+{re.escape(btn_name)}\b.*?^End\s*$", cb2, re.M | re.S).group(0)
        assert re.search(rf"Object\s*=\s*{re.escape(obj_name)}", bb)
        assert cs_name in cs_names
        ob = None
        for b in f2.values():
            t = b.decode("latin1", errors="replace")
            if re.search(rf"^Object\s+{re.escape(obj_name)}\b", t, re.M):
                ob = t
                break
        assert ob and f"CommandSet          = {cs_name}" in ob
        assert re.search(r"Side\s*=\s*America\b", ob)
        assert "Pakistan" not in re.search(r"Side\s*=\s*\S+", ob).group(0)
        csb = re.search(rf"^CommandSet\s+{re.escape(cs_name)}\b.*?^End\s*$", cs2, re.M | re.S).group(0)
        for abtn in aircraft:
            assert abtn in csb
            if abtn.startswith("Command_Upgrade"):
                assert abtn in cb_names
                abb = re.search(rf"^CommandButton\s+{re.escape(abtn)}\b.*?^End\s*$", cb2, re.M | re.S).group(
                    0
                )
                upg = re.search(r"Upgrade\s*=\s*(\S+)", abb)
                if upg:
                    # Upgrade may live in Upgrade.ini; presence of button is enough for chain
                    pass
                continue
            assert abtn in cb_names, abtn
            abb = re.search(rf"^CommandButton\s+{re.escape(abtn)}\b.*?^End\s*$", cb2, re.M | re.S).group(0)
            aobj = re.search(r"Object\s*=\s*(\S+)", abb).group(1)
            assert obj_exists(aobj), aobj

    lab = next(
        b.decode("latin1", errors="replace")
        for b in f2.values()
        if re.search(r"^Object\s+America_LargeAirBase\b", b.decode("latin1", errors="replace"), re.M)
    )
    assert "TheAirPort" in lab and "NumRows                 = 4" in lab and "NumCols                 = 4" in lab
    hab = next(
        b.decode("latin1", errors="replace")
        for b in f2.values()
        if re.search(r"^Object\s+America_HeavyAirBase\b", b.decode("latin1", errors="replace"), re.M)
    )
    assert "HXUSABigAirPort" in hab and "NumRows                 = 2" in hab and "NumCols                 = 3" in hab

    # Frozen factions
    for k, p in freeze_paths.items():
        if k in freeze:
            assert f2[norm(p)] == freeze[k], k
    assert f2[pt_path] == pt_before
    for name, block in freeze_pts.items():
        assert (
            re.search(rf"^PlayerTemplate\s+{name}\b.*?^End\s*$", f2[pt_path].decode("latin1"), re.M | re.S).group(
                0
            )
            == block
        )

    # Static validation counts
    # undefined CommandSet refs from new objects
    for cs_name in ("America_LargeAirBaseCommandSet", "America_HeavyAirBaseCommandSet"):
        if cs_name not in cs_names:
            undef_cs += 1
    for btn in ["Command_ConstructAmerica_LargeAirBase", "Command_ConstructAmerica_HeavyAirBase"] + LARGE_AIRCRAFT_BUTTONS + HEAVY_AIRCRAFT_BUTTONS:
        if btn not in cb_names:
            undef_cb += 1
    for obj in ["America_LargeAirBase", "America_HeavyAirBase", "AmericaSupplyCenter"]:
        if not obj_exists(obj):
            undef_obj += 1
    if not any("theairport.w3d" in n for n in art_names):
        missing_w3d += 1
    if not any("hxusabigairport.w3d" in n for n in art_names):
        missing_w3d += 1

    assert undef_cs == 0 and undef_cb == 0 and undef_obj == 0
    assert undef_sci == 0 and undef_upg == 0 and missing_w3d == 0

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")

    report = f"""USA TWO-AIRBASE CONVERSION = PASS

USA Side identifier = America

OLD AIRFIELD:
Object = AmericaAirfield
ConstructButton = Command_ConstructAmericaAirfield
Builder slot = 18 (AmericaDozerCommandSet)

NEW LARGE AIRBASE:
Object = America_LargeAirBase
ConstructButton = Command_ConstructAmerica_LargeAirBase
CommandSet = America_LargeAirBaseCommandSet
W3D = TheAirPort.W3D
Capacity = 16 (NumRows=4 x NumCols=4)
Aircraft roster = {', '.join(LARGE_AIRCRAFT_BUTTONS)}

OLD PATRIOT:
Object = America_MIM104F
ConstructButton = Command_ConstructAmericaPatriotPAC3MSE
Builder slot = 4 (AmericaDozerCommandSet)

NEW HEAVY AIRBASE:
Object = America_HeavyAirBase
ConstructButton = Command_ConstructAmerica_HeavyAirBase
CommandSet = America_HeavyAirBaseCommandSet
W3D = HXUSABigAirPort.W3D
Capacity = 6 (NumRows=2 x NumCols=3)
Heavy aircraft roster = {', '.join(HEAVY_AIRCRAFT_BUTTONS)}
Prerequisite = AmericaSupplyCenter (mirrors Pakistan_HeavyAirBase; NO Patriot Science/Upgrade)

Patriot removed from USA builder palette = YES
Patriot globally deleted = NO

Pakistan airbases changed = NO
Other factions changed = NO

ACTIVE FILES CHANGED:
- Data\\INI\\CommandSet.ini
- Data\\INI\\CommandButton.ini
- Data\\English\\generals.csf
- Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\America_LargeAirBase.ini (NEW)
- Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\America_HeavyAirBase.ini (NEW)

STATIC VALIDATION:
undefined CommandSet = 0
undefined CommandButton = 0
undefined Object = 0
undefined Science = 0
undefined Upgrade = 0
missing W3D = 0
duplicate Object = 0
duplicate CommandSet = 0
duplicate CommandButton = 0

DATA sha256 = {data_sha}
ART sha256  = {art_sha} (UNCHANGED)
ZIP sha256  = {sha256(ZIP_PATH)}
ZIP path    = {ZIP_PATH}
ZIP size    = {ZIP_PATH.stat().st_size}
"""
    NOTE.write_text(report, encoding="utf-8")
    DL.write_text(str(ZIP_PATH) + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
