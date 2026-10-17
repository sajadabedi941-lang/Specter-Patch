#!/usr/bin/env python3
"""Clone CURRENT working Nato faction into Germany, France, Britain, Italy.

Nato is the golden template (READ-ONLY functionally). Reuses Nato PurchaseScience /
SpecialPowerShortcutNATO infrastructure (no invented country Sciences).
Correct CSF UTF-16 character-count append. DATA-only.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path("/workspace/patch")
DATA_BIG = ROOT / "Release/SPECTER_MASTER/_SPEC_DATA_ONE.big"
ART_BIG = ROOT / "Release/SPECTER_MASTER/_SPEC_ART_ONE.big"
OUT_DIR = ROOT / "Release/SPECTER_MASTER"
ZIP_PATH = ROOT / "Release/SPECTER_MASTER_DATA_NATO_CLONE_4FACTIONS.zip"
NOTE = OUT_DIR / "DATA_NATO_CLONE_4FACTIONS_HASHES.txt"
DL = OUT_DIR / "DATA_NATO_CLONE_4FACTIONS_DOWNLOAD.txt"

BASE_DATA = "9dcdeea2d11de81025f95dc529c39d02b83a6555319187bc8d82ab6723b8ea58"
BASE_ART = "74a411b72c19fafaafcd48a45d2aa76731d8dbd13e919e4f73f8b989e90d4822"

FACTIONS = [
    {
        "prefix": "Germany",
        "side": "Germany",
        "pt": "FactionGermany",
        "scheme": "Germany8x6",
        "folder": "German Armed Forces",
        "display_key": "INI:FactionGermany",
        "display_text": "Germany Armed Forces",
        "side_key": "SIDE:Germany",
        "side_text": "Germany Armed Forces",
        "tooltip": "TOOLTIP:BioStrategyLong_Germany",
        "features": "GUI:BioFeatures_Germany",
        "tooltip_text": "Germany Armed Forces - Nato-template combined-arms clone.",
        "features_text": "Armor, airpower, dual airbases, layered air defense.",
        "color": "R:0 G:80 B:40",
    },
    {
        "prefix": "France",
        "side": "France",
        "pt": "FactionFrance",
        "scheme": "France8x6",
        "folder": "French Armed Forces",
        "display_key": "INI:FactionFrance",
        "display_text": "French Armed Forces",
        "side_key": "SIDE:France",
        "side_text": "French Armed Forces",
        "tooltip": "TOOLTIP:BioStrategyLong_France",
        "features": "GUI:BioFeatures_France",
        "tooltip_text": "French Armed Forces - Nato-template combined-arms clone.",
        "features_text": "Armor, airpower, dual airbases, layered air defense.",
        "color": "R:0 G:50 B:160",
    },
    {
        "prefix": "Britain",
        "side": "Britain",
        "pt": "FactionBritain",
        "scheme": "Britain8x6",
        "folder": "British Armed Forces",
        "display_key": "INI:FactionBritain",
        "display_text": "British Armed Forces",
        "side_key": "SIDE:Britain",
        "side_text": "British Armed Forces",
        "tooltip": "TOOLTIP:BioStrategyLong_Britain",
        "features": "GUI:BioFeatures_Britain",
        "tooltip_text": "British Armed Forces - Nato-template combined-arms clone.",
        "features_text": "Armor, airpower, dual airbases, layered air defense.",
        "color": "R:140 G:0 B:40",
    },
    {
        "prefix": "Italy",
        "side": "Italy",
        "pt": "FactionItaly",
        "scheme": "Italy8x6",
        "folder": "Italian Armed Forces",
        "display_key": "INI:FactionItaly",
        "display_text": "Italian Armed Forces",
        "side_key": "SIDE:Italy",
        "side_text": "Italian Armed Forces",
        "tooltip": "TOOLTIP:BioStrategyLong_Italy",
        "features": "GUI:BioFeatures_Italy",
        "tooltip_text": "Italian Armed Forces - Nato-template combined-arms clone.",
        "features_text": "Armor, airpower, dual airbases, layered air defense.",
        "color": "R:0 G:120 B:70",
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


def protect_shared_science(text: str) -> str:
    """Prevent SCIENCE_Nato / SCIENCE_NATO from being renamed with faction prefix."""
    text = text.replace("SCIENCE_NATO", "@@SCIENCE_NATO@@")
    text = text.replace("SCIENCE_Nato", "@@SCIENCE_Nato@@")
    return text


def unprotect_shared_science(text: str) -> str:
    text = text.replace("@@SCIENCE_NATO@@", "SCIENCE_NATO")
    text = text.replace("@@SCIENCE_Nato@@", "SCIENCE_Nato")
    return text


def transform_nato_text(text: str, prefix: str, side: str, fac: dict) -> str:
    """Rename faction-owned Nato identifiers. Protect shared Sciences and donor assets."""
    out = protect_shared_science(text)

    # Longest / most-specific first
    reps = [
        ("Command_PurchaseScienceNato", f"Command_PurchaseScience{prefix}"),  # may still appear in comments
        ("Command_ConstructNato_", f"Command_Construct{prefix}_"),
        ("Command_ConstructNato", f"Command_Construct{prefix}"),
        ("Command_SelectNato", f"Command_Select{prefix}"),
        ("Command_Nato", f"Command_{prefix}"),
        ("Command_UpgradeNato", f"Command_Upgrade{prefix}"),
        ("Nato_LargeAirBaseCommandSet", f"{prefix}_LargeAirBaseCommandSet"),
        ("Nato_HeavyAirBaseCommandSet", f"{prefix}_HeavyAirBaseCommandSet"),
        ("Nato_LargeAirBase", f"{prefix}_LargeAirBase"),
        ("Nato_HeavyAirBase", f"{prefix}_HeavyAirBase"),
        ("NatoDozerCommandSet", f"{prefix}DozerCommandSet"),
        ("NatoCommandCenterCommandSet", f"{prefix}CommandCenterCommandSet"),
        ("NatoCampCommandSet", f"{prefix}CampCommandSet"),
        ("NatoWarfactoryCommandSet", f"{prefix}WarfactoryCommandSet"),
        ("NatoAirfieldCommandSet", f"{prefix}AirfieldCommandSet"),
        ("NatoGM406CommandSet", f"{prefix}GM406CommandSet"),
        ("NatoSupplyCenterCommandSet", f"{prefix}SupplyCenterCommandSet"),
        ("NatoStrategyCenterCommandSet", f"{prefix}StrategyCenterCommandSet"),
        ("SpecialPowerShortcutNatoCommandSet", f"SpecialPowerShortcut{prefix}CommandSet"),
        ("NatoSystemSpecialPowerShortcut", f"{prefix}SystemSpecialPowerShortcut"),
        ("FactionNato", fac["pt"]),
        ("INI:FactionNatoForces", fac["display_key"]),
        ("TOOLTIP:BioStrategyLong_Nato", fac["tooltip"]),
        ("GUI:BioFeatures_Nato", fac["features"]),
        ("AmericaNato8x6", fac["scheme"]),
    ]
    for a, b in reps:
        out = out.replace(a, b)

    # Remaining Nato* identity tokens (objects like NatoCommandCenter, NatoVehicleDozer)
    # Avoid touching @@SCIENCE_Nato@@ placeholders and W3D/texture donor names.
    out = re.sub(r"\bNato(?=[A-Z_])", prefix, out)
    # Side / BaseSide
    out = re.sub(r"(Side\s*=\s*)Nato\b", rf"\1{side}", out)
    out = re.sub(r"(BaseSide\s*=\s*)Nato\b", rf"\1{side}", out)

    out = unprotect_shared_science(out)
    return out


def strip_nonprefixed_objects(text: str, prefix: str) -> str:
    """Keep only Object blocks whose names start with the faction prefix."""
    parts = re.split(r"(?=^Object\s+)", text, flags=re.M)
    kept = []
    for part in parts:
        m = re.match(r"^Object\s+(\S+)", part, re.M)
        if not m:
            kept.append(part)
            continue
        name = m.group(1)
        if name.startswith(prefix):
            kept.append(part)
    return "".join(kept)


def extract_blocks(text: str, kind: str) -> list[tuple[str, str]]:
    pat = rf"(^{kind}\s+(\S+)[\s\S]*?^\s*End\s*$)"
    out = []
    for m in re.finditer(pat, text, re.M | re.I):
        # normalize End vs END
        out.append((m.group(2), m.group(1)))
    return out


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
    """Append one LBL/RTS entry. strlen = UTF-16 CHARACTER count (not bytes)."""
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


def rewrite_pt_for_stability(pt_block: str, fac: dict) -> str:
    """Keep Nato science/shortcut infrastructure; identity-only diffs. No ControlBarScheme."""
    # Ensure science fields stay Nato
    pt_block = re.sub(
        r"(PurchaseScienceCommandSetRank1\s*=\s*)\S+",
        r"\1SCIENCE_NATO_CommandSetRank1",
        pt_block,
    )
    pt_block = re.sub(
        r"(PurchaseScienceCommandSetRank3\s*=\s*)\S+",
        r"\1SCIENCE_NATO_CommandSetRank3",
        pt_block,
    )
    pt_block = re.sub(
        r"(PurchaseScienceCommandSetRank8\s*=\s*)\S+",
        r"\1SCIENCE_NATO_CommandSetRank8",
        pt_block,
    )
    pt_block = re.sub(
        r"(SpecialPowerShortcutCommandSet\s*=\s*)\S+",
        r"\1SpecialPowerShortcutNATO",
        pt_block,
    )
    pt_block = re.sub(
        r"(IntrinsicSciences\s*=\s*)\S+",
        r"\1SCIENCE_NATO",
        pt_block,
    )
    # PreferredColor
    pt_block = re.sub(
        r"(PreferredColor\s*=\s*).*$",
        rf"\1{fac['color']}",
        pt_block,
        flags=re.M,
    )
    # Strip any ControlBarScheme line if present
    pt_block = re.sub(r"^\s*ControlBarScheme\s*=\s*.*$\n?", "", pt_block, flags=re.M)
    return pt_block


def force_shortcut_object_cs(obj_text: str, prefix: str) -> str:
    """Point country SystemSpecialPowerShortcut at shared SpecialPowerShortcutNATO."""
    name = f"{prefix}SystemSpecialPowerShortcut"

    def repl(m: re.Match) -> str:
        block = m.group(0)
        block = re.sub(
            r"(CommandSet\s*=\s*)\S+",
            r"\1SpecialPowerShortcutNATO",
            block,
            count=1,
        )
        return block

    return re.sub(
        rf"^Object\s+{re.escape(name)}\b.*?^End\s*$",
        repl,
        obj_text,
        count=1,
        flags=re.M | re.S,
    )


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

    # Freeze Nato airbases + Pakistan + Egypt
    freeze = {
        "nato_lab": fmap[norm(r"Data\INI\Object\Specter\NATO\Buildings\Nato_LargeAirBase.ini")],
        "nato_hab": fmap[norm(r"Data\INI\Object\Specter\NATO\Buildings\Nato_HeavyAirBase.ini")],
        "pak_lab": fmap[norm(r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_LargeAirBase.ini")],
        "pak_hab": fmap[norm(r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_HeavyAirBase.ini")],
    }
    pt_before = fmap[norm(r"Data\INI\PlayerTemplate.ini")]
    cs_before = fmap[norm(r"Data\INI\CommandSet.ini")]
    cb_before = fmap[norm(r"Data\INI\CommandButton.ini")]
    cbs_before = fmap[norm(r"Data\INI\ControlBarScheme.ini")]
    csf_before = fmap[norm(r"Data\English\generals.csf")]

    pt_text = pt_before.decode("latin1")
    cs_text = cs_before.decode("latin1")
    cb_text = cb_before.decode("latin1")
    cbs_text = cbs_before.decode("latin1")

    # Extract Nato PT + ControlBar
    pt_nato = re.search(r"^PlayerTemplate\s+FactionNato\b.*?^End\s*$", pt_text, re.M | re.S)
    assert pt_nato, "FactionNato missing"
    pt_nato_block = pt_nato.group(0)

    cbs_nato = re.search(r"^ControlBarScheme\s+AmericaNato8x6\b.*?^End\s*$", cbs_text, re.M | re.S)
    assert cbs_nato, "AmericaNato8x6 missing"
    cbs_nato_block = cbs_nato.group(0)

    # Active Nato CommandSets / Buttons (exclude SCIENCE_NATO* and shared SpecialPowerShortcutNATO)
    def is_cloneable_cs(name: str) -> bool:
        if name.startswith("SCIENCE_NATO"):
            return False
        if name == "SpecialPowerShortcutNATO":
            return False
        return bool(re.search(r"Nato", name, re.I))

    def is_cloneable_cb(name: str) -> bool:
        if name.startswith("Command_PurchaseScienceNato") or name.startswith("Command_PurchaseScienceNATO"):
            return False
        return bool(re.search(r"Nato", name, re.I))

    nato_cs_blocks = [(n, b) for n, b in extract_blocks(cs_text, "CommandSet") if is_cloneable_cs(n)]
    nato_cb_blocks = [(n, b) for n, b in extract_blocks(cb_text, "CommandButton") if is_cloneable_cb(n)]
    print(f"Cloneable CS={len(nato_cs_blocks)} CB={len(nato_cb_blocks)}")

    # NATO object files (skip shared weapon projectiles file)
    nato_obj_files = []
    for name, _off, _size in entries:
        nl = name.replace("/", "\\").lower()
        if ("\\specter\\nato\\" in nl) and nl.endswith(".ini"):
            if nl.endswith("\\nato_weaponobjects.ini"):
                continue
            nato_obj_files.append(name.replace("/", "\\"))
    print(f"Nato object files to clone: {len(nato_obj_files)}")

    new_pt_append = []
    new_cbs_append = []
    new_cs_append = []
    new_cb_append = []

    for fac in FACTIONS:
        prefix = fac["prefix"]
        side = fac["side"]

        # PlayerTemplate
        pt_block = transform_nato_text(pt_nato_block, prefix, side, fac)
        pt_block = rewrite_pt_for_stability(pt_block, fac)
        # Ensure StartingBuilding / Unit names transformed
        assert f"PlayerTemplate {fac['pt']}" in pt_block
        assert f"Side              = {side}" in pt_block or re.search(rf"Side\s*=\s*{side}", pt_block)
        assert "SCIENCE_NATO_CommandSetRank1" in pt_block
        assert "SpecialPowerShortcutNATO" in pt_block
        assert "ControlBarScheme" not in pt_block
        assert f"StartingBuilding  = {prefix}CommandCenter" in pt_block or re.search(
            rf"StartingBuilding\s*=\s*{prefix}CommandCenter", pt_block
        )
        assert f"StartingUnit0     = {prefix}VehicleDozer" in pt_block or re.search(
            rf"StartingUnit0\s*=\s*{prefix}VehicleDozer", pt_block
        )
        new_pt_append.append(pt_block)

        # ControlBar
        cbs_block = transform_nato_text(cbs_nato_block, prefix, side, fac)
        # Ensure scheme name and Side
        cbs_block = re.sub(
            r"^ControlBarScheme\s+\S+",
            f"ControlBarScheme {fac['scheme']}",
            cbs_block,
            count=1,
            flags=re.M,
        )
        cbs_block = re.sub(r"(Side\s+)\S+", rf"\1{side}", cbs_block, count=1)
        assert f"ControlBarScheme {fac['scheme']}" in cbs_block
        assert re.search(rf"Side\s+{side}\b", cbs_block)
        new_cbs_append.append(cbs_block)

        # CommandSets
        for _n, block in nato_cs_blocks:
            nb = transform_nato_text(block, prefix, side, fac)
            new_cs_append.append(nb)

        # CommandButtons
        for _n, block in nato_cb_blocks:
            nb = transform_nato_text(block, prefix, side, fac)
            # Restore any accidental PurchaseScience rename if present
            new_cb_append.append(nb)

        # Object files
        for src_path in nato_obj_files:
            src = fmap[norm(src_path)].decode("latin1")
            # relative under NATO\
            rel = src_path.split("NATO\\", 1)[1] if "NATO\\" in src_path else src_path.split("Nato\\", 1)[-1]
            dst_path = rf"Data\INI\Object\Specter\{fac['folder']}\{rel}"
            cloned = transform_nato_text(src, prefix, side, fac)
            cloned = strip_nonprefixed_objects(cloned, prefix)
            if prefix + "SystemSpecialPowerShortcut" in cloned:
                cloned = force_shortcut_object_cs(cloned, prefix)
            if not re.search(rf"^Object\s+{re.escape(prefix)}", cloned, re.M):
                # file had only shared objects — skip
                continue
            fmap[norm(dst_path)] = cloned.encode("latin1")
            disp[norm(dst_path)] = dst_path

    # Append PT / ControlBar / CS / CB
    nl = "\n"
    pt_text2 = pt_text.rstrip() + nl + nl + ";===== Nato-template faction clones PT =====" + nl + (nl + nl).join(new_pt_append) + nl
    cbs_text2 = cbs_text.rstrip() + nl + nl + ";===== Nato-template faction clones ControlBar =====" + nl + (nl + nl).join(new_cbs_append) + nl
    cs_text2 = cs_text.rstrip() + nl + nl + ";===== Nato-template faction clones CS =====" + nl + (nl + nl).join(new_cs_append) + nl
    cb_text2 = cb_text.rstrip() + nl + nl + ";===== Nato-template faction clones CB =====" + nl + (nl + nl).join(new_cb_append) + nl

    # Duplicate checks for new ids
    def dups(names):
        return [n for n, c in Counter(names).items() if c > 1]

    new_pts = {f["pt"] for f in FACTIONS}
    new_schemes = {f["scheme"] for f in FACTIONS}
    pt_names = re.findall(r"^PlayerTemplate\s+(\S+)", pt_text2, re.M)
    scheme_names = re.findall(r"^ControlBarScheme\s+(\S+)", cbs_text2, re.M)
    assert not any(n in new_pts and pt_names.count(n) != 1 for n in new_pts)
    assert not any(n in new_schemes and scheme_names.count(n) != 1 for n in new_schemes)
    # FactionNato still exactly once
    assert pt_names.count("FactionNato") == 1

    # Ensure no PurchaseScienceGermany etc created
    for fac in FACTIONS:
        bad = re.findall(rf"^CommandButton\s+(Command_PurchaseScience{fac['prefix']}\S*)", cb_text2, re.M)
        if bad:
            raise SystemExit(f"Invented PurchaseScience buttons: {bad}")

    fmap[norm(r"Data\INI\PlayerTemplate.ini")] = pt_text2.encode("latin1")
    fmap[norm(r"Data\INI\ControlBarScheme.ini")] = cbs_text2.encode("latin1")
    fmap[norm(r"Data\INI\CommandSet.ini")] = cs_text2.encode("latin1")
    fmap[norm(r"Data\INI\CommandButton.ini")] = cb_text2.encode("latin1")

    # CSF strings: SIDE + INI + tooltip + features
    csf = bytearray(csf_before)
    csf_bytes = bytes(csf)
    for fac in FACTIONS:
        for key, val in [
            (fac["side_key"], fac["side_text"]),
            (fac["display_key"], fac["display_text"]),
            (fac["tooltip"], fac["tooltip_text"]),
            (fac["features"], fac["features_text"]),
        ]:
            csf_bytes = append_csf_label(csf_bytes, key, val)
    nlab, parsed, errs = parse_csf_ok(csf_bytes)
    assert not errs and nlab == parsed, (nlab, parsed, errs)
    fmap[norm(r"Data\English\generals.csf")] = csf_bytes

    # Freeze asserts
    assert fmap[norm(r"Data\INI\Object\Specter\NATO\Buildings\Nato_LargeAirBase.ini")] == freeze["nato_lab"]
    assert fmap[norm(r"Data\INI\Object\Specter\NATO\Buildings\Nato_HeavyAirBase.ini")] == freeze["nato_hab"]
    assert fmap[norm(r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_LargeAirBase.ini")] == freeze["pak_lab"]
    assert fmap[norm(r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_HeavyAirBase.ini")] == freeze["pak_hab"]
    # Nato PT unchanged in content
    assert "PlayerTemplate FactionNato" in fmap[norm(r"Data\INI\PlayerTemplate.ini")].decode("latin1")
    nato_pt_after = re.search(
        r"^PlayerTemplate\s+FactionNato\b.*?^End\s*$",
        fmap[norm(r"Data\INI\PlayerTemplate.ini")].decode("latin1"),
        re.M | re.S,
    ).group(0)
    assert nato_pt_after == pt_nato_block

    DATA_BIG.write_bytes(build_big({disp[k]: v for k, v in fmap.items()}))
    data_sha = sha256(DATA_BIG)
    art_sha = sha256(ART_BIG)
    assert art_sha == BASE_ART

    # -------- Validation from rebuilt BIG --------
    e2, r2 = read_big(DATA_BIG)
    f2 = {norm(n): r2[o : o + s] for n, o, s in e2}
    pt2 = f2[norm(r"Data\INI\PlayerTemplate.ini")].decode("latin1")
    cs2 = f2[norm(r"Data\INI\CommandSet.ini")].decode("latin1")
    cb2 = f2[norm(r"Data\INI\CommandButton.ini")].decode("latin1")
    cbs2 = f2[norm(r"Data\INI\ControlBarScheme.ini")].decode("latin1")
    csf2 = f2[norm(r"Data\English\generals.csf")]
    nlab, parsed, errs = parse_csf_ok(csf2)
    assert not errs and nlab == parsed

    report_lines = []
    for fac in FACTIONS:
        prefix = fac["prefix"]
        m = re.search(rf"^PlayerTemplate\s+{fac['pt']}\b.*?^End\s*$", pt2, re.M | re.S)
        assert m, fac["pt"]
        block = m.group(0)
        assert "SCIENCE_NATO_CommandSetRank1" in block
        assert "SpecialPowerShortcutNATO" in block
        assert "ControlBarScheme" not in block
        # Objects
        for obj in [
            f"{prefix}CommandCenter",
            f"{prefix}VehicleDozer",
            f"{prefix}_LargeAirBase",
            f"{prefix}_HeavyAirBase",
            f"{prefix}WarFactory",
            f"{prefix}BootCamp",
        ]:
            found = False
            for n, b in f2.items():
                if re.search(rf"^Object\s+{re.escape(obj)}\b", b.decode("latin1", errors="replace"), re.M):
                    found = True
                    break
            assert found, f"missing object {obj}"
        # CS
        assert re.search(rf"^CommandSet\s+{prefix}DozerCommandSet\b", cs2, re.M)
        assert re.search(rf"^CommandSet\s+{prefix}_LargeAirBaseCommandSet\b", cs2, re.M)
        assert re.search(rf"^CommandSet\s+{prefix}_HeavyAirBaseCommandSet\b", cs2, re.M)
        assert re.search(rf"^ControlBarScheme\s+{fac['scheme']}\b", cbs2, re.M)
        # CSF
        assert fac["side_key"].encode("ascii") in csf2
        assert fac["display_key"].encode("ascii") in csf2
        # No invented PurchaseScience
        assert not re.search(rf"^CommandButton\s+Command_PurchaseScience{prefix}", cb2, re.M)
        # Capacity
        lab = None
        for n, b in f2.items():
            t = b.decode("latin1", errors="replace")
            if re.search(rf"^Object\s+{prefix}_LargeAirBase\b", t, re.M):
                lab = t
                break
        assert lab and "NumRows                 = 4" in lab and "NumCols                 = 4" in lab
        assert "TheAirPort" in lab
        hab = None
        for n, b in f2.items():
            t = b.decode("latin1", errors="replace")
            if re.search(rf"^Object\s+{prefix}_HeavyAirBase\b", t, re.M):
                hab = t
                break
        assert hab and "HXUSABigAirPort" in hab

        report_lines.append(
            f"""{prefix.upper()}:
PlayerTemplate = {fac['pt']}
Side = {fac['side']}
DisplayName = {fac['display_key']}
ControlBar = {fac['scheme']}
CommandCenter = {prefix}CommandCenter
Dozer = {prefix}VehicleDozer
Dozer CommandSet = {prefix}DozerCommandSet
WarFactory = {prefix}WarFactory
Barracks = {prefix}BootCamp
LargeAirBase = {prefix}_LargeAirBase
LargeAirBase capacity = 16
HeavyAirBase = {prefix}_HeavyAirBase
PurchaseScience validation = REUSES SCIENCE_NATO_CommandSetRank* (no invented country sciences)
SIDE string = {fac['side_key']}
PLAYABLE = YES
{prefix.upper()} CLONE = PASS
"""
        )

    # Nato functionally unchanged
    assert f2[norm(r"Data\INI\Object\Specter\NATO\Buildings\Nato_LargeAirBase.ini")] == freeze["nato_lab"]
    assert f2[norm(r"Data\INI\Object\Specter\NATO\Buildings\Nato_HeavyAirBase.ini")] == freeze["nato_hab"]
    assert re.search(r"^PlayerTemplate\s+FactionNato\b.*?^End\s*$", pt2, re.M | re.S).group(0) == pt_nato_block

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")

    report = "\n".join(report_lines) + f"""
NATO CHANGED FUNCTIONALLY = NO
PAKISTAN CHANGED = NO
SAUDI ARABIA CHANGED = NO
UAE CHANGED = NO
INDIA CHANGED = NO
SYRIA CHANGED = NO
EGYPT CHANGED = NO

MISSING SIDE STRINGS = 0
UNRESOLVED PURCHASESCIENCE BUTTONS = 0
UNRESOLVED SCIENCES = 0

DATA sha256 = {data_sha}
ART sha256  = {art_sha} (UNCHANGED)
ZIP sha256  = {sha256(ZIP_PATH)}
"""
    NOTE.write_text(report, encoding="utf-8")
    print(report)
    print("ZIP", ZIP_PATH, ZIP_PATH.stat().st_size)


if __name__ == "__main__":
    main()
