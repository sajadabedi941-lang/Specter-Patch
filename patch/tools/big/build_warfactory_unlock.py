#!/usr/bin/env python3
"""Unlock destination War Factory units at game start.

Clones locked reference units into dest-only objects with empty Prerequisites,
adds dest-only CommandButtons, and rewrites live dest CommandSets to use them.
Strips dest Japan/Vietnam/SouthKorea CommandSetUpgrade modules.
Does not edit protected-country objects, CommandSets, or CommandButtons.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/tmp/warfactory_runtime/_SPEC_DATA_ONE.big")
OUT_DIR = Path("/tmp/warfactory_unlock")
REPO_OBJ = Path("/workspace/patch/Data/INI/Object/Specter/DestinationWarFactoryUnlock/WFUnlock_Objects.ini")
REPO_BTN = Path("/workspace/patch/Data/INI/CommandButton_WFUnlock.ini")

CS_INI = r"Data\INI\CommandSet.ini"
PK_INI = r"Data\INI\CommandSet_Pakistan.ini"
OBJ_NAME = r"Data\INI\Object\Specter\DestinationWarFactoryUnlock\WFUnlock_Objects.ini"
BTN_NAME = r"Data\INI\CommandButton_WFUnlock.ini"

LIVE_CS = [
    "BritainWarfactoryCommandSet",
    "GermanyWarfactoryCommandSet",
    "FranceWarfactoryCommandSet",
    "ItalyWarfactoryCommandSet",
    "UkraineWarfactoryCommandSet",
    "TurkeyWarfactoryCommandSet",
    "SwedenWarfactoryCommandSet",
    "Libya_WarFactoryCommandSet",
    "Libya_WarFactoryCommandSet1",
    "Libya_WarFactoryCommandSet2",
    "Libya_WarFactoryCommandSet3",
    "SouthAfrica_WarFactoryCommandSet",
    "SouthAfrica_WarFactoryCommandSet1",
    "SouthAfrica_WarFactoryCommandSet2",
    "SouthAfrica_WarFactoryCommandSet3",
    "UAE_WarFactoryCommandSet",
    "UAE_WarFactoryCommandSet1",
    "UAE_WarFactoryCommandSet2",
    "UAE_WarFactoryCommandSet3",
    "SaudiArabia_WarFactoryCommandSet",
    "SaudiArabia_WarFactoryCommandSet1",
    "SaudiArabia_WarFactoryCommandSet2",
    "SaudiArabia_WarFactoryCommandSet3",
    "Syria_WarFactoryCommandSet",
    "Syria_WarFactoryCommandSet1",
    "Syria_WarFactoryCommandSet2",
    "Syria_WarFactoryCommandSet3",
    "Japan_WarFactoryCommandSet",
    "Vietnam_WarFactoryCommandSet",
    "SouthKorea_WarFactoryCommandSet",
    "India_WarFactoryCommandSet",
    "India_WarFactoryCommandSet1",
    "India_WarFactoryCommandSet2",
    "India_WarFactoryCommandSet3",
    "Pakistan_WarFactoryCommandSet",
    "Pakistan_WarFactoryCommandSet1",
    "Pakistan_WarFactoryCommandSet2",
    "Pakistan_WarFactoryCommandSet3",
]

PROTECTED_CS = [
    "NatoWarfactoryCommandSet",
    "AmericaWarFactoryCommandSet",
    "AmericaWarFactoryCommandSet_T3",
    "RussiaWarFactoryCommandSet",
    "EgyptWarFactoryCommandSet",
    "Egypt_WarFactoryCommandSet",
    "Iraq_WarFactoryCommandSet_T3",
    "IranWarfactoryCommandSet",
    "Israel_WarFactoryCommandSet",
    "NorthKorea_WarFactoryCommandSet",
    "ChinaWarFactoryCommandSet",
]

PROTECTED_PATHS = (
    r"\united states of america\\",
    r"\armed forces of russian federation\\",
    r"\pla\\",
    r"\iranian army\\",
    r"\israel defense forces\\",
    r"\nato\\",
    r"\egyptian armed forces\\",
    r"\iraq army\\",
    r"\north korea\\",
    r"data\ini\playertemplate.ini",
    r"data\ini\science.ini",
    r"data\ini\commandbutton.ini",
)

DEST_UPGRADE_NEEDLES = (
    r"\japan self-defense forces\buildings\japan_warfactory.ini",
    r"\vietnam people's armed forces\buildings\vietnam_warfactory.ini",
    r"\south korean armed forces\buildings\southkorea_warfactory.ini",
)

SKIP_BTNS = {"Command_Sell", "Command_SetRallyPoint"}


def parse_big(path: Path):
    data = path.read_bytes()
    nfiles = struct.unpack(">I", data[8:12])[0]
    off = 16
    entries = []
    for _ in range(nfiles):
        eoff, esz = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries.append((name, data[eoff : eoff + esz]))
    return entries


def build_big_ordered(entries):
    header_size = 16
    encoded = [(n.encode("latin1"), b) for n, b in entries]
    for nb, _blob in encoded:
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for nb, blob in encoded:
        index.append((nb, offset, len(blob)))
        blobs.append(blob)
        offset += len(blob)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(encoded))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def parse_block(text, start):
    depth = 0
    buf = []
    for i, line in enumerate(text[start:].splitlines(True)):
        buf.append(line)
        raw = line.split(";", 1)[0]
        if i == 0:
            depth = 1
            continue
        if re.match(r"(?i)^\s*End\b", raw):
            depth -= 1
            if depth <= 0:
                break
        elif re.match(
            r"(?i)^\s*(Draw|Behavior|Body|WeaponSet|ArmorSet|Prerequisites|DefaultConditionState|ConditionState|UnitSpecificSounds|Turret)\b",
            raw,
        ):
            depth += 1
    return "".join(buf)


def last_block(kind, name, entries, reskin=False):
    found = None
    src = None
    if reskin:
        pat = re.compile(rf"(?im)^Object(?:Reskin)?\s+{re.escape(name)}\b")
    else:
        pat = re.compile(rf"(?im)^{kind}\s+{re.escape(name)}\b")
    for fname, blob in entries:
        text = blob.decode("latin1", errors="ignore")
        for m in pat.finditer(text):
            found = parse_block(text, m.start())
            src = fname
    return src, found


def extract_cs(text, name):
    pat = re.compile(rf"(?im)^CommandSet\s+{re.escape(name)}\b")
    found = None
    for m in pat.finditer(text):
        found = parse_block(text, m.start())
    return found


def cs_slots(blk):
    out = []
    if not blk:
        return out
    for line in blk.splitlines():
        raw = line.split(";", 1)[0]
        m = re.match(r"\s*(\d+)\s*=\s*(\S+)", raw)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def field(blk, key):
    if not blk:
        return None
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(\S+)", blk)
    return m.group(1) if m else None


def has_lock_prereq(oblk):
    if not oblk:
        return False
    m = re.search(r"(?ims)^\s*Prerequisites\b.*?^\s*End\b", oblk)
    if not m:
        return False
    body = m.group(0)
    return bool(re.search(r"(?im)^\s*(Object|Science)\s*=", body))


def strip_prereq(oblk, new_name, old_name):
    blk = re.sub(rf"(?im)^(Object(?:Reskin)?)\s+{re.escape(old_name)}\b", rf"\1 {new_name}", oblk, count=1)
    blk = re.sub(r"(?ims)^\s*Prerequisites\b.*?^\s*End\s*\r?\n", "", blk)
    return blk


def strip_upgrades(text):
    return re.sub(
        r"(?ims)^\s*Behavior\s*=\s*CommandSetUpgrade\b.*?^\s*End\s*\r?\n",
        "",
        text,
    )


def format_cs(name, slots, nl):
    lines = [f"CommandSet {name}"]
    for slot, btn in slots:
        if len(slot) == 1:
            lines.append(f"  {slot}  = {btn}")
        else:
            lines.append(f" {slot}  = {btn}")
    lines.append("End")
    return nl.join(lines) + nl


def replace_cs(text, name, slots):
    nl = "\r\n" if "\r\n" in text else "\n"
    pat = re.compile(rf"(?im)^CommandSet\s+{re.escape(name)}\b")
    matches = list(pat.finditer(text))
    if not matches:
        return text, 0
    new_blk = format_cs(name, slots, nl)
    out = text
    count = 0
    for m in reversed(matches):
        start = m.start()
        depth = 0
        end = None
        pos = start
        for i, line in enumerate(out[start:].splitlines(True)):
            raw = line.split(";", 1)[0]
            if i == 0:
                depth = 1
                pos += len(line)
                continue
            pos += len(line)
            if re.match(r"(?i)^\s*End\b", raw):
                depth -= 1
                if depth <= 0:
                    end = pos
                    break
        if end is None:
            raise SystemExit(f"unclosed CommandSet {name}")
        out = out[:start] + new_blk + out[end:]
        count += 1
    return out, count


def main() -> int:
    src = parse_big(SRC_DATA)
    cs_blob = pk_blob = None
    for n, b in src:
        key = n.replace("/", "\\")
        if key == CS_INI:
            cs_blob = b
        elif key == PK_INI:
            pk_blob = b
    if not cs_blob or not pk_blob:
        raise SystemExit("missing CommandSet.ini or CommandSet_Pakistan.ini")
    cs_text = cs_blob.decode("latin1")
    pk_text = pk_blob.decode("latin1")
    prot_before = {n: extract_cs(cs_text, n) for n in PROTECTED_CS}

    print("indexing objects/buttons")
    btn_idx = {}
    obj_idx = {}
    bpat = re.compile(r"(?im)^CommandButton\s+(\S+)")
    opat = re.compile(r"(?im)^Object(?:Reskin)?\s+(\S+)")
    for _fname, blob in src:
        text = blob.decode("latin1", errors="ignore")
        for m in bpat.finditer(text):
            btn_idx[m.group(1)] = parse_block(text, m.start())
        for m in opat.finditer(text):
            obj_idx[m.group(1)] = parse_block(text, m.start())

    # Collect dest buttons/objects that are locked
    locked = {}  # orig_obj -> (orig_btn, obj_blk, btn_blk)
    for name in LIVE_CS:
        blk = extract_cs(cs_text, name)
        if name.startswith("Pakistan"):
            pblk = extract_cs(pk_text, name)
            if pblk:
                blk = pblk
        for _slot, btn in cs_slots(blk):
            if btn in SKIP_BTNS:
                continue
            bblk = btn_idx.get(btn)
            obj = field(bblk, "Object")
            oblk = obj_idx.get(obj) if obj else None
            if obj and has_lock_prereq(oblk):
                locked[obj] = (btn, oblk, bblk)

    print("locked units", len(locked))
    for obj, (btn, _o, _b) in sorted(locked.items()):
        print(" ", obj, "via", btn)

    obj_parts = [
        "; Dest-only unlocked War Factory unit clones.",
        "; Prerequisites / Science / tech locks removed.",
        "; Protected country objects are not redefined here.",
        "",
    ]
    btn_parts = [
        "; Dest-only unlocked War Factory CommandButtons.",
        "; New names only. Protected CommandButtons are not redefined.",
        "",
    ]
    unlock_btn = {}  # orig_btn -> new_btn
    for obj, (btn, oblk, bblk) in sorted(locked.items()):
        new_obj = "WFUnlock_" + obj
        new_btn = "Command_ConstructWFUnlock_" + obj.replace("-", "_")
        unlock_btn[btn] = new_btn
        cloned = strip_prereq(oblk, new_obj, obj)
        if has_lock_prereq(cloned):
            print("FAIL still locked after strip", obj)
            return 1
        obj_parts.append(cloned.rstrip() + "\r\n\r\n")
        # rewrite button
        nb = bblk
        nb = re.sub(rf"(?im)^CommandButton\s+{re.escape(btn)}\b", f"CommandButton {new_btn}", nb, count=1)
        nb = re.sub(r"(?im)^(\s*Object\s*=\s*)\S+", rf"\1{new_obj}", nb, count=1)
        btn_parts.append(nb.rstrip() + "\r\n\r\n")

    obj_blob = ("\r\n".join(obj_parts[:4]) + "\r\n\r\n" + "".join(obj_parts[4:])).encode("latin1")
    btn_blob = ("\r\n".join(btn_parts[:3]) + "\r\n\r\n" + "".join(btn_parts[3:])).encode("latin1")

    REPO_OBJ.parent.mkdir(parents=True, exist_ok=True)
    REPO_OBJ.write_bytes(obj_blob)
    REPO_BTN.write_bytes(btn_blob)
    print("wrote", REPO_OBJ, len(obj_blob))
    print("wrote", REPO_BTN, len(btn_blob))

    # Rewrite dest CommandSets
    for name in LIVE_CS:
        use_pk = name.startswith("Pakistan")
        src_text = pk_text if use_pk else cs_text
        blk = extract_cs(src_text, name)
        if not blk and not use_pk:
            continue
        if not blk and use_pk:
            blk = extract_cs(cs_text, name)
            use_pk = False
            src_text = cs_text
        if not blk:
            print("WARN missing", name)
            continue
        slots = []
        for slot, btn in cs_slots(blk):
            slots.append((slot, unlock_btn.get(btn, btn)))
        if use_pk:
            pk_text, n = replace_cs(pk_text, name, slots)
            print("CS", name, "Pakistan.ini", n)
        else:
            cs_text, n = replace_cs(cs_text, name, slots)
            print("CS", name, "CommandSet.ini", n)

    for n in PROTECTED_CS:
        if extract_cs(cs_text, n) != prot_before[n]:
            print("FAIL protected CS mutated", n)
            return 1
    print("PROTECTED_CS_UNCHANGED")

    new_cs = cs_text.encode("latin1")
    new_pk = pk_text.encode("latin1")

    out = []
    for n, b in src:
        key = n.replace("/", "\\")
        low = key.lower()
        if key == CS_INI:
            out.append((n, new_cs))
        elif key == PK_INI:
            out.append((n, new_pk))
        elif any(low.endswith(needle) or needle in low for needle in DEST_UPGRADE_NEEDLES):
            stripped = strip_upgrades(b.decode("latin1"))
            if stripped == b.decode("latin1"):
                print("WARN no upgrades stripped", n)
            else:
                print("stripped CommandSetUpgrade", n)
            out.append((n, stripped.encode("latin1")))
        else:
            out.append((n, b))
    out.append((OBJ_NAME, obj_blob))
    out.append((BTN_NAME, btn_blob))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(out)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    dsha = hashlib.sha256(data_big).hexdigest()
    print("DATA", dsha, len(data_big))
    (OUT_DIR / "SHA256.txt").write_text(f"DATA {dsha}\n")

    packed = parse_big(OUT_DIR / "_SPEC_DATA_ONE.big")
    src_map = {n.replace("/", "\\").lower(): b for n, b in src}
    new_map = {n.replace("/", "\\").lower(): (n, b) for n, b in packed}
    print("DATA diffs:")
    for k, (n, b) in new_map.items():
        if src_map.get(k) != b:
            print(" ", n)
            low = n.lower()
            if any(tok in low for tok in PROTECTED_PATHS):
                print("FAIL protected path changed", n)
                return 1
    for n, _ in src:
        if n.replace("/", "\\").lower() not in new_map:
            print("  DEL", n)
    print("PACK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
