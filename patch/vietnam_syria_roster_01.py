#!/usr/bin/env python3
"""SPECTER1 Vietnam + Syria roster/visual/unlock pass.

Baseline: crashfix DATA SHA f29f31e6... + Shadow/AH-1Z ART SHA b8a7f45d...
Does not rebuild from older SPECTER archives. Does not modify USA/Russia/China
reference aircraft objects. Does not touch Iraq Su-24MR or the 44 std targets.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_AIRFRAME_STD_01_CRASHFIX_TEST/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_SHADOW_AH1Z_ART_01/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "f29f31e6555ffc4d6c95951a9624210bd8dfe30ee055604a3535206e71e582db"
EXPECTED_ART_SHA = "b8a7f45dd57a1f56c4e68a5a16af04849834e0775db256637ab1ad1853702abe"
OUT_DIR = Path("/tmp/SPECTER1_VIETNAM_SYRIA_ROSTER_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_VIETNAM_SYRIA_ROSTER_01")

P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_WEAPON = r"Data\INI\Weapon.ini"
P_IRAQ_MR = r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Su-24MR.ini"

VN_YAK = r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetYak130.ini"
VN_MIG29 = r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetMig29S.ini"
VN_F5E = r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetF5E.ini"
VN_MI17 = r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetMi17.ini"
VN_MIG21 = r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetMig21.ini"
VN_MIG21BIS = r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetMig21bis.ini"
VN_SU22 = r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu22.ini"
VN_SU22M4 = r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu22M4.ini"
VN_SU27UB = r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu27UB.ini"
VN_SU30 = r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu30.ini"
VN_SU30MK2 = r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu30MK2.ini"
VN_L39 = r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetL39.ini"
VN_B21_NEW = r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetB21.ini"

SY_MIG21 = r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig21.ini"
SY_MIG21MF = r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig21MF.ini"
SY_MIG23 = r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig23.ini"
SY_MIG25 = r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetMig25.ini"
SY_SU22 = r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetSu22.ini"
SY_SU22M4 = r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetSu22M4.ini"
SY_SU24 = r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetSu24.ini"
SY_L39 = r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetL39.ini"
SY_MIG29 = r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\Syria_Mig-29A.ini"
SY_MIRAGE = r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\Syria_MirageF1-Bq.ini"
SY_SU25 = r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\Syria_Su-25K.ini"
SY_MI8 = r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\Syria_Mi-8.ini"
SY_H6K_NEW = r"Data\INI\Object\Specter\Syrian Armed Forces\Airforce\SyriaBomberH6K.ini"

USA_B21 = r"Data\INI\Object\Specter\United States Of America\AmericaJetB21Clean.ini"
CHINA_H6K = r"Data\INI\Object\Specter\PLA\Airforce\H6K.ini"

STD44 = [
    r"Data\INI\Object\Specter\British Armed Forces\Airforce\BritainJetF35B.ini",
    r"Data\INI\Object\Specter\British Armed Forces\Rotary\CH47F.ini",
    r"Data\INI\Object\Specter\German Armed Forces\Rotary\CH47F.ini",
    r"Data\INI\Object\Specter\Iraq Army\Airforce\IraqJetF16IQ.ini",
    r"Data\INI\Object\Specter\Iraq Army\Airforce\IraqJetIL76.ini",
    r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Tu-22M3.ini",
    r"Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyJetF35B.ini",
    r"Data\INI\Object\Specter\Italian Armed Forces\Rotary\CH47F.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetEA6B.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF18G.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF35B.ini",
    r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetIL76.ini",
    r"Data\INI\Object\Specter\Libyan Armed Forces\Airforce\LibyaJetJ7.ini",
    r"Data\INI\Object\Specter\NATO\Airforce\NatoJetF18E.ini",
    r"Data\INI\Object\Specter\NATO\Airforce\NatoJetF18F.ini",
    r"Data\INI\Object\Specter\NATO\Airforce\NatoJetF35B.ini",
    r"Data\INI\Object\Specter\NATO\FixedWings\EA18G.ini",
    r"Data\INI\Object\Specter\NATO\FixedWings\F35A.ini",
    r"Data\INI\Object\Specter\NATO\Rotary\AH64E.ini",
    r"Data\INI\Object\Specter\NATO\Rotary\CH47F.ini",
    r"Data\INI\Object\Specter\NATO\Rotary\UH60.ini",
    r"Data\INI\Object\Specter\North Korea\Airforce\Iraq_Mig-25BM.ini",
    r"Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetJ7.ini",
    r"Data\INI\Object\Specter\Pakistan Armed Forces\Airforce\Pakistan_F16Blk52.ini",
    r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetAH64E.ini",
    r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF35B.ini",
    r"Data\INI\Object\Specter\Shared\SpecterPlayableIL76.ini",
    r"Data\INI\Object\Specter\South African National Defence Force\Airforce\SouthAfricaJetIL76.ini",
    r"Data\INI\Object\Specter\Swedish Armed Forces\Rotary\AH64E.ini",
    r"Data\INI\Object\Specter\Swedish Armed Forces\Rotary\CH47F.ini",
    r"Data\INI\Object\Specter\Swedish Armed Forces\Rotary\UH60.ini",
    r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetJ7.ini",
    r"Data\INI\Object\Specter\Turkish Armed Forces\Rotary\AH64E.ini",
    r"Data\INI\Object\Specter\Turkish Armed Forces\Rotary\CH47F.ini",
    r"Data\INI\Object\Specter\Turkish Armed Forces\Rotary\UH60.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Airforce\UkraineJetSu27.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Rotary\AH64E.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Rotary\CH47F.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Rotary\UH60.ini",
    r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Airforce\UAE_F16Blk52.ini",
    r"Data\INI\Object\Specter\United Arab Emirates\Airforce\UAEJetF15E.ini",
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Airforce\Iraq_Mig-25BM.ini",
    r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetIL76.ini",
    r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu27.ini",
]

REF_PROTECTED = [
    USA_B21,
    r"Data\INI\Object\Specter\United States Of America\AmericaJetB21A.ini",
    CHINA_H6K,
    r"Data\INI\Object\Specter\PLA\Airforce\H20.ini",
    r"Data\INI\Object\Specter\PLA\Airforce\H20A.ini",
    r"Data\INI\Object\Specter\PLA\Airforce\JH7A2.ini",
    r"Data\INI\Object\Specter\PLA\Airforce\ChinaBomberH6K_B21A.ini",
    P_IRAQ_MR,
    P_WEAPON,
]


def norm(name: str) -> str:
    return name.replace("/", "\\")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_big_list(path: Path) -> list[tuple[str, bytes]]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries: list[tuple[str, bytes]] = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def build_big_ordered(entries: list[tuple[str, bytes]]) -> bytes:
    header_size = 16
    encoded_names: list[bytes] = []
    for name, _ in entries:
        nb = name.encode("latin1", errors="replace")
        encoded_names.append(nb)
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded_names):
        content = bytes(content)
        index.append((nb, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def find_index(entries: list[tuple[str, bytes]], target: str) -> int:
    t = norm(target).lower()
    hits = [i for i, (n, _) in enumerate(entries) if norm(n).lower() == t]
    if len(hits) != 1:
        raise SystemExit(f"{target}: expected 1 packed path, got {len(hits)}")
    return hits[0]


def raw_of(entries, target) -> bytes:
    return entries[find_index(entries, target)][1]


def text_of(entries, target) -> str:
    return raw_of(entries, target).decode("latin1", errors="replace")


def set_text(entries, target, text: str) -> None:
    i = find_index(entries, target)
    name = entries[i][0]
    entries[i] = (name, text.encode("latin1", errors="replace"))


def add_file(entries, name: str, text: str) -> None:
    n = norm(name)
    if any(norm(x).lower() == n.lower() for x, _ in entries):
        raise SystemExit(f"already packed: {name}")
    entries.append((n, text.encode("latin1", errors="replace")))


def file_nl(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def to_nl(s: str, nl: str) -> str:
    return s.replace("\r\n", "\n").replace("\n", nl)


def must_replace_once(text: str, old: str, new: str, label: str) -> str:
    nl = file_nl(text)
    old = to_nl(old, nl)
    new = to_nl(new, nl)
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly 1 occurrence, got {n}; OLD={old[:220]!r}")
    return text.replace(old, new, 1)


def replace_commandset(text: str, name: str, body_lines: list[str]) -> str:
    nl = file_nl(text)
    m = re.search(rf"(?im)^CommandSet\s+{re.escape(name)}\s*$", text)
    if not m:
        raise SystemExit(f"missing CommandSet {name}")
    m2 = re.search(r"(?im)^CommandSet\s+\S+", text[m.end() :])
    end = m.end() + m2.start() if m2 else len(text)
    block = "CommandSet " + name + nl
    for line in body_lines:
        block += line + nl
    block += "End" + nl + nl
    return text[: m.start()] + block + text[end:].lstrip("\r\n")


def patch_button_image(text: str, button: str, new_image: str, label: str) -> str:
    m = re.search(rf"(?im)^CommandButton\s+{re.escape(button)}\s*$", text)
    if not m:
        raise SystemExit(f"{label}: missing CommandButton {button}")
    m2 = re.search(r"(?im)^CommandButton\s+\S+", text[m.end() :])
    end = m.end() + m2.start() if m2 else len(text)
    block = text[m.start() : end]
    new_block, n = re.subn(
        r"(?im)^(\s*ButtonImage\s*=\s*)\S+",
        rf"\1{new_image}",
        block,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"{label}: ButtonImage replace failed for {button} n={n}")
    return text[: m.start()] + new_block + text[end:]


def patch_object_portraits(text: str, portrait: str) -> str:
    text2, n1 = re.subn(r"(?im)^(\s*SelectPortrait\s*=\s*)\S+", rf"\1{portrait}", text, count=1)
    text3, n2 = re.subn(r"(?im)^(\s*ButtonImage\s*=\s*)\S+", rf"\1{portrait}", text2, count=1)
    if n1 != 1 or n2 != 1:
        raise SystemExit(f"portrait patch failed n1={n1} n2={n2}")
    return text3


def set_scale(text: str, new_scale: str, label: str) -> str:
    m = re.search(r"(?im)^Scale\s*=\s*\S+", text)
    if not m:
        raise SystemExit(f"{label}: no Scale")
    return text[: m.start()] + f"Scale = {new_scale}" + text[m.end() :]


def replace_weapon_slot(text: str, slot: str, old_wpn: str, new_wpn: str, label: str) -> str:
    nl = file_nl(text)
    rx = re.compile(
        rf"^([ \t]*Weapon[ \t]*=[ \t]*{re.escape(slot)}[ \t]+){re.escape(old_wpn)}\b",
        re.M,
    )
    hits = list(rx.finditer(text))
    if len(hits) != 1:
        raise SystemExit(f"{label}: expected 1 {slot} {old_wpn}, got {len(hits)}")
    m = hits[0]
    return text[: m.start()] + m.group(1) + new_wpn + text[m.end() :]


def add_tertiary_weapon(text: str, weapon: str, label: str) -> str:
    nl = file_nl(text)
    m = re.search(r"(?im)^(\s*Weapon\s*=\s*PRIMARY\s+\S+[^\n]*\n)", text)
    if not m:
        raise SystemExit(f"{label}: no PRIMARY weapon to insert after")
    insert = m.group(1) + f"    Weapon            = TERTIARY    {weapon}" + nl
    return text[: m.start()] + insert + text[m.end() :]


def promote_player_upgrade_weaponset(text: str, label: str) -> tuple[str, bool]:
    """If a PLAYER_UPGRADE WeaponSet exists, make it Conditions=None and drop the old None set."""
    blocks = list(re.finditer(r"^  WeaponSet\b[^\n]*\n(?:.*\n)*?^  End", text, re.M))
    none_i = None
    up_i = None
    for i, m in enumerate(blocks):
        if re.search(r"(?im)^\s*Conditions\s*=\s*PLAYER_UPGRADE\b", m.group(0)):
            up_i = i
        elif re.search(r"(?im)^\s*Conditions\s*=\s*None\b", m.group(0)):
            none_i = i
    if up_i is None:
        return text, False
    up = blocks[up_i].group(0)
    up_new = re.sub(r"(?im)^(\s*Conditions\s*=\s*)PLAYER_UPGRADE\b", r"\1None", up, count=1)
    if none_i is not None:
        # replace None block with promoted, delete PLAYER_UPGRADE block
        none = blocks[none_i]
        upm = blocks[up_i]
        if none.start() < upm.start():
            text = text[: none.start()] + up_new + text[none.end() : upm.start()] + text[upm.end() :]
        else:
            text = text[: upm.start()] + text[upm.end() : none.start()] + up_new + text[none.end() :]
    else:
        text = text[: blocks[up_i].start()] + up_new + text[blocks[up_i].end() :]
    return text, True


def strip_unit_science_locks(text: str) -> tuple[str, int]:
    """Remove object-level Science/RequiredScience/NeededUpgrade production locks.

    Leaves building Object= prerequisites and TriggeredBy optional upgrades.
    """
    n = 0

    def drop(rx: str, s: str) -> str:
        nonlocal n
        s2, c = re.subn(rx, "", s, flags=re.M)
        n += c
        return s2

    text = drop(r"^[ \t]*Science[ \t]*=[ \t]*.*\n", text)
    text = drop(r"^[ \t]*RequiredScience[ \t]*=[ \t]*.*\n", text)
    text = drop(r"^[ \t]*ForbiddenScience[ \t]*=[ \t]*.*\n", text)
    text = drop(r"^[ \t]*NeededUpgrade[ \t]*=[ \t]*.*\n", text)
    return text, n


def clone_b21(src: str) -> str:
    t = src
    t = t.replace("Object AmericaJetB21Clean", "Object VietnamJetB21", 1)
    t = t.replace("  Side                = America", "  Side                = Vietnam", 1)
    t = t.replace("  BuildCost           = 12000", "  BuildCost           = 15000", 1)
    t = t.replace("  DisplayName         = OBJECT:AmericaJetB21", "  DisplayName         = OBJECT:VietnamJetB21", 1)
    header = (
        "; SPECTER1 Vietnam B-21 clone. Donor AmericaJetB21Clean (NOT modified).\n"
        "; Same visual AVB21_A, same weapons/locomotor, Vietnam identity, cost 15000.\n"
    )
    if not t.startswith(";"):
        t = header + t
    else:
        t = header + t
    if "Object VietnamJetB21" not in t or "Side                = Vietnam" not in t:
        raise SystemExit("B21 clone identity failed")
    if "AmericaJetB21Clean" in t.split("\n", 8)[-1] and "Object AmericaJetB21Clean" in t:
        raise SystemExit("B21 clone still named America")
    if re.search(r"(?m)^Object AmericaJetB21Clean\b", t):
        raise SystemExit("B21 clone still has America object name")
    return t


def clone_h6k(src: str) -> str:
    t = src
    t = t.replace("Object ChinaBomberH6K", "Object SyriaBomberH6K", 1)
    t = t.replace("  Side                = China", "  Side                = Syria", 1)
    t = t.replace("  BuildCost           = 4500", "  BuildCost           = 20000", 1)
    t = t.replace("  DisplayName         = OBJECT:ChinaBomberH6K", "  DisplayName         = OBJECT:SyriaBomberH6K", 1)
    header = (
        "; SPECTER1 Syria H-6K clone. Donor ChinaBomberH6K (NOT modified).\n"
        "; Same visual h6k, same weapons/locomotor, Syria identity, cost 20000.\n"
    )
    t = header + t
    if re.search(r"(?m)^Object ChinaBomberH6K\b", t):
        raise SystemExit("H6K clone still has China object name")
    if "Side                = Syria" not in t:
        raise SystemExit("H6K clone side failed")
    return t


def parse_buttons(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r"(?im)^CommandButton\s+(\S+)\s*$", text):
        m2 = re.search(r"(?im)^CommandButton\s+\S+", text[m.end() :])
        out[m.group(1)] = text[m.start() : m.end() + m2.start() if m2 else len(text)]
    return out


def parse_commandsets(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r"(?im)^CommandSet\s+(\S+)\s*$", text):
        m2 = re.search(r"(?im)^CommandSet\s+\S+", text[m.end() :])
        out[m.group(1)] = text[m.start() : m.end() + m2.start() if m2 else len(text)]
    return out


def parse_objects(entries) -> dict[str, str]:
    names: dict[str, str] = {}
    for n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        if "\\object\\" not in n.lower().replace("/", "\\"):
            continue
        t = b.decode("latin1", errors="replace")
        for m in re.finditer(r"(?im)^Object\s+(\S+)", t):
            names.setdefault(m.group(1), n)
    return names


def object_folder_illegal(entries) -> list[str]:
    bad = []
    rx = re.compile(r"(?im)^(CommandSet|CommandButton|MappedImage|Science|Upgrade)\s+(\S+)")
    for n, b in entries:
        ln = n.lower().replace("/", "\\")
        if "\\ini\\object\\" not in ln or not ln.endswith(".ini"):
            continue
        t = b.decode("latin1", errors="replace")
        for i, line in enumerate(t.splitlines(), 1):
            if line.strip().startswith(";"):
                continue
            m = rx.match(line)
            if m:
                bad.append(f"{n}:{i} {m.group(1)} {m.group(2)}")
    return bad


def mapped_images(entries) -> set[str]:
    names: set[str] = set()
    for n, b in entries:
        if "mappedimage" not in n.lower() and not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", errors="replace")
        if "MappedImage" not in t:
            continue
        for m in re.finditer(r"(?im)^MappedImage\s+(\S+)", t):
            names.add(m.group(1))
    return names


def art_stems(art_entries) -> set[str]:
    stems: set[str] = set()
    for n, _ in art_entries:
        base = n.replace("/", "\\").split("\\")[-1]
        stem = base.rsplit(".", 1)[0].lower()
        stems.add(stem)
    return stems


def weapon_clip(weapon_text: str, name: str) -> str:
    m = re.search(rf"(?im)^Weapon\s+{re.escape(name)}\s*$", weapon_text)
    if not m:
        return "?"
    m2 = re.search(r"(?im)^Weapon\s+\S+", weapon_text[m.end() :])
    blk = weapon_text[m.start() : m.end() + m2.start() if m2 else m.end() + 800]
    c = re.search(r"(?im)^\s*ClipSize\s*=\s*(\S+)", blk)
    return c.group(1) if c else "?"


def main() -> int:
    data_sha = sha256_file(SRC_DATA)
    art_sha = sha256_file(SRC_ART)
    if data_sha != EXPECTED_DATA_SHA:
        raise SystemExit(f"DATA SHA mismatch {data_sha}")
    if art_sha != EXPECTED_ART_SHA:
        raise SystemExit(f"ART SHA mismatch {art_sha}")

    entries = read_big_list(SRC_DATA)
    art_entries = read_big_list(SRC_ART)
    baseline_hashes = {norm(n).lower(): hashlib.sha256(b).hexdigest() for n, b in entries}

    # --- Vietnam Yak-130 visual: Italy M346 / Yak-130 family mesh LSFT50d ---
    yak = text_of(entries, VN_YAK)
    yak = must_replace_once(
        yak,
        "    DefaultConditionState\n      Model               = LSFT50\n",
        "    DefaultConditionState\n      Model               = LSFT50d\n",
        "yak130 default model",
    )
    set_text(entries, VN_YAK, yak)

    # --- scales ---
    mig29 = set_scale(text_of(entries, VN_MIG29), "1.00", "vn mig29")
    set_text(entries, VN_MIG29, mig29)
    f5e = set_scale(text_of(entries, VN_F5E), "0.90", "vn f5e")
    set_text(entries, VN_F5E, f5e)
    sy21 = set_scale(text_of(entries, SY_MIG21), "1.18", "sy mig21bis")
    set_text(entries, SY_MIG21, sy21)
    sy21mf = set_scale(text_of(entries, SY_MIG21MF), "1.08", "sy mig21mf")
    set_text(entries, SY_MIG21MF, sy21mf)

    # --- Vietnam Mi-17 visual + combat fire from VietnamHelicopterMi8AMTSh ---
    mi17 = text_of(entries, VN_MI17)
    mi17 = must_replace_once(
        mi17,
        "    ConditionState = REALLYDAMAGED\n      Model = Egy_MI17\n",
        "    ConditionState = REALLYDAMAGED\n      Model = Egy_MI17D\n",
        "mi17 damaged model",
    )
    mi17 = must_replace_once(
        mi17,
        "  ArmorSet\n    Conditions      = None\n    Armor           = ChinookArmor\n    DamageFX        = None\n  End\n",
        "  WeaponSet\n    Conditions        = None\n    Weapon            = PRIMARY    16x_80mm_S8_Rockets_Mi17\n  End\n"
        "  ArmorSet\n    Conditions      = None\n    Armor           = ChinookArmor\n    DamageFX        = None\n  End\n",
        "mi17 weaponset insert",
    )
    mi17 = must_replace_once(
        mi17,
        "  KindOf          = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE TRANSPORT AIRCRAFT SCORE PRODUCED_AT_HELIPAD\n",
        "  KindOf          = PRELOAD CAN_ATTACK CAN_CAST_REFLECTIONS SELECTABLE VEHICLE TRANSPORT AIRCRAFT SCORE PRODUCED_AT_HELIPAD\n",
        "mi17 can_attack",
    )
    mi17 = must_replace_once(
        mi17,
        "    AutoAcquireEnemiesWhenIdle    = No\n",
        "    AutoAcquireEnemiesWhenIdle    = Yes\n",
        "mi17 autoacquire",
    )
    set_text(entries, VN_MI17, mi17)

    # --- Vietnam bomb diversity (do not touch STD44 VietnamJetSu27) ---
    set_text(
        entries,
        VN_MIG29,
        replace_weapon_slot(
            text_of(entries, VN_MIG29),
            "TERTIARY",
            "VietnamJetMig29S_WpnGun",
            "Gbu-12II_Paveway",
            "vn mig29 bomb",
        ),
    )
    # Mig21 already Kab500_LeaserGuidedBomb — keep
    # Su22 already GBU24 projectile via VietnamJetSu22_WpnBomb — keep
    set_text(
        entries,
        VN_SU30,
        replace_weapon_slot(
            text_of(entries, VN_SU30),
            "TERTIARY",
            "VietnamJetSu30_WpnStrike",
            "GBU_31V2_JDAM_F15E",
            "vn su30 bomb",
        ),
    )
    set_text(
        entries,
        VN_YAK,
        replace_weapon_slot(
            text_of(entries, VN_YAK),
            "TERTIARY",
            "VietnamJetYak130_WpnBomb",
            "GBU38_JDAM_F16C",
            "vn yak bomb",
        ),
    )
    set_text(
        entries,
        VN_F5E,
        replace_weapon_slot(
            text_of(entries, VN_F5E),
            "TERTIARY",
            "VietnamJetF5E_WpnBomb",
            "6_MK-82",
            "vn f5e bomb",
        ),
    )
    # Mig21bis already China_Weapon_Bomb_Q5 — keep as Chinese/Q-5 family
    set_text(
        entries,
        VN_SU22M4,
        replace_weapon_slot(
            text_of(entries, VN_SU22M4),
            "TERTIARY",
            "VietnamJetSu22M4_WpnBomb",
            "ODAB_500_PMV_SU39",
            "vn su22m4 bomb",
        ),
    )
    set_text(
        entries,
        VN_SU27UB,
        replace_weapon_slot(
            text_of(entries, VN_SU27UB),
            "TERTIARY",
            "VietnamJetSu27UB_WpnGun",
            "GBU-39_SDB_F22A",
            "vn su27ub bomb",
        ),
    )
    set_text(
        entries,
        VN_SU30MK2,
        replace_weapon_slot(
            text_of(entries, VN_SU30MK2),
            "SECONDARY",
            "VietnamJetSu30MK2_WpnBomb",
            "Kab2500_LeaserGuidedBomb",
            "vn su30mk2 bomb",
        ),
    )
    set_text(
        entries,
        VN_L39,
        replace_weapon_slot(
            text_of(entries, VN_L39),
            "TERTIARY",
            "VietnamJetL39_WpnBomb",
            "Paveway_IV_EF2000",
            "vn l39 bomb",
        ),
    )

    # --- Syria bomb diversity (do not touch STD44 SyriaJetJ7) ---
    sy_mig29 = text_of(entries, SY_MIG29)
    sy_mig29 = patch_object_portraits(sy_mig29, "irq_mig29a")
    if ";Weapon            = SECONDARY   Vympel_R-73_Mig29A" in sy_mig29:
        sy_mig29 = must_replace_once(
            sy_mig29,
            ";Weapon            = SECONDARY   Vympel_R-73_Mig29A\n",
            "    Weapon            = SECONDARY   Vympel_R-73_Mig29A\n"
            "    Weapon            = TERTIARY    Gbu-12II_Paveway\n",
            "sy mig29 weapons",
        )
    else:
        sy_mig29 = add_tertiary_weapon(sy_mig29, "Gbu-12II_Paveway", "sy mig29 tertiary")
    sy_mig29 = must_replace_once(
        sy_mig29,
        "      DefaultConditionState\n      Model               = Irq_Mig29A\n      HideSubObject       = BurnerFX01 BurnerFX02\n      WeaponLaunchBone    = PRIMARY Weapona\n",
        "      DefaultConditionState\n      Model               = Irq_Mig29A\n      HideSubObject       = BurnerFX01 BurnerFX02\n      WeaponLaunchBone    = PRIMARY Weapona\n      WeaponLaunchBone    = TERTIARY Weapona\n",
        "sy mig29 launch bone",
    )
    set_text(entries, SY_MIG29, sy_mig29)

    sy_mirage = text_of(entries, SY_MIRAGE)
    sy_mirage = patch_object_portraits(sy_mirage, "irq_miragef")
    sy_mirage = add_tertiary_weapon(sy_mirage, "Paveway_IV_EF2000", "sy mirage bomb")
    set_text(entries, SY_MIRAGE, sy_mirage)

    set_text(
        entries,
        SY_MIG23,
        replace_weapon_slot(
            text_of(entries, SY_MIG23),
            "TERTIARY",
            "SyriaJetMig23_WpnStrike",
            "GBU_31V2_JDAM_F15E",
            "sy mig23 bomb",
        ),
    )
    sy_mig25 = add_tertiary_weapon(text_of(entries, SY_MIG25), "AGM-154C_JSOW_F16C", "sy mig25 bomb")
    set_text(entries, SY_MIG25, sy_mig25)
    # SyriaJetMig21 already Kab500 — keep
    set_text(
        entries,
        SY_MIG21MF,
        replace_weapon_slot(
            text_of(entries, SY_MIG21MF),
            "TERTIARY",
            "SyriaJetMig21MF_WpnBomb",
            "6_MK-82",
            "sy mig21mf bomb",
        ),
    )
    # SyriaJetJ7 STD44 — keep Kab500
    set_text(
        entries,
        SY_SU22,
        replace_weapon_slot(
            text_of(entries, SY_SU22),
            "SECONDARY",
            "SyriaJetSu22_WpnBomb",
            "Kab1500_LeaserGuidedBomb",
            "sy su22 bomb",
        ),
    )
    set_text(
        entries,
        SY_SU22M4,
        replace_weapon_slot(
            text_of(entries, SY_SU22M4),
            "TERTIARY",
            "SyriaJetSu22M4_WpnBomb",
            "ODAB_500_PMV_SU39",
            "sy su22m4 bomb",
        ),
    )
    set_text(
        entries,
        SY_SU24,
        replace_weapon_slot(
            text_of(entries, SY_SU24),
            "SECONDARY",
            "SyriaJetSu24_WpnBomb",
            "Kab2500_LeaserGuidedBomb",
            "sy su24 bomb",
        ),
    )
    set_text(
        entries,
        SY_L39,
        replace_weapon_slot(
            text_of(entries, SY_L39),
            "TERTIARY",
            "SyriaJetL39_WpnBomb",
            "GBU38_JDAM_F16C",
            "sy l39 bomb",
        ),
    )

    sy_su25 = text_of(entries, SY_SU25)
    sy_su25 = patch_object_portraits(sy_su25, "irq_su25k")
    sy_su25, promoted = promote_player_upgrade_weaponset(sy_su25, "sy su25")
    if not promoted:
        raise SystemExit("Syria_Su-25K PLAYER_UPGRADE WeaponSet not found")
    set_text(entries, SY_SU25, sy_su25)

    sy_mi8 = patch_object_portraits(text_of(entries, SY_MI8), "irq_mi8t")
    set_text(entries, SY_MI8, sy_mi8)

    # --- Syria unlock: strip science/upgrade unit locks on Syria object INIs ---
    unlock_files = 0
    unlock_lines = 0
    loadout_gates_remaining = 0
    for n, b in list(entries):
        ln = n.replace("/", "\\")
        if not ln.lower().endswith(".ini"):
            continue
        if "Syrian" not in ln:
            continue
        if "\\object\\" not in ln.lower():
            continue
        if norm(ln).lower() in {norm(x).lower() for x in STD44}:
            continue
        t = b.decode("latin1", errors="replace")
        t2, stripped = strip_unit_science_locks(t)
        t3, did_promo = promote_player_upgrade_weaponset(t2, n)
        if stripped or did_promo or t3 != t:
            set_text(entries, n, t3)
            unlock_files += 1
            unlock_lines += stripped
        if re.search(r"(?im)^\s*Conditions\s*=\s*PLAYER_UPGRADE\b", t3):
            if re.search(r"(?im)^Object\s+", t3) and "WeaponSet" in t3:
                # remaining PLAYER_UPGRADE weaponsets on this file
                loadout_gates_remaining += len(
                    re.findall(r"(?im)^\s*Conditions\s*=\s*PLAYER_UPGRADE\b", t3)
                )

    # --- clones (new files; donors untouched) ---
    add_file(entries, VN_B21_NEW, clone_b21(text_of(entries, USA_B21)))
    add_file(entries, SY_H6K_NEW, clone_h6k(text_of(entries, CHINA_H6K)))

    # --- CommandButtons ---
    btn = text_of(entries, P_CMDBTN)
    btn = patch_button_image(btn, "Command_ConstructSyria_Mig-29A", "irq_mig29a", "btn mig29")
    btn = patch_button_image(btn, "Command_ConstructSyria_MirageF1_Bq", "irq_miragef", "btn mirage")
    btn = patch_button_image(btn, "Command_ConstructSyria_Su-25K", "irq_su25k", "btn su25")
    btn = patch_button_image(btn, "Command_ConstructSyria_Mi-8T", "irq_mi8t", "btn mi8")
    btn = patch_button_image(btn, "Command_ConstructSyria_IL-76", "yier76", "btn il76")
    nl = file_nl(btn)
    extra_btns = (
        nl
        + "CommandButton Command_ConstructVietnamJetB21"
        + nl
        + "  Command          = UNIT_BUILD"
        + nl
        + "  Object           = VietnamJetB21"
        + nl
        + "  TextLabel        = CONTROLBAR:ConstructAmericaJetB21"
        + nl
        + "  ButtonImage      = B21_L"
        + nl
        + "  ButtonBorderType = BUILD"
        + nl
        + "  DescriptLabel    = CONTROLBAR:ToolTipAmericaJetB21"
        + nl
        + "End"
        + nl
        + nl
        + "CommandButton Command_ConstructSyriaBomberH6K"
        + nl
        + "  Command          = UNIT_BUILD"
        + nl
        + "  Object           = SyriaBomberH6K"
        + nl
        + "  TextLabel        = CONTROLBAR:ConstructChinaBomberH6K"
        + nl
        + "  ButtonImage      = pla_h6k"
        + nl
        + "  ButtonBorderType = BUILD"
        + nl
        + "  DescriptLabel    = CONTROLBAR:ToolTipChinaBomberH6K"
        + nl
        + "End"
        + nl
    )
    if not btn.endswith(nl):
        btn += nl
    btn += extra_btns
    set_text(entries, P_CMDBTN, btn)

    # --- CommandSets ---
    cs = text_of(entries, P_CMDSET)
    cs = replace_commandset(
        cs,
        "Vietnam_AirfieldCommandSet",
        [
            "  1 = Command_ConstructVietnamJetMig29S",
            "  2 = Command_ConstructVietnamJetMig21",
            "  3 = Command_ConstructVietnamJetSu22",
            "  4 = Command_ConstructVietnamJetSu27",
            "  5 = Command_ConstructVietnamJetSu30",
            "  6 = Command_ConstructVietnamJetYak130",
            "  7 = Command_ConstructVietnamJetF5E",
            "  8 = Command_ConstructVietnamJetMig21bis",
            "  9 = Command_ConstructVietnamJetSu22M4",
            "  10 = Command_ConstructVietnamJetSu30MK2",
            "  11 = Command_ConstructVietnamJetSu27UB",
            "  12 = Command_ConstructVietnamJetL39",
            "  13 = Command_SetRallyPoint",
            "  14 = Command_Sell",
        ],
    )
    cs = replace_commandset(
        cs,
        "Vietnam_HeavyAirBaseCommandSet",
        [
            "  1 = Command_ConstructVietnamJetMi8",
            "  2 = Command_ConstructVietnamJetMi17",
            "  3 = Command_ConstructVietnamJetIL76",
            "  4 = Command_ConstructVietnamAir_Tu22M3M",
            "  5 = Command_ConstructVietnamJetB21",
            "  6 = Command_ConstructVietnamAir_Ka52M",
            "  13 = Command_SetRallyPoint",
            "  14 = Command_Sell",
        ],
    )
    cs = replace_commandset(
        cs,
        "Syria_BarracksCommandSet",
        [
            "  1 = Command_ConstructIraq_RepublicanGuard_AKMS",
            "  2 = Command_ConstructIraq_RepublicanGuard_RPG7",
            "  3 = Command_ConstructIraq_RepublicanGuardMortar",
            "  4 = Command_ConstructIraq_RepublicanGuardKornet",
            "  5 = Command_ConstructIraq_RepublicanGuard_Pkm",
            "  6 = Command_ConstructIraq_RepublicanGuard_TBK14",
            "  7 = Command_ConstructIraq_RepublicanGuard_Eng",
            "  8 = Command_ConstructIraq_SpecialForces",
            "  9 = Command_ConstructIraq_RepublicanGuardIgla",
            "  14 = Command_Sell",
        ],
    )
    cs = replace_commandset(
        cs,
        "Syria_HeavyAirBaseCommandSet",
        [
            "  1 = Command_ConstructSyria_Mi-8T",
            "  2 = Command_ConstructSyria_IL-76",
            "  3 = Command_ConstructSyriaBomberH6K",
            "  13 = Command_SetRallyPoint",
            "  14 = Command_Sell",
        ],
    )
    set_text(entries, P_CMDSET, cs)

    # --- integrity: protected files unchanged ---
    for p in STD44 + REF_PROTECTED:
        i = find_index(entries, p)
        new_h = hashlib.sha256(entries[i][1]).hexdigest()
        old_h = baseline_hashes[norm(p).lower()]
        if new_h != old_h:
            raise SystemExit(f"PROTECTED FILE CHANGED: {p}")

    # donors still original names
    if "Object AmericaJetB21Clean" not in text_of(entries, USA_B21):
        raise SystemExit("USA B21 damaged")
    if "BuildCost           = 12000" not in text_of(entries, USA_B21):
        raise SystemExit("USA B21 cost changed")
    if "Object ChinaBomberH6K" not in text_of(entries, CHINA_H6K):
        raise SystemExit("China H6K damaged")
    if "BuildCost           = 4500" not in text_of(entries, CHINA_H6K):
        raise SystemExit("China H6K cost changed")

    # --- static validation ---
    objs = parse_objects(entries)
    seen: dict[str, list[str]] = {}
    for n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        if "\\object\\" not in n.lower().replace("/", "\\"):
            continue
        t = b.decode("latin1", errors="replace")
        for m in re.finditer(r"(?im)^Object\s+(\S+)", t):
            seen.setdefault(m.group(1), []).append(n)
    # Baseline already contains cross-country duplicate Object names. Fail only on NEW ones.
    new_dupes = []
    for on in ("VietnamJetB21", "SyriaBomberH6K"):
        files = seen.get(on, [])
        if len(files) != 1:
            new_dupes.append(f"{on} files={files}")
    if "VietnamJetB21" not in seen or "SyriaBomberH6K" not in seen:
        raise SystemExit("clone objects missing from Object parse")
    dupes = new_dupes
    # last-win map for command button Object= checks
    last_seen = {k: v[-1] for k, v in seen.items()}
    seen = last_seen
    illegal = object_folder_illegal(entries)
    btns = parse_buttons(text_of(entries, P_CMDBTN))
    btns.update(parse_buttons(text_of(entries, P_CMDSET)))
    csets = parse_commandsets(text_of(entries, P_CMDSET))
    images = mapped_images(entries)
    astems = art_stems(art_entries)
    weapons = set(re.findall(r"(?im)^Weapon\s+(\S+)", text_of(entries, P_WEAPON)))

    missing_btn = []
    missing_obj = []
    missing_img = []
    missing_wpn = []
    locked_counts = {
        "barracks": 0,
        "warfactory": 0,
        "aircraft": 0,
        "helicopter": 0,
    }

    def audit_cs(cs_name: str, bucket: str | None = None) -> list[str]:
        blk = csets[cs_name]
        cmds = re.findall(r"(?m)^\s*\d+\s*=\s*(\S+)", blk)
        rows = []
        for c in cmds:
            if c in ("Command_SetRallyPoint", "Command_Sell"):
                continue
            b = btns.get(c)
            if not b:
                missing_btn.append(f"{cs_name} -> {c}")
                continue
            if re.search(r"(?i)RequiredScience|NeededUpgrade", b) or re.search(
                r"(?i)Options\s*=\s*.*NEED", b
            ):
                if bucket:
                    locked_counts[bucket] += 1
            objm = re.search(r"(?im)^\s*Object\s*=\s*(\S+)", b)
            imgm = re.search(r"(?im)^\s*ButtonImage\s*=\s*(\S+)", b)
            if objm and objm.group(1) not in seen:
                missing_obj.append(f"{c} Object={objm.group(1)}")
            if imgm and imgm.group(1) not in images:
                missing_img.append(f"{c} ButtonImage={imgm.group(1)}")
            rows.append(c)
        return rows

    vn_air = audit_cs("Vietnam_AirfieldCommandSet", "aircraft")
    vn_heavy = audit_cs("Vietnam_HeavyAirBaseCommandSet", "helicopter")
    sy_air = audit_cs("Syria_AirfieldCommandSet", "aircraft")
    sy_heavy = audit_cs("Syria_HeavyAirBaseCommandSet", "helicopter")
    sy_bar = audit_cs("Syria_BarracksCommandSet", "barracks")
    sy_wf = audit_cs("Syria_WarFactoryCommandSet", "warfactory")

    # weapon refs on edited aircraft
    for path, wpn in [
        (VN_MIG29, "Gbu-12II_Paveway"),
        (VN_SU30, "GBU_31V2_JDAM_F15E"),
        (VN_YAK, "GBU38_JDAM_F16C"),
        (VN_F5E, "6_MK-82"),
        (VN_SU22M4, "ODAB_500_PMV_SU39"),
        (VN_SU27UB, "GBU-39_SDB_F22A"),
        (VN_SU30MK2, "Kab2500_LeaserGuidedBomb"),
        (VN_L39, "Paveway_IV_EF2000"),
        (VN_MI17, "16x_80mm_S8_Rockets_Mi17"),
        (SY_MIG23, "GBU_31V2_JDAM_F15E"),
        (SY_MIG25, "AGM-154C_JSOW_F16C"),
        (SY_MIG21MF, "6_MK-82"),
        (SY_SU22, "Kab1500_LeaserGuidedBomb"),
        (SY_SU22M4, "ODAB_500_PMV_SU39"),
        (SY_SU24, "Kab2500_LeaserGuidedBomb"),
        (SY_L39, "GBU38_JDAM_F16C"),
        (VN_B21_NEW, "AmericaB21_DualGBU72Weapon"),
        (SY_H6K_NEW, "China_Weapon_Carpet_H6K"),
    ]:
        if wpn not in weapons:
            missing_wpn.append(wpn)

    # models for changed visuals
    model_checks = {
        "LSFT50d": "yak130",
        "Egy_MI17": "mi17",
        "Egy_MI17D": "mi17d",
        "AVB21_A": "b21",
        "h6k": "h6k",
        "RUS_Ka52M2": "ka52",
    }
    missing_models = [m for m in model_checks if m.lower() not in astems]

    if dupes:
        raise SystemExit("duplicate objects: " + "; ".join(dupes[:8]))
    if illegal:
        raise SystemExit("illegal Object-folder blocks: " + "; ".join(illegal[:8]))
    if missing_btn:
        raise SystemExit("missing buttons: " + "; ".join(missing_btn[:8]))
    if missing_obj:
        raise SystemExit("missing objects: " + "; ".join(missing_obj[:8]))
    if missing_wpn:
        raise SystemExit("missing weapons: " + "; ".join(missing_wpn[:8]))
    if missing_models:
        raise SystemExit("missing W3D: " + ", ".join(missing_models))
    if len(vn_air) != 12:
        raise SystemExit(f"Vietnam fighters {len(vn_air)} != 12")

    # recount Syria PLAYER_UPGRADE weaponsets on playable producers after edits
    loadout_after = 0
    playable_syria = [
        SY_MIG21, SY_MIG21MF, SY_MIG23, SY_MIG25, SY_SU22, SY_SU22M4, SY_SU24, SY_L39,
        SY_MIG29, SY_MIRAGE, SY_SU25, SY_MI8, SY_H6K_NEW,
        r"Data\INI\Object\Specter\Syrian Arab Army\Airforce\SyriaJetJ7.ini",
    ]
    ws_up_rx = re.compile(r"^  WeaponSet\b[^\n]*\n(?:.*\n)*?^  End", re.M)
    for p in playable_syria:
        t = text_of(entries, p)
        for blk in ws_up_rx.findall(t):
            if re.search(r"(?im)^\s*Conditions\s*=\s*PLAYER_UPGRADE\b", blk):
                loadout_after += 1

    wtxt = text_of(entries, P_WEAPON)

    def clip(name: str) -> str:
        return weapon_clip(wtxt, name)

    changed = []
    for n, b in entries:
        h = hashlib.sha256(b).hexdigest()
        key = norm(n).lower()
        if key not in baseline_hashes or baseline_hashes[key] != h:
            changed.append(n)
    changed.sort()

    blob = build_big_ordered(entries)
    new_sha = hashlib.sha256(blob).hexdigest()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(blob)
    (WS_OUT / "_SPEC_DATA_ONE.big").write_bytes(blob)
    # ART unchanged — copy baseline ART into this release so the ZIP is complete
    art_bytes = SRC_ART.read_bytes()
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(art_bytes)
    (WS_OUT / "_SPEC_ART_ONE.big").write_bytes(art_bytes)

    lines: list[str] = []
    p = lines.append
    p("SPECTER1 VIETNAM + SYRIA ROSTER 01")
    p("BASELINE_DATA_SHA256 = " + EXPECTED_DATA_SHA)
    p("BASELINE_ART_SHA256 = " + EXPECTED_ART_SHA)
    p("NEW_DATA_SHA256 = " + new_sha)
    p("NEW_ART_SHA256 = " + EXPECTED_ART_SHA + " (unchanged copy)")
    p("NEW_DATA_BYTES = " + str(len(blob)))
    p("NEW_DATA_FILE_COUNT = " + str(len(entries)))
    p("MODE = DATA edits from crashfix+shadow ART baseline; ART packed unchanged")
    p("")
    p("=== VIETNAM YAK-130 ===")
    p("CURRENT_MODEL_BEFORE = LSFT50 (T-50 / FA-50 / L-159 family mesh)")
    p("DEDICATED_YAK130_W3D_IN_ART = NONE")
    p("CORRECT_EXISTING_YAK130_FAMILY_VISUAL = ItalyJetM346FA DefaultConditionState Model LSFT50d")
    p("NOTE = M-346 is the Yak-130 derivative; LSFT50d is the live Yak-130-family visual already in Specter ART.")
    p("VIETNAM_YAK130_NEW_MODEL = LSFT50d")
    p("VIETNAM_YAK130_BUTTON_PRESERVED = SPEC_VietnamJetYak130")
    p("VIETNAM_YAK130_SIDE_PRESERVED = Vietnam")
    p("VIETNAM_YAK130_VISUAL_FIXED = YES")
    p("")
    p("=== VIETNAM SCALES ===")
    p("VIETNAM_MIG29_OLD_SCALE = 0.90")
    p("VIETNAM_MIG29_NEW_SCALE = 1.00")
    p("VIETNAM_MIG29_REFERENCE = UkraineJetMig29 0.96 / GermanyJetMiG29G 0.90 same mesh LSFruMiG29; moderate +11%")
    p("VIETNAM_MIG29_SCALE_FIXED = YES")
    p("VIETNAM_F5E_OLD_SCALE = 0.80")
    p("VIETNAM_F5E_NEW_SCALE = 0.90")
    p("VIETNAM_F5E_REFERENCE = SouthKoreaJetF5E 1.00 same mesh LSFKoreaF5; moderate +12.5% not full jump")
    p("VIETNAM_F5E_SCALE_FIXED = YES")
    p("")
    p("=== VIETNAM MI-17 ===")
    p("BUG = production VietnamJetMi17 had Egy_MI17 visual but no WeaponSet, no CAN_ATTACK, AutoAcquire=No")
    p("VISUAL_FIX = damaged mesh Egy_MI17D (Egypt donor draw); live mesh remains Egy_MI17")
    p("DONOR_OBJECT = VietnamHelicopterMi8AMTSh")
    p("DONOR_WEAPON = 16x_80mm_S8_Rockets_Mi17")
    p("DONOR_LOGIC = CAN_ATTACK + AutoAcquireEnemiesWhenIdle=Yes + same ChinookLocomotor / JetAIUpdate")
    p("VIETNAM_MI17_BUG_FIXED = YES")
    p("VIETNAM_MI17_FIRE_WORKING = YES (static: weapon+CAN_ATTACK grafted from working donor)")
    p("")
    p("=== VIETNAM FIGHTERS 7 -> 12 ===")
    p("CURRENT_7 = VietnamJetMig29S, VietnamJetMig21, VietnamJetSu22, VietnamJetSu27, VietnamJetSu30, VietnamJetYak130, VietnamJetF5E")
    p("ADDED_5 = VietnamJetMig21bis, VietnamJetSu22M4, VietnamJetSu30MK2, VietnamJetSu27UB, VietnamJetL39")
    p("ADDED_SOURCE = existing Vietnam People's Army objects + CommandButtons already in CommandSet.ini")
    p("VIETNAM_FIGHTER_COUNT = 12")
    p("FINAL_12 =")
    p("  1 VietnamJetMig29S")
    p("  2 VietnamJetMig21")
    p("  3 VietnamJetSu22")
    p("  4 VietnamJetSu27")
    p("  5 VietnamJetSu30")
    p("  6 VietnamJetYak130")
    p("  7 VietnamJetF5E")
    p("  8 VietnamJetMig21bis")
    p("  9 VietnamJetSu22M4")
    p("  10 VietnamJetSu30MK2")
    p("  11 VietnamJetSu27UB")
    p("  12 VietnamJetL39")
    p("")
    p("=== VIETNAM BOMB DIVERSITY ===")
    p("VIETNAM AIRCRAFT | DEFAULT AIR WEAPON | BOMB TYPE | BOMB COUNT")
    p(f"VietnamJetMig29S | VietnamJetMig29S_WpnRadar / WpnIR | GBU-12 Paveway (Gbu-12II_Paveway) | {clip('Gbu-12II_Paveway')}")
    p(f"VietnamJetMig21 | VietnamJetMig21_WpnIR / WpnGun | KAB-500 (Kab500_LeaserGuidedBomb) | {clip('Kab500_LeaserGuidedBomb')}")
    p(f"VietnamJetSu22 | VietnamJetSu22_WpnIR | GBU-24 (VietnamJetSu22_WpnBomb / GBU24_GuidedBombObject) | {clip('VietnamJetSu22_WpnBomb')}")
    p(f"VietnamJetSu27 | KH29T_AGM_SU30MKA | FAB-500 (4x_Fab500_SU34) [STD44 preserved] | {clip('4x_Fab500_SU34')}")
    p(f"VietnamJetSu30 | VietnamJetSu30_WpnRadar / WpnIR | GBU-31 JDAM (GBU_31V2_JDAM_F15E) | {clip('GBU_31V2_JDAM_F15E')}")
    p(f"VietnamJetYak130 | VietnamJetYak130_WpnGun / WpnRkt | GBU-38 JDAM (GBU38_JDAM_F16C) | {clip('GBU38_JDAM_F16C')}")
    p(f"VietnamJetF5E | VietnamJetF5E_WpnGun / WpnRkt | Mk-82 (6_MK-82) | {clip('6_MK-82')}")
    p(f"VietnamJetMig21bis | VietnamJetMig21bis_WpnIR / WpnGun | Q-5 bomb family (China_Weapon_Bomb_Q5) | {clip('China_Weapon_Bomb_Q5')}")
    p(f"VietnamJetSu22M4 | VietnamJetSu22M4_WpnGun / WpnRkt | ODAB-500 (ODAB_500_PMV_SU39) | {clip('ODAB_500_PMV_SU39')}")
    p(f"VietnamJetSu27UB | VietnamJetSu27UB_WpnRadar / WpnIR | GBU-39 SDB (GBU-39_SDB_F22A) | {clip('GBU-39_SDB_F22A')}")
    p(f"VietnamJetSu30MK2 | VietnamJetSu30MK2_WpnIR | KAB-2500 (Kab2500_LeaserGuidedBomb) | {clip('Kab2500_LeaserGuidedBomb')}")
    p(f"VietnamJetL39 | VietnamJetL39_WpnGun / WpnRkt | Paveway IV (Paveway_IV_EF2000) | {clip('Paveway_IV_EF2000')}")
    p("VIETNAM_BOMB_DIVERSITY_APPLIED = YES")
    p("WEAPON_INI_NEW_ENTRIES = 0")
    p("")
    p("=== VIETNAM B-21 / COMBAT HELI ===")
    p("VIETNAM_B21_ADDED = YES")
    p("VIETNAM_B21_OBJECT = VietnamJetB21")
    p("VIETNAM_B21_DONOR = AmericaJetB21Clean (NOT modified)")
    p("VIETNAM_B21_MODEL = AVB21_A")
    p("VIETNAM_B21_WEAPON = AmericaB21_DualGBU72Weapon")
    p("VIETNAM_B21_COST = 15000")
    p("VIETNAM_COMBAT_HELICOPTER_ADDED = YES")
    p("VIETNAM_COMBAT_HELICOPTER = VietnamHelicopterKa52M")
    p("VIETNAM_COMBAT_HELICOPTER_BUTTON = Command_ConstructVietnamAir_Ka52M")
    p("VIETNAM_COMBAT_HELICOPTER_MODEL = RUS_Ka52M2")
    p("VIETNAM_COMBAT_HELICOPTER_WEAPONS = 30mm_2A42_Ka52 / 12x_ATGM_9K121_Vikhr / Vympel_R-73_Ka52")
    p("")
    p("=== SYRIA SCALES ===")
    p("SYRIA_MIG21BIS_OBJECT = SyriaJetMig21 (live slot 5; UVMig-21 bis mesh)")
    p("SYRIA_MIG21BIS_OLD_SCALE = 1.08")
    p("SYRIA_MIG21BIS_NEW_SCALE = 1.18")
    p("SYRIA_MIG21BIS_REFERENCE = UkraineJetMig21/LibyaJetMig21 1.06-1.08 same UVMig-21; moderate +9%")
    p("SYRIA_MIG21BIS_SCALE_FIXED = YES")
    p("SYRIA_MIG21MF_OBJECT = SyriaJetMig21MF")
    p("SYRIA_MIG21MF_OLD_SCALE = 0.96")
    p("SYRIA_MIG21MF_NEW_SCALE = 1.08")
    p("SYRIA_MIG21MF_REFERENCE = LibyaJetMig21MF 0.96; match prior Syria bis size; moderate +12.5%")
    p("SYRIA_MIG21MF_SCALE_FIXED = YES")
    p("")
    p("=== SYRIA AIRCRAFT BUTTONS ===")
    p("SYRIA AIRCRAFT -> OLD BUTTON IMAGE -> NEW BUTTON IMAGE -> SELECT PORTRAIT")
    p("Syria_Mig-29A -> irq_t72a / us_airfield -> irq_mig29a -> irq_mig29a")
    p("Syria_MirageF1_Bq -> irq_t72a / us_commandcenter -> irq_miragef -> irq_miragef")
    p("SyriaJetMig23 -> SPEC_SyriaJetMig23 -> SPEC_SyriaJetMig23 (correct, unchanged) -> SPEC_SyriaJetMig23")
    p("SyriaJetMig25 -> SPEC_SyriaJetMig25 -> SPEC_SyriaJetMig25 (correct, unchanged) -> SPEC_SyriaJetMig25")
    p("SyriaJetMig21 -> SPEC_SyriaJetMig21 -> SPEC_SyriaJetMig21 (correct, unchanged) -> SPEC_SyriaJetMig21")
    p("SyriaJetMig21MF -> SPEC_SyriaJetMig21MF -> SPEC_SyriaJetMig21MF (correct, unchanged) -> SPEC_SyriaJetMig21MF")
    p("SyriaJetJ7 -> SPEC_SyriaJetJ7 -> SPEC_SyriaJetJ7 (correct, unchanged) -> SPEC_SyriaJetJ7")
    p("SyriaJetSu22 -> SPEC_SyriaJetSu22 -> SPEC_SyriaJetSu22 (correct, unchanged) -> SPEC_SyriaJetSu22")
    p("SyriaJetSu22M4 -> SPEC_SyriaJetSu22M4 -> SPEC_SyriaJetSu22M4 (correct, unchanged) -> SPEC_SyriaJetSu22M4")
    p("Syria_Su-25K -> irq_t72a / us_airfield -> irq_su25k -> irq_su25k")
    p("SyriaJetSu24 -> SPEC_SyriaJetSu24 -> SPEC_SyriaJetSu24 (correct, unchanged) -> SPEC_SyriaJetSu24")
    p("SyriaJetL39 -> SPEC_SyriaJetL39 -> SPEC_SyriaJetL39 (correct, unchanged) -> SPEC_SyriaJetL39")
    p("Syria_Mi-8T -> irq_t72a / us_commandcenter -> irq_mi8t -> irq_mi8t")
    p("SpecterPlayableIL76 (Syria IL-76 button) -> irq_t72a -> yier76 -> yier76")
    p("SYRIA_AIRCRAFT_BUTTONS_FIXED = YES")
    p("")
    p("=== SYRIA CHINESE BOMBER ===")
    p("SYRIA_CHINESE_BOMBER_ADDED = YES")
    p("SYRIA_CHINESE_BOMBER_OBJECT = SyriaBomberH6K")
    p("SYRIA_CHINESE_BOMBER_DONOR = ChinaBomberH6K (China_HeavyAirBase slot 3, NOT modified)")
    p("SYRIA_CHINESE_BOMBER_MODEL = h6k")
    p("SYRIA_CHINESE_BOMBER_WEAPONS = China_Weapon_Carpet_H6K / China_Weapon_CJ10_H6K / China_Weapon_FAB_H6K")
    p("SYRIA_CHINESE_BOMBER_COST = 20000")
    p("")
    p("=== SYRIA BOMB DIVERSITY ===")
    p("SYRIA AIRCRAFT | DEFAULT AIR WEAPON | BOMB TYPE | BOMB COUNT")
    p(f"Syria_Mig-29A | 4x_R27_MRBVR_Mig29A / Vympel_R-73_Mig29A | GBU-12 Paveway (Gbu-12II_Paveway) | {clip('Gbu-12II_Paveway')}")
    p(f"Syria_MirageF1_Bq | 2x_KH29L_AGM_F1EQ | Paveway IV (Paveway_IV_EF2000) | {clip('Paveway_IV_EF2000')}")
    p(f"SyriaJetMig23 | SyriaJetMig23_WpnRadar / WpnIR | GBU-31 JDAM (GBU_31V2_JDAM_F15E) | {clip('GBU_31V2_JDAM_F15E')}")
    p(f"SyriaJetMig25 | SyriaJetMig25_WpnRadar / WpnIR | JSOW (AGM-154C_JSOW_F16C) | {clip('AGM-154C_JSOW_F16C')}")
    p(f"SyriaJetMig21 | SyriaJetMig21_WpnIR / WpnGun | KAB-500 (Kab500_LeaserGuidedBomb) | {clip('Kab500_LeaserGuidedBomb')}")
    p(f"SyriaJetMig21MF | SyriaJetMig21MF_WpnIR / WpnGun | Mk-82 (6_MK-82) | {clip('6_MK-82')}")
    p(f"SyriaJetJ7 | China_Weapon_S5_J7 | KAB-500 (Kab500_LeaserGuidedBomb) [STD44 preserved] | {clip('Kab500_LeaserGuidedBomb')}")
    p(f"SyriaJetSu22 | SyriaJetSu22_WpnIR | KAB-1500 (Kab1500_LeaserGuidedBomb) | {clip('Kab1500_LeaserGuidedBomb')}")
    p(f"SyriaJetSu22M4 | SyriaJetSu22M4_WpnGun / WpnRkt | ODAB-500 (ODAB_500_PMV_SU39) | {clip('ODAB_500_PMV_SU39')}")
    p(f"Syria_Su-25K | KH-25ML_Missile / S-8_Rocket_SU25 | FAB-250 (Fab-250) | {clip('Fab-250')}")
    p(f"SyriaJetSu24 | SyriaJetSu24_WpnIR | KAB-2500 (Kab2500_LeaserGuidedBomb) | {clip('Kab2500_LeaserGuidedBomb')}")
    p(f"SyriaJetL39 | SyriaJetL39_WpnGun / WpnRkt | GBU-38 JDAM (GBU38_JDAM_F16C) | {clip('GBU38_JDAM_F16C')}")
    p("SYRIA_BOMB_DIVERSITY_APPLIED = YES")
    p("")
    p("=== SYRIA INFANTRY ===")
    p("SYRIA_OLD_INFANTRY_REMOVED_FROM_PRODUCTION = YES")
    p("IRAQ_INFANTRY_ROSTER_USED_FOR_SYRIA = YES")
    p("SYRIA BARRACKS INFANTRY OBJECTS =")
    p("  Iraq_RepublicanGuard_AKMS")
    p("  Iraq_RepublicanGuard_RPG7")
    p("  Iraq_RepublicanGuardMortar")
    p("  Iraq_RepublicanGuardKornet")
    p("  Iraq_RepublicanGuard_Pkm")
    p("  Iraq_RepublicanGuard_TBK14")
    p("  Iraq_RepublicanGuard_Eng")
    p("  Iraq_SpecialForces_Akms")
    p("  Iraq_RepublicanGuardIgla")
    p("SYRIA_INFANTRY_REPLACED_WITH_IRAQ = YES")
    p("")
    p("=== SYRIA UNLOCK ===")
    p("UNLOCK_OBJECT_FILES_TOUCHED = " + str(unlock_files))
    p("SCIENCE_LOCK_LINES_REMOVED = " + str(unlock_lines))
    p("SYRIA_BARRACKS_LOCKED_UNIT_COUNT = " + str(locked_counts["barracks"]))
    p("SYRIA_WARFACTORY_LOCKED_UNIT_COUNT = " + str(locked_counts["warfactory"]))
    p("SYRIA_AIRCRAFT_LOCKED_UNIT_COUNT = " + str(locked_counts["aircraft"]))
    p("SYRIA_HELICOPTER_LOCKED_UNIT_COUNT = " + str(locked_counts["helicopter"]))
    p("SYRIA_WEAPON_LOADOUT_UPGRADE_GATE_COUNT = " + str(loadout_after))
    p("SYRIA_ALL_UNIT_UPGRADE_LOCKS_REMOVED = YES")
    p("BUILDING_CHAIN_PREREQS_PRESERVED = YES (Power/Supply/Barracks/WarFactory/Airbase Object prereqs not stripped from buildings)")
    p("")
    p("=== SAFETY ===")
    p("USA_B21_DONOR_UNCHANGED = YES")
    p("CHINA_H6K_DONOR_UNCHANGED = YES")
    p("IRAQ_SU24MR_UNCHANGED = YES")
    p("STD44_FILES_UNCHANGED = YES")
    p("AIRBASE_ARCHITECTURE_UNCHANGED = YES")
    p("WEAPON_INI_CHANGED = NO")
    p("OBJECT_FOLDER_COMMANDSET_BLOCKS = " + str(len(illegal)))
    p("DUPLICATE_OBJECT_NAMES = " + str(len(dupes)))
    p("MISSING_COMMANDBUTTONS = " + str(len(missing_btn)))
    p("MISSING_BUTTONIMAGES = " + str(len(missing_img)) + ((" " + "; ".join(missing_img[:12])) if missing_img else ""))
    p("")
    p("CHANGED_PATHS =")
    for n in changed:
        p("  " + n)
    p("")
    p("DATA_CHANGED = YES")
    p("ART_CHANGED = NO")
    p("INGAME_TESTED = NO")
    p("RELEASE_OVERWRITES_PREVIOUS = NO")

    audit = "\n".join(lines) + "\n"
    changelog = """SPECTER1 Vietnam + Syria Roster 01

Continues from SPECTER1_Aircraft_Standardization_01_CRASHFIX_TEST DATA and SPECTER1_Shadow_AH1Z_ART_01 ART.
Does not rebuild from older SPECTER archives. Does not overwrite previous GitHub Releases.

Vietnam:
- Yak-130 visual: no dedicated Yak-130 W3D exists in current ART. Switched DefaultConditionState from LSFT50 (T-50 family) to LSFT50d, the live Italy M-346 / Yak-130-family mesh. Button/side preserved.
- MiG-29 scale 0.90 -> 1.00. F-5E scale 0.80 -> 0.90.
- Mi-17: fixed missing weapons/CAN_ATTACK; damaged mesh Egy_MI17D; combat fire from VietnamHelicopterMi8AMTSh weapon 16x_80mm_S8_Rockets_Mi17. Model remains Egy_MI17.
- Airfield fighters 7 -> 12 by adding existing VietnamJetMig21bis, Su22M4, Su30MK2, Su27UB, L39.
- Bomb diversity across 12 fighters using existing Weapon.ini families (GBU-12/24/31/38/39, Mk-82, KAB-500/2500, ODAB, Paveway IV, Q-5). STD44 VietnamJetSu27 FAB-500 left unchanged.
- Added VietnamJetB21 clone of AmericaJetB21Clean at cost 15000. USA B-21 not modified.
- Added existing VietnamHelicopterKa52M to HeavyAirBase.

Syria:
- MiG-21bis (SyriaJetMig21) 1.08 -> 1.18. MiG-21MF 0.96 -> 1.08.
- Replaced tank-icon aircraft buttons (irq_t72a / us_airfield / us_commandcenter) with irq_mig29a, irq_miragef, irq_su25k, irq_mi8t, yier76. SPEC_SyriaJet* buttons were already correct.
- Added SyriaBomberH6K clone of live ChinaBomberH6K at cost 20000. China H-6K not modified.
- Bomb diversity across Syrian fighters using existing families. STD44 SyriaJetJ7 KAB-500 left unchanged.
- Barracks production replaced with Iraq infantry roster. Old Syria infantry buttons removed from production only.
- Stripped Science/RequiredScience/NeededUpgrade unit locks on Syria object INIs. Promoted Syria_Su-25K PLAYER_UPGRADE WeaponSet to default. Building-chain Object prerequisites kept.

No Weapon.ini new entries. No airbase architecture change. No Iraq Su-24MR / USA / Russia / China donor edits. ART packed unchanged.
INGAME_TESTED = NO
"""
    (OUT_DIR / "audit.txt").write_text(audit, encoding="utf-8")
    (OUT_DIR / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")

    zpath = WS_OUT / "SPECTER1_Vietnam_Syria_Roster_01.zip"
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(WS_OUT / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(WS_OUT / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(WS_OUT / "audit.txt", "audit.txt")
        zf.write(WS_OUT / "changelog.txt", "changelog.txt")
    (OUT_DIR / "SPECTER1_Vietnam_Syria_Roster_01.zip").write_bytes(zpath.read_bytes())

    print(audit)
    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", len(blob), new_sha)
    print("ZIP", zpath, zpath.stat().st_size)
    if locked_counts["barracks"] or locked_counts["warfactory"] or locked_counts["aircraft"] or locked_counts["helicopter"]:
        raise SystemExit(f"locks remain {locked_counts}")
    if loadout_after != 0:
        raise SystemExit(f"loadout gates remain {loadout_after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
