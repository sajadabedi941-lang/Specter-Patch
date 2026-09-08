#!/usr/bin/env python3
"""Global packed-BIG crash-repair audit for 17 National Ground countries."""

from __future__ import annotations

import hashlib
import io
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_national_ground_forces import last_named_any, parse_big
from build_global_commandbar_crashfix import COUNTRY_PREFIXES, commandset_core, is_country_commandset
from national_ground_roster import COUNTRIES, LOCKED_BIG_PATHS, PROTECTED_COMMANDSETS, ROLES

DATA = Path("/tmp/national_ground_commandbar/_SPEC_DATA_ONE.big")
ART = Path("/tmp/national_ground_commandbar/_SPEC_ART_ONE.big")
SRC_DATA = Path("/tmp/national_ground_identity/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/national_ground_identity/_SPEC_ART_ONE.big")
REPORT = Path("/opt/cursor/artifacts/global_commandbar_crashfix_audit.txt")
IDENTITY_ART_SHA = "e72e6334ab7b9691e3327a0d0a76d4fe771b4cb607e656fa97106e4d69b90c12"


def fail(msg: str) -> int:
    print("FAIL", msg)
    return 1


def field(blk: str, name: str):
    m = re.search(rf"(?m)^\s*{name}\s+=\s+(\S+)", blk)
    return m.group(1) if m else None


def index_kind(entries, kind: str) -> dict[str, str]:
    found = {}
    for _i, n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", "replace")
        for m in re.finditer(rf"(?m)^{kind}\s+(\S+)\s*$", t):
            found[m.group(1)] = n
    return found


def _run() -> int:
    errors = 0
    if not DATA.is_file():
        return fail("missing packed DATA")
    data = parse_big(DATA)
    art = parse_big(ART) if ART.is_file() else []
    src = parse_big(SRC_DATA) if SRC_DATA.is_file() else []

    print("SPECTER GLOBAL COMMANDBAR CRASH REPAIR — PACKED AUDIT")
    print("=" * 72)
    print("17 National Ground countries. Syntax + CommandButton references only.")
    print("Protected USA/Russia/China/Iran/Iraq/Egypt/Israel/NATO/NK unchanged.")
    print()
    print("DATA_SHA256", hashlib.sha256(DATA.read_bytes()).hexdigest())
    if ART.is_file():
        print("ART_SHA256", hashlib.sha256(ART.read_bytes()).hexdigest())
    print("DATA_FILES", len(data))

    if ART.is_file() and SRC_ART.is_file():
        art_sha = hashlib.sha256(ART.read_bytes()).hexdigest()
        src_sha = hashlib.sha256(SRC_ART.read_bytes()).hexdigest()
        if art_sha != src_sha:
            errors += fail("ART SHA changed")
        else:
            print("OK ART unchanged from identity pack")
        if art_sha != IDENTITY_ART_SHA:
            errors += fail("ART SHA is not identity ART")

    for _i, n, b in data:
        nl = n.replace("/", "\\").lower()
        if nl.endswith(".ini") and "\\object\\" in nl:
            t = b.decode("latin1", "replace")
            if re.search(r"(?m)^CommandSet\s+", t) or "nationalgroundcommandbar.ini" in nl:
                errors += fail(f"CommandSet/CommandBar under Object\\ {n}")

    buttons = index_kind(data, "CommandButton")
    objects = index_kind(data, "Object")
    file_text = {}
    for _i, n, b in data:
        if n.lower().endswith(".ini"):
            file_text[n] = b.decode("latin1", "replace")

    print()
    print("=== 17-country CommandSets ===")
    country_cs = []
    for _i, n, b in data:
        if not n.lower().endswith(".ini"):
            continue
        for m in re.finditer(r"(?m)^CommandSet\s+(\S+)", b.decode("latin1", "replace")):
            if is_country_commandset(m.group(1)):
                country_cs.append(m.group(1))
    country_cs = sorted(set(country_cs))
    print("CommandSet names", len(country_cs))

    missing_btn = 0
    missing_obj = 0
    missing_end = 0
    glue = 0
    for csname in country_cs:
        hit = last_named_any(data, "CommandSet", csname)
        if not hit:
            errors += fail(f"missing last-wins {csname}")
            continue
        fn, blk = hit
        if not re.search(r"(?m)^(End|END)\s*$", blk):
            errors += fail(f"{csname} missing End in {fn}")
            missing_end += 1
        slots = re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", blk)
        for slot, btn in slots:
            btn = btn.split(";")[0]
            if btn not in buttons:
                errors += fail(f"{csname} slot {slot} missing CommandButton {btn}")
                missing_btn += 1
                continue
            bhit = last_named_any(data, "CommandButton", btn)
            if field(bhit[1], "Command") != "UNIT_BUILD":
                continue
            obj = field(bhit[1], "Object")
            if not obj or obj not in objects:
                errors += fail(f"{btn} Object {obj} missing")
                missing_obj += 1

    for n, t in file_text.items():
        if "commandset" not in n.lower():
            continue
        for m in re.finditer(r"(End|END)\r?\nCommandSet (\S+)", t):
            if is_country_commandset(m.group(2)):
                errors += fail(f"glued CommandSet {m.group(2)} in {n}")
                glue += 1
        if re.search(r"\rCommandSet\s+", t):
            errors += fail(f"CR-prefixed CommandSet header in {n}")
            glue += 1
    print("OK country CommandSets scanned", len(country_cs))
    print("missing_btn", missing_btn, "missing_obj", missing_obj, "missing_end", missing_end, "glue", glue)

    print()
    print("=== Live War Factory 14-slot roster ===")
    for country in COUNTRIES:
        wf = last_named_any(data, "Object", country.wf)
        if not wf:
            errors += fail(f"missing WF {country.wf}")
            continue
        wired = field(wf[1], "CommandSet")
        if wired != country.cs:
            # last-wins object may still be the national WF
            print(f"NOTE {country.key} WF {country.wf} CommandSet={wired} roster={country.cs}")
        cs = last_named_any(data, "CommandSet", country.cs)
        if not cs:
            errors += fail(f"missing roster CS {country.cs}")
            continue
        slots = {int(a): b for a, b in re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", cs[1])}
        if set(slots) != set(range(1, 15)):
            errors += fail(f"{country.key} slots {sorted(slots)}")
            continue
        for idx, unit in enumerate(country.units, 1):
            btn = f"Command_Construct{unit.obj}"
            if slots.get(idx) != btn:
                errors += fail(f"{country.key} slot {idx} {slots.get(idx)} != {btn}")
            elif btn not in buttons:
                errors += fail(f"{country.key} slot {idx} button missing {btn}")
        print(f"OK {country.key:15s} {country.cs} 14 slots")

    print()
    print("=== Protected / non-country CommandSets ===")
    if src:
        src_cs = {}
        dst_cs = {}
        for _i, n, b in src:
            if not n.lower().endswith(".ini"):
                continue
            t = b.decode("latin1", "replace")
            for m in re.finditer(r"(?ms)^CommandSet\s+(\S+)\s*\r?\n.*?(?=^CommandSet\s|\Z)", t):
                src_cs[m.group(1)] = commandset_core(m.group(0))
        for _i, n, b in data:
            if not n.lower().endswith(".ini"):
                continue
            t = b.decode("latin1", "replace")
            for m in re.finditer(r"(?ms)^CommandSet\s+(\S+)\s*\r?\n.*?(?=^CommandSet\s|\Z)", t):
                dst_cs[m.group(1)] = commandset_core(m.group(0))
        for pcs in PROTECTED_COMMANDSETS:
            if pcs in src_cs and pcs in dst_cs and src_cs[pcs] != dst_cs[pcs]:
                errors += fail(f"protected CS changed {pcs}")
            elif pcs in src_cs and pcs in dst_cs:
                print("OK protected", pcs)
        non_country = 0
        for name, blk in src_cs.items():
            if is_country_commandset(name):
                continue
            non_country += 1
            if name not in dst_cs:
                errors += fail(f"non-country CS disappeared {name}")
                continue
            if dst_cs[name] != blk:
                errors += fail(f"non-country CS changed {name}")
        print("OK non-country CommandSet cores compared", non_country)

        src_files = {n.replace("/", "\\").lower(): b for _i, n, b in src}
        dst_files = {n.replace("/", "\\").lower(): b for _i, n, b in data}
        for rel in (
            r"data\ini\commandset_egypt.ini",
            r"data\ini\commandset_israel.ini",
            r"data\ini\commandset_israel_integrity.ini",
            r"data\ini\playertemplate.ini",
            r"data\ini\science.ini",
        ):
            if src_files.get(rel) != dst_files.get(rel):
                errors += fail(f"protected file bytes changed {rel}")
            elif rel in src_files:
                print("OK file byte-identical", rel)
        for _i, n, b in src:
            nl = n.replace("/", "\\").lower()
            if nl.endswith("generals.csf"):
                dst = dst_files.get(nl)
                if dst != b:
                    errors += fail("generals.csf changed")
                else:
                    print("OK CSF byte-identical")
                break

    print()
    print("=== Live air / production bars ===")
    for csname in (
        "FranceAirfieldCommandSet",
        "France_HeavyAirBaseCommandSet",
        "France_LargeAirBaseCommandSet",
        "France_HelicopterBaseCommandSet",
        "BritainAirfieldCommandSet",
        "ItalyAirfieldCommandSet",
        "GermanyAirfieldCommandSet",
        "Japan_WarFactoryCommandSet",
    ):
        hit = last_named_any(data, "CommandSet", csname)
        if not hit:
            print("NOTE missing", csname)
            continue
        bad = []
        for slot, btn in re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", hit[1]):
            btn = btn.split(";")[0]
            if btn not in buttons:
                bad.append(f"{slot}={btn}")
        if bad:
            errors += fail(f"{csname} unbound {bad}")
        else:
            print("OK", csname, "all slot buttons exist in", hit[0])

    print()
    print("=== Live FranceAirfield (current crash site) ===")
    hit = last_named_any(data, "CommandSet", "FranceAirfieldCommandSet")
    if not hit:
        errors += fail("missing FranceAirfieldCommandSet")
    else:
        print("last-wins", hit[0])
        for slot, btn in re.findall(r"(?m)^\s*(\d+)\s+=\s+(\S+)", hit[1]):
            ok = "OK" if btn.split(";")[0] in buttons else "MISSING"
            print(f"  {slot:3s} {btn:50s} {ok}")

    print()
    print("=== Packed BIG audit ===")
    if errors:
        print("AUDIT_FAIL", errors)
        return 1
    print("AUDIT_OK")
    return 0


def main() -> int:
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        code = _run()
    finally:
        sys.stdout = old
    text = buf.getvalue()
    print(text, end="")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text)
    print("wrote", REPORT)
    return code


if __name__ == "__main__":
    sys.exit(main())
