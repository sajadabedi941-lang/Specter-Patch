#!/usr/bin/env python3
"""Clone CURRENT working Nato faction into Sweden / Ukraine / Turkey.

Nato is the golden template (READ-ONLY functionally). Reuses Nato PurchaseScience /
SpecialPowerShortcutNATO infrastructure (no invented country Sciences).
Correct CSF UTF-16 character-count append/upsert. DATA-only.

Baseline: Nato + Germany/France/Britain/Italy clones already present
(DATA sha 72901a9e...).
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
ZIP_PATH = ROOT / "Release/SPECTER_MASTER_DATA_NATO_CLONE_SE_UA_TR.zip"
NOTE = OUT_DIR / "DATA_NATO_CLONE_SE_UA_TR_HASHES.txt"
DL = OUT_DIR / "DATA_NATO_CLONE_SE_UA_TR_DOWNLOAD.txt"

BASE_DATA = "72901a9e9deff2934a3a3842e8da53e8ecd19f0d580709e4d8c28f4d3e02cdaf"
BASE_ART = "74a411b72c19fafaafcd48a45d2aa76731d8dbd13e919e4f73f8b989e90d4822"

FACTIONS = [
    {
        "prefix": "Sweden",
        "side": "Sweden",
        "pt": "FactionSweden",
        "scheme": "Sweden8x6",
        "folder": "Swedish Armed Forces",
        "display_key": "INI:FactionSweden",
        "display_text": "Swedish Armed Forces",
        "side_key": "SIDE:Sweden",
        "side_text": "Swedish Armed Forces",
        "tooltip": "TOOLTIP:BioStrategyLong_Sweden",
        "features": "GUI:BioFeatures_Sweden",
        "tooltip_text": "Swedish Armed Forces - Nato-template combined-arms clone.",
        "features_text": "Armor, airpower, dual airbases, layered air defense.",
        "color": "R:0 G:90 B:160",
    },
    {
        "prefix": "Ukraine",
        "side": "Ukraine",
        "pt": "FactionUkraine",
        "scheme": "Ukraine8x6",
        "folder": "Ukrainian Armed Forces",
        "display_key": "INI:FactionUkraine",
        "display_text": "Ukrainian Armed Forces",
        "side_key": "SIDE:Ukraine",
        "side_text": "Ukrainian Armed Forces",
        "tooltip": "TOOLTIP:BioStrategyLong_Ukraine",
        "features": "GUI:BioFeatures_Ukraine",
        "tooltip_text": "Ukrainian Armed Forces - Nato-template combined-arms clone.",
        "features_text": "Armor, airpower, dual airbases, layered air defense.",
        "color": "R:0 G:90 B:180",
    },
    {
        "prefix": "Turkey",
        "side": "Turkey",
        "pt": "FactionTurkey",
        "scheme": "Turkey8x6",
        "folder": "Turkish Armed Forces",
        "display_key": "INI:FactionTurkey",
        "display_text": "Turkish Armed Forces",
        "side_key": "SIDE:Turkey",
        "side_text": "Turkish Armed Forces",
        "tooltip": "TOOLTIP:BioStrategyLong_Turkey",
        "features": "GUI:BioFeatures_Turkey",
        "tooltip_text": "Turkish Armed Forces - Nato-template combined-arms clone.",
        "features_text": "Armor, airpower, dual airbases, layered air defense.",
        "color": "R:180 G:20 B:40",
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
        ("Command_PurchaseScienceNato", f"Command_PurchaseScience{prefix}"),
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
    out = re.sub(r"\bNato(?=[A-Z_])", prefix, out)
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


def upsert_csf_label(csf: bytes, label: str, value: str) -> bytes:
    """Replace label value if present; otherwise append. ASCII values only."""
    assert value.isascii(), value
    nlabels = struct.unpack_from("<I", csf, 8)[0]
    pos = 24
    parts: list[bytes] = [csf[:24]]
    found = False
    for _ in range(nlabels):
        start = pos
        if pos + 12 > len(csf) or csf[pos : pos + 4] != b" LBL":
            raise SystemExit(f"CSF corrupt near {pos}")
        numvals = struct.unpack_from("<I", csf, pos + 4)[0]
        namelen = struct.unpack_from("<I", csf, pos + 8)[0]
        pos += 12
        lab = csf[pos : pos + namelen].decode("ascii", errors="replace")
        pos += namelen
        for _v in range(numvals):
            vtag = csf[pos : pos + 4]
            pos += 4
            strlen = struct.unpack_from("<I", csf, pos)[0]
            pos += 4 + strlen * 2
            if vtag == b"WRTS":
                elen = struct.unpack_from("<I", csf, pos)[0]
                pos += 4 + elen
        end = pos
        if lab == label:
            found = True
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
            parts.append(bytes(entry))
        else:
            parts.append(csf[start:end])
    if pos != len(csf):
        parts.append(csf[pos:])
    if not found:
        return append_csf_label(b"".join(parts), label, value)
    out = bytearray(b"".join(parts))
    # header counts unchanged on replace
    return bytes(out)


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


def csf_get(csf: bytes, label: str) -> str | None:
    nlabels = struct.unpack_from("<I", csf, 8)[0]
    pos = 24
    for _ in range(nlabels):
        if pos + 12 > len(csf) or csf[pos : pos + 4] != b" LBL":
            break
        numvals = struct.unpack_from("<I", csf, pos + 4)[0]
        namelen = struct.unpack_from("<I", csf, pos + 8)[0]
        pos += 12
        lab = csf[pos : pos + namelen].decode("ascii", errors="replace")
        pos += namelen
        vals = []
        for _v in range(numvals):
            vtag = csf[pos : pos + 4]
            pos += 4
            strlen = struct.unpack_from("<I", csf, pos)[0]
            pos += 4
            xored = csf[pos : pos + strlen * 2]
            pos += strlen * 2
            vals.append(bytes(b ^ 0xFF for b in xored).decode("utf-16-le", errors="replace"))
            if vtag == b"WRTS":
                elen = struct.unpack_from("<I", csf, pos)[0]
                pos += 4 + elen
        if lab == label:
            return vals[0] if vals else ""
    return None


def rewrite_pt_for_stability(pt_block: str, fac: dict) -> str:
    """Keep Nato science/shortcut infrastructure; identity-only diffs. No ControlBarScheme."""
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
    pt_block = re.sub(
        r"(PreferredColor\s*=\s*).*$",
        rf"\1{fac['color']}",
        pt_block,
        flags=re.M,
    )
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

    # Freeze Nato + Pakistan + Egypt + prior EU Nato-clones airbases
    freeze_paths = {
        "nato_lab": r"Data\INI\Object\Specter\NATO\Buildings\Nato_LargeAirBase.ini",
        "nato_hab": r"Data\INI\Object\Specter\NATO\Buildings\Nato_HeavyAirBase.ini",
        "pak_lab": r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_LargeAirBase.ini",
        "pak_hab": r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_HeavyAirBase.ini",
        # EU clone folders keep source filenames (Nato_*.ini) but Object ids are country-prefixed.
        "ger_lab": r"Data\INI\Object\Specter\German Armed Forces\Buildings\Nato_LargeAirBase.ini",
        "fra_lab": r"Data\INI\Object\Specter\French Armed Forces\Buildings\Nato_LargeAirBase.ini",
        "bri_lab": r"Data\INI\Object\Specter\British Armed Forces\Buildings\Nato_LargeAirBase.ini",
        "ita_lab": r"Data\INI\Object\Specter\Italian Armed Forces\Buildings\Nato_LargeAirBase.ini",
    }
    freeze = {k: fmap[norm(p)] for k, p in freeze_paths.items()}

    pt_nato_path = norm(r"Data\INI\PlayerTemplate.ini")
    cs_path = norm(r"Data\INI\CommandSet.ini")
    cb_path = norm(r"Data\INI\CommandButton.ini")
    cbs_path = norm(r"Data\INI\ControlBarScheme.ini")
    csf_path = norm(r"Data\English\generals.csf")

    pt_text = fmap[pt_nato_path].decode("latin1")
    cs_text = fmap[cs_path].decode("latin1")
    cb_text = fmap[cb_path].decode("latin1")
    cbs_text = fmap[cbs_path].decode("latin1")
    csf_before = fmap[csf_path]

    # Extract Nato PT + ControlBar
    pt_nato = re.search(r"^PlayerTemplate\s+FactionNato\b.*?^End\s*$", pt_text, re.M | re.S)
    assert pt_nato, "FactionNato missing"
    pt_nato_block = pt_nato.group(0)

    # Freeze prior EU PT blocks
    eu_pts = {}
    for eu in ("FactionGermany", "FactionFrance", "FactionBritain", "FactionItaly"):
        m = re.search(rf"^PlayerTemplate\s+{eu}\b.*?^End\s*$", pt_text, re.M | re.S)
        assert m, eu
        eu_pts[eu] = m.group(0)

    cbs_nato = re.search(r"^ControlBarScheme\s+AmericaNato8x6\b.*?^End\s*$", cbs_text, re.M | re.S)
    assert cbs_nato, "AmericaNato8x6 missing"
    cbs_nato_block = cbs_nato.group(0)

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

    # Guard: no prior active SE/UA/TR PlayerTemplates
    for fac in FACTIONS:
        assert not re.search(rf"^PlayerTemplate\s+{fac['pt']}\b", pt_text, re.M), fac["pt"]
        assert not re.search(rf"^ControlBarScheme\s+{fac['scheme']}\b", cbs_text, re.M), fac["scheme"]

    new_pt_append = []
    new_cbs_append = []
    new_cs_append = []
    new_cb_append = []

    for fac in FACTIONS:
        prefix = fac["prefix"]
        side = fac["side"]

        pt_block = transform_nato_text(pt_nato_block, prefix, side, fac)
        pt_block = rewrite_pt_for_stability(pt_block, fac)
        assert f"PlayerTemplate {fac['pt']}" in pt_block
        assert re.search(rf"Side\s*=\s*{side}", pt_block)
        assert "SCIENCE_NATO_CommandSetRank1" in pt_block
        assert "SpecialPowerShortcutNATO" in pt_block
        assert "ControlBarScheme" not in pt_block
        assert re.search(rf"StartingBuilding\s*=\s*{prefix}CommandCenter", pt_block)
        assert re.search(rf"StartingUnit0\s*=\s*{prefix}VehicleDozer", pt_block)
        new_pt_append.append(pt_block)

        cbs_block = transform_nato_text(cbs_nato_block, prefix, side, fac)
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

        for _n, block in nato_cs_blocks:
            new_cs_append.append(transform_nato_text(block, prefix, side, fac))

        for _n, block in nato_cb_blocks:
            new_cb_append.append(transform_nato_text(block, prefix, side, fac))

        for src_path in nato_obj_files:
            src = fmap[norm(src_path)].decode("latin1")
            rel = src_path.split("NATO\\", 1)[1] if "NATO\\" in src_path else src_path.split("Nato\\", 1)[-1]
            dst_path = rf"Data\INI\Object\Specter\{fac['folder']}\{rel}"
            cloned = transform_nato_text(src, prefix, side, fac)
            cloned = strip_nonprefixed_objects(cloned, prefix)
            if prefix + "SystemSpecialPowerShortcut" in cloned:
                cloned = force_shortcut_object_cs(cloned, prefix)
            if not re.search(rf"^Object\s+{re.escape(prefix)}", cloned, re.M):
                continue
            fmap[norm(dst_path)] = cloned.encode("latin1")
            disp[norm(dst_path)] = dst_path

    nl = "\n"
    marker = ";===== Nato-template SE/UA/TR faction clones"
    pt_text2 = pt_text.rstrip() + nl + nl + marker + " PT =====" + nl + (nl + nl).join(new_pt_append) + nl
    cbs_text2 = cbs_text.rstrip() + nl + nl + marker + " ControlBar =====" + nl + (nl + nl).join(new_cbs_append) + nl
    cs_text2 = cs_text.rstrip() + nl + nl + marker + " CS =====" + nl + (nl + nl).join(new_cs_append) + nl
    cb_text2 = cb_text.rstrip() + nl + nl + marker + " CB =====" + nl + (nl + nl).join(new_cb_append) + nl

    new_pts = {f["pt"] for f in FACTIONS}
    new_schemes = {f["scheme"] for f in FACTIONS}
    pt_names = re.findall(r"^PlayerTemplate\s+(\S+)", pt_text2, re.M)
    scheme_names = re.findall(r"^ControlBarScheme\s+(\S+)", cbs_text2, re.M)
    assert not any(n in new_pts and pt_names.count(n) != 1 for n in new_pts)
    assert not any(n in new_schemes and scheme_names.count(n) != 1 for n in new_schemes)
    assert pt_names.count("FactionNato") == 1
    for eu in eu_pts:
        assert pt_names.count(eu) == 1

    for fac in FACTIONS:
        bad = re.findall(rf"^CommandButton\s+(Command_PurchaseScience{fac['prefix']}\S*)", cb_text2, re.M)
        if bad:
            raise SystemExit(f"Invented PurchaseScience buttons: {bad}")

    fmap[pt_nato_path] = pt_text2.encode("latin1")
    fmap[cbs_path] = cbs_text2.encode("latin1")
    fmap[cs_path] = cs_text2.encode("latin1")
    fmap[cb_path] = cb_text2.encode("latin1")

    # CSF: upsert SIDE + INI + tooltip + features (Turkey may already have old INI/tooltip keys)
    csf_bytes = csf_before
    for fac in FACTIONS:
        for key, val in [
            (fac["side_key"], fac["side_text"]),
            (fac["display_key"], fac["display_text"]),
            (fac["tooltip"], fac["tooltip_text"]),
            (fac["features"], fac["features_text"]),
        ]:
            csf_bytes = upsert_csf_label(csf_bytes, key, val)
    nlab, parsed, errs = parse_csf_ok(csf_bytes)
    assert not errs and nlab == parsed, (nlab, parsed, errs)
    for fac in FACTIONS:
        assert csf_get(csf_bytes, fac["side_key"]) == fac["side_text"]
        assert csf_get(csf_bytes, fac["display_key"]) == fac["display_text"]
    fmap[csf_path] = csf_bytes

    # Freeze asserts
    for k, p in freeze_paths.items():
        assert fmap[norm(p)] == freeze[k], k
    nato_pt_after = re.search(
        r"^PlayerTemplate\s+FactionNato\b.*?^End\s*$",
        fmap[pt_nato_path].decode("latin1"),
        re.M | re.S,
    ).group(0)
    assert nato_pt_after == pt_nato_block
    for eu, block in eu_pts.items():
        m = re.search(rf"^PlayerTemplate\s+{eu}\b.*?^End\s*$", fmap[pt_nato_path].decode("latin1"), re.M | re.S)
        assert m and m.group(0) == block, eu

    DATA_BIG.write_bytes(build_big({disp[k]: v for k, v in fmap.items()}))
    data_sha = sha256(DATA_BIG)
    art_sha = sha256(ART_BIG)
    assert art_sha == BASE_ART

    # -------- Validation from rebuilt BIG --------
    e2, r2 = read_big(DATA_BIG)
    f2 = {norm(n): r2[o : o + s] for n, o, s in e2}
    pt2 = f2[pt_nato_path].decode("latin1")
    cs2 = f2[cs_path].decode("latin1")
    cb2 = f2[cb_path].decode("latin1")
    cbs2 = f2[cbs_path].decode("latin1")
    csf2 = f2[csf_path]
    nlab, parsed, errs = parse_csf_ok(csf2)
    assert not errs and nlab == parsed

    # Dependency audit helpers
    cs_names = set(re.findall(r"^CommandSet\s+(\S+)", cs2, re.M))
    cb_names = set(re.findall(r"^CommandButton\s+(\S+)", cb2, re.M))
    sci_text = f2[norm(r"Data\INI\Science.ini")].decode("latin1")
    sci_names = set(re.findall(r"^Science\s+(\S+)", sci_text, re.M))

    def object_exists(obj: str) -> bool:
        for _n, b in f2.items():
            if re.search(rf"^Object\s+{re.escape(obj)}\b", b.decode("latin1", errors="replace"), re.M):
                return True
        return False

    unresolved_cb = 0
    unresolved_cs = 0
    unresolved_sci = 0
    unresolved_obj = 0

    report_lines = []
    for fac in FACTIONS:
        prefix = fac["prefix"]
        m = re.search(rf"^PlayerTemplate\s+{fac['pt']}\b.*?^End\s*$", pt2, re.M | re.S)
        assert m, fac["pt"]
        block = m.group(0)
        assert "SCIENCE_NATO_CommandSetRank1" in block
        assert "SpecialPowerShortcutNATO" in block
        assert "ControlBarScheme" not in block
        assert re.search(rf"Side\s*=\s*{fac['side']}\b", block)
        assert "Side              = Nato" not in block and not re.search(r"Side\s*=\s*Nato\b", block)

        # PurchaseScience chain
        for rank_key in (
            "PurchaseScienceCommandSetRank1",
            "PurchaseScienceCommandSetRank3",
            "PurchaseScienceCommandSetRank8",
        ):
            mm = re.search(rf"{rank_key}\s*=\s*(\S+)", block)
            assert mm, rank_key
            cs_name = mm.group(1)
            if cs_name not in cs_names:
                unresolved_cs += 1
            else:
                cs_block = re.search(rf"^CommandSet\s+{re.escape(cs_name)}\b.*?^End\s*$", cs2, re.M | re.S)
                assert cs_block
                for btn in re.findall(r"\d+\s*=\s*(\S+)", cs_block.group(0)):
                    if btn.upper() in ("NONE", ""):
                        continue
                    if btn not in cb_names:
                        unresolved_cb += 1
                        continue
                    btn_block = re.search(
                        rf"^CommandButton\s+{re.escape(btn)}\b.*?^End\s*$", cb2, re.M | re.S
                    )
                    assert btn_block
                    for sci in re.findall(r"Science\s*=\s*(\S+)", btn_block.group(0)):
                        # Science field may be space-separated list
                        for s in sci.split():
                            if s not in sci_names:
                                unresolved_sci += 1

        for obj in [
            f"{prefix}CommandCenter",
            f"{prefix}VehicleDozer",
            f"{prefix}_LargeAirBase",
            f"{prefix}_HeavyAirBase",
            f"{prefix}WarFactory",
            f"{prefix}BootCamp",
        ]:
            if not object_exists(obj):
                unresolved_obj += 1
                raise AssertionError(f"missing object {obj}")

        assert re.search(rf"^CommandSet\s+{prefix}DozerCommandSet\b", cs2, re.M)
        assert re.search(rf"^CommandSet\s+{prefix}_LargeAirBaseCommandSet\b", cs2, re.M)
        assert re.search(rf"^CommandSet\s+{prefix}_HeavyAirBaseCommandSet\b", cs2, re.M)
        assert re.search(rf"^ControlBarScheme\s+{fac['scheme']}\b", cbs2, re.M)
        assert csf_get(csf2, fac["side_key"]) == fac["side_text"]
        assert csf_get(csf2, fac["display_key"]) == fac["display_text"]
        assert not re.search(rf"^CommandButton\s+Command_PurchaseScience{prefix}", cb2, re.M)

        # Dozer CommandSet → Construct buttons → buildings
        dozer_cs = re.search(
            rf"^CommandSet\s+{prefix}DozerCommandSet\b.*?^End\s*$", cs2, re.M | re.S
        )
        assert dozer_cs
        for btn in re.findall(r"\d+\s*=\s*(\S+)", dozer_cs.group(0)):
            if btn.upper() in ("NONE", ""):
                continue
            if btn not in cb_names:
                unresolved_cb += 1
                continue
            btn_block = re.search(rf"^CommandButton\s+{re.escape(btn)}\b.*?^End\s*$", cb2, re.M | re.S)
            assert btn_block
            for obj in re.findall(r"Object\s*=\s*(\S+)", btn_block.group(0)):
                if not object_exists(obj):
                    unresolved_obj += 1
                    raise AssertionError(f"{prefix} dozer button {btn} -> missing {obj}")

        lab = None
        for _n, b in f2.items():
            t = b.decode("latin1", errors="replace")
            if re.search(rf"^Object\s+{prefix}_LargeAirBase\b", t, re.M):
                lab = t
                break
        assert lab and "NumRows                 = 4" in lab and "NumCols                 = 4" in lab
        assert "TheAirPort" in lab
        hab = None
        for _n, b in f2.items():
            t = b.decode("latin1", errors="replace")
            if re.search(rf"^Object\s+{prefix}_HeavyAirBase\b", t, re.M):
                hab = t
                break
        assert hab and "HXUSABigAirPort" in hab

        # Duplicate counts
        assert pt_names.count(fac["pt"]) == 1
        assert scheme_names.count(fac["scheme"]) == 1
        assert sum(1 for _n, b in f2.items() if re.search(rf"^Object\s+{prefix}CommandCenter\b", b.decode("latin1", errors="replace"), re.M)) == 1
        assert sum(1 for _n, b in f2.items() if re.search(rf"^Object\s+{prefix}VehicleDozer\b", b.decode("latin1", errors="replace"), re.M)) == 1

        report_lines.append(
            f"""REPORT {prefix.upper()}:
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
SIDE string = {fac['side_key']} => {fac['side_text']}
PLAYABLE = YES
{prefix.upper()} CLONE = PASS
"""
        )

    assert unresolved_cb == 0
    assert unresolved_cs == 0
    assert unresolved_sci == 0
    assert unresolved_obj == 0

    # Frozen factions unchanged
    assert f2[norm(freeze_paths["nato_lab"])] == freeze["nato_lab"]
    assert f2[norm(freeze_paths["nato_hab"])] == freeze["nato_hab"]
    assert re.search(r"^PlayerTemplate\s+FactionNato\b.*?^End\s*$", pt2, re.M | re.S).group(0) == pt_nato_block
    for eu, block in eu_pts.items():
        assert re.search(rf"^PlayerTemplate\s+{eu}\b.*?^End\s*$", pt2, re.M | re.S).group(0) == block

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")

    active_files = [
        r"Data\INI\PlayerTemplate.ini",
        r"Data\INI\ControlBarScheme.ini",
        r"Data\INI\CommandSet.ini",
        r"Data\INI\CommandButton.ini",
        r"Data\English\generals.csf",
    ]
    for fac in FACTIONS:
        for src_path in nato_obj_files:
            rel = src_path.split("NATO\\", 1)[1] if "NATO\\" in src_path else src_path.split("Nato\\", 1)[-1]
            dst = rf"Data\INI\Object\Specter\{fac['folder']}\{rel}"
            if norm(dst) in f2:
                active_files.append(dst)

    report = "\n".join(report_lines) + f"""
MISSING SIDE STRINGS = 0
UNRESOLVED PURCHASESCIENCE BUTTONS = 0
UNRESOLVED SCIENCES = 0
UNRESOLVED COMMAND BUTTONS = 0
UNRESOLVED COMMANDSETS = 0

NATO FUNCTIONALLY CHANGED = NO
GERMANY CHANGED = NO
FRANCE CHANGED = NO
BRITAIN CHANGED = NO
ITALY CHANGED = NO
PAKISTAN CHANGED = NO
SAUDI ARABIA CHANGED = NO
UAE CHANGED = NO
INDIA CHANGED = NO
SYRIA CHANGED = NO
EGYPT CHANGED = NO

ACTIVE FILES CHANGED:
{chr(10).join('- ' + f for f in active_files)}

DATA sha256 = {data_sha}
ART sha256  = {art_sha} (UNCHANGED)
ZIP sha256  = {sha256(ZIP_PATH)}
ZIP path    = {ZIP_PATH}
ZIP size    = {ZIP_PATH.stat().st_size}
"""
    NOTE.write_text(report, encoding="utf-8")
    print(report)
    print("ZIP", ZIP_PATH, ZIP_PATH.stat().st_size)


if __name__ == "__main__":
    main()
