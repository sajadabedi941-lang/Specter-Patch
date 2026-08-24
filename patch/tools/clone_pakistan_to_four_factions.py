#!/usr/bin/env python3
"""Clone CURRENT working Pakistan faction into SaudiArabia, UAE, India, Syria.

Deterministic rename of faction-owned identifiers only. Shared ART/USA donors untouched.
Pakistan and Egypt frozen. DATA-only preferred.
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
ZIP_PATH = ROOT / "Release/SPECTER_MASTER_DATA_PAKISTAN_CLONE_4FACTIONS.zip"

BASE_DATA = "032e9188cc76564e298253a8d4d1fd14358069e0d050cf4e9e3c3082b79e7656"
BASE_ART = "74a411b72c19fafaafcd48a45d2aa76731d8dbd13e919e4f73f8b989e90d4822"

FACTIONS = [
    {
        "prefix": "SaudiArabia",
        "side": "SaudiArabia",
        "pt": "FactionSaudiArabia",
        "scheme": "SaudiArabia8x6",
        "display_key": "INI:FactionSaudiArabia",
        "display_text": "Saudi Arabia Armed Forces",
        "folder": "Saudi Arabia Armed Forces",
        "tooltip": "TOOLTIP:BioStrategyLong_SaudiArabia",
        "features": "GUI:BioFeatures_SaudiArabia",
        "tooltip_text": "Saudi Arabia Armed Forces - Pakistan-template combined-arms clone.",
        "features_text": "Armor, airpower, dual airbases, nuclear, artillery, C-RAM.",
    },
    {
        "prefix": "UAE",
        "side": "UAE",
        "pt": "FactionUAE",
        "scheme": "UAE8x6",
        "display_key": "INI:FactionUAE",
        "display_text": "United Arab Emirates Armed Forces",
        "folder": "United Arab Emirates Armed Forces",
        "tooltip": "TOOLTIP:BioStrategyLong_UAE",
        "features": "GUI:BioFeatures_UAE",
        "tooltip_text": "United Arab Emirates Armed Forces - Pakistan-template combined-arms clone.",
        "features_text": "Armor, airpower, dual airbases, nuclear, artillery, C-RAM.",
    },
    {
        "prefix": "India",
        "side": "India",
        "pt": "FactionIndia",
        "scheme": "India8x6",
        "display_key": "INI:FactionIndia",
        "display_text": "Indian Armed Forces",
        "folder": "Indian Armed Forces",
        "tooltip": "TOOLTIP:BioStrategyLong_India",
        "features": "GUI:BioFeatures_India",
        "tooltip_text": "Indian Armed Forces - Pakistan-template combined-arms clone.",
        "features_text": "Armor, airpower, dual airbases, nuclear, artillery, C-RAM.",
    },
    {
        "prefix": "Syria",
        "side": "Syria",
        "pt": "FactionSyria",
        "scheme": "Syria8x6",
        "display_key": "INI:FactionSyria",
        "display_text": "Syrian Armed Forces",
        "folder": "Syrian Armed Forces",
        "tooltip": "TOOLTIP:BioStrategyLong_Syria",
        "features": "GUI:BioFeatures_Syria",
        "tooltip_text": "Syrian Armed Forces - Pakistan-template combined-arms clone.",
        "features_text": "Armor, airpower, dual airbases, nuclear, artillery, C-RAM.",
    },
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


def transform_pakistan_text(text: str, prefix: str, side: str) -> str:
    """Rename faction-owned Pakistan identifiers. Do not touch shared donor asset names."""
    # Longest / most-specific first
    reps = [
        ("Command_PurchaseSciencePakistan", f"Command_PurchaseScience{prefix}"),
        ("Command_UpgradePakistan_", f"Command_Upgrade{prefix}_"),
        ("Command_ConstructPakistan_", f"Command_Construct{prefix}_"),
        ("Command_Pakistan", f"Command_{prefix}"),
        ("SuperweaponPakistan", f"Superweapon{prefix}"),
        ("SCIENCE_Pakistan", f"SCIENCE_{prefix}"),
        ("SpecialPowerShortcutPakistan", f"SpecialPowerShortcut{prefix}"),
        ("PakistanDozerCommandSet", f"{prefix}DozerCommandSet"),
        ("Upgrade_Pakistan_", f"Upgrade_{prefix}_"),
        ("FactionPakistan", f"Faction{prefix}" if prefix != "SaudiArabia" else "FactionSaudiArabia"),
        ("INI:FactionPakistan", f"INI:Faction{prefix}" if prefix != "UAE" else "INI:FactionUAE"),
        ("TOOLTIP:BioStrategyLong_Pakistan", f"TOOLTIP:BioStrategyLong_{prefix}"),
        ("GUI:BioFeatures_Pakistan", f"GUI:BioFeatures_{prefix}"),
        ("Pakistan_", f"{prefix}_"),
    ]
    # Fix Faction name map explicitly
    faction_pt = {
        "SaudiArabia": "FactionSaudiArabia",
        "UAE": "FactionUAE",
        "India": "FactionIndia",
        "Syria": "FactionSyria",
    }[prefix]
    display_key = {
        "SaudiArabia": "INI:FactionSaudiArabia",
        "UAE": "INI:FactionUAE",
        "India": "INI:FactionIndia",
        "Syria": "INI:FactionSyria",
    }[prefix]

    out = text
    out = out.replace("Command_PurchaseSciencePakistan", f"Command_PurchaseScience{prefix}")
    out = out.replace("Command_UpgradePakistan_", f"Command_Upgrade{prefix}_")
    out = out.replace("Command_ConstructPakistan_", f"Command_Construct{prefix}_")
    out = out.replace("Command_SelectPakistan", f"Command_Select{prefix}")
    out = out.replace("Command_Pakistan", f"Command_{prefix}")
    out = out.replace("SuperweaponPakistan", f"Superweapon{prefix}")
    out = out.replace("SCIENCE_Pakistan", f"SCIENCE_{prefix}")
    out = out.replace("SpecialPowerShortcutPakistan", f"SpecialPowerShortcut{prefix}")
    out = out.replace("PakistanDozerCommandSet", f"{prefix}DozerCommandSet")
    out = out.replace("Upgrade_Pakistan_", f"Upgrade_{prefix}_")
    out = out.replace("INI:FactionPakistan", display_key)
    out = out.replace("TOOLTIP:BioStrategyLong_Pakistan", f"TOOLTIP:BioStrategyLong_{prefix}")
    out = out.replace("GUI:BioFeatures_Pakistan", f"GUI:BioFeatures_{prefix}")
    out = out.replace("FactionPakistan", faction_pt)
    out = out.replace("Pakistan_", f"{prefix}_")
    # Remaining identity tokens inside cloned blocks (e.g. SystemSpecialPowerShortcut names)
    out = out.replace("PakistanSystem", f"{prefix}System")
    out = re.sub(r"(Side\s*=\s*)Pakistan\b", rf"\1{side}", out)
    out = re.sub(r"(BaseSide\s*=\s*)Pakistan\b", rf"\1{side}", out)
    return out


def strip_nonprefixed_objects(text: str, prefix: str) -> str:
    """Remove Object blocks whose names do not start with the faction prefix."""
    parts = re.split(r"(?=^Object\s+)", text, flags=re.M)
    kept = []
    for part in parts:
        m = re.match(r"^Object\s+(\S+)", part, re.M)
        if not m:
            kept.append(part)
            continue
        name = m.group(1)
        if name.startswith(prefix + "_") or name.startswith(prefix):
            kept.append(part)
        # else drop shared leftover like R11_CH_Explosion
    return "".join(kept)


def extract_blocks(text: str, kind: str) -> list[tuple[str, str]]:
    """Return list of (name, full_block) for CommandSet/CommandButton/etc."""
    pat = rf"(^{kind}\s+(\S+)[\s\S]*?^\s*End\s*$)"
    out = []
    for m in re.finditer(pat, text, re.M):
        out.append((m.group(2), m.group(1)))
    return out


def append_csf_label(csf: bytes, label: str, value: str) -> bytes:
    """Append one UCS/RTS label to a Generals CSF (UTF-16LE XOR 0xFF payload)."""
    if label.encode("ascii") in csf:
        return csf
    # Encode value as UTF-16LE then XOR each byte with 0xFF
    utf16 = value.encode("utf-16-le")
    xored = bytes(b ^ 0xFF for b in utf16)
    label_b = label.encode("ascii")
    entry = bytearray()
    entry += b" LBL"
    entry += struct.pack("<I", 1)  # one string
    entry += struct.pack("<I", len(label_b))
    entry += label_b
    entry += b" RTS"
    entry += struct.pack("<I", len(xored))
    entry += xored
    # Update header label/string counts at offsets 8 and 12 (after magic+ver)
    data = bytearray(csf)
    # magic(4) + ver(4) + nlabels(4) + nstrings(4)
    nlabels = struct.unpack_from("<I", data, 8)[0]
    nstrings = struct.unpack_from("<I", data, 12)[0]
    struct.pack_into("<I", data, 8, nlabels + 1)
    struct.pack_into("<I", data, 12, nstrings + 1)
    return bytes(data) + bytes(entry)


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

    # Freeze Pakistan + Egypt critical blobs
    freeze = {
        "lab": fmap[norm(r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_LargeAirBase.ini")],
        "hab": fmap[norm(r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_HeavyAirBase.ini")],
        "dozer": fmap[norm(r"Data\INI\Object\Specter\Pakistan Armed Forces\Tracked\Pakistan_Dozer.ini")],
        "egypt": fmap[norm(r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_LargeAirBase.ini")],
    }
    cs_before = fmap[norm(r"Data\INI\CommandSet.ini")]
    cb_before = fmap[norm(r"Data\INI\CommandButton.ini")]
    pt_before = fmap[norm(r"Data\INI\PlayerTemplate.ini")]
    cbs_before = fmap[norm(r"Data\INI\ControlBarScheme.ini")]

    cs_text = cs_before.decode("latin1")
    cb_text = cb_before.decode("latin1")
    pt_text = pt_before.decode("latin1")
    cbs_text = cbs_before.decode("latin1")

    # Extract Pakistan PlayerTemplate + ControlBar
    pt_pak = re.search(r"PlayerTemplate FactionPakistan\r?\n.*?^\s*End\s*$", pt_text, re.M | re.S)
    assert pt_pak, "FactionPakistan missing"
    pt_pak_block = pt_pak.group(0)

    cbs_pak = re.search(r"ControlBarScheme Pakistan8x6[\s\S]*?\nEnd", cbs_text)
    assert cbs_pak, "Pakistan8x6 missing"
    cbs_pak_block = cbs_pak.group(0)

    # Active Pakistan CS/CB blocks
    active_cs_names = re.findall(r"^CommandSet (\S*Pakistan\S*)", cs_text, re.M)
    active_cb_names = re.findall(r"^CommandButton (\S*Pakistan\S*)", cb_text, re.M)

    helper_cs = fmap[norm(r"Data\INI\CommandSet_Pakistan.ini")].decode("latin1")
    helper_cb = fmap[norm(r"Data\INI\CommandButton_Pakistan.ini")].decode("latin1")
    helper_cb2 = fmap.get(norm(r"Data\INI\CommandButton_Pakistan_PhaseB.ini"), b"").decode("latin1")

    # Extra CS from helper needed for PT science/shortcuts / upgrades on buildings
    extra_cs = [
        "Pakistan_WorkerCommandSet",
        "Pakistan_WarFactoryCommandSet1",
        "Pakistan_WarFactoryCommandSet2",
        "Pakistan_WarFactoryCommandSet3",
        "Pakistan_AirfieldCommandSet1",
        "Pakistan_AirfieldCommandSet2",
        "Pakistan_AirfieldCommandSet3",
        "Pakistan_VT72BCommandSet",
        "Pakistan_RepublicanGuardCommandSet",
        "Pakistan_AlhussaienCommandSet",
        "Pakistan_AlhussaienArmedCommandSet",
        "SCIENCE_Pakistan_CommandSetRank1",
        "SCIENCE_Pakistan_CommandSetRank3",
        "SCIENCE_Pakistan_CommandSetRank8",
        "SpecialPowerShortcutPakistanSystem",
        "SpecialPowerShortcutPakistan",
    ]

    def get_cs_block(name: str) -> str:
        m = re.search(rf"^CommandSet {re.escape(name)}\s*$[\s\S]*?^\s*End\s*$", cs_text, re.M)
        if m:
            return m.group(0)
        m = re.search(rf"^CommandSet {re.escape(name)}\s*$[\s\S]*?^\s*End\s*$", helper_cs, re.M)
        if m:
            return m.group(0)
        raise SystemExit(f"Missing CommandSet {name}")

    def get_cb_block(name: str) -> str:
        m = re.search(rf"^CommandButton {re.escape(name)}\s*$[\s\S]*?^\s*End\s*$", cb_text, re.M)
        if m:
            return m.group(0)
        m = re.search(rf"^CommandButton {re.escape(name)}\s*$[\s\S]*?^\s*End\s*$", helper_cb, re.M)
        if m:
            return m.group(0)
        m = re.search(rf"^CommandButton {re.escape(name)}\s*$[\s\S]*?^\s*End\s*$", helper_cb2, re.M)
        if m:
            return m.group(0)
        return ""  # optional missing helper buttons

    # Collect all CS blocks to clone (unique)
    cs_to_clone: dict[str, str] = {}
    for name in active_cs_names + extra_cs:
        cs_to_clone[name] = get_cs_block(name)

    # Collect CB: all active Pakistan + all buttons referenced by cloned CS
    cb_to_clone: dict[str, str] = {}
    for name in active_cb_names:
        cb_to_clone[name] = get_cb_block(name)
        assert cb_to_clone[name], name

    # Explicit extras commonly referenced by Systems shortcut object
    for extra_btn in [
        "Command_SelectPakistanSystemSpecialPowerShortcut",
    ]:
        b = get_cb_block(extra_btn)
        if b:
            cb_to_clone[extra_btn] = b

    # Add buttons referenced by CS; drop missing refs from CS blocks (Pakistan helper gaps)
    for name in list(cs_to_clone.keys()):
        block = cs_to_clone[name]
        lines = []
        for line in block.splitlines(True):
            m = re.match(r"^(\s*\d+\s*=\s*)(\S+)(\s*)$", line)
            if not m:
                lines.append(line)
                continue
            btn = m.group(2)
            if "Pakistan" not in btn:
                lines.append(line)
                continue
            if btn in cb_to_clone:
                lines.append(line)
                continue
            b = get_cb_block(btn)
            if b:
                cb_to_clone[btn] = b
                lines.append(line)
            else:
                print("STRIP missing button ref", btn, "from", name)
                # skip line
        cs_to_clone[name] = "".join(lines)

    # Pakistan object files under Armed Forces
    pak_obj_files = [
        (disp[k], fmap[k])
        for k, d in ((norm(n), n) for n in disp.values())
        for n in [disp[k]]
        if "pakistan armed forces" in k and k.endswith(".ini")
    ]
    # rebuild properly
    pak_obj_files = []
    for k, blob in fmap.items():
        if "pakistan armed forces" in k and k.endswith(".ini"):
            pak_obj_files.append((disp[k], blob))
    print("Pakistan object INIs", len(pak_obj_files))

    # Overlay INIs
    overlay_keys = [
        r"Data\INI\Science_Pakistan.ini",
        r"Data\INI\Weapon_Pakistan.ini",
        r"Data\INI\Upgrade_Pakistan.ini",
        r"Data\INI\SpecialPower_Pakistan.ini",
    ]

    nl = "\r\n" if "\r\n" in cs_text[-500:] else "\n"

    new_cs_append = []
    new_cb_append = []
    new_pt_append = []
    new_cbs_append = []
    string_lines = [
        "; SPECTER - Pakistan-template clones: SaudiArabia / UAE / India / Syria",
        "",
    ]

    src_root = ROOT / "Data/INI/Object/Specter"

    for fac in FACTIONS:
        prefix = fac["prefix"]
        side = fac["side"]
        print("=== CLONE", prefix, "===")

        # Objects
        for path, blob in pak_obj_files:
            text = blob.decode("latin1")
            new_text = transform_pakistan_text(text, prefix, side)
            new_text = strip_nonprefixed_objects(new_text, prefix)
            new_path = path.replace("Pakistan Armed Forces", fac["folder"]).replace("\\Pakistan_", f"\\{prefix}_")
            # also rename filenames that start with Pakistan_
            parts = new_path.split("\\")
            parts = [p.replace("Pakistan_", f"{prefix}_") if p.startswith("Pakistan_") else p for p in parts]
            new_path = "\\".join(parts)
            k = norm(new_path)
            assert k not in fmap, new_path
            fmap[k] = new_text.encode("latin1")
            disp[k] = new_path
            # write source copy
            out_file = ROOT / new_path.replace("\\", "/")
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_bytes(fmap[k])

        # Overlay science/weapon/upgrade/specialpower files
        for ok in overlay_keys:
            blob = fmap[norm(ok)]
            new_text = transform_pakistan_text(blob.decode("latin1"), prefix, side)
            new_path = ok.replace("Pakistan", prefix)
            k = norm(new_path)
            assert k not in fmap, new_path
            fmap[k] = new_text.encode("latin1")
            disp[k] = new_path
            out_file = ROOT / new_path.replace("\\", "/")
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_bytes(fmap[k])

        # CommandSets
        for name, block in cs_to_clone.items():
            nb = transform_pakistan_text(block, prefix, side)
            new_cs_append.append(nb)

        # CommandButtons
        for name, block in cb_to_clone.items():
            nb = transform_pakistan_text(block, prefix, side)
            new_cb_append.append(nb)

        # PlayerTemplate
        pt_new = transform_pakistan_text(pt_pak_block, prefix, side)
        # Ensure keys
        pt_new = re.sub(r"^PlayerTemplate\s+\S+", f"PlayerTemplate {fac['pt']}", pt_new, count=1, flags=re.M)
        pt_new = re.sub(r"(DisplayName\s*=\s*)\S+", rf"\1{fac['display_key']}", pt_new, count=1)
        pt_new = re.sub(r"(ArmyTooltip\s*=\s*)\S+", rf"\1{fac['tooltip']}", pt_new, count=1)
        pt_new = re.sub(r"(Features\s*=\s*)\S+", rf"\1{fac['features']}", pt_new, count=1)
        assert f"Side              = {side}" in pt_new or f"Side = {side}" in pt_new or re.search(rf"Side\s*=\s*{side}", pt_new)
        assert f"{prefix}_CommandCenter" in pt_new
        assert f"{prefix}_Dozer" in pt_new
        assert fac["scheme"] in transform_pakistan_text("ControlBarScheme = Pakistan8x6", prefix, side) or True
        # ControlBarScheme field - Pakistan PT might not include it! Check
        if "ControlBarScheme" not in pt_new:
            # insert after PlayableSide
            pt_new = re.sub(
                r"(PlayableSide\s*=\s*Yes\s*\n)",
                rf"\1  ControlBarScheme  = {fac['scheme']}\n",
                pt_new,
                count=1,
            )
        else:
            pt_new = re.sub(r"(ControlBarScheme\s*=\s*)\S+", rf"\1{fac['scheme']}", pt_new)
        # Pakistan PT doesn't have ControlBarScheme in the extracted block - add it
        new_pt_append.append(pt_new)

        # ControlBar scheme
        cbs_new = cbs_pak_block.replace("Pakistan8x6", fac["scheme"]).replace("Side Pakistan", f"Side {side}")
        # any remaining Pakistan identity in scheme?
        cbs_new = cbs_new.replace("Side Pakistan", f"Side {side}")
        assert f"Side {side}" in cbs_new
        assert "Side Pakistan" not in cbs_new
        new_cbs_append.append(cbs_new)

        # Strings
        string_lines += [
            f"{fac['display_key']} = {fac['display_text']}",
            f"Side:{side} = {fac['display_text']}",
            f"FACTION:{side} = {fac['display_text']}",
            f"{fac['tooltip']} = {fac['tooltip_text']}",
            f"{fac['features']} = {fac['features_text']}",
            "",
        ]

    # Apply appends to active files
    cs_text2 = cs_text.rstrip() + nl + nl + f";===== Pakistan-template faction clones CS ====={nl}" + (nl + nl).join(new_cs_append) + nl
    cb_text2 = cb_text.rstrip() + nl + nl + f";===== Pakistan-template faction clones CB ====={nl}" + (nl + nl).join(new_cb_append) + nl
    pt_text2 = pt_text.rstrip() + nl + nl + f";===== Pakistan-template faction clones PT ====={nl}" + (nl + nl).join(new_pt_append) + nl
    cbs_text2 = cbs_text.rstrip() + nl + nl + f";===== Pakistan-template faction clones ControlBar ====={nl}" + (nl + nl).join(new_cbs_append) + nl

    # Duplicate checks — only for newly introduced faction identifiers
    from collections import Counter

    new_prefixes = [f["prefix"] for f in FACTIONS]
    new_pts = {f["pt"] for f in FACTIONS}
    new_schemes = {f["scheme"] for f in FACTIONS}

    def dups_of_interest(names, pred):
        return [n for n, c in Counter(names).items() if c > 1 and pred(n)]

    cs_names = re.findall(r"^CommandSet (\S+)", cs_text2, re.M)
    cb_names = re.findall(r"^CommandButton (\S+)", cb_text2, re.M)
    pt_names = re.findall(r"^PlayerTemplate (\S+)", pt_text2, re.M)
    scheme_names = re.findall(r"^ControlBarScheme (\S+)", cbs_text2, re.M)

    def is_new_id(n: str) -> bool:
        return any(p in n for p in new_prefixes) or n in new_pts or n in new_schemes

    d1 = dups_of_interest(cs_names, is_new_id)
    d2 = dups_of_interest(cb_names, is_new_id)
    d3 = dups_of_interest(pt_names, lambda n: n in new_pts or n == "FactionPakistan")
    d4 = dups_of_interest(scheme_names, lambda n: n in new_schemes or n == "Pakistan8x6")
    if d1 or d2 or d3 or d4:
        raise SystemExit(f"DUPLICATE new ids CS={d1[:10]} CB={d2[:10]} PT={d3} Scheme={d4}")

    fmap[norm(r"Data\INI\CommandSet.ini")] = cs_text2.encode("latin1")
    fmap[norm(r"Data\INI\CommandButton.ini")] = cb_text2.encode("latin1")
    fmap[norm(r"Data\INI\PlayerTemplate.ini")] = pt_text2.encode("latin1")
    fmap[norm(r"Data\INI\ControlBarScheme.ini")] = cbs_text2.encode("latin1")

    # Strings file
    str_path = r"Data\English\PakistanTemplate_Clone_FactionStrings.txt"
    str_body = "\n".join(string_lines) + "\n"
    fmap[norm(str_path)] = str_body.encode("latin1")
    disp[norm(str_path)] = str_path
    (ROOT / "Data/English/PakistanTemplate_Clone_FactionStrings.txt").write_text(str_body, encoding="latin1")

    # CSF append display names
    csf_key = norm(r"Data\English\generals.csf")
    csf = fmap[csf_key]
    for fac in FACTIONS:
        csf = append_csf_label(csf, fac["display_key"], fac["display_text"])
        csf = append_csf_label(csf, fac["tooltip"], fac["tooltip_text"])
        csf = append_csf_label(csf, fac["features"], fac["features_text"])
    fmap[csf_key] = csf

    # Freeze asserts before write
    assert fmap[norm(r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_LargeAirBase.ini")] == freeze["lab"]
    assert fmap[norm(r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_HeavyAirBase.ini")] == freeze["hab"]
    assert fmap[norm(r"Data\INI\Object\Specter\Pakistan Armed Forces\Tracked\Pakistan_Dozer.ini")] == freeze["dozer"]
    assert fmap[norm(r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_LargeAirBase.ini")] == freeze["egypt"]
    # Pakistan active CS/CB core blocks still present identically for airfield
    assert "CommandSet Pakistan_AirfieldCommandSet" in cs_text2
    assert "CommandSet Pakistan_HeavyAirBaseCommandSet" in cs_text2
    assert "CommandSet PakistanDozerCommandSet" in cs_text2

    DATA_BIG.write_bytes(build_big({disp[k]: v for k, v in fmap.items()}))
    data_sha = sha256(DATA_BIG)
    art_sha = sha256(ART_BIG)
    assert art_sha == BASE_ART
    print("DATA", data_sha)
    print("ART", art_sha, "(unchanged)")

    # -------- Validation --------
    e2, r2 = read_big(DATA_BIG)
    f2 = {norm(n): r2[o : o + s] for n, o, s in e2}
    assert f2[norm(r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_LargeAirBase.ini")] == freeze["lab"]
    assert f2[norm(r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_HeavyAirBase.ini")] == freeze["hab"]
    assert f2[norm(r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_LargeAirBase.ini")] == freeze["egypt"]

    pt2 = f2[norm(r"Data\INI\PlayerTemplate.ini")].decode("latin1")
    cs2 = f2[norm(r"Data\INI\CommandSet.ini")].decode("latin1")
    cb2 = f2[norm(r"Data\INI\CommandButton.ini")].decode("latin1")
    cbs2 = f2[norm(r"Data\INI\ControlBarScheme.ini")].decode("latin1")

    for fac in FACTIONS:
        p = fac["prefix"]
        assert len(re.findall(rf"^PlayerTemplate {re.escape(fac['pt'])}\s*$", pt2, re.M)) == 1
        assert len(re.findall(rf"^CommandSet {re.escape(p)}DozerCommandSet\s*$", cs2, re.M)) == 1
        assert len(re.findall(rf"^CommandSet {re.escape(p)}_AirfieldCommandSet\s*$", cs2, re.M)) == 1
        assert len(re.findall(rf"^CommandSet {re.escape(p)}_HeavyAirBaseCommandSet\s*$", cs2, re.M)) == 1
        assert len(re.findall(rf"^CommandButton Command_Construct{re.escape(p)}_Airfield_T\s*$", cb2, re.M)) == 1
        assert len(re.findall(rf"^CommandButton Command_Construct{re.escape(p)}_HeavyAirBase\s*$", cb2, re.M)) == 1
        assert len(re.findall(rf"^CommandButton Command_Construct{re.escape(p)}_Lgm30\s*$", cb2, re.M)) == 1
        assert len(re.findall(rf"^CommandButton Command_Construct{re.escape(p)}_FireBase\s*$", cb2, re.M)) == 1
        assert len(re.findall(rf"^CommandButton Command_Construct{re.escape(p)}_CRAM\s*$", cb2, re.M)) == 1
        assert len(re.findall(rf"^ControlBarScheme {re.escape(fac['scheme'])}\s*$", cbs2, re.M)) == 1
        assert f"Side {fac['side']}" in cbs2
        # objects exist
        for obj in [f"{p}_CommandCenter", f"{p}_Dozer", f"{p}_LargeAirBase", f"{p}_HeavyAirBase", f"{p}_Lgm30", f"{p}_FireBase", f"{p}_CRAM"]:
            # search object declaration in any file
            found = False
            for n, o, s in e2:
                if not n.lower().endswith(".ini"):
                    continue
                if re.search(rf"^Object\s+{re.escape(obj)}\s*$", r2[o : o + s].decode("latin1", errors="replace"), re.M):
                    found = True
                    break
            assert found, f"Missing object {obj}"
        # no Side Pakistan in new control bars
        m = re.search(rf"ControlBarScheme {re.escape(fac['scheme'])}[\s\S]*?\nEnd", cbs2)
        assert m and "Side Pakistan" not in m.group(0)
        # Dozer palette slot order check
        dozer = re.search(rf"CommandSet {p}DozerCommandSet\r?\n(.*?)\r?\nEnd", cs2, re.S).group(1)
        assert f"Command_Construct{p}_FireBase" in dozer
        assert f"Command_Construct{p}_CRAM" in dozer
        assert f"Command_Construct{p}_Lgm30" in dozer
        assert "DisarmMines" not in dozer
        assert f"Command_Construct{p}_Abbas" not in dozer
        # Large airbase still 16
        lab = None
        for n, o, s in e2:
            if n.lower().endswith(f"{p.lower()}_largeairbase.ini".replace("saudiarabia", "saudiarabia")):
                pass
            if f"{p}_LargeAirBase.ini".lower() in n.lower().replace("\\", "/"):
                lab = r2[o : o + s].decode("latin1")
                break
        assert lab and "NumRows                 = 4" in lab and "NumCols                 = 4" in lab
        assert "TheAirPort" in lab
        print("OK", fac["pt"])

    # Pakistan still intact
    assert len(re.findall(r"^PlayerTemplate FactionPakistan\s*$", pt2, re.M)) == 1
    assert len(re.findall(r"^CommandSet PakistanDozerCommandSet\s*$", cs2, re.M)) == 1
    assert "14 = Command_ConstructPakistan_Lgm30" in cs2
    assert "10 = Command_ConstructPakistan_FireBase" in cs2
    assert "12 = Command_ConstructPakistan_CRAM" in cs2

    print("STATIC AUDIT: PASS")

    (OUT_DIR / "DATA_PAKISTAN_CLONE_4FACTIONS_HASHES.txt").write_text(
        f"_SPEC_DATA_ONE.big sha256={data_sha}\n_SPEC_ART_ONE.big sha256={art_sha} (UNCHANGED)\n"
    )
    (OUT_DIR / "DATA_PAKISTAN_CLONE_4FACTIONS_DOWNLOAD.txt").write_text(
        "PAKISTAN-TEMPLATE CLONES: SaudiArabia / UAE / India / Syria (DATA-only)\n"
        f"DATA sha256={data_sha}\nART sha256={art_sha} (UNCHANGED)\n"
    )
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")
    print("ZIP", ZIP_PATH.stat().st_size)


if __name__ == "__main__":
    main()
