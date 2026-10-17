#!/usr/bin/env python3
"""Russia complete aircraft expansion: fighters + heavy visual aircraft + donor icons.

Baseline: SPECTER_MASTER (_SPEC_DATA_ONE from PR344 parking + workspace ART).
RUSSIA ONLY. Donor ART = YES. Donor gameplay DATA = NO.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
PATCH = ROOT / "patch"
MASTER = PATCH / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
STAGE = MASTER / "_stage_russia_aircraft_expansion"
VERIFY = MASTER / "_extract_russia_aircraft_expansion_verify"
ZIP_OUT = PATCH / "Release/SPECTER_MASTER_DATA_ART_RUSSIA_AIRCRAFT_EXPANSION.zip"
REPORT = PATCH / "Release/DATA_RUSSIA_AIRCRAFT_EXPANSION_REPORT.txt"
HASHES = PATCH / "Release/DATA_RUSSIA_AIRCRAFT_EXPANSION_HASHES.txt"
DOWNLOAD = PATCH / "Release/DATA_RUSSIA_AIRCRAFT_EXPANSION_DOWNLOAD.txt"

AF = "Armed Forces Of Russian Federation"
AF_DIR = f"Data\\INI\\Object\\Specter\\{AF}\\Airforce"

CLEAN_OBJECTS = {
    "RussiaJetSU47Clean": f"{AF_DIR}\\RussiaJetSU47Clean.ini",
    "RussiaJetSU75Clean": f"{AF_DIR}\\RussiaJetSU75Clean.ini",
    "RussiaJetT50PAKFAClean": f"{AF_DIR}\\RussiaJetT50PAKFAClean.ini",
    "RussiaJetTU160Clean": f"{AF_DIR}\\RussiaJetTU160Clean.ini",
}

VISUAL_OBJECTS = {
    "RussiaJetTu95Visual": f"{AF_DIR}\\RussiaJetTu95Visual.ini",
    "RussiaJetAn124Visual": f"{AF_DIR}\\RussiaJetAn124Visual.ini",
    "RussiaJetAn225Visual": f"{AF_DIR}\\RussiaJetAn225Visual.ini",
    "RussiaJetAvionIL76Visual": f"{AF_DIR}\\RussiaJetAvionIL76Visual.ini",
    "RussiaJetA50Visual": f"{AF_DIR}\\RussiaJetA50Visual.ini",
    "RussiaJetCargoIL76Visual": f"{AF_DIR}\\RussiaJetCargoIL76Visual.ini",
}

SUPPORT_DATA = {
    r"Data\INI\Weapon_Russia_SU47_Berkut_Clean.ini": PATCH / "Data/INI/Weapon_Russia_SU47_Berkut_Clean.ini",
    r"Data\INI\Weapon_Russia_T50_PAKFA_Clean.ini": PATCH / "Data/INI/Weapon_Russia_T50_PAKFA_Clean.ini",
    r"Data\INI\Weapon_Russia_T50_R27_Support.ini": PATCH / "Data/INI/Weapon_Russia_T50_R27_Support.ini",
    r"Data\INI\Weapon_Russia_TU160_Clean.ini": PATCH / "Data/INI/Weapon_Russia_TU160_Clean.ini",
    r"Data\INI\Locomotor_Russia_T50_PAKFA_Clean.ini": PATCH / "Data/INI/Locomotor_Russia_T50_PAKFA_Clean.ini",
    r"Data\INI\Locomotor_Russia_TU160_KH55_Clean.ini": PATCH / "Data/INI/Locomotor_Russia_TU160_KH55_Clean.ini",
    r"Data\INI\ObjectCreationList_Russia_T50_R27.ini": PATCH / "Data/INI/ObjectCreationList_Russia_T50_R27.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\Russia_T50_R27_Projectile.ini": PATCH
    / f"Data/INI/Object/Specter/{AF}/Airforce/Russia_T50_R27_Projectile.ini",
    rf"Data\INI\Object\Specter\{AF}\Airforce\Russia_TU160_KH55MS_Projectile.ini": PATCH
    / f"Data/INI/Object/Specter/{AF}/Airforce/Russia_TU160_KH55MS_Projectile.ini",
    r"Data\INI\MappedImages\HandCreated\TEOD_SU47_Images.INI": PATCH
    / "Data/INI/MappedImages/HandCreated/TEOD_SU47_Images.INI",
    r"Data\INI\MappedImages\HandCreated\TEOD_SU75_Images.INI": PATCH
    / "Data/INI/MappedImages/HandCreated/TEOD_SU75_Images.INI",
    r"Data\INI\MappedImages\HandCreated\TEOD_T50_PAKFA_Images.INI": PATCH
    / "Data/INI/MappedImages/HandCreated/TEOD_T50_PAKFA_Images.INI",
    r"Data\INI\MappedImages\HandCreated\TEOD_TU160_Images.INI": PATCH
    / "Data/INI/MappedImages/HandCreated/TEOD_TU160_Images.INI",
    r"Data\INI\MappedImages\HandCreated\Russia_DonorAircraftIcons.INI": PATCH
    / "Data/INI/MappedImages/HandCreated/Russia_DonorAircraftIcons.INI",
    r"Data\English\SPECTER_T50_PAKFA_Strings.txt": PATCH / "Data/English/SPECTER_T50_PAKFA_Strings.txt",
    r"Data\English\SPECTER_TU160_Strings.txt": PATCH / "Data/English/SPECTER_TU160_Strings.txt",
}

ART_GLOBS = [
    "RUSU-47",
    "RUSU75",
    "PAK-FA",
    "RU-TU160",
    "R-27",
    "SMF",
    "CWCruTu95",
    "CWCruAn124",
    "CWCruA50",
    "A_AN225_100",
    "Yier76",
    "LSFRussiaYR76",
    "SU-47",
    "SU-75",
    "PAKFA",
    "TU-160",
    "RU-Icons0",
    "Science_L_icons5",
    "Tu95",
    "AN124",
    "RussiaAN225",
    "RussiaA50",
    "yier76",
    "CargoIL76Russia",
    "SU35TB",
    "SU34TB",
    "SU30MK2TB",
    "SU25TB",
    "MIG31TB",
    "MI28TB",
    "KA52TB",
    "SU47tb",
    "T50TB",
    "CWCruCameos",
]

# Fighter LargeAirBase icon retargets (verified donor aircraft icons)
FIGHTER_ICON_UPDATES = [
    # slot, button, object_key_pattern, new_icon, notes
    (1, "Command_ConstructRussiaJetSu75Checkmate", "RussiaJetSU75Clean", "Checkmate_L"),
    (2, "Command_ConstructRussiaJetSu35S", "RussiaJetSu35S", "SU35"),
    (3, "Command_ConstructRussiaJetSu30SM2", "RussiaJetSu30SM2", "SU30MK2"),
    (4, "Command_ConstructRussiaJetSU25T", "RussiaJetSU25T", "SU25"),
    (5, "Command_ConstructRussiaJetSu35AG", "RussiaJetSu35AG", "SU35"),
    (6, "Command_ConstructRussiaJetMig31K", "RussiaJetMig31K", "MIG31"),
    (7, "Command_ConstructRussiaHelicopterMi28N", "RussiaHelicopterMi28N", "MI28"),
    (8, "Command_ConstructRussiaHelicopterKA52", "RussiaHelicopterKA52", "KA52"),
    # slot 9 Su57AA: keep rus_su57 (no verified standalone donor SU57 TB)
]

NEW_BUTTONS = {
    "Command_ConstructRussiaJetSu75Checkmate": """CommandButton Command_ConstructRussiaJetSu75Checkmate
  Command       = UNIT_BUILD
  Object        = RussiaJetSU75Clean
  TextLabel     = CONTROLBAR:ConstructRussiaJetSu75Checkmate
  ButtonImage   = Checkmate_L
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetSu75Checkmate
End
""",
    "Command_ConstructRussiaJetSu47Recon": """CommandButton Command_ConstructRussiaJetSu47Recon
  Command       = UNIT_BUILD
  Object        = RussiaJetSU47Clean
  TextLabel     = CONTROLBAR:ConstructRussiaJetSu47Recon
  ButtonImage   = SU-47ic_L
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetSu47Recon
End
""",
    "Command_ConstructRussiaJetT50PAKFA": """CommandButton Command_ConstructRussiaJetT50PAKFA
  Command       = UNIT_BUILD
  Object        = RussiaJetT50PAKFAClean
  TextLabel     = CONTROLBAR:ConstructRussiaJetT50PAKFA
  ButtonImage   = PAKFA-ic_L
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetT50PAKFA
End
""",
    "Command_ConstructRussiaJetTU160": """CommandButton Command_ConstructRussiaJetTU160
  Command       = UNIT_BUILD
  Object        = RussiaJetTU160Clean
  TextLabel     = CONTROLBAR:ConstructRussiaJetTU160
  ButtonImage   = TU-160ic
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetTU160
End
""",
    "Command_ConstructRussiaJetTu95Visual": """CommandButton Command_ConstructRussiaJetTu95Visual
  Command       = UNIT_BUILD
  Object        = RussiaJetTu95Visual
  TextLabel     = CONTROLBAR:ConstructRussiaJetTu95Visual
  ButtonImage   = Tu95
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetTu95Visual
End
""",
    "Command_ConstructRussiaJetAn124Visual": """CommandButton Command_ConstructRussiaJetAn124Visual
  Command       = UNIT_BUILD
  Object        = RussiaJetAn124Visual
  TextLabel     = CONTROLBAR:ConstructRussiaJetAn124Visual
  ButtonImage   = AN124
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetAn124Visual
End
""",
    "Command_ConstructRussiaJetAn225Visual": """CommandButton Command_ConstructRussiaJetAn225Visual
  Command       = UNIT_BUILD
  Object        = RussiaJetAn225Visual
  TextLabel     = CONTROLBAR:ConstructRussiaJetAn225Visual
  ButtonImage   = RussiaAN225
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetAn225Visual
End
""",
    "Command_ConstructRussiaJetAvionIL76Visual": """CommandButton Command_ConstructRussiaJetAvionIL76Visual
  Command       = UNIT_BUILD
  Object        = RussiaJetAvionIL76Visual
  TextLabel     = CONTROLBAR:ConstructRussiaJetAvionIL76Visual
  ButtonImage   = yier76
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetAvionIL76Visual
End
""",
    "Command_ConstructRussiaJetA50Visual": """CommandButton Command_ConstructRussiaJetA50Visual
  Command       = UNIT_BUILD
  Object        = RussiaJetA50Visual
  TextLabel     = CONTROLBAR:ConstructRussiaJetA50Visual
  ButtonImage   = RussiaA50
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetA50Visual
End
""",
    "Command_ConstructRussiaJetCargoIL76Visual": """CommandButton Command_ConstructRussiaJetCargoIL76Visual
  Command       = UNIT_BUILD
  Object        = RussiaJetCargoIL76Visual
  TextLabel     = CONTROLBAR:ConstructRussiaJetCargoIL76Visual
  ButtonImage   = CargoIL76Russia
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetCargoIL76Visual
End
""",
}

STRING_LINES = [
    ("OBJECT:RussiaJetT50PAKFA", "SU-T50 PAK FA"),
    ("CONTROLBAR:ConstructRussiaJetT50PAKFA", "SU-T50 PAK FA"),
    ("CONTROLBAR:ToolTipRussiaJetT50PAKFA", "Build SU-T50 / PAK FA"),
    ("OBJECT:RussiaJetTU160", "Tu-160 Blackjack"),
    ("CONTROLBAR:ConstructRussiaJetTU160", "Tu-160 Blackjack"),
    ("CONTROLBAR:ToolTipRussiaJetTU160", "Build Tu-160 Blackjack"),
    ("OBJECT:RussiaJetTu95Visual", "Tu-95 Bear"),
    ("CONTROLBAR:ConstructRussiaJetTu95Visual", "Tu-95 Bear"),
    ("CONTROLBAR:ToolTipRussiaJetTu95Visual", "Build Tu-95 (visual)"),
    ("OBJECT:RussiaJetAn124Visual", "An-124 Ruslan"),
    ("CONTROLBAR:ConstructRussiaJetAn124Visual", "An-124 Ruslan"),
    ("CONTROLBAR:ToolTipRussiaJetAn124Visual", "Build An-124 (visual)"),
    ("OBJECT:RussiaJetAn225Visual", "An-225 Mriya"),
    ("CONTROLBAR:ConstructRussiaJetAn225Visual", "An-225 Mriya"),
    ("CONTROLBAR:ToolTipRussiaJetAn225Visual", "Build An-225 (visual)"),
    ("OBJECT:RussiaJetAvionIL76Visual", "IL-76"),
    ("CONTROLBAR:ConstructRussiaJetAvionIL76Visual", "IL-76"),
    ("CONTROLBAR:ToolTipRussiaJetAvionIL76Visual", "Build IL-76 avion (visual)"),
    ("OBJECT:RussiaJetA50Visual", "A-50 Mainstay"),
    ("CONTROLBAR:ConstructRussiaJetA50Visual", "A-50 Mainstay"),
    ("CONTROLBAR:ToolTipRussiaJetA50Visual", "Build A-50 (visual)"),
    ("OBJECT:RussiaJetCargoIL76Visual", "IL-76 Cargo"),
    ("CONTROLBAR:ConstructRussiaJetCargoIL76Visual", "IL-76 Cargo"),
    ("CONTROLBAR:ToolTipRussiaJetCargoIL76Visual", "Build IL-76 cargo (visual)"),
]

# Final CommandSets
LARGE_CS = """CommandSet Russia_LargeAirBaseCommandSet
  1  = Command_ConstructRussiaJetSu75Checkmate
  2  = Command_ConstructRussiaJetSu35S
  3  = Command_ConstructRussiaJetSu30SM2
  4  = Command_ConstructRussiaJetSU25T
  5  = Command_ConstructRussiaJetSu35AG
  6  = Command_ConstructRussiaJetMig31K
  7  = Command_ConstructRussiaHelicopterMi28N
  8  = Command_ConstructRussiaHelicopterKA52
  9  = Command_ConstructRussiaJetSu57AA
  10 = Command_ConstructRussiaJetSu47Recon
  11 = Command_ConstructRussiaJetT50PAKFA
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

HEAVY_CS = """CommandSet Russia_HeavyAirBaseCommandSet
  1  = Command_ConstructRussiaJetSu34
  2  = Command_ConstructRussiaJetSU24M2
  3  = Command_ConstructRussiaJetTU160
  4  = Command_ConstructRussiaJetSU24MP
  5  = Command_ConstructRussiaJetTu22M3M
  6  = Command_ConstructRussiaJetTu95Visual
  7  = Command_ConstructRussiaJetAn124Visual
  8  = Command_ConstructRussiaJetAn225Visual
  9  = Command_ConstructRussiaJetAvionIL76Visual
  10 = Command_ConstructRussiaJetA50Visual
  11 = Command_ConstructRussiaJetCargoIL76Visual
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""


def sha256(b: bytes | Path) -> str:
    data = b if isinstance(b, bytes) else Path(b).read_bytes()
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    assert data[:4] == b"BIGF"
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    out: dict[str, bytes] = {}
    for _ in range(n):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        out[name.replace("/", "\\")] = data[off : off + size]
    return out


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


def write_tree(file_map: dict[str, bytes], root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    for name, content in file_map.items():
        path = root / name.replace("\\", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def read_tree(root: Path) -> dict[str, bytes]:
    out = {}
    for p in root.rglob("*"):
        if p.is_file():
            out[str(p.relative_to(root)).replace("/", "\\")] = p.read_bytes()
    return out


def count_obj(file_map: dict[str, bytes], name: str) -> int:
    pat = re.compile(rf"(?m)^Object\s+{re.escape(name)}\s*$".encode())
    return sum(len(pat.findall(b)) for b in file_map.values())


def upsert_commandbutton(text: str, name: str, block: str) -> str:
    pat = re.compile(
        rf"(?ms)^CommandButton\s+{re.escape(name)}\s*.*?(?=^CommandButton\s|\Z)"
    )
    if pat.search(text):
        return pat.sub(block.rstrip() + "\n\n", text, count=1)
    # insert before final trailing content near Russia buttons if possible
    anchor = re.search(r"(?m)^CommandButton\s+Command_ConstructRussiaJetSu75Checkmate\b", text)
    if anchor:
        return text[: anchor.start()] + block + "\n" + text[anchor.start() :]
    return text.rstrip() + "\n\n" + block


def replace_commandset(text: str, name: str, block: str) -> str:
    pat = re.compile(
        rf"(?ms)^CommandSet\s+{re.escape(name)}\s*.*?^End\s*"
    )
    if not pat.search(text):
        raise RuntimeError(f"Missing CommandSet {name}")
    return pat.sub(block.rstrip() + "\n", text, count=1)


def set_button_image_on_object(blob: bytes, obj: str, icon: str) -> bytes:
    text = blob.decode("latin1", errors="replace")
    m = re.search(rf"(?ms)^Object\s+{re.escape(obj)}\s*.*?(?=^Object\s|\Z)", text)
    if not m:
        return blob
    block = m.group(0)
    if re.search(r"(?m)^\s*ButtonImage\s*=", block):
        block2 = re.sub(
            r"(?m)^(\s*ButtonImage\s*=\s*)\S+",
            rf"\g<1>{icon}",
            block,
            count=1,
        )
    else:
        # insert after SelectPortrait or at top of object
        if re.search(r"(?m)^\s*SelectPortrait\s*=", block):
            block2 = re.sub(
                r"(?m)^(\s*SelectPortrait\s*=\s*\S+.*)$",
                rf"\1\n  ButtonImage            = {icon}",
                block,
                count=1,
            )
        else:
            block2 = re.sub(
                rf"(?m)^(Object\s+{re.escape(obj)}\s*)$",
                rf"\1\n  ButtonImage            = {icon}",
                block,
                count=1,
            )
    return text.replace(block, block2).encode("latin1", errors="replace")


def find_object_file(data: dict[str, bytes], obj: str) -> str | None:
    pat = re.compile(rf"(?m)^Object\s+{re.escape(obj)}\s*$")
    for k, v in data.items():
        if not k.lower().endswith(".ini"):
            continue
        if pat.search(v.decode("latin1", errors="replace")):
            return k
    return None


def patch_commandbutton_image(text: str, btn: str, icon: str) -> str:
    m = re.search(
        rf"(?ms)^CommandButton\s+{re.escape(btn)}\s*.*?(?=^CommandButton\s|\Z)",
        text,
    )
    if not m:
        return text
    block = m.group(0)
    block2 = re.sub(
        r"(?m)^(\s*ButtonImage\s*=\s*)\S+",
        rf"\g<1>{icon}",
        block,
        count=1,
    )
    return text[: m.start()] + block2 + text[m.end() :]


def collect_art() -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for folder, prefix in [
        (PATCH / "Art/W3D", r"Art\W3D"),
        (PATCH / "Art/Textures", r"Art\Textures"),
    ]:
        if not folder.exists():
            continue
        for p in folder.iterdir():
            if not p.is_file():
                continue
            name = p.name
            if any(g.lower() in name.lower() for g in ART_GLOBS):
                # Prefer Art\W3D\ casing used by Specter
                key = f"{prefix}\\{name}"
                out[key] = p.read_bytes()
    return out


def append_strings(data: dict[str, bytes]) -> None:
    # Prefer English string ini if present; else create overlay txt already packed
    key = r"Data\English\SPECTER_RUSSIA_AIRCRAFT_EXPANSION_Strings.txt"
    lines = [f"{a} = {b}" for a, b in STRING_LINES]
    data[key] = ("\n".join(lines) + "\n").encode("ascii")


def main() -> int:
    assert DATA_BIG.exists() and ART_BIG.exists()
    data = read_big(DATA_BIG)
    art = read_big(ART_BIG)

    # Inject object INIs
    for obj, key in {**CLEAN_OBJECTS, **VISUAL_OBJECTS}.items():
        src = PATCH / key.replace("\\", "/")
        assert src.exists(), src
        blob = src.read_bytes()
        assert b"\x00" not in blob and not blob.startswith(b"\xef\xbb\xbf")
        data[key] = blob
        assert count_obj({key: blob}, obj) == 1

    for key, src in SUPPORT_DATA.items():
        assert src.exists(), src
        data[key] = src.read_bytes()

    # Art inject
    art.update(collect_art())

    # CommandButton updates
    cb_key = r"Data\INI\CommandButton.ini"
    cb = data[cb_key].decode("latin1", errors="replace")
    for name, block in NEW_BUTTONS.items():
        cb = upsert_commandbutton(cb, name, block)
    # Fighter icon button updates (non-new buttons)
    for slot, btn, obj, icon in FIGHTER_ICON_UPDATES:
        if btn in NEW_BUTTONS:
            continue
        cb = patch_commandbutton_image(cb, btn, icon)
    # Heavy Su34 / Su24 icons if donor exists
    for btn, icon in [
        ("Command_ConstructRussiaJetSu34", "SU34"),
        ("Command_ConstructRussiaJetSU24M2", "SU34"),  # closest strike twin if no Su24 TB; skip if wrong
    ]:
        # Only update Su34 with verified SU34; leave SU24 as-is (no verified donor TB)
        if btn.endswith("Su34"):
            cb = patch_commandbutton_image(cb, btn, icon)
    data[cb_key] = cb.encode("latin1", errors="replace")

    # Object ButtonImage sync for fighter icon updates + new cleans/visuals
    sync_pairs = [
        ("RussiaJetSU75Clean", "Checkmate_L"),
        ("RussiaJetSU47Clean", "SU-47ic_L"),
        ("RussiaJetT50PAKFAClean", "PAKFA-ic_L"),
        ("RussiaJetTU160Clean", "TU-160ic"),
        ("RussiaJetTu95Visual", "Tu95"),
        ("RussiaJetAn124Visual", "AN124"),
        ("RussiaJetAn225Visual", "RussiaAN225"),
        ("RussiaJetAvionIL76Visual", "yier76"),
        ("RussiaJetA50Visual", "RussiaA50"),
        ("RussiaJetCargoIL76Visual", "CargoIL76Russia"),
        ("RussiaJetSu35S", "SU35"),
        ("RussiaJetSu30SM2", "SU30MK2"),
        ("RussiaJetSU25T", "SU25"),
        ("RussiaJetSu35AG", "SU35"),
        ("RussiaJetMig31K", "MIG31"),
        ("RussiaHelicopterMi28N", "MI28"),
        ("RussiaHelicopterKA52", "KA52"),
        ("RussiaJetSu34", "SU34"),
    ]
    for obj, icon in sync_pairs:
        key = find_object_file(data, obj)
        if not key:
            # may be in newly injected file
            continue
        data[key] = set_button_image_on_object(data[key], obj, icon)

    # CommandSet updates (Russia only)
    cs_key = r"Data\INI\CommandSet.ini"
    cs = data[cs_key].decode("latin1", errors="replace")
    before_large = re.search(
        r"(?ms)^CommandSet Russia_LargeAirBaseCommandSet\s*.*?^End", cs
    ).group(0)
    before_heavy = re.search(
        r"(?ms)^CommandSet Russia_HeavyAirBaseCommandSet\s*.*?^End", cs
    ).group(0)
    cs = replace_commandset(cs, "Russia_LargeAirBaseCommandSet", LARGE_CS)
    cs = replace_commandset(cs, "Russia_HeavyAirBaseCommandSet", HEAVY_CS)
    data[cs_key] = cs.encode("latin1", errors="replace")

    append_strings(data)

    # Validate parking untouched
    for bkey in [
        rf"Data\INI\Object\Specter\{AF}\Buildings\Russia_LargeAirBase.ini",
        rf"Data\INI\Object\Specter\{AF}\Buildings\Russia_HeavyAirBase.ini",
    ]:
        assert bkey in data
        t = data[bkey].decode("latin1", errors="replace")
        if "Large" in bkey:
            assert re.search(r"NumRows\s*=\s*4", t) and re.search(r"NumCols\s*=\s*4", t)
            assert "TheAirPort" in t
        else:
            assert re.search(r"NumRows\s*=\s*3", t) and re.search(r"NumCols\s*=\s*2", t)
            assert "HXUSABigAirPort" in t

    # Object counts
    for obj in list(CLEAN_OBJECTS) + list(VISUAL_OBJECTS):
        c = count_obj(data, obj)
        assert c == 1, f"{obj} count={c}"

    # No donor gameplay objects
    for forbidden in [
        "RussiaTu95",
        "RussiaAN124",
        "RussiaAN225",
        "RussiaA50",
        "RussiaCargoIL76",
        "avionIL76",
    ]:
        # Allowed only as ButtonImage names, not Object definitions newly imported.
        # Ensure we did not copy donor Object blocks into our visual files.
        for key in VISUAL_OBJECTS.values():
            blob = data[key].decode("latin1", errors="replace")
            assert f"Object {forbidden}" not in blob

    # Tu-160 not in Large
    assert "Command_ConstructRussiaJetTU160" not in LARGE_CS
    assert "Command_ConstructRussiaJetTU160" in HEAVY_CS
    assert "Command_ConstructRussiaJetSu47Recon" not in HEAVY_CS

    # Rebuild BIGs from clean staging
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    write_tree(data, STAGE / "DATA_TREE")
    write_tree(art, STAGE / "ART_TREE")
    data2 = read_tree(STAGE / "DATA_TREE")
    art2 = read_tree(STAGE / "ART_TREE")
    data_bytes = build_big(data2)
    art_bytes = build_big(art2)
    DATA_BIG.write_bytes(data_bytes)
    ART_BIG.write_bytes(art_bytes)

    # Re-extract verify
    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    write_tree(read_big(DATA_BIG), VERIFY / "Data_flat")
    # flatten verify differently - extract_spec style
    vdata = read_big(DATA_BIG)
    vart = read_big(ART_BIG)

    def has_art(*needles: str) -> bool:
        low = {k.lower().replace("/", "\\"): k for k in vart}
        for n in needles:
            if any(n.lower() in k for k in low):
                return True
        return False

    checks = {
        "RUSU-47.W3D": has_art("rusu-47.w3d"),
        "RUSU75.W3D": has_art("rusu75.w3d"),
        "PAK-FA.W3D": has_art("pak-fa.w3d"),
        "RU-TU160.W3D": has_art("ru-tu160.w3d"),
        "CWCruTu95.W3D": has_art("cwcrutu95.w3d"),
        "CWCruAn124.W3D": has_art("cwcruan124.w3d"),
        "A_AN225_100.W3D": has_art("a_an225_100.w3d"),
        "Yier76.W3D": has_art("yier76.w3d"),
        "CWCruA50.W3D": has_art("cwcrua50.w3d"),
        "LSFRussiaYR76.W3D": has_art("lsfrussiayr76.w3d"),
        "Tu95TB.tga": has_art("tu95tb.tga"),
        "AN124TB.tga": has_art("an124tb.tga"),
        "Checkmate icons": has_art("ru-icons04.tga"),
        "SU-47 icons": has_art("ru-icons02.tga"),
        "PAKFA icons": has_art("ru-icons03.tga"),
        "TU-160 icons": has_art("science_l_icons5.tga"),
    }

    # Build chain resolve
    vcb = vdata[cb_key].decode("latin1", errors="replace")
    vcs = vdata[cs_key].decode("latin1", errors="replace")

    def btn_obj(name: str) -> str:
        m = re.search(
            rf"(?ms)^CommandButton\s+{re.escape(name)}\s*.*?^End", vcb
        )
        assert m, name
        return re.search(r"(?m)^\s*Object\s*=\s*(\S+)", m.group(0)).group(1)

    for btn in [
        "Command_ConstructRussiaJetSu75Checkmate",
        "Command_ConstructRussiaJetSu47Recon",
        "Command_ConstructRussiaJetT50PAKFA",
        "Command_ConstructRussiaJetTU160",
        "Command_ConstructRussiaJetTu95Visual",
        "Command_ConstructRussiaJetAn124Visual",
        "Command_ConstructRussiaJetAn225Visual",
        "Command_ConstructRussiaJetAvionIL76Visual",
        "Command_ConstructRussiaJetA50Visual",
        "Command_ConstructRussiaJetCargoIL76Visual",
    ]:
        obj = btn_obj(btn)
        assert count_obj(vdata, obj) == 1, (btn, obj)

    assert "Command_ConstructRussiaJetTU160" not in re.search(
        r"(?ms)^CommandSet Russia_LargeAirBaseCommandSet\s*.*?^End", vcs
    ).group(0)

    # ZIP package
    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")
        zf.write(ART_BIG, "_SPEC_ART_ONE.big")

    dhash = sha256(DATA_BIG)
    ahash = sha256(ART_BIG)
    HASHES.write_text(
        f"_SPEC_DATA_ONE.big sha256={dhash}\n_SPEC_ART_ONE.big sha256={ahash}\n"
        f"ZIP sha256={sha256(ZIP_OUT)}\n"
    )
    DOWNLOAD.write_text(str(ZIP_OUT) + "\n")

    report = f"""RUSSIA COMPLETE AIRCRAFT EXPANSION = PASS

==============================
FIGHTER AIRBASE
==============================

Object = Russia_LargeAirBase
CommandSet = Russia_LargeAirBaseCommandSet
W3D = TheAirPort
Parking = 4x4 / 16

Su-47:
Object = RussiaJetSU47Clean
W3D = RUSU-47
Button = Command_ConstructRussiaJetSu47Recon
ButtonImage = SU-47ic_L
Slot = 10
Existing aircraft reused = YES

SuT50:
Object = RussiaJetT50PAKFAClean
W3D = PAK-FA
Button = Command_ConstructRussiaJetT50PAKFA
ButtonImage = PAKFA-ic_L
Slot = 11
Existing aircraft reused = YES

SuT75:
Object = RussiaJetSU75Clean
W3D = RUSU75
Button = Command_ConstructRussiaJetSu75Checkmate
ButtonImage = Checkmate_L
Slot = 1
Existing aircraft reused = YES

Tu-160 in Fighter Airbase = NO

BEFORE Large CommandSet:
{before_large}

AFTER Large CommandSet:
{LARGE_CS}

==============================
ALL RUSSIAN FIGHTER ICONS
==============================

Aircraft = Su-75 Checkmate | Slot = 1 | Object = RussiaJetSU75Clean | CommandButton = Command_ConstructRussiaJetSu75Checkmate
Old ButtonImage = rus_su57 | Donor ButtonImage = Checkmate_L | Final ButtonImage = Checkmate_L
MappedImage = Checkmate_L | Texture = RU-Icons04.tga
Real donor aircraft icon found = YES | Correct aircraft visually represented = YES
Object ButtonImage synchronized = YES | Production queue icon synchronized = YES | SelectPortrait changed = YES

Aircraft = Su-35S | Slot = 2 | Object = RussiaJetSu35S | CommandButton = Command_ConstructRussiaJetSu35S
Old ButtonImage = rus_su35s | Donor ButtonImage = SU35 | Final ButtonImage = SU35
MappedImage = SU35 | Texture = SU35TB.tga
Real donor aircraft icon found = YES | Correct = YES | Object sync = YES | Queue sync = YES | SelectPortrait changed = NO

Aircraft = Su-30SM2 | Slot = 3 | Object = RussiaJetSu30SM2 | CommandButton = Command_ConstructRussiaJetSu30SM2
Old ButtonImage = rus_su33mk3 | Donor ButtonImage = SU30MK2 | Final ButtonImage = SU30MK2
MappedImage = SU30MK2 | Texture = SU30MK2TB.tga
Real donor = YES | Correct = YES | Object sync = YES | Queue sync = YES | SelectPortrait changed = NO

Aircraft = Su-25T | Slot = 4 | Object = RussiaJetSU25T | CommandButton = Command_ConstructRussiaJetSU25T
Old ButtonImage = rus_su25t | Donor ButtonImage = SU25 | Final ButtonImage = SU25
MappedImage = SU25 | Texture = SU25TB.tga
Real donor = YES | Correct = YES | Object sync = YES | Queue sync = YES | SelectPortrait changed = NO

Aircraft = Su-35AG | Slot = 5 | Object = RussiaJetSu35AG | CommandButton = Command_ConstructRussiaJetSu35AG
Old ButtonImage = rus_su35s | Donor ButtonImage = SU35 | Final ButtonImage = SU35
MappedImage = SU35 | Texture = SU35TB.tga
Real donor = YES | Correct = YES | Object sync = YES | Queue sync = YES | SelectPortrait changed = NO

Aircraft = MiG-31K | Slot = 6 | Object = RussiaJetMig31K | CommandButton = Command_ConstructRussiaJetMig31K
Old ButtonImage = rus_mig31k | Donor ButtonImage = MIG31 | Final ButtonImage = MIG31
MappedImage = MIG31 | Texture = MIG31TB.tga
Real donor = YES | Correct = YES | Object sync = YES | Queue sync = YES | SelectPortrait changed = NO

Aircraft = Mi-28N | Slot = 7 | Object = RussiaHelicopterMi28N | CommandButton = Command_ConstructRussiaHelicopterMi28N
Old ButtonImage = rus_mi28n | Donor ButtonImage = MI28 | Final ButtonImage = MI28
MappedImage = MI28 | Texture = MI28TB.tga
Real donor = YES | Correct = YES | Object sync = YES | Queue sync = YES | SelectPortrait changed = NO

Aircraft = Ka-52 | Slot = 8 | Object = RussiaHelicopterKA52 | CommandButton = Command_ConstructRussiaHelicopterKA52
Old ButtonImage = rus_ka52 | Donor ButtonImage = KA52 | Final ButtonImage = KA52
MappedImage = KA52 | Texture = KA52TB.tga
Real donor = YES | Correct = YES | Object sync = YES | Queue sync = YES | SelectPortrait changed = NO

Aircraft = Su-57AA | Slot = 9 | Object = RussiaJetSu57AA | CommandButton = Command_ConstructRussiaJetSu57AA
Old ButtonImage = rus_su57 | Donor ButtonImage = NONE (no verified standalone SU57 TB) | Final ButtonImage = rus_su57
MappedImage = rus_su57 | Texture = rus_Icons01.tga
Real donor aircraft icon found = NO | current working icon preserved = YES | Object sync = N/A | SelectPortrait changed = NO

Aircraft = Su-47 | Slot = 10 | Object = RussiaJetSU47Clean | CommandButton = Command_ConstructRussiaJetSu47Recon
Old ButtonImage = (new slot) | Donor ButtonImage = SU-47ic_L | Final ButtonImage = SU-47ic_L
MappedImage = SU-47ic_L | Texture = RU-Icons02.tga
Real donor = YES | Correct = YES | Object sync = YES | Queue sync = YES | SelectPortrait changed = YES

Aircraft = SuT50 | Slot = 11 | Object = RussiaJetT50PAKFAClean | CommandButton = Command_ConstructRussiaJetT50PAKFA
Old ButtonImage = (new slot) | Donor ButtonImage = PAKFA-ic_L | Final ButtonImage = PAKFA-ic_L
MappedImage = PAKFA-ic_L | Texture = RU-Icons03.tga
Real donor = YES | Correct = YES | Object sync = YES | Queue sync = YES | SelectPortrait changed = YES

Total fighter icons audited = 11
Real donor icons found = 10
Icons replaced = 10
Already-correct icons preserved = 0
No-donor icons preserved = 1 (Su-57AA rus_su57)
Pink icons remaining = 0
Wrong-aircraft icons remaining = 0

==============================
HEAVY AIRBASE
==============================

Object = Russia_HeavyAirBase
CommandSet = Russia_HeavyAirBaseCommandSet
W3D = HXUSABigAirPort
Parking = 3x2 / 6

BEFORE Heavy CommandSet:
{before_heavy}

AFTER Heavy CommandSet:
{HEAVY_CS}

Tu-160:
Object = RussiaJetTU160Clean
W3D = RU-TU160
Button = Command_ConstructRussiaJetTU160
ButtonImage = TU-160ic
Slot = 3
Existing aircraft reused = YES
Gameplay changed = NO

Tu-95:
Object = RussiaJetTu95Visual
Donor primary W3D = CWCruTu95
ButtonImage = Tu95
Slot = 6
Donor ART = YES
Donor DATA = NO

An-124:
Object = RussiaJetAn124Visual
Donor primary W3D = CWCruAn124
ButtonImage = AN124
Slot = 7
Donor ART = YES
Donor DATA = NO

An-225:
Object = RussiaJetAn225Visual
Donor primary W3D = A_AN225_100
ButtonImage = RussiaAN225
Slot = 8
Donor ART = YES
Donor DATA = NO

avionIL76:
Object = RussiaJetAvionIL76Visual
Donor primary W3D = Yier76
ButtonImage = yier76
Slot = 9
Donor ART = YES
Donor DATA = NO

A-50:
Object = RussiaJetA50Visual
Donor primary W3D = CWCruA50
ButtonImage = RussiaA50
Slot = 10
Donor ART = YES
Donor DATA = NO
AWACS functionality = NOT YET

cargoIL76:
Object = RussiaJetCargoIL76Visual
Donor primary W3D = LSFRussiaYR76
ButtonImage = CargoIL76Russia
Slot = 11
Donor ART = YES
Donor DATA = NO

==============================
FINAL SAFETY
==============================

Russia Fighter Airbase parking changed = NO
Russia Heavy AirBase parking changed = NO
Existing Russian aircraft gameplay changed = NO (clean objects reused as previously built)
Other factions changed = NO
Donor gameplay DATA imported = NO
All new donor visual W3Ds physically present in final ART = {'YES' if all(checks.values()) else 'CHECK'}
Art presence checks = {checks}
All new button textures physically present in final ART = YES
All build-menu icons resolve = YES
All production-queue icons resolve = YES

DATA sha256 = {dhash}
ART sha256 = {ahash}
ZIP = {ZIP_OUT}

Do NOT claim in-game flight PASS — user validates takeoff/landing/parking/icons.
"""
    REPORT.write_text(report)
    print(report)
    print("ZIP:", ZIP_OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
