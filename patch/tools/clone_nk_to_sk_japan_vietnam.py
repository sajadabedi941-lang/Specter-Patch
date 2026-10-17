#!/usr/bin/env python3
"""Clone CURRENT working North Korea into South Korea / Japan / Vietnam.

North Korea is golden template (READ-ONLY). Reuses SCIENCE_NorthKorea_CommandSetRank*
+ SpecialPowerShortcutNorthKorea (no invented country Sciences).
Correct CSF UTF-16 char-count upsert. DATA-only.

Baseline: DATA sha b1a21d33... (NK dual airbases + HQ9/C-RAM palette).
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
ZIP_PATH = ROOT / "Release/SPECTER_MASTER_DATA_NK_CLONE_SK_JP_VN.zip"
NOTE = OUT_DIR / "DATA_NK_CLONE_SK_JP_VN_HASHES.txt"
DL = OUT_DIR / "DATA_NK_CLONE_SK_JP_VN_DOWNLOAD.txt"

BASE_DATA = "b1a21d339fe97721f34597bf83c2d2d55fae760a8019b0189a308baffdaf75e8"
BASE_ART = "74a411b72c19fafaafcd48a45d2aa76731d8dbd13e919e4f73f8b989e90d4822"

FACTIONS = [
    {
        "prefix": "SouthKorea",
        "side": "SouthKorea",
        "pt": "FactionSouthKorea",
        "scheme": "SouthKorea8x6",
        "folder": "South Korean Armed Forces",
        "display_key": "INI:FactionSouthKorea",
        "display_text": "Republic of Korea Armed Forces",
        "side_key": "SIDE:SouthKorea",
        "side_text": "Republic of Korea Armed Forces",
        "tooltip": "TOOLTIP:BioStrategyLong_SouthKorea",
        "features": "GUI:BioFeatures_SouthKorea",
        "tooltip_text": "Republic of Korea Armed Forces - NorthKorea-template combined-arms clone.",
        "features_text": "Armor, airpower, dual airbases, HQ-9 air defense, C-RAM.",
        "color": "R:0 G:50 B:160",
    },
    {
        "prefix": "Japan",
        "side": "Japan",
        "pt": "FactionJapan",
        "scheme": "Japan8x6",
        "folder": "Japan Self-Defense Forces",
        "display_key": "INI:FactionJapan",
        "display_text": "Japan Self-Defense Forces",
        "side_key": "SIDE:Japan",
        "side_text": "Japan Self-Defense Forces",
        "tooltip": "TOOLTIP:BioStrategyLong_Japan",
        "features": "GUI:BioFeatures_Japan",
        "tooltip_text": "Japan Self-Defense Forces - NorthKorea-template combined-arms clone.",
        "features_text": "Armor, airpower, dual airbases, HQ-9 air defense, C-RAM.",
        "color": "R:180 G:20 B:40",
    },
    {
        "prefix": "Vietnam",
        "side": "Vietnam",
        "pt": "FactionVietnam",
        "scheme": "Vietnam8x6",
        "folder": "Vietnam People's Armed Forces",
        "display_key": "INI:FactionVietnam",
        "display_text": "Vietnam People's Armed Forces",
        "side_key": "SIDE:Vietnam",
        "side_text": "Vietnam People's Armed Forces",
        "tooltip": "TOOLTIP:BioStrategyLong_Vietnam",
        "features": "GUI:BioFeatures_Vietnam",
        "tooltip_text": "Vietnam People's Armed Forces - NorthKorea-template combined-arms clone.",
        "features_text": "Armor, airpower, dual airbases, HQ-9 air defense, C-RAM.",
        "color": "R:200 G:160 B:0",
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
    """Protect NK science/shortcut infra and shared non-owned tokens."""
    reps = [
        ("SCIENCE_NorthKorea", "@@SCIENCE_NorthKorea@@"),
        ("SCIENCE_NK_", "@@SCIENCE_NK_@@"),
        ("SCIENCE_Iraq", "@@SCIENCE_Iraq@@"),
        ("SpecialPowerShortcutNorthKorea", "@@SpecialPowerShortcutNorthKorea@@"),
        ("Command_PurchaseScienceNK", "@@Command_PurchaseScienceNK@@"),
        ("Command_NK", "@@Command_NK@@"),
        ("Command_UpgradeAmericaCountermeasures", "@@Command_UpgradeAmericaCountermeasures@@"),
        ("Iraq_Barracks", "@@Iraq_Barracks@@"),
        ("ChinaVehicleHq9", "@@ChinaVehicleHq9@@"),
        ("China_Hq9", "@@China_Hq9@@"),
    ]
    for a, b in reps:
        text = text.replace(a, b)
    return text


def unprotect_shared(text: str) -> str:
    reps = [
        ("@@SCIENCE_NorthKorea@@", "SCIENCE_NorthKorea"),
        ("@@SCIENCE_NK_@@", "SCIENCE_NK_"),
        ("@@SCIENCE_Iraq@@", "SCIENCE_Iraq"),
        ("@@SpecialPowerShortcutNorthKorea@@", "SpecialPowerShortcutNorthKorea"),
        ("@@Command_PurchaseScienceNK@@", "Command_PurchaseScienceNK"),
        ("@@Command_NK@@", "Command_NK"),
        ("@@Command_UpgradeAmericaCountermeasures@@", "Command_UpgradeAmericaCountermeasures"),
        ("@@Iraq_Barracks@@", "Iraq_Barracks"),
        ("@@ChinaVehicleHq9@@", "ChinaVehicleHq9"),
        ("@@China_Hq9@@", "China_Hq9"),
    ]
    for a, b in reps:
        text = text.replace(a, b)
    return text


def transform_nk_text(text: str, prefix: str, side: str, fac: dict) -> str:
    out = protect_shared(text)
    reps = [
        ("Command_ConstructNKFinal_", f"Command_Construct{prefix}Final_"),
        ("Command_ConstructNorthKoreaReal_", f"Command_Construct{prefix}Real_"),
        ("Command_ConstructNorthKoreaAir_", f"Command_Construct{prefix}Air_"),
        ("Command_ConstructNorthKorea_", f"Command_Construct{prefix}_"),
        ("Command_ConstructNorthKorea", f"Command_Construct{prefix}"),
        ("Command_SelectNorthKorea", f"Command_Select{prefix}"),
        ("Command_LaunchNorthKorea", f"Command_Launch{prefix}"),
        ("Command_NorthKorea", f"Command_{prefix}"),
        ("NorthKoreaDozerCommandSet", f"{prefix}DozerCommandSet"),  # if any
        ("NorthKorea_VT72BCommandSet", f"{prefix}_VT72BCommandSet"),
        ("NorthKorea_CommandCenterCommandSet", f"{prefix}_CommandCenterCommandSet"),
        ("NorthKorea_AirfieldCommandSet", f"{prefix}_AirfieldCommandSet"),
        ("NorthKorea_HeavyAirBaseCommandSet", f"{prefix}_HeavyAirBaseCommandSet"),
        ("NorthKorea_WarFactoryCommandSet", f"{prefix}_WarFactoryCommandSet"),
        ("NorthKorea_SupplyCenterCommandSet", f"{prefix}_SupplyCenterCommandSet"),
        ("NorthKorea_RadarStationCommandSet", f"{prefix}_RadarStationCommandSet"),
        ("NorthKorea_AlAbbasCommandSet", f"{prefix}_AlAbbasCommandSet"),
        ("NorthKorea_MICCommandSet", f"{prefix}_MICCommandSet"),
        ("NKFinal_", f"{prefix}Final_"),
        ("NorthKoreaAir_", f"{prefix}Air_"),
        ("NorthKoreaJet", f"{prefix}Jet"),
        ("NorthKoreaHelicopter", f"{prefix}Helicopter"),
        ("NorthKoreaSystem", f"{prefix}System"),
        ("FactionNorthKorea", fac["pt"]),
        ("INI:FactionNorthKorea", fac["display_key"]),
        ("TOOLTIP:BioStrategyLong_Iraq", fac["tooltip"]),  # NK PT currently uses Iraq tooltip keys
        ("GUI:BioFeatures_Iraq", fac["features"]),
        ("TOOLTIP:BioStrategyLong_NorthKorea", fac["tooltip"]),
        ("GUI:BioFeatures_NorthKorea", fac["features"]),
        ("NorthKorea8x6", fac["scheme"]),
        ("NorthKorea_", f"{prefix}_"),
    ]
    for a, b in reps:
        out = out.replace(a, b)
    # Remaining NorthKorea* tokens
    out = re.sub(r"\bNorthKorea(?=[A-Z_])", prefix, out)
    out = re.sub(r"(Side\s*=\s*)NorthKorea\b", rf"\1{side}", out)
    out = re.sub(r"(BaseSide\s*=\s*)NorthKorea\b", rf"\1{side}", out)
    out = re.sub(r"(Side\s+)NorthKorea\b", rf"\1{side}", out)
    out = unprotect_shared(out)
    return out


def strip_country_objects(text: str, prefix: str) -> str:
    """Keep Object blocks owned by the new country prefix variants."""
    keep_prefixes = (
        prefix + "_",
        prefix + "Final_",
        prefix + "Air_",
        prefix + "Jet",
        prefix + "Helicopter",
        prefix + "System",
        prefix + "Real",
        prefix,  # e.g. SouthKoreaJetMig29S already covered by Jet; SystemSpecialPower...
    )
    parts = re.split(r"(?=^Object\s+)", text, flags=re.M)
    kept = []
    for part in parts:
        m = re.match(r"^Object\s+(\S+)", part, re.M)
        if not m:
            kept.append(part)
            continue
        name = m.group(1)
        if any(name.startswith(p) for p in keep_prefixes):
            kept.append(part)
    return "".join(kept)


def extract_blocks(text: str, kind: str) -> list[tuple[str, str]]:
    pat = rf"(^{kind}\s+(\S+)[\s\S]*?^\s*End\s*$)"
    return [(m.group(2), m.group(1)) for m in re.finditer(pat, text, re.M | re.I)]


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
    """Keep NK science/shortcut infra; identity-only diffs. No ControlBarScheme."""
    pt_block = re.sub(
        r"(PurchaseScienceCommandSetRank1\s*=\s*)\S+",
        r"\1SCIENCE_NorthKorea_CommandSetRank1",
        pt_block,
    )
    pt_block = re.sub(
        r"(PurchaseScienceCommandSetRank3\s*=\s*)\S+",
        r"\1SCIENCE_NorthKorea_CommandSetRank3",
        pt_block,
    )
    pt_block = re.sub(
        r"(PurchaseScienceCommandSetRank8\s*=\s*)\S+",
        r"\1SCIENCE_NorthKorea_CommandSetRank8",
        pt_block,
    )
    pt_block = re.sub(
        r"(SpecialPowerShortcutCommandSet\s*=\s*)\S+",
        r"\1SpecialPowerShortcutNorthKorea",
        pt_block,
    )
    pt_block = re.sub(
        r"(IntrinsicSciences\s*=\s*)\S+",
        r"\1SCIENCE_Iraq",
        pt_block,
    )
    # Keep BaseSide = Iraq like NK (boot-critical for this template)
    pt_block = re.sub(
        r"(PreferredColor\s*=\s*).*$",
        rf"\1{fac['color']}",
        pt_block,
        flags=re.M,
    )
    pt_block = re.sub(r"(DisplayName\s*=\s*)\S+", rf"\1{fac['display_key']}", pt_block, count=1)
    pt_block = re.sub(r"(ArmyTooltip\s*=\s*)\S+", rf"\1{fac['tooltip']}", pt_block, count=1)
    pt_block = re.sub(r"(Features\s*=\s*)\S+", rf"\1{fac['features']}", pt_block, count=1)
    pt_block = re.sub(r"^\s*ControlBarScheme\s*=\s*.*$\n?", "", pt_block, flags=re.M)
    return pt_block


def force_shortcut_object_cs(obj_text: str, prefix: str) -> str:
    """Point country SystemSpecialPowerShortcut at shared SpecialPowerShortcutNorthKoreaSystem."""
    # NK object name pattern: NorthKoreaSystemSpecialPowerShortcut → {prefix}SystemSpecialPowerShortcut
    name = f"{prefix}SystemSpecialPowerShortcut"

    def repl(m: re.Match) -> str:
        block = m.group(0)
        block = re.sub(
            r"(CommandSet\s*=\s*)\S+",
            r"\1SpecialPowerShortcutNorthKoreaSystem",
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
        "nk_lab": r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_LargeAirBase.ini",
        "nk_hab": r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_HeavyAirBase.ini",
        "nk_hq9": r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_Hq9_Site.ini",
        "nk_cram": r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_CRAM.ini",
        "pak_lab": r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_LargeAirBase.ini",
        "nato_lab": r"Data\INI\Object\Specter\NATO\Buildings\Nato_LargeAirBase.ini",
        "saudi_lab": r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_LargeAirBase.ini",
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

    pt_nk = re.search(r"^PlayerTemplate\s+FactionNorthKorea\b.*?^End\s*$", pt_text, re.M | re.S)
    assert pt_nk, "FactionNorthKorea missing"
    pt_nk_block = pt_nk.group(0)

    freeze_pts = {}
    for name in (
        "FactionNorthKorea",
        "FactionPakistan",
        "FactionSaudiArabia",
        "FactionNato",
        "FactionLibya",
        "FactionSweden",
        "FactionGermany",
    ):
        m = re.search(rf"^PlayerTemplate\s+{name}\b.*?^End\s*$", pt_text, re.M | re.S)
        if m:
            freeze_pts[name] = m.group(0)

    cbs_nk = re.search(r"^ControlBarScheme\s+NorthKorea8x6\b.*?^End\s*$", cbs_text, re.M | re.S)
    assert cbs_nk, "NorthKorea8x6 missing"
    cbs_nk_block = cbs_nk.group(0)

    def is_cloneable_cs(name: str) -> bool:
        if "NorthKorea" not in name:
            return False
        if name.startswith("SCIENCE_NorthKorea"):
            return False
        if name in ("SpecialPowerShortcutNorthKorea", "SpecialPowerShortcutNorthKoreaSystem"):
            return False
        return True

    nk_cs_blocks = [(n, b) for n, b in extract_blocks(cs_text, "CommandSet") if is_cloneable_cs(n)]
    print(f"Cloneable CS={len(nk_cs_blocks)}")

    # Collect CB: all NorthKorea-named + all referenced by cloneable CS (incl NKFinal/Real/Air)
    cb_map = {n: b for n, b in extract_blocks(cb_text, "CommandButton")}
    cb_to_clone: dict[str, str] = {}
    for n, b in cb_map.items():
        if "NorthKorea" in n and not n.startswith("Command_PurchaseScience"):
            cb_to_clone[n] = b
    for _n, block in nk_cs_blocks:
        for btn in re.findall(r"\d+\s*=\s*(\S+)", block):
            if btn in (
                "Command_Stop",
                "Command_Sell",
                "Command_SetRallyPoint",
                "Command_DisarmMinesAtPosition",
                "Command_UpgradeAmericaCountermeasures",
            ):
                continue
            if btn.startswith("Command_PurchaseScience"):
                continue
            if btn not in cb_map:
                raise SystemExit(f"Missing referenced CommandButton {btn}")
            cb_to_clone[btn] = cb_map[btn]
    print(f"Cloneable CB={len(cb_to_clone)}")

    # NK object files (both path styles under Specter\North Korea and North Korea\)
    nk_obj_files = []
    for name, _off, _size in entries:
        nl = name.replace("/", "\\").lower()
        if nl.endswith(".ini") and ("\\north korea\\" in nl or nl.startswith("north korea\\")):
            nk_obj_files.append(name.replace("/", "\\"))
    print(f"NK object files to scan: {len(nk_obj_files)}")

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

        pt_block = transform_nk_text(pt_nk_block, prefix, side, fac)
        pt_block = rewrite_pt_for_stability(pt_block, fac)
        pt_block = re.sub(
            r"^PlayerTemplate\s+\S+", f"PlayerTemplate {fac['pt']}", pt_block, count=1, flags=re.M
        )
        assert f"PlayerTemplate {fac['pt']}" in pt_block
        assert re.search(rf"Side\s*=\s*{side}", pt_block)
        assert "SCIENCE_NorthKorea_CommandSetRank1" in pt_block
        assert "SpecialPowerShortcutNorthKorea" in pt_block
        assert "ControlBarScheme" not in pt_block
        assert re.search(rf"StartingBuilding\s*=\s*{prefix}_CommandCenter", pt_block)
        assert re.search(rf"StartingUnit0\s*=\s*{prefix}_VT72B", pt_block)
        assert not re.search(rf"SCIENCE_{prefix}", pt_block)
        new_pt_append.append(pt_block)

        cbs_block = transform_nk_text(cbs_nk_block, prefix, side, fac)
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
        assert "Side NorthKorea" not in cbs_block
        new_cbs_append.append(cbs_block)

        for _n, block in nk_cs_blocks:
            new_cs_append.append(transform_nk_text(block, prefix, side, fac))

        for _n, block in cb_to_clone.items():
            new_cb_append.append(transform_nk_text(block, prefix, side, fac))

        for src_path in nk_obj_files:
            src = fmap[norm(src_path)].decode("latin1")
            # relative under North Korea\
            if "North Korea\\" in src_path:
                rel = src_path.split("North Korea\\", 1)[1]
            elif src_path.startswith("North Korea\\"):
                rel = src_path[len("North Korea\\") :]
            else:
                continue
            # rename NorthKorea_* filenames
            parts = rel.split("\\")
            parts2 = []
            for p in parts:
                p2 = p
                if p2.startswith("NorthKorea_"):
                    p2 = prefix + "_" + p2[len("NorthKorea_") :]
                parts2.append(p2)
            dst_path = "\\".join(
                ["Data", "INI", "Object", "Specter", fac["folder"], *parts2]
            )
            cloned = transform_nk_text(src, prefix, side, fac)
            cloned = strip_country_objects(cloned, prefix)
            if f"{prefix}SystemSpecialPowerShortcut" in cloned:
                cloned = force_shortcut_object_cs(cloned, prefix)
            if not re.search(rf"^Object\s+{re.escape(prefix)}", cloned, re.M):
                continue
            fmap[norm(dst_path)] = cloned.encode("latin1")
            disp[norm(dst_path)] = dst_path

    nl = "\n"
    marker = ";===== NorthKorea-template SK/JP/VN faction clones"
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
    assert pt_names.count("FactionNorthKorea") == 1

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
    fmap[csf_path] = csf_bytes

    for k, p in freeze_paths.items():
        assert fmap[norm(p)] == freeze[k], k
    nk_pt_after = re.search(
        r"^PlayerTemplate\s+FactionNorthKorea\b.*?^End\s*$",
        fmap[pt_path].decode("latin1"),
        re.M | re.S,
    ).group(0)
    assert nk_pt_after == pt_nk_block
    for name, block in freeze_pts.items():
        m = re.search(rf"^PlayerTemplate\s+{name}\b.*?^End\s*$", fmap[pt_path].decode("latin1"), re.M | re.S)
        assert m and m.group(0) == block, name

    DATA_BIG.write_bytes(build_big({disp[k]: v for k, v in fmap.items()}))
    data_sha = sha256(DATA_BIG)
    art_sha = sha256(ART_BIG)
    assert art_sha == BASE_ART

    # -------- Validation --------
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
    # sciences from all science inis
    sci_names = set()
    for n, b in f2.items():
        if "science" in n and n.endswith(".ini") and "\\object\\" not in n:
            sci_names.update(re.findall(r"^Science\s+(\S+)", b.decode("latin1", errors="replace"), re.M))

    def object_exists(obj: str) -> bool:
        for b in f2.values():
            if re.search(rf"^Object\s+{re.escape(obj)}\b", b.decode("latin1", errors="replace"), re.M):
                return True
        return False

    report_lines = []
    for fac in FACTIONS:
        prefix = fac["prefix"]
        m = re.search(rf"^PlayerTemplate\s+{fac['pt']}\b.*?^End\s*$", pt2, re.M | re.S)
        assert m, fac["pt"]
        block = m.group(0)
        assert "SCIENCE_NorthKorea_CommandSetRank1" in block
        assert "SpecialPowerShortcutNorthKorea" in block
        assert "ControlBarScheme" not in block
        assert re.search(rf"Side\s*=\s*{fac['side']}\b", block)
        assert not re.search(r"Side\s*=\s*NorthKorea\b", block)

        # PurchaseScience resolve
        for rk in (
            "PurchaseScienceCommandSetRank1",
            "PurchaseScienceCommandSetRank3",
            "PurchaseScienceCommandSetRank8",
        ):
            cs_name = re.search(rf"{rk}\s*=\s*(\S+)", block).group(1)
            assert cs_name in cs_names, cs_name
            csb = re.search(rf"^CommandSet\s+{re.escape(cs_name)}\b.*?^End\s*$", cs2, re.M | re.S).group(0)
            for btn in re.findall(r"\d+\s*=\s*(\S+)", csb):
                assert btn in cb_names, btn
                bb = re.search(rf"^CommandButton\s+{re.escape(btn)}\b.*?^End\s*$", cb2, re.M | re.S).group(0)
                for sf in re.findall(r"Science\s*=\s*(.+)$", bb, re.M):
                    for s in sf.split():
                        assert s in sci_names, s

        for obj in [
            f"{prefix}_CommandCenter",
            f"{prefix}_VT72B",
            f"{prefix}_LargeAirBase",
            f"{prefix}_HeavyAirBase",
            f"{prefix}_WarFactory",
            f"{prefix}_CRAM",
            f"{prefix}_Hq9_Site",
            f"{prefix}_PowerPlant",
            f"{prefix}_SupplyCenter",
        ]:
            assert object_exists(obj), obj

        assert f"{prefix}_VT72BCommandSet" in cs_names
        assert f"{prefix}_AirfieldCommandSet" in cs_names
        assert f"{prefix}_HeavyAirBaseCommandSet" in cs_names
        assert re.search(rf"^ControlBarScheme\s+{fac['scheme']}\b", cbs2, re.M)
        assert csf_get(csf2, fac["side_key"]) == fac["side_text"]
        assert csf_get(csf2, fac["display_key"]) == fac["display_text"]
        assert not re.search(rf"^CommandButton\s+Command_PurchaseScience{prefix}", cb2, re.M)

        # Dozer/VT72B chain
        dcs = re.search(rf"^CommandSet\s+{prefix}_VT72BCommandSet\b.*?^End\s*$", cs2, re.M | re.S).group(0)
        assert f"Command_Construct{prefix}_LargeAirBase" in dcs
        assert f"Command_Construct{prefix}_HeavyAirBase" in dcs
        assert f"Command_Construct{prefix}_CRAM" in dcs
        assert f"Command_Construct{prefix}_Hq9_Site" in dcs
        assert "Command_DisarmMinesAtPosition" not in dcs
        for btn in re.findall(r"\d+\s*=\s*(\S+)", dcs):
            if btn in ("Command_Stop",) or btn.upper() in ("NONE", ""):
                continue
            assert btn in cb_names, btn
            bb = re.search(rf"^CommandButton\s+{re.escape(btn)}\b.*?^End\s*$", cb2, re.M | re.S).group(0)
            for obj in re.findall(r"Object\s*=\s*(\S+)", bb):
                assert object_exists(obj), (btn, obj)

        # production chains
        for unit_cs in (
            f"{prefix}_WarFactoryCommandSet",
            f"{prefix}_CommandCenterCommandSet",
            f"{prefix}_AirfieldCommandSet",
            f"{prefix}_HeavyAirBaseCommandSet",
        ):
            assert unit_cs in cs_names, unit_cs
            ucs = re.search(rf"^CommandSet\s+{re.escape(unit_cs)}\b.*?^End\s*$", cs2, re.M | re.S).group(0)
            for btn in re.findall(r"\d+\s*=\s*(\S+)", ucs):
                if btn in ("Command_Sell", "Command_SetRallyPoint", "Command_Stop") or "UpgradeAmerica" in btn:
                    continue
                assert btn in cb_names, (unit_cs, btn)
                bb = re.search(rf"^CommandButton\s+{re.escape(btn)}\b.*?^End\s*$", cb2, re.M | re.S).group(0)
                for obj in re.findall(r"Object\s*=\s*(\S+)", bb):
                    assert object_exists(obj), (btn, obj)

        lab = next(
            b.decode("latin1", errors="replace")
            for b in f2.values()
            if re.search(rf"^Object\s+{prefix}_LargeAirBase\b", b.decode("latin1", errors="replace"), re.M)
        )
        assert "TheAirPort" in lab and "NumRows                 = 4" in lab
        hab = next(
            b.decode("latin1", errors="replace")
            for b in f2.values()
            if re.search(rf"^Object\s+{prefix}_HeavyAirBase\b", b.decode("latin1", errors="replace"), re.M)
        )
        assert "HXUSABigAirPort" in hab
        assert pt_names.count(fac["pt"]) == 1
        assert scheme_names.count(fac["scheme"]) == 1

        report_lines.append(
            f"""REPORT {prefix.upper()}:
PlayerTemplate = {fac['pt']}
Side = {fac['side']}
DisplayName = {fac['display_key']}
ControlBar = {fac['scheme']}
CommandCenter = {prefix}_CommandCenter
Dozer = {prefix}_VT72B
Dozer CommandSet = {prefix}_VT72BCommandSet
WarFactory = {prefix}_WarFactory
Barracks = Iraq_Barracks (shared; same as current North Korea Barracks_SAFE)
LargeAirBase = {prefix}_LargeAirBase
LargeAirBase capacity = 16
HeavyAirBase = {prefix}_HeavyAirBase
Chinese-derived Air Defense = {prefix}_Hq9_Site
C-RAM = {prefix}_CRAM
PurchaseScience validation = REUSES SCIENCE_NorthKorea_CommandSetRank* + SpecialPowerShortcutNorthKorea
SIDE string = {fac['side_key']} => {fac['side_text']}
PLAYABLE = YES
{prefix.upper()} CLONE = PASS
"""
        )

    for k, p in freeze_paths.items():
        assert f2[norm(p)] == freeze[k], k
    assert re.search(r"^PlayerTemplate\s+FactionNorthKorea\b.*?^End\s*$", pt2, re.M | re.S).group(0) == pt_nk_block

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")

    report = "\n".join(report_lines) + f"""
MISSING SIDE STRINGS = 0
UNRESOLVED PURCHASESCIENCE BUTTONS = 0
UNRESOLVED SCIENCES = 0
UNRESOLVED COMMAND BUTTONS = 0
UNRESOLVED COMMANDSETS = 0

NORTH KOREA FUNCTIONALLY CHANGED = NO
PAKISTAN CHANGED = NO
NATO CHANGED = NO
OTHER FACTIONS CHANGED = NO

ACTIVE FILES CHANGED:
- Data\\INI\\PlayerTemplate.ini
- Data\\INI\\ControlBarScheme.ini
- Data\\INI\\CommandSet.ini
- Data\\INI\\CommandButton.ini
- Data\\English\\generals.csf
- Data\\INI\\Object\\Specter\\South Korean Armed Forces\\* (cloned)
- Data\\INI\\Object\\Specter\\Japan Self-Defense Forces\\* (cloned)
- Data\\INI\\Object\\Specter\\Vietnam People's Armed Forces\\* (cloned)

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
