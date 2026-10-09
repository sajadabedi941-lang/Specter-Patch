#!/usr/bin/env python3
"""Iraq missile roster: move WF 9P117/Sarab7/Al-Abbas ICBM/BM-21 to factory.

Baseline: PR #599 / magenta-waves DATA
  SHA256 ec066f71382d3d1d732d4a9cdde54ffee86258eb0362aa0c8087155bc5e7f4d8

Packed last-wins mapping (existing objects, empty factory slots):
  missile E slot 5  <- Iraq_Sarab7     (was WF slot 9)
  missile G slot 7  <- Iraq_R11ScudB   (9P117; was WF slot 13)
  missile K slot 11 <- Iraq_Alhussaien (Al-Abbas ICBM; was WF slot 10)
  missile M slot 13 <- Iraq_BM-21      (replaces factory Rally Point)

Missile D display: OBJECT:Iraq_AlAbbas CSF 'Al-Abbas' -> 'Al-Raad'.
Internal ID Iraq_AlAbbas, weapon, cost, factory slot D unchanged.
Al-Abbas ICBM object Iraq_Alhussaien is not modified.

ART is copied byte-identical from PR #599. No cooldown / rider / rearm.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_MAGENTA_WAVES/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MAGENTA_WAVES/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_ROSTER"

SHA_DATA_599 = "ec066f71382d3d1d732d4a9cdde54ffee86258eb0362aa0c8087155bc5e7f4d8"
SIZE_DATA_599 = 366615017
SHA_ART_599 = "9c1dc445c17b024f8a4c1c55e699371a94d4991d1dff1eb377f3976a6c54545e"
SIZE_ART_599 = 1295713019

CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
CSF_KEY = r"Data\English\generals.csf"

OBJ = {
    "Iraq_AlAbbas": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlAbbas.ini",
    "Iraq_R11ScudB": r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini",
    "Iraq_Sarab7": r"Data\INI\Object\Specter\Iraq Army\Wheeled\AlNida.ini",
    "Iraq_Alhussaien": r"Data\INI\Object\Specter\Iraq Army\Wheeled\AbbasLauncher.ini",
    "Iraq_BM-21": r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_BM-21.ini",
    "Iraq_AlFahdMissileFactory": r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini",
}

MOVED = [
    "Command_ConstructIraq_Sarab7",
    "Command_ConstructIraq_Alhussaien",
    "Command_ConstructIraq_BM-21",
    "Command_ConstructIraq_R11ScudB",
    "Command_ConstructIraq_Alhussaien_AI",
]

IRAQ_WF_SETS = [
    "Iraq_WarFactoryCommandSet_T",
    "Iraq_WarFactoryCommandSet_T1",
    "Iraq_WarFactoryCommandSet_T2",
    "Iraq_WarFactoryCommandSet_T3",
    "Iraq_WarFactoryCommandSet",
]

FACTORY_NEW = """CommandSet Iraq_AlFahdMissileFactoryCommandSet
  1  = CB_MISSILE_A
  2  = CB_MISSILE_B
  3  = CB_MISSILE_C
  4  = CB_MISSILE_D
  5  = CB_MISSILE_E
  ; 6 reserved (F)
  7  = CB_MISSILE_G
  8  = CB_MISSILE_H
  9  = CB_MISSILE_I
  10 = CB_MISSILE_J
  11 = CB_MISSILE_K
  ; 12 reserved (L)
  13 = CB_MISSILE_M
  14 = Command_Sell
End"""

WF_T_NEW = """CommandSet {name}
  1 = Command_ConstructIraq_T-72
  2 = Command_ConstructIraq_BMP-1
  3 = Command_ConstructIraq_BMP-2
  4 = Command_ConstructIraq_BTR-90
  5 = Command_ConstructIraq_2S1
  6 = Command_ConstructIraq_Sam8
  7 = Command_ConstructIraq_AssadBabel-2
  8 = Command_ConstructIraq_SA-6
  11 = Command_ConstructIraqVehicleRoland3K
  14 = Command_Sell
End"""

WF_AI_NEW = """CommandSet Iraq_WarFactoryCommandSet
  1 = Command_ConstructIraq_T-72
  2 = Command_ConstructIraq_BMP-1
  3 = Command_ConstructIraq_BMP-2
  4 = Command_ConstructIraq_BTR-90
  5 = Command_ConstructIraq_2S1
  6 = Command_ConstructIraq_Sam8
  7 = Command_ConstructIraqTankAssadBabel2_AI
  8 = Command_ConstructIraq_SA-6
  12 = Command_ConstructIraqVehicleRoland3K
  14 = Command_Sell
End"""

CB_E_NEW = """CommandButton CB_MISSILE_E
  Command       = UNIT_BUILD
  Object        = Iraq_Sarab7
  TextLabel     = CONTROLBAR:SpecterMissileE
  ButtonImage   = specter_missile_e
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipSpecterMissileE
End"""

CB_G_NEW = """CommandButton CB_MISSILE_G
  Command       = UNIT_BUILD
  Object        = Iraq_R11ScudB
  TextLabel     = CONTROLBAR:SpecterMissileG
  ButtonImage   = specter_missile_g
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipSpecterMissileG
End"""

CB_K_NEW = """CommandButton CB_MISSILE_K
  Command       = UNIT_BUILD
  Object        = Iraq_Alhussaien
  TextLabel     = CONTROLBAR:SpecterMissileK
  ButtonImage   = specter_missile_k
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipSpecterMissileK
End"""

CB_M_NEW = """CommandButton CB_MISSILE_M
  Command       = UNIT_BUILD
  Object        = Iraq_BM-21
  TextLabel     = CONTROLBAR:SpecterMissileM
  ButtonImage   = irq_bm21
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipSpecterMissileM
End"""


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_big(data: bytes) -> dict[str, bytes]:
    if data[:4] != b"BIGF":
        raise SystemExit("not BIGF")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files: dict[str, bytes] = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name.replace("/", "\\")] = data[off : off + size]
    return files


def parse_index(data: bytes):
    archive_size = struct.unpack(">I", data[4:8])[0]
    count = struct.unpack(">I", data[8:12])[0]
    header_size = struct.unpack(">I", data[12:16])[0]
    pos = 16
    files = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files.append((name, off, size))
    return archive_size, count, header_size, pos, files


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    index = []
    blobs = []
    offset = header_size
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def big_structure_ok(blob: bytes) -> list[str]:
    issues = []
    arch, count, header, index_end, files = parse_index(blob)
    if arch != len(blob):
        issues.append("archive size field mismatch")
    if header != index_end:
        issues.append("header size mismatch")
    if count != len(files):
        issues.append("count mismatch")
    lows = [n.replace("/", "\\").lower() for n, _, _ in files]
    if len(lows) != len(set(lows)):
        issues.append("duplicate paths")
    return issues


def decode(blob: bytes) -> str:
    return blob.decode("latin1").replace("\r\n", "\n")


def to_crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


def last_block(kind: str, name: str, text: str) -> re.Match[str] | None:
    matches = list(re.finditer(rf"(?ms)^{kind} {re.escape(name)}\n.*?^End", text))
    return matches[-1] if matches else None


def replace_last_block(kind: str, name: str, text: str, new_block: str) -> str:
    m = last_block(kind, name, text)
    if not m:
        raise SystemExit(f"missing last-wins {kind} {name}")
    return text[: m.start()] + new_block.strip() + text[m.end() :]


def insert_after_last_block(kind: str, name: str, text: str, new_block: str) -> str:
    m = last_block(kind, name, text)
    if not m:
        raise SystemExit(f"missing insert-after {kind} {name}")
    return text[: m.end()] + "\n\n" + new_block.strip() + text[m.end() :]


def object_body(text: str, name: str) -> str | None:
    found = [(m.group(1), m.start()) for m in re.finditer(r"^Object\s+(\S+)\s*$", text, re.M)]
    for i, (n, start) in enumerate(found):
        if n == name:
            end = found[i + 1][1] if i + 1 < len(found) else len(text)
            return text[start:end]
    return None


def field(body: str | None, key: str) -> str:
    if not body:
        return ""
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", body, re.M)
    return m.group(1).strip() if m else ""


def cmdset_slots(block: str) -> dict[int, str]:
    out: dict[int, str] = {}
    for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)\s*$", block, re.M):
        out[int(m.group(1))] = m.group(2)
    return out


def cb_field(block: str, key: str) -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block, re.M)
    return m.group(1).strip() if m else ""


def csf_parse(csf: bytes):
    if csf[:4] != b" FSC":
        raise SystemExit(f"unexpected CSF magic {csf[:4]!r}")
    magic, ver, nlab, nstr, unused, lang = struct.unpack_from("<4sIIIII", csf, 0)
    labels = []
    pos = 24
    while pos < len(csf):
        if csf[pos : pos + 4] != b" LBL":
            break
        pos += 4
        cnt, nlen = struct.unpack_from("<II", csf, pos)
        pos += 8
        name = csf[pos : pos + nlen].decode("latin1")
        pos += nlen
        strs = []
        for _ in range(cnt):
            smag = csf[pos : pos + 4]
            pos += 4
            slen = struct.unpack_from("<I", csf, pos)[0]
            pos += 4
            raw = csf[pos : pos + slen * 2]
            pos += slen * 2
            val = bytes(x ^ 0xFF for x in raw).decode("utf-16le")
            extra = None
            if smag == b"WRTS":
                elen = struct.unpack_from("<I", csf, pos)[0]
                pos += 4
                extra = csf[pos : pos + elen]
                pos += elen
            strs.append((smag, val, extra))
        labels.append((name, strs))
    return magic, ver, unused, lang, labels


def csf_build(magic, ver, unused, lang, labels) -> bytes:
    body = bytearray()
    nstr = 0
    for name, strs in labels:
        body += b" LBL"
        body += struct.pack("<II", len(strs), len(name))
        body += name.encode("latin1")
        for smag, val, extra in strs:
            encoded = val.encode("utf-16le")
            xored = bytes(x ^ 0xFF for x in encoded)
            tag = smag if smag in (b" RTS", b"WRTS") else b" RTS"
            body += tag
            body += struct.pack("<I", len(val))
            body += xored
            nstr += 1
            if tag == b"WRTS" and extra is not None:
                body += struct.pack("<I", len(extra))
                body += extra
    header = bytearray()
    header += magic
    header += struct.pack("<IIIII", ver, len(labels), nstr, unused, lang)
    return bytes(header + body)


def csf_upsert(csf: bytes, mapping: dict[str, str]) -> bytes:
    magic, ver, unused, lang, labels = csf_parse(csf)
    by_name = {n: i for i, (n, _) in enumerate(labels)}
    for key, value in mapping.items():
        if key in by_name:
            i = by_name[key]
            name, strs = labels[i]
            if strs:
                smag, _old, extra = strs[0]
                strs[0] = (smag, value, extra)
            else:
                strs.append((b" RTS", value, None))
            labels[i] = (name, strs)
        else:
            labels.append((key, [(b" RTS", value, None)]))
    return csf_build(magic, ver, unused, lang, labels)


def csf_get(csf: bytes, key: str) -> str | None:
    _m, _v, _u, _l, labels = csf_parse(csf)
    for name, strs in labels:
        if name == key and strs:
            return strs[0][1]
    return None


def csf_values(csf: bytes) -> dict[str, str]:
    _m, _v, _u, _l, labels = csf_parse(csf)
    out = {}
    for name, strs in labels:
        if strs:
            out[name] = strs[0][1]
    return out


def validate(data: dict[str, bytes], src: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    cs = decode(data[CS_KEY])
    cb = decode(data[CB_KEY])
    src_cs = decode(src[CS_KEY])
    src_cb = decode(src[CB_KEY])

    factory = last_block("CommandSet", "Iraq_AlFahdMissileFactoryCommandSet", cs)
    if not factory:
        fails.append("factory CommandSet missing")
        slots = {}
    else:
        slots = cmdset_slots(factory.group(0))
    expected_slots = {
        1: "CB_MISSILE_A",
        2: "CB_MISSILE_B",
        3: "CB_MISSILE_C",
        4: "CB_MISSILE_D",
        5: "CB_MISSILE_E",
        7: "CB_MISSILE_G",
        8: "CB_MISSILE_H",
        9: "CB_MISSILE_I",
        10: "CB_MISSILE_J",
        11: "CB_MISSILE_K",
        13: "CB_MISSILE_M",
        14: "Command_Sell",
    }
    if slots != expected_slots:
        fails.append(f"factory slots {slots} != {expected_slots}")
    if 13 in slots and slots[13] == "Command_SetRallyPoint":
        fails.append("factory slot 13 still Rally Point")
    if 6 in slots or 12 in slots:
        fails.append("factory reserved F/L slots were filled")

    for name in IRAQ_WF_SETS:
        block = last_block("CommandSet", name, cs)
        if not block:
            fails.append(f"missing {name}")
            continue
        body = block.group(0)
        for btn in MOVED:
            if re.search(rf"^\s*\d+\s*=\s*{re.escape(btn)}\s*$", body, re.M):
                fails.append(f"{name} still produces {btn}")
        if "Command_Sell" not in body:
            fails.append(f"{name} lost Sell")
        if "Command_ConstructIraqVehicleRoland3K" not in body:
            fails.append(f"{name} lost Roland")
        if name != "Iraq_WarFactoryCommandSet" and "Command_ConstructIraq_T-72" not in body:
            fails.append(f"{name} lost T-72")

    # Other countries that still share the old construct buttons must keep them.
    saudi = last_block("CommandSet", "SaudiArabia_WarFactoryCommandSet", cs)
    if saudi and "Command_ConstructIraq_Sarab7" not in saudi.group(0):
        fails.append("unrelated SaudiArabia_WarFactoryCommandSet mutated")
    libya = last_block("CommandSet", "Libya_WarFactoryCommandSet", cs)
    if libya and "Command_ConstructIraq_R11ScudB" not in libya.group(0):
        fails.append("unrelated Libya_WarFactoryCommandSet mutated")
    cc = last_block("CommandSet", "Iraq_CommandCenterCommandSet", cs)
    src_cc = last_block("CommandSet", "Iraq_CommandCenterCommandSet", src_cs)
    if cc and src_cc and cc.group(0) != src_cc.group(0):
        fails.append("Iraq_CommandCenterCommandSet mutated")

    mapping = {
        "CB_MISSILE_E": "Iraq_Sarab7",
        "CB_MISSILE_G": "Iraq_R11ScudB",
        "CB_MISSILE_K": "Iraq_Alhussaien",
        "CB_MISSILE_M": "Iraq_BM-21",
        "CB_MISSILE_D": "Iraq_AlAbbas",
        "CB_MISSILE_A": "Iraq_AlFahd500",
    }
    for btn, obj in mapping.items():
        block = last_block("CommandButton", btn, cb)
        if not block:
            fails.append(f"missing {btn}")
            continue
        if cb_field(block.group(0), "Object") != obj:
            fails.append(f"{btn} Object={cb_field(block.group(0), 'Object')} != {obj}")
        if cb_field(block.group(0), "Command") != "UNIT_BUILD":
            fails.append(f"{btn} Command changed")
        if btn != "CB_MISSILE_M" and "specter_missile_" not in cb_field(block.group(0), "ButtonImage"):
            fails.append(f"{btn} ButtonImage changed")
        if btn == "CB_MISSILE_M" and cb_field(block.group(0), "ButtonImage") != "irq_bm21":
            fails.append("CB_MISSILE_M ButtonImage != irq_bm21")

    # Construct buttons remain defined (objects/assets kept; other countries still use them).
    for btn, obj in [
        ("Command_ConstructIraq_R11ScudB", "Iraq_R11ScudB"),
        ("Command_ConstructIraq_Sarab7", "Iraq_Sarab7"),
        ("Command_ConstructIraq_Alhussaien", "Iraq_Alhussaien"),
        ("Command_ConstructIraq_BM-21", "Iraq_BM-21"),
    ]:
        block = last_block("CommandButton", btn, cb)
        src_block = last_block("CommandButton", btn, src_cb)
        if not block or not src_block:
            fails.append(f"construct button missing {btn}")
        elif block.group(0) != src_block.group(0):
            fails.append(f"construct button mutated {btn}")
        elif cb_field(block.group(0), "Object") != obj:
            fails.append(f"{btn} Object drifted")

    # Object bodies / costs / weapons unchanged except we do not touch them.
    costs = {
        "Iraq_AlAbbas": "2600",
        "Iraq_R11ScudB": "1200",
        "Iraq_Sarab7": "1200",
        "Iraq_Alhussaien": "20000",
        "Iraq_BM-21": "1000",
    }
    displays = {
        "Iraq_AlAbbas": "OBJECT:Iraq_AlAbbas",
        "Iraq_R11ScudB": "OBJECT:9P117S",
        "Iraq_Sarab7": "OBJECT:Sarab7",
        "Iraq_Alhussaien": "OBJECT:abbasicbmm",
        "Iraq_BM-21": "OBJECT:BM-21",
    }
    for obj, path in OBJ.items():
        if obj == "Iraq_AlFahdMissileFactory":
            continue
        body = object_body(decode(data[path]), obj)
        src_body = object_body(decode(src[path]), obj)
        if body != src_body:
            fails.append(f"{obj} object body mutated")
        if obj in costs and field(body, "BuildCost") != costs[obj]:
            fails.append(f"{obj} BuildCost {field(body, 'BuildCost')}")
        if obj in displays and field(body, "DisplayName") != displays[obj]:
            fails.append(f"{obj} DisplayName key changed")
        if "VEHICLE" not in field(body, "KindOf"):
            fails.append(f"{obj} lost VEHICLE KindOf")

    bld = object_body(decode(data[OBJ["Iraq_AlFahdMissileFactory"]]), "Iraq_AlFahdMissileFactory")
    if field(bld, "CommandSet") != "Iraq_AlFahdMissileFactoryCommandSet":
        fails.append("factory building CommandSet changed")

    icbm = object_body(decode(data[OBJ["Iraq_Alhussaien"]]), "Iraq_Alhussaien")
    src_icbm = object_body(decode(src[OBJ["Iraq_Alhussaien"]]), "Iraq_Alhussaien")
    if icbm != src_icbm:
        fails.append("Al-Abbas ICBM object mutated")

    d_tel = object_body(decode(data[OBJ["Iraq_AlAbbas"]]), "Iraq_AlAbbas")
    if field(d_tel, "CommandSet") != "Scud_B_CommandSet":
        fails.append("missile D CommandSet changed")
    if "Weapon_Iraq_AlAbbas" not in (d_tel or ""):
        fails.append("missile D weapon changed")

    def name_counts(kind: str, text: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for m in re.finditer(rf"^{kind} (\S+)", text, re.M):
            counts[m.group(1)] = counts.get(m.group(1), 0) + 1
        return counts

    src_cs_counts = name_counts("CommandSet", src_cs)
    new_cs_counts = name_counts("CommandSet", cs)
    if new_cs_counts != src_cs_counts:
        fails.append(f"CommandSet name counts changed {new_cs_counts != src_cs_counts}")
        for n in sorted(set(src_cs_counts) | set(new_cs_counts)):
            if src_cs_counts.get(n) != new_cs_counts.get(n):
                fails.append(f"CommandSet {n} count {src_cs_counts.get(n)} -> {new_cs_counts.get(n)}")

    src_cb_counts = name_counts("CommandButton", src_cb)
    new_cb_counts = name_counts("CommandButton", cb)
    for n in sorted(set(src_cb_counts) | set(new_cb_counts)):
        old_n = src_cb_counts.get(n, 0)
        new_n = new_cb_counts.get(n, 0)
        if n == "CB_MISSILE_M":
            if new_n != 1:
                fails.append(f"CB_MISSILE_M count {new_n}")
            continue
        if old_n != new_n:
            fails.append(f"CommandButton {n} count {old_n} -> {new_n}")
    for ch in "ABCDEFGHIJKLM":
        n = f"CB_MISSILE_{ch}"
        if new_cb_counts.get(n, 0) != 1:
            fails.append(f"{n} last-wins count {new_cb_counts.get(n, 0)}")

    csf = data[CSF_KEY]
    if csf_get(csf, "OBJECT:Iraq_AlAbbas") != "Al-Raad":
        fails.append(f"missile D display {csf_get(csf, 'OBJECT:Iraq_AlAbbas')!r}")
    icbm_name = csf_get(csf, "OBJECT:abbasicbmm")
    src_icbm_name = csf_get(src[CSF_KEY], "OBJECT:abbasicbmm")
    if icbm_name != src_icbm_name:
        fails.append("ICBM CSF display mutated")
    if csf_get(csf, "CONTROLBAR:ConstructAlhussaiengls") != csf_get(
        src[CSF_KEY], "CONTROLBAR:ConstructAlhussaiengls"
    ):
        fails.append("ICBM construct label mutated")
    tip = csf_get(csf, "CONTROLBAR:ToolTipSpecterMissileD") or ""
    if not tip.startswith("Al-Raad"):
        fails.append(f"missile D tooltip still {tip[:40]!r}")
    if "Al-Abbas" in tip:
        fails.append("missile D tooltip still contains Al-Abbas")
    if csf_get(csf, "CONTROLBAR:SpecterMissileM") != "Missile M":
        fails.append("missing SpecterMissileM CSF")

    # Exact display 'Al-Raad' should now exist once as missile D.
    values = csf_values(csf)
    raad_keys = [k for k, v in values.items() if v.replace("\r", "") == "Al-Raad"]
    if "OBJECT:Iraq_AlAbbas" not in raad_keys:
        fails.append("Al-Raad not on OBJECT:Iraq_AlAbbas")
    # Existing Alraad MLRS leftover must remain distinct.
    if values.get("OBJECT:Alraad") != csf_get(src[CSF_KEY], "OBJECT:Alraad"):
        fails.append("OBJECT:Alraad mutated")

    # No cooldown / rider / rearm introduced in mutated files.
    for key in (CS_KEY, CB_KEY):
        if "Rearm" in decode(data[key]) and "Rearm" not in decode(src[key]):
            fails.append(f"{key} gained Rearm")
        if "Cooldown" in decode(data[key]):
            fails.append(f"{key} gained Cooldown")

    allowed = {CS_KEY, CB_KEY, CSF_KEY}
    for k in data:
        if k not in allowed and data[k] != src[k]:
            fails.append(f"unrelated DATA mutated: {k}")
            break
    if set(data) != set(src):
        fails.append(f"DATA file set changed added={set(data)-set(src)} removed={set(src)-set(data)}")

    return fails


def main() -> int:
    if sha256_path(SRC_DATA) != SHA_DATA_599 or SRC_DATA.stat().st_size != SIZE_DATA_599:
        raise SystemExit("PR #599 DATA mismatch")
    if sha256_path(SRC_ART) != SHA_ART_599 or SRC_ART.stat().st_size != SIZE_ART_599:
        raise SystemExit("PR #599 ART mismatch")

    src = parse_big(SRC_DATA.read_bytes())
    data = dict(src)
    cs = decode(data[CS_KEY])
    cb = decode(data[CB_KEY])

    for name in [
        "Iraq_WarFactoryCommandSet_T",
        "Iraq_WarFactoryCommandSet_T1",
        "Iraq_WarFactoryCommandSet_T2",
        "Iraq_WarFactoryCommandSet_T3",
    ]:
        cs = replace_last_block("CommandSet", name, cs, WF_T_NEW.format(name=name))
    cs = replace_last_block("CommandSet", "Iraq_WarFactoryCommandSet", cs, WF_AI_NEW)
    cs = replace_last_block(
        "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet", cs, FACTORY_NEW
    )

    cb = replace_last_block("CommandButton", "CB_MISSILE_E", cb, CB_E_NEW)
    cb = replace_last_block("CommandButton", "CB_MISSILE_G", cb, CB_G_NEW)
    cb = replace_last_block("CommandButton", "CB_MISSILE_K", cb, CB_K_NEW)
    if last_block("CommandButton", "CB_MISSILE_M", cb):
        cb = replace_last_block("CommandButton", "CB_MISSILE_M", cb, CB_M_NEW)
    else:
        cb = insert_after_last_block("CommandButton", "CB_MISSILE_L", cb, CB_M_NEW)

    old_tip = csf_get(data[CSF_KEY], "CONTROLBAR:ToolTipSpecterMissileD") or ""
    new_tip = old_tip
    if new_tip.startswith("Al-Abbas"):
        new_tip = "Al-Raad" + new_tip[len("Al-Abbas") :]
    elif "Al-Abbas" in new_tip:
        new_tip = new_tip.replace("Al-Abbas", "Al-Raad", 1)
    else:
        new_tip = "Al-Raad\nRange: 1600 km\nWarhead: 1200 kg\nPoint Accuracy: 25/100\nRadar Stealth: 15/100\nRebuild Time: 35 sec\nPrice: $2600"

    csf_map = {
        "OBJECT:Iraq_AlAbbas": "Al-Raad",
        "CONTROLBAR:ToolTipSpecterMissileD": new_tip,
        "CONTROLBAR:SpecterMissileM": "Missile M",
        "CONTROLBAR:ToolTipSpecterMissileM": "Strategic missile slot M.",
    }
    data[CS_KEY] = to_crlf(cs)
    data[CB_KEY] = to_crlf(cb)
    data[CSF_KEY] = csf_upsert(data[CSF_KEY], csf_map)

    fails = validate(data, src)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    packed = build_big(data)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed))
    extracted = parse_big(packed)
    fails.extend(validate(extracted, src))

    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_data.write_bytes(packed)
    shutil.copy2(SRC_ART, out_art)

    data_sha = sha256_path(out_data)
    art_sha = sha256_path(out_art)
    if art_sha != SHA_ART_599 or out_art.stat().st_size != SIZE_ART_599:
        fails.append("ART is not byte-identical to PR #599")

    factory = last_block(
        "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet", decode(extracted[CS_KEY])
    )
    t3 = last_block("CommandSet", "Iraq_WarFactoryCommandSet_T3", decode(extracted[CS_KEY]))
    ai = last_block("CommandSet", "Iraq_WarFactoryCommandSet", decode(extracted[CS_KEY]))

    report = [
        "# SPECTER Iraq missile roster + missile D display rename",
        "",
        "Baseline packed last-wins: PR #599 DATA",
        f"  SHA256 {SHA_DATA_599}",
        "",
        "Identified existing objects (not created):",
        "  missile G / 9P117     Object=Iraq_R11ScudB   DisplayName=OBJECT:9P117S",
        "  missile E / Sarab7    Object=Iraq_Sarab7     DisplayName=OBJECT:Sarab7",
        "  missile K / Al-Abbas  Object=Iraq_Alhussaien DisplayName=OBJECT:abbasicbmm",
        "  missile M / BM-21     Object=Iraq_BM-21      DisplayName=OBJECT:BM-21",
        "  missile D             Object=Iraq_AlAbbas    DisplayName key OBJECT:Iraq_AlAbbas",
        "",
        "War Factory last-wins (Iraq_WarFactoryCommandSet_T/T1/T2/T3 + unsuffixed AI):",
        "  REMOVED Command_ConstructIraq_R11ScudB (9P117)",
        "  REMOVED Command_ConstructIraq_Sarab7",
        "  REMOVED Command_ConstructIraq_Alhussaien (+ Alhussaien_AI on AI set)",
        "  REMOVED Command_ConstructIraq_BM-21",
        "  Objects/assets/buttons kept. Other-country WF sets that still reference",
        "  those construct buttons were not changed.",
        "",
        "Missile factory Iraq_AlFahdMissileFactoryCommandSet last-wins:",
        "  slot 5  CB_MISSILE_E Object=Iraq_Sarab7",
        "  slot 7  CB_MISSILE_G Object=Iraq_R11ScudB",
        "  slot 11 CB_MISSILE_K Object=Iraq_Alhussaien",
        "  slot 13 CB_MISSILE_M Object=Iraq_BM-21 (replaces Rally Point)",
        "  A-D/H-J/Sell unchanged. F/L remain reserved/empty.",
        "",
        "Missile D display:",
        "  CSF OBJECT:Iraq_AlAbbas 'Al-Abbas' -> 'Al-Raad'",
        "  Internal ID Iraq_AlAbbas unchanged. ICBM OBJECT:abbasicbmm unchanged.",
        "  Exact 'Al-Raad' was unused. Distinct leftover OBJECT:Alraad='Alraad' (MLRS) kept.",
        "",
        "No cooldown, rider, or paid rearm work in this pack.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        f"- ART size: {out_art.stat().st_size} (UNCHANGED vs PR #599)",
        f"- ART SHA256: {art_sha}",
        "",
        "Factory last-wins:",
        (factory.group(0) if factory else "MISSING"),
        "",
        "Iraq WF T3 last-wins:",
        (t3.group(0) if t3 else "MISSING"),
        "",
        "Iraq WF unsuffixed last-wins:",
        (ai.group(0) if ai else "MISSING"),
        "",
    ]
    if fails:
        # unique preserve order
        seen = set()
        uniq = []
        for f in fails:
            if f not in seen:
                seen.add(f)
                uniq.append(f)
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in uniq)
        report.append("RUNTIME_TEST=NOT RUN")
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("\n".join(report))
        return 1

    report += [
        "## VALIDATION PASS (static / packed last-wins)",
        "- Factory E/G/K/M buttons point at existing Iraq_Sarab7 / Iraq_R11ScudB / Iraq_Alhussaien / Iraq_BM-21",
        "- Iraq WF last-wins no longer produce those four units",
        "- Construct buttons and object bodies still present (not deleted)",
        "- Other-country WF and Iraq Command Center rosters unchanged",
        "- Missile D CSF display is Al-Raad; ICBM display unchanged",
        "- No duplicate CommandSet/CommandButton names",
        "- Only CommandSet.ini, CommandButton.ini, generals.csf mutated vs PR #599",
        "- ART byte-identical to PR #599",
        "- No cooldown / rider / rearm added",
        "",
        "Static validation completed; runtime game test not performed.",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=NO\n"
        "DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={data_sha}\n"
        f"DATA_FILES={len(extracted)}\n"
        "ART_FILE=_SPEC_ART_ONE.big\n"
        f"ART_SIZE={out_art.stat().st_size}\n"
        f"ART_SHA256={art_sha}\n"
        f"ART_FILES=4642\n"
        "BASELINE=PR #599 magenta-waves DATA+ART\n"
        "MISSILE_D_DISPLAY=Al-Raad\n"
        "MISSILE_D_OBJECT=Iraq_AlAbbas\n"
        "FACTORY_E=Iraq_Sarab7\n"
        "FACTORY_G=Iraq_R11ScudB\n"
        "FACTORY_K=Iraq_Alhussaien\n"
        "FACTORY_M=Iraq_BM-21\n"
        "COOLDOWN=NOT IMPLEMENTED\n"
        "FACTORY_REARM=STILL OFF\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: Iraq missile roster reorganization + missile D rename\n"
        "\n"
        "War Factory no longer produces 9P117, Sarab7, Al-Abbas ICBM, or BM-21 Grad.\n"
        "Those existing units are produced from the Iraq missile factory:\n"
        "  E = Sarab7 (Iraq_Sarab7)\n"
        "  G = 9P117 (Iraq_R11ScudB)\n"
        "  K = Al-Abbas ICBM (Iraq_Alhussaien)\n"
        "  M = BM-21 Grad (Iraq_BM-21)  [replaces Rally Point]\n"
        "\n"
        "Missile D display name is now Al-Raad (object ID Iraq_AlAbbas unchanged).\n"
        "Al-Abbas ICBM itself is unchanged.\n"
        "\n"
        "Place both complete replacement BIGs in the SPECTER folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "  _SPEC_ART_ONE.big   (unchanged from PR #599)\n"
        "\n"
        "No 5-minute cooldown in this pack. Static validation only.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_ROSTER.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
