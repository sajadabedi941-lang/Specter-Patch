#!/usr/bin/env python3
"""CRLF-only parser-safety pass for packed Data\\INI\\CommandSet.ini.

Does not add/remove slots, CommandButtons, Objects, weapons, ART, or factions.
Rebuilds only _SPEC_DATA_ONE.big.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_global_commandbar_crashfix import last_blocks
from audit_national_ground_forces import parse_big as parse_big_idx
from build_global_commandbar_crashfix import is_country_commandset
from build_national_ground_forces import build_big_ordered, norm, parse_big
from national_ground_roster import COUNTRIES, LOCKED_BIG_PATHS, PROTECTED_COMMANDSETS

SRC_DATA = Path("/tmp/national_ground_commandbar/_SPEC_DATA_ONE.big")
ART = Path("/tmp/national_ground_commandbar/_SPEC_ART_ONE.big")
OUT_DATA = Path("/tmp/national_ground_commandbar/_SPEC_DATA_ONE.big")
IDENTITY_ART_SHA = "e72e6334ab7b9691e3327a0d0a76d4fe771b4cb607e656fa97106e4d69b90c12"
CS_KEY = r"data\ini\commandset.ini"


def nl(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


def commandset_slots(text: str) -> dict[str, list[tuple[str, str]]]:
    found = {}
    for m in re.finditer(r"(?ms)^CommandSet\s+(\S+)\s*\n.*?(?=^CommandSet\s|\Z)", nl(text)):
        found[m.group(1)] = re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", m.group(0))
    return found


def non_empty_lines(text: str) -> list[str]:
    return [ln.rstrip() for ln in nl(text).split("\n") if ln.strip() != ""]


def normalize_commandset_crlf(text: str) -> str:
    body = nl(text)
    body = re.sub(r"(?m)^(End|END)(?=CommandSet\s)", r"\1\n\n", body)
    body = re.sub(r"(?m)^(End|END)\n+(?=CommandSet\s)", r"\1\n\n", body)
    if not body.endswith("\n"):
        body += "\n"
    return body.replace("\n", "\r\n")


def scan_malformed(blob: bytes) -> list[str]:
    errs = []
    if blob.count(b"\r\r\n"):
        errs.append(r"found \r\r\n")
    if re.search(b"(?<!\r)\n", blob):
        errs.append("found LF not preceded by CR")
    if re.search(b"\r(?!\n)", blob):
        errs.append("found CR not followed by LF")
    if blob.count(b"\r\n\n"):
        errs.append(r"found \r\n\n")
    if re.search(b"\rCommandSet", blob):
        errs.append("found CR immediately before CommandSet")
    if b"EndCommandSet" in blob or b"ENDCommandSet" in blob:
        errs.append("found EndCommandSet concat")
    text = blob.decode("latin1")
    if re.search(r"(End|END)\r?\nCommandSet\s", text):
        errs.append("found End/CommandSet without blank line")
    if re.search(r"(End|END)\rCommandSet", text):
        errs.append("found End\\rCommandSet")
    # Every End/END that is followed by CommandSet must be End\r\n\r\nCommandSet
    for m in re.finditer(r"(End|END)\r\n(?:\r\n)+CommandSet\s", text):
        if m.group(0) != m.group(1) + "\r\n\r\nCommandSet ":
            # more than one blank line
            if not m.group(0).startswith(m.group(1) + "\r\n\r\n"):
                errs.append("unexpected End/CommandSet spacing")
    return errs


def main() -> int:
    if not SRC_DATA.is_file():
        print("missing packed DATA", file=sys.stderr)
        return 1
    art_sha = hashlib.sha256(ART.read_bytes()).hexdigest() if ART.is_file() else None
    if art_sha != IDENTITY_ART_SHA:
        raise SystemExit(f"ART SHA is not identity pack {art_sha}")

    entries = parse_big(SRC_DATA)
    src_names = [n for n, _ in entries]
    src_map = {norm(n): b for n, b in entries}
    idx = {norm(n): i for i, (n, _) in enumerate(entries)}
    i = idx[CS_KEY]
    name, old_blob = entries[i]
    old_text = old_blob.decode("latin1")
    old_slots = commandset_slots(old_text)
    old_nonempty = non_empty_lines(old_text)
    src_entries_idx = parse_big_idx(SRC_DATA)
    src_cs_blocks = last_blocks(src_entries_idx, "CommandSet")
    src_protected_slots = {
        pcs: re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", src_cs_blocks[pcs][1])
        for pcs in PROTECTED_COMMANDSETS
        if pcs in src_cs_blocks
    }
    src_commandbutton = src_map[norm(r"Data\INI\CommandButton.ini")]
    src_art = ART.read_bytes()

    new_text = normalize_commandset_crlf(old_text)
    new_blob = new_text.encode("latin1")
    if non_empty_lines(new_text) != old_nonempty:
        raise SystemExit("non-empty line content changed")
    new_slots = commandset_slots(new_text)
    if set(new_slots) != set(old_slots):
        raise SystemExit("CommandSet names changed")
    for csname, slots in old_slots.items():
        if new_slots[csname] != slots:
            raise SystemExit(f"slots changed {csname}")

    entries[i] = (name, new_blob)
    if [n for n, _ in entries] != src_names:
        raise SystemExit("DATA entry names/order changed")
    for n, b in entries:
        key = norm(n)
        if key == CS_KEY:
            continue
        if src_map[key] != b:
            raise SystemExit(f"non-CommandSet.ini file changed {n}")
        if key in {norm(p) for p in LOCKED_BIG_PATHS} and src_map[key] != b:
            raise SystemExit(f"locked file changed {n}")

    malformed = scan_malformed(new_blob)
    if malformed:
        raise SystemExit("malformed after normalize: " + "; ".join(malformed))
    if b"\n" in new_blob.replace(b"\r\n", b""):
        raise SystemExit("mixed line endings remain")

    data_big = build_big_ordered(entries)
    OUT_DATA.write_bytes(data_big)
    sha = hashlib.sha256(data_big).hexdigest()
    print("wrote", OUT_DATA)
    print("DATA_SHA256", sha)
    print("ART_SHA256", art_sha)

    # Re-extract and byte-scan
    extracted = parse_big(OUT_DATA)
    got = None
    for n, b in extracted:
        if norm(n) == CS_KEY:
            got = b
            break
    if got is None:
        raise SystemExit("CommandSet.ini missing after rebuild")
    if got != new_blob:
        raise SystemExit("re-extracted CommandSet.ini does not match written blob")
    bad = scan_malformed(got)
    if bad:
        raise SystemExit("re-extract malformed: " + "; ".join(bad))
    if b"\n" in got.replace(b"\r\n", b""):
        raise SystemExit("re-extract mixed line endings")
    if commandset_slots(got.decode("latin1")) != old_slots:
        raise SystemExit("re-extract slots changed")

    data = parse_big_idx(OUT_DATA)
    extracted_map = {norm(n): b for _i, n, b in data}
    if extracted_map[norm(r"Data\INI\CommandButton.ini")] != src_commandbutton:
        raise SystemExit("CommandButton.ini changed")
    if ART.read_bytes() != src_art:
        raise SystemExit("ART changed")

    def index_kind(kind):
        found = {}
        for _i, n, b in data:
            if not n.lower().endswith(".ini"):
                continue
            t = b.decode("latin1")
            for m in re.finditer(rf"(?m)^{kind}\s+(\S+)\s*$", t):
                found[m.group(1)] = n
        return found

    buttons = index_kind("CommandButton")
    objects = index_kind("Object")
    cs_blocks = last_blocks(data, "CommandSet")
    obj_blocks = last_blocks(data, "Object")
    btn_blocks = last_blocks(data, "CommandButton")

    def field(blk, name):
        m = re.search(rf"(?m)^\s*{name}\s+=\s+(\S+)", blk)
        return m.group(1) if m else None

    missing_btn = 0
    missing_obj = 0
    for csname, (_fn, blk) in cs_blocks.items():
        if not is_country_commandset(csname):
            continue
        for slot, btn in re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", blk):
            btn = btn.split(";")[0]
            if btn not in buttons:
                print("MISSING_BTN", csname, slot, btn)
                missing_btn += 1
                continue
            bhit = btn_blocks.get(btn)
            if not bhit:
                continue
            cmd = field(bhit[1], "Command")
            if cmd != "UNIT_BUILD":
                continue
            obj = field(bhit[1], "Object")
            if obj and obj not in objects:
                print("MISSING_OBJ", btn, obj)
                missing_obj += 1
    if missing_btn or missing_obj:
        raise SystemExit(f"missing_btn {missing_btn} missing_obj {missing_obj}")

    def live_obj(*names):
        for nm in names:
            if nm in obj_blocks:
                return nm
        return None

    for country in COUNTRIES:
        k = country.key
        if country.wf not in obj_blocks:
            raise SystemExit(f"missing WF object {country.wf}")
        wired = field(obj_blocks[country.wf][1], "CommandSet")
        if wired != country.cs:
            raise SystemExit(f"{k} WF wired {wired} != {country.cs}")
        hit = cs_blocks.get(country.cs)
        if not hit:
            raise SystemExit(f"missing CS {country.cs}")
        slots = {int(a): b.split(";")[0] for a, b in re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", hit[1])}
        if set(slots) != set(range(1, 15)):
            raise SystemExit(f"{k} slots {sorted(slots)}")
        for idx_u, unit in enumerate(country.units, 1):
            btn = f"Command_Construct{unit.obj}"
            if slots.get(idx_u) != btn:
                raise SystemExit(f"{k} slot {idx_u} {slots.get(idx_u)} != {btn}")
            if btn not in buttons:
                raise SystemExit(f"{k} missing button {btn}")
        for kind, obj_name in (
            ("CC", live_obj(f"{k}CommandCenter", f"{k}_CommandCenter")),
            ("Dozer", live_obj(f"{k}VehicleDozer", f"{k}_Dozer", f"{k}Dozer", f"{k}_VT72B")),
            ("Airfield", live_obj(f"{k}Airfield", f"{k}_Airfield", f"{k}_Airfield_T", f"{k}Airfield_T")),
        ):
            if not obj_name:
                continue
            csn = field(obj_blocks[obj_name][1], "CommandSet")
            if not csn or csn.startswith(";"):
                continue
            if csn not in cs_blocks:
                raise SystemExit(f"{k} {kind} CS missing {csn}")
            bad = [
                b.split(";")[0]
                for _s, b in re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", cs_blocks[csn][1])
                if b.split(";")[0] not in buttons
            ]
            if bad:
                raise SystemExit(f"{k} {kind} unbound {bad[:4]}")
        print("OK", k)

    for pcs, src_slot in src_protected_slots.items():
        if pcs not in cs_blocks:
            raise SystemExit(f"protected CS disappeared {pcs}")
        dst_slot = re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", cs_blocks[pcs][1])
        if src_slot != dst_slot:
            raise SystemExit(f"protected CS slots changed {pcs}")
        print("OK protected", pcs)

    print("CRLF_NORMALIZATION_OK")
    print(sha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
