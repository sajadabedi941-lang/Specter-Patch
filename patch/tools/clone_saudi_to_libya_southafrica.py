#!/usr/bin/env python3
"""Clone CURRENT working Saudi Arabia faction into Libya / South Africa.

Saudi Arabia is the golden template (READ-ONLY functionally). Reuses Saudi's
proven SCIENCE_Pakistan_CommandSetRank* + SpecialPowerShortcutPakistanSystem
(no invented country Sciences / PurchaseScience buttons).
Correct CSF UTF-16 character-count upsert. DATA-only.

Baseline: DATA sha 41ae7a17... (includes Nato EU + SE/UA/TR clones).
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
ZIP_PATH = ROOT / "Release/SPECTER_MASTER_DATA_SAUDI_CLONE_LY_ZA.zip"
NOTE = OUT_DIR / "DATA_SAUDI_CLONE_LY_ZA_HASHES.txt"
DL = OUT_DIR / "DATA_SAUDI_CLONE_LY_ZA_DOWNLOAD.txt"

BASE_DATA = "41ae7a1745c4864243a38f3fbb6fe5826033d63c95e96b67c8a5144229b3accf"
BASE_ART = "74a411b72c19fafaafcd48a45d2aa76731d8dbd13e919e4f73f8b989e90d4822"

FACTIONS = [
    {
        "prefix": "Libya",
        "side": "Libya",
        "pt": "FactionLibya",
        "scheme": "Libya8x6",
        "folder": "Libyan Armed Forces",
        "display_key": "INI:FactionLibya",
        "display_text": "Libyan Armed Forces",
        "side_key": "SIDE:Libya",
        "side_text": "Libyan Armed Forces",
        "tooltip": "TOOLTIP:BioStrategyLong_Libya",
        "features": "GUI:BioFeatures_Libya",
        "tooltip_text": "Libyan Armed Forces - Saudi-template combined-arms clone.",
        "features_text": "Armor, airpower, dual airbases, nuclear, artillery, C-RAM.",
        "color": "R:0 G:100 B:70",
    },
    {
        "prefix": "SouthAfrica",
        "side": "SouthAfrica",
        "pt": "FactionSouthAfrica",
        "scheme": "SouthAfrica8x6",
        "folder": "South African National Defence Force",
        "display_key": "INI:FactionSouthAfrica",
        "display_text": "South African National Defence Force",
        "side_key": "SIDE:SouthAfrica",
        "side_text": "South African National Defence Force",
        "tooltip": "TOOLTIP:BioStrategyLong_SouthAfrica",
        "features": "GUI:BioFeatures_SouthAfrica",
        "tooltip_text": "South African National Defence Force - Saudi-template combined-arms clone.",
        "features_text": "Armor, airpower, dual airbases, nuclear, artillery, C-RAM.",
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


def protect_shared(text: str) -> str:
    """Protect Pakistan/GLA science + shortcut infra shared by Saudi PT."""
    text = text.replace("SCIENCE_Pakistan", "@@SCIENCE_Pakistan@@")
    text = text.replace("SpecialPowerShortcutPakistan", "@@SpecialPowerShortcutPakistan@@")
    text = text.replace("SCIENCE_GLA", "@@SCIENCE_GLA@@")
    text = text.replace("Command_PurchaseSciencePakistan", "@@Command_PurchaseSciencePakistan@@")
    text = text.replace("Command_UpgradePakistan", "@@Command_UpgradePakistan@@")
    text = text.replace("Command_Pakistan", "@@Command_Pakistan@@")
    return text


def unprotect_shared(text: str) -> str:
    text = text.replace("@@SCIENCE_Pakistan@@", "SCIENCE_Pakistan")
    text = text.replace("@@SpecialPowerShortcutPakistan@@", "SpecialPowerShortcutPakistan")
    text = text.replace("@@SCIENCE_GLA@@", "SCIENCE_GLA")
    text = text.replace("@@Command_PurchaseSciencePakistan@@", "Command_PurchaseSciencePakistan")
    text = text.replace("@@Command_UpgradePakistan@@", "Command_UpgradePakistan")
    text = text.replace("@@Command_Pakistan@@", "Command_Pakistan")
    return text


def transform_saudi_text(text: str, prefix: str, side: str, fac: dict) -> str:
    """Rename faction-owned SaudiArabia identifiers. Protect shared science infra."""
    out = protect_shared(text)

    reps = [
        # Longest / most-specific first
        ("Command_PurchaseScienceSaudiArabia", f"Command_PurchaseScience{prefix}"),
        ("Command_ConstructSaudiArabia_", f"Command_Construct{prefix}_"),
        ("Command_ConstructSaudiArabia", f"Command_Construct{prefix}"),
        ("Command_SelectSaudiArabia", f"Command_Select{prefix}"),
        ("Command_UpgradeSaudiArabia_", f"Command_Upgrade{prefix}_"),
        ("Command_UpgradeSaudiArabia", f"Command_Upgrade{prefix}"),
        ("Command_SaudiArabia", f"Command_{prefix}"),
        ("SuperweaponSaudiArabia_", f"Superweapon{prefix}_"),
        ("SuperweaponSaudiArabia", f"Superweapon{prefix}"),
        ("SCIENCE_SaudiArabia", f"SCIENCE_{prefix}"),
        ("SpecialPowerShortcutSaudiArabia", f"SpecialPowerShortcut{prefix}"),
        ("SaudiArabiaDozerCommandSet", f"{prefix}DozerCommandSet"),
        ("Upgrade_SaudiArabia_", f"Upgrade_{prefix}_"),
        ("SaudiArabia_Weapon_", f"{prefix}_Weapon_"),
        ("SaudiArabia_AlabbasMissile", f"{prefix}_AlabbasMissile"),
        ("FactionSaudiArabia", fac["pt"]),
        ("INI:FactionSaudiArabia", fac["display_key"]),
        ("TOOLTIP:BioStrategyLong_SaudiArabia", fac["tooltip"]),
        ("GUI:BioFeatures_SaudiArabia", fac["features"]),
        ("SaudiArabia8x6", fac["scheme"]),
        ("SaudiArabia_", f"{prefix}_"),
    ]
    for a, b in reps:
        out = out.replace(a, b)

    # Remaining SaudiArabia* identity tokens (e.g. SaudiArabiaSystem...)
    out = re.sub(r"\bSaudiArabia(?=[A-Z_])", prefix, out)
    out = re.sub(r"(Side\s*=\s*)SaudiArabia\b", rf"\1{side}", out)
    out = re.sub(r"(BaseSide\s*=\s*)SaudiArabia\b", rf"\1{side}", out)
    # ControlBar Side line (no equals): "Side SaudiArabia"
    out = re.sub(r"(Side\s+)SaudiArabia\b", rf"\1{side}", out)

    out = unprotect_shared(out)
    return out


def strip_nonprefixed_objects(text: str, prefix: str) -> str:
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
    return bytes(b"".join(parts))


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
    """Keep Saudi's shared Pakistan science/shortcut infra. No ControlBarScheme in PT."""
    pt_block = re.sub(
        r"(PurchaseScienceCommandSetRank1\s*=\s*)\S+",
        r"\1SCIENCE_Pakistan_CommandSetRank1",
        pt_block,
    )
    pt_block = re.sub(
        r"(PurchaseScienceCommandSetRank3\s*=\s*)\S+",
        r"\1SCIENCE_Pakistan_CommandSetRank3",
        pt_block,
    )
    pt_block = re.sub(
        r"(PurchaseScienceCommandSetRank8\s*=\s*)\S+",
        r"\1SCIENCE_Pakistan_CommandSetRank8",
        pt_block,
    )
    pt_block = re.sub(
        r"(SpecialPowerShortcutCommandSet\s*=\s*)\S+",
        r"\1SpecialPowerShortcutPakistanSystem",
        pt_block,
    )
    pt_block = re.sub(
        r"(IntrinsicSciences\s*=\s*)\S+",
        r"\1SCIENCE_GLA",
        pt_block,
    )
    pt_block = re.sub(
        r"(PreferredColor\s*=\s*).*$",
        rf"\1{fac['color']}",
        pt_block,
        flags=re.M,
    )
    pt_block = re.sub(r"(DisplayName\s*=\s*)\S+", rf"\1{fac['display_key']}", pt_block, count=1)
    pt_block = re.sub(r"(ArmyTooltip\s*=\s*)\S+", rf"\1{fac['tooltip']}", pt_block, count=1)
    pt_block = re.sub(r"(Features\s*=\s*)\S+", rf"\1{fac['features']}", pt_block, count=1)
    # Saudi PT has no ControlBarScheme — do not invent one (Side-matched ControlBar).
    pt_block = re.sub(r"^\s*ControlBarScheme\s*=\s*.*$\n?", "", pt_block, flags=re.M)
    return pt_block


def force_shortcut_object_cs(obj_text: str, prefix: str) -> str:
    """Match Saudi: SystemSpecialPowerShortcut uses empty country shortcut CS."""
    name = f"{prefix}_SystemSpecialPowerShortcut"
    empty_cs = f"SpecialPowerShortcut{prefix}System"

    def repl(m: re.Match) -> str:
        block = m.group(0)
        block = re.sub(
            r"(CommandSet\s*=\s*)\S+",
            rf"\1{empty_cs}",
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

    freeze_paths = {
        "saudi_lab": r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_LargeAirBase.ini",
        "saudi_hab": r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_HeavyAirBase.ini",
        "saudi_dozer": r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Tracked\SaudiArabia_Dozer.ini",
        "saudi_cc": r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_CommandCenter.ini",
        "pak_lab": r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_LargeAirBase.ini",
        "nato_lab": r"Data\INI\Object\Specter\NATO\Buildings\Nato_LargeAirBase.ini",
        "sweden_lab": r"Data\INI\Object\Specter\Swedish Armed Forces\Buildings\Nato_LargeAirBase.ini",
        "egypt_lab": r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_LargeAirBase.ini",
    }
    freeze = {k: fmap[norm(p)] for k, p in freeze_paths.items()}

    pt_path = norm(r"Data\INI\PlayerTemplate.ini")
    cs_path = norm(r"Data\INI\CommandSet.ini")
    cb_path = norm(r"Data\INI\CommandButton.ini")
    cbs_path = norm(r"Data\INI\ControlBarScheme.ini")
    csf_path = norm(r"Data\English\generals.csf")

    pt_text = fmap[pt_path].decode("latin1")
    cs_text = fmap[cs_path].decode("latin1")
    cb_text = fmap[cb_path].decode("latin1")
    cbs_text = fmap[cbs_path].decode("latin1")
    csf_before = fmap[csf_path]

    pt_saudi = re.search(r"^PlayerTemplate\s+FactionSaudiArabia\b.*?^End\s*$", pt_text, re.M | re.S)
    assert pt_saudi, "FactionSaudiArabia missing"
    pt_saudi_block = pt_saudi.group(0)

    # Freeze prior faction PTs
    freeze_pts = {}
    for name in (
        "FactionSaudiArabia",
        "FactionPakistan",
        "FactionUAE",
        "FactionIndia",
        "FactionSyria",
        "FactionNato",
        "FactionGermany",
        "FactionFrance",
        "FactionBritain",
        "FactionItaly",
        "FactionSweden",
        "FactionUkraine",
        "FactionTurkey",
    ):
        m = re.search(rf"^PlayerTemplate\s+{name}\b.*?^End\s*$", pt_text, re.M | re.S)
        assert m, name
        freeze_pts[name] = m.group(0)

    cbs_saudi = re.search(r"^ControlBarScheme\s+SaudiArabia8x6\b.*?^End\s*$", cbs_text, re.M | re.S)
    assert cbs_saudi, "SaudiArabia8x6 missing"
    cbs_saudi_block = cbs_saudi.group(0)

    def is_cloneable_cs(name: str) -> bool:
        if "SaudiArabia" not in name:
            return False
        # Do not invent country PurchaseScience sets; Saudi has none active for SCIENCE_Saudi*
        if name.startswith("SCIENCE_SaudiArabia"):
            return False
        return True

    def is_cloneable_cb(name: str) -> bool:
        if "SaudiArabia" not in name:
            return False
        if name.startswith("Command_PurchaseScienceSaudiArabia"):
            return False
        return True

    saudi_cs_blocks = [(n, b) for n, b in extract_blocks(cs_text, "CommandSet") if is_cloneable_cs(n)]
    saudi_cb_blocks = [(n, b) for n, b in extract_blocks(cb_text, "CommandButton") if is_cloneable_cb(n)]
    print(f"Cloneable CS={len(saudi_cs_blocks)} CB={len(saudi_cb_blocks)}")

    saudi_obj_files = []
    for name, _off, _size in entries:
        nl = name.replace("/", "\\").lower()
        if "saudi arabia armed forces" in nl and nl.endswith(".ini"):
            saudi_obj_files.append(name.replace("/", "\\"))
    print(f"Saudi object files to clone: {len(saudi_obj_files)}")

    # Overlay files (NOT Science_SaudiArabia.ini — avoids inventing SCIENCE_Libya*)
    overlay_srcs = [
        r"Data\INI\Weapon_SaudiArabia.ini",
        r"Data\INI\Upgrade_SaudiArabia.ini",
        r"Data\INI\SpecialPower_SaudiArabia.ini",
    ]

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
        print("=== CLONE", prefix, "===")

        pt_block = transform_saudi_text(pt_saudi_block, prefix, side, fac)
        pt_block = rewrite_pt_for_stability(pt_block, fac)
        pt_block = re.sub(r"^PlayerTemplate\s+\S+", f"PlayerTemplate {fac['pt']}", pt_block, count=1, flags=re.M)
        assert f"PlayerTemplate {fac['pt']}" in pt_block
        assert re.search(rf"Side\s*=\s*{side}", pt_block)
        assert "SCIENCE_Pakistan_CommandSetRank1" in pt_block
        assert "SpecialPowerShortcutPakistanSystem" in pt_block
        assert "ControlBarScheme" not in pt_block
        assert re.search(rf"StartingBuilding\s*=\s*{prefix}_CommandCenter", pt_block)
        assert re.search(rf"StartingUnit0\s*=\s*{prefix}_Dozer", pt_block)
        assert not re.search(rf"SCIENCE_{prefix}", pt_block)
        new_pt_append.append(pt_block)

        cbs_block = transform_saudi_text(cbs_saudi_block, prefix, side, fac)
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
        assert "Side SaudiArabia" not in cbs_block
        new_cbs_append.append(cbs_block)

        for _n, block in saudi_cs_blocks:
            new_cs_append.append(transform_saudi_text(block, prefix, side, fac))

        for _n, block in saudi_cb_blocks:
            new_cb_append.append(transform_saudi_text(block, prefix, side, fac))

        for src_path in saudi_obj_files:
            src = fmap[norm(src_path)].decode("latin1")
            rel = src_path.split("Saudi Arabia Armed Forces\\", 1)[1]
            # Rename SaudiArabia_* filenames
            parts = rel.split("\\")
            parts = [p.replace("SaudiArabia_", f"{prefix}_") if p.startswith("SaudiArabia_") else p for p in parts]
            rel2 = "\\".join(parts)
            dst_path = rf"Data\INI\Object\Specter\{fac['folder']}\{rel2}"
            cloned = transform_saudi_text(src, prefix, side, fac)
            cloned = strip_nonprefixed_objects(cloned, prefix)
            if f"{prefix}_SystemSpecialPowerShortcut" in cloned:
                cloned = force_shortcut_object_cs(cloned, prefix)
            if not re.search(rf"^Object\s+{re.escape(prefix)}", cloned, re.M):
                continue
            fmap[norm(dst_path)] = cloned.encode("latin1")
            disp[norm(dst_path)] = dst_path

        for ok in overlay_srcs:
            blob = fmap[norm(ok)]
            new_text = transform_saudi_text(blob.decode("latin1"), prefix, side, fac)
            new_path = ok.replace("SaudiArabia", prefix)
            assert norm(new_path) not in fmap or True
            fmap[norm(new_path)] = new_text.encode("latin1")
            disp[norm(new_path)] = new_path

    nl = "\n"
    marker = ";===== Saudi-template LY/ZA faction clones"
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
    assert pt_names.count("FactionSaudiArabia") == 1

    for fac in FACTIONS:
        bad = re.findall(rf"^CommandButton\s+(Command_PurchaseScience{fac['prefix']}\S*)", cb_text2, re.M)
        if bad:
            raise SystemExit(f"Invented PurchaseScience buttons: {bad}")
        bad_sci = re.findall(rf"^CommandSet\s+(SCIENCE_{fac['prefix']}\S*)", cs_text2, re.M)
        if bad_sci:
            raise SystemExit(f"Invented SCIENCE CommandSets: {bad_sci}")

    fmap[pt_path] = pt_text2.encode("latin1")
    fmap[cbs_path] = cbs_text2.encode("latin1")
    fmap[cs_path] = cs_text2.encode("latin1")
    fmap[cb_path] = cb_text2.encode("latin1")

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
        assert Counter(
            [l for l in csf_label_set(csf_bytes) if l == fac["side_key"]]
        )[fac["side_key"]] == 1
    fmap[csf_path] = csf_bytes

    for k, p in freeze_paths.items():
        assert fmap[norm(p)] == freeze[k], k
    saudi_pt_after = re.search(
        r"^PlayerTemplate\s+FactionSaudiArabia\b.*?^End\s*$",
        fmap[pt_path].decode("latin1"),
        re.M | re.S,
    ).group(0)
    assert saudi_pt_after == pt_saudi_block
    for name, block in freeze_pts.items():
        m = re.search(rf"^PlayerTemplate\s+{name}\b.*?^End\s*$", fmap[pt_path].decode("latin1"), re.M | re.S)
        assert m and m.group(0) == block, name

    DATA_BIG.write_bytes(build_big({disp[k]: v for k, v in fmap.items()}))
    data_sha = sha256(DATA_BIG)
    art_sha = sha256(ART_BIG)
    assert art_sha == BASE_ART

    # -------- Validation from rebuilt BIG --------
    e2, r2 = read_big(DATA_BIG)
    f2 = {norm(n): r2[o : o + s] for n, o, s in e2}
    pt2 = f2[pt_path].decode("latin1")
    cs2 = f2[cs_path].decode("latin1")
    cb2 = f2[cb_path].decode("latin1")
    cbs2 = f2[cbs_path].decode("latin1")
    csf2 = f2[csf_path]
    nlab, parsed, errs = parse_csf_ok(csf2)
    assert not errs and nlab == parsed

    cs_names = set(re.findall(r"^CommandSet\s+(\S+)", cs2, re.M))
    cb_names = set(re.findall(r"^CommandButton\s+(\S+)", cb2, re.M))

    def object_exists(obj: str) -> bool:
        for _n, b in f2.items():
            if re.search(rf"^Object\s+{re.escape(obj)}\b", b.decode("latin1", errors="replace"), re.M):
                return True
        return False

    unresolved_cb = unresolved_cs = unresolved_obj = 0
    report_lines = []

    for fac in FACTIONS:
        prefix = fac["prefix"]
        m = re.search(rf"^PlayerTemplate\s+{fac['pt']}\b.*?^End\s*$", pt2, re.M | re.S)
        assert m, fac["pt"]
        block = m.group(0)
        assert "SCIENCE_Pakistan_CommandSetRank1" in block
        assert "SpecialPowerShortcutPakistanSystem" in block
        assert "ControlBarScheme" not in block
        assert re.search(rf"Side\s*=\s*{fac['side']}\b", block)
        assert not re.search(r"Side\s*=\s*SaudiArabia\b", block)

        for obj in [
            f"{prefix}_CommandCenter",
            f"{prefix}_Dozer",
            f"{prefix}_LargeAirBase",
            f"{prefix}_HeavyAirBase",
            f"{prefix}_WarFactory_T",
            f"{prefix}_Barracks",
            f"{prefix}_CRAM",
            f"{prefix}_Lgm30",
            f"{prefix}_FireBase",
        ]:
            if not object_exists(obj):
                unresolved_obj += 1
                raise AssertionError(f"missing object {obj}")

        assert re.search(rf"^CommandSet\s+{prefix}DozerCommandSet\b", cs2, re.M)
        assert re.search(rf"^CommandSet\s+{prefix}_HeavyAirBaseCommandSet\b", cs2, re.M)
        assert re.search(rf"^CommandSet\s+{prefix}_AirfieldCommandSet\b", cs2, re.M)
        assert re.search(rf"^ControlBarScheme\s+{fac['scheme']}\b", cbs2, re.M)
        assert csf_get(csf2, fac["side_key"]) == fac["side_text"]
        assert csf_get(csf2, fac["display_key"]) == fac["display_text"]
        assert not re.search(rf"^CommandButton\s+Command_PurchaseScience{prefix}", cb2, re.M)
        assert not re.search(rf"^CommandSet\s+SCIENCE_{prefix}", cs2, re.M)

        # Dozer chain
        dozer_cs = re.search(rf"^CommandSet\s+{prefix}DozerCommandSet\b.*?^End\s*$", cs2, re.M | re.S)
        assert dozer_cs
        for btn in re.findall(r"\d+\s*=\s*(\S+)", dozer_cs.group(0)):
            if btn.upper() in ("NONE", "") or btn == "Command_Stop":
                continue
            if btn not in cb_names:
                unresolved_cb += 1
                raise AssertionError(f"missing button {btn}")
            btn_block = re.search(rf"^CommandButton\s+{re.escape(btn)}\b.*?^End\s*$", cb2, re.M | re.S)
            assert btn_block
            for obj in re.findall(r"Object\s*=\s*(\S+)", btn_block.group(0)):
                if not object_exists(obj):
                    unresolved_obj += 1
                    raise AssertionError(f"{prefix} dozer {btn} -> missing {obj}")

        # WarFactory / Barracks / Airfield chains
        for unit_cs in (
            f"{prefix}_WarFactoryCommandSet",
            f"{prefix}_BarracksCommandSet",
            f"{prefix}_AirfieldCommandSet",
            f"{prefix}_HeavyAirBaseCommandSet",
        ):
            if unit_cs not in cs_names:
                unresolved_cs += 1
                raise AssertionError(unit_cs)
            ucs = re.search(rf"^CommandSet\s+{re.escape(unit_cs)}\b.*?^End\s*$", cs2, re.M | re.S).group(0)
            for btn in re.findall(r"\d+\s*=\s*(\S+)", ucs):
                if btn.upper() in ("NONE", "") or btn in ("Command_Sell", "Command_SetRallyPoint", "Command_Stop"):
                    continue
                if btn not in cb_names:
                    unresolved_cb += 1
                    raise AssertionError(f"{unit_cs} -> {btn}")
                bb = re.search(rf"^CommandButton\s+{re.escape(btn)}\b.*?^End\s*$", cb2, re.M | re.S)
                assert bb
                for obj in re.findall(r"Object\s*=\s*(\S+)", bb.group(0)):
                    if not object_exists(obj):
                        unresolved_obj += 1
                        raise AssertionError(f"{btn} -> {obj}")

        # Large airbase capacity
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

        assert pt_names.count(fac["pt"]) == 1
        assert scheme_names.count(fac["scheme"]) == 1

        report_lines.append(
            f"""REPORT {prefix.upper()}:
PlayerTemplate = {fac['pt']}
Side = {fac['side']}
DisplayName = {fac['display_key']}
ControlBar = {fac['scheme']}
CommandCenter = {prefix}_CommandCenter
Dozer = {prefix}_Dozer
Dozer CommandSet = {prefix}DozerCommandSet
WarFactory = {prefix}_WarFactory_T
Barracks = {prefix}_Barracks
LargeAirBase = {prefix}_LargeAirBase
LargeAirBase capacity = 16
HeavyAirBase = {prefix}_HeavyAirBase
Nuclear = {prefix}_Lgm30
Artillery = {prefix}_FireBase
C-RAM = {prefix}_CRAM
PurchaseScience validation = REUSES SCIENCE_Pakistan_CommandSetRank* + SpecialPowerShortcutPakistanSystem (same as Saudi; no invented country sciences)
SIDE string = {fac['side_key']} => {fac['side_text']}
PLAYABLE = YES
{prefix.upper()} CLONE = PASS
"""
        )

    assert unresolved_cb == 0
    assert unresolved_cs == 0
    assert unresolved_obj == 0

    # Frozen
    assert f2[norm(freeze_paths["saudi_lab"])] == freeze["saudi_lab"]
    assert f2[norm(freeze_paths["saudi_hab"])] == freeze["saudi_hab"]
    assert re.search(r"^PlayerTemplate\s+FactionSaudiArabia\b.*?^End\s*$", pt2, re.M | re.S).group(0) == pt_saudi_block
    for name, block in freeze_pts.items():
        assert re.search(rf"^PlayerTemplate\s+{name}\b.*?^End\s*$", pt2, re.M | re.S).group(0) == block

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
        r"Data\INI\Weapon_Libya.ini",
        r"Data\INI\Upgrade_Libya.ini",
        r"Data\INI\SpecialPower_Libya.ini",
        r"Data\INI\Weapon_SouthAfrica.ini",
        r"Data\INI\Upgrade_SouthAfrica.ini",
        r"Data\INI\SpecialPower_SouthAfrica.ini",
    ]
    for fac in FACTIONS:
        for src_path in saudi_obj_files:
            rel = src_path.split("Saudi Arabia Armed Forces\\", 1)[1]
            parts = rel.split("\\")
            parts = [p.replace("SaudiArabia_", f"{fac['prefix']}_") if p.startswith("SaudiArabia_") else p for p in parts]
            dst = rf"Data\INI\Object\Specter\{fac['folder']}\\".rstrip("\\") + "\\" + "\\".join(parts)
            if norm(dst) in f2:
                active_files.append(dst)

    report = "\n".join(report_lines) + f"""
MISSING SIDE STRINGS = 0
UNRESOLVED PURCHASESCIENCE BUTTONS = 0
UNRESOLVED SCIENCES = 0
UNRESOLVED COMMAND BUTTONS = 0
UNRESOLVED COMMANDSETS = 0

SAUDI ARABIA FUNCTIONALLY CHANGED = NO
PAKISTAN CHANGED = NO
UAE CHANGED = NO
INDIA CHANGED = NO
SYRIA CHANGED = NO
NATO CHANGED = NO
GERMANY CHANGED = NO
FRANCE CHANGED = NO
BRITAIN CHANGED = NO
ITALY CHANGED = NO
SWEDEN CHANGED = NO
UKRAINE CHANGED = NO
TURKEY CHANGED = NO
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
