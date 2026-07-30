#!/usr/bin/env python3
"""Package Egypt ROOT CAUSE FIXED drop-in _SPEC_DATA_ONE.big

Uses full merged Specter Data (all content retained) with USA-donor
Egypt_CommandCenter already applied. Adds forensic reports from investigation.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path("patch")
SRC = ROOT / "Release/SPECTER_FULL_MERGED_FIXED/_SPEC_DATA_ONE.big"
CC_SRC = (
    ROOT
    / "Data/INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_CommandCenter.ini"
)
CC_KEY = r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_CommandCenter.ini"
OUT = ROOT / "Release/SPECTER_EGYPT_ROOT_CAUSE_FIXED"
OUT_BIG = OUT / "_SPEC_DATA_ONE.big"
OUT_ZIP = OUT / "_SPECTER_EGYPT_ROOT_CAUSE_FIXED.zip"
BROKEN = "1b559b9e0d4eb1400e76934196eb71205c1ff21317e610d717c1da1dc7870b61"


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    _, n, _ = struct.unpack_from(">III", data, 4)
    e: dict[str, bytes] = {}
    off = 16
    for _ in range(n):
        eoff, esize = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1", errors="replace")
        off = end + 1
        e[name] = data[eoff : eoff + esize]
    return e


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1
    index, blobs, offset = [], [], header_size
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
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def catalogs(ini: dict[str, str]):
    cats: dict[str, set[str]] = defaultdict(set)
    for text in ini.values():
        cats["Object"].update(re.findall(r"^\s*Object\s+(?![=])(\S+)", text, re.M))
        cats["CommandSet"].update(
            re.findall(r"^\s*CommandSet\s+(?![=])(\S+)", text, re.M)
        )
        cats["CommandButton"].update(
            re.findall(r"^\s*CommandButton\s+(?![=])(\S+)", text, re.M)
        )
        cats["SpecialPower"].update(
            re.findall(r"^\s*SpecialPower\s+(?![=])(\S+)", text, re.M)
        )
        cats["Science"].update(re.findall(r"^\s*Science\s+(?![=])(\S+)", text, re.M))
        cats["Upgrade"].update(re.findall(r"^\s*Upgrade\s+(?![=])(\S+)", text, re.M))
        cats["Weapon"].update(re.findall(r"^\s*Weapon\s+(?![=])(\S+)", text, re.M))
        cats["OCL"].update(
            re.findall(r"^\s*ObjectCreationList\s+(?![=])(\S+)", text, re.M)
        )
    return cats


def parse_ok(text: str) -> bool:
    open_re = re.compile(
        r"^\s*(?:Object\s+(?![=])\S+|Draw\s*=|Behavior\s*=|ArmorSet\b|Body\s*=|"
        r"UnitSpecificSounds\b|ConditionState\s*=|TransitionState\s*=|WeaponSet\b)"
    )
    depth = 0
    for line in text.splitlines():
        code = line.split(";", 1)[0]
        if not code.strip():
            continue
        if re.match(r"^\s*End\s*$", code):
            depth -= 1
            if depth < 0:
                return False
            continue
        if open_re.match(code):
            depth += 1
    return depth == 0


def validate(entries: dict[str, bytes]) -> tuple[bool, list[str], list[str]]:
    passes, fails = [], []
    ini = {
        k: v.decode("utf-8", errors="replace")
        for k, v in entries.items()
        if k.lower().endswith(".ini")
    }
    cats = catalogs(ini)

    cc_keys = [
        k
        for k in entries
        if "egypt" in k.lower()
        and "commandcenter" in k.lower().replace("_", "").replace(" ", "")
        and k.lower().endswith(".ini")
    ]
    if len(cc_keys) == 1 and cc_keys[0] == CC_KEY:
        passes.append("Egypt_CommandCenter copies = 1")
    else:
        fails.append(f"Egypt_CommandCenter copies={len(cc_keys)}")

    cc_sha = hashlib.sha256(entries[CC_KEY]).hexdigest()
    if cc_sha == BROKEN:
        fails.append("Egypt_CommandCenter still broken vendor sha")
    else:
        passes.append(f"Egypt_CommandCenter repaired sha={cc_sha[:16]}…")

    code = "\n".join(
        line.split(";", 1)[0]
        for line in entries[CC_KEY].decode("utf-8", errors="replace").splitlines()
    )
    if re.search(
        r"\birq_|\bIraq_Adnan1\b|\bIrq_Command\b|\bSUPERWEAPON_Iraqi|\bSUPERWEAPON_Iraq",
        code,
    ):
        fails.append("Iraq/irq crash tokens remain in Egypt_CommandCenter")
    else:
        passes.append("No Iraq/irq crash tokens in Egypt_CommandCenter")

    if parse_ok(ini[CC_KEY]):
        passes.append("INI parser PASS")
    else:
        fails.append("INI parser FAIL")

    obj_map: dict[str, list[str]] = defaultdict(list)
    for name, text in ini.items():
        for m in re.finditer(r"^\s*Object\s+(?![=])(\S+)", text, re.M):
            obj_map[m.group(1)].append(name)
    if obj_map.get("Egypt_CommandCenter") == [CC_KEY]:
        passes.append("Object duplicates = 0 for Egypt_CommandCenter")
    else:
        fails.append(f"Egypt_CommandCenter defs={obj_map.get('Egypt_CommandCenter')}")

    # Keep America/Iraq separate (not converted)
    if "AmericaCommandCenter" in cats["Object"] and "Iraq_CommandCenter" in cats["Object"]:
        passes.append("AmericaCommandCenter + Iraq_CommandCenter preserved (Egypt not replaced)")
    else:
        fails.append("USA/Iraq CommandCenter missing")

    missing = []
    cc = ini[CC_KEY]
    for label, rx, pool in [
        ("CommandSet", r"^\s*CommandSet\s*=\s*(\S+)", "CommandSet"),
        ("SpecialPower", r"^\s*SpecialPowerTemplate\s*=\s*(\S+)", "SpecialPower"),
        ("OCL", r"^\s*(?:OCL|CreationList|UpgradeObject)\s*=\s*(\S+)", "OCL"),
        ("Object", r"^\s*GunshipTemplateName\s*=\s*(\S+)", "Object"),
        ("Upgrade", r"^\s*(?:UpgradeToGrant|TriggeredBy)\s*=\s*(\S+)", "Upgrade"),
        ("Science", r"^\s*GrantScience\s*=\s*(\S+)", "Science"),
        ("Weapon", r"^\s*DeathWeapon\s*=\s*(\S+)", "Weapon"),
    ]:
        for m in re.finditer(rx, cc, re.M):
            ref = m.group(1)
            if ref not in cats[pool]:
                missing.append(f"{label}={ref}")
    for sci, ocl in re.findall(r"^\s*UpgradeOCL\s*=\s*(\S+)\s+(\S+)", cc, re.M):
        if sci not in cats["Science"]:
            missing.append(f"Science={sci}")
        if ocl not in cats["OCL"]:
            missing.append(f"OCL={ocl}")
    if not missing:
        passes.append("Missing references = 0 (Egypt_CommandCenter)")
    else:
        fails.append("Missing references: " + "; ".join(missing[:12]))

    if not fails:
        passes.append("Game initialization PASS (static)")
    return (not fails), passes, fails


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if not SRC.exists():
        print("MISSING full merged source", SRC)
        print("Run build_specter_full_merged_fixed_big.py first")
        return 1

    entries = read_big(SRC)
    # Re-assert USA-donor Egypt CC from patch Data
    if CC_SRC.exists():
        text = CC_SRC.read_text(encoding="utf-8", errors="replace")
        if not text.endswith("\n"):
            text += "\n"
        entries[CC_KEY] = text.encode("utf-8")

    big = build_big(entries)
    OUT_BIG.write_bytes(big)
    sha = hashlib.sha256(big).hexdigest()
    cc_sha = hashlib.sha256(entries[CC_KEY]).hexdigest()
    (OUT / "_SPEC_DATA_ONE.big.sha256").write_text(sha + "\n", encoding="utf-8")

    ok, passes, fails = validate(read_big(OUT_BIG))
    verdict = "PASS" if ok else "FAIL"

    # Ensure forensic verdict exists / refresh summary
    summary = f"""EGYPT ROOT CAUSE FIXED — PACKAGE SUMMARY
========================================

Forensic conclusion (see CRASH_FORENSIC_VERDICT.txt):
  Vendor _SPEC_DATA_ONE.big embeds broken Iraq-donor Egypt_CommandCenter.ini
  SHA {BROKEN}
  Exact broken refs at L25-26 irq_comndcntr, L35 Irq_Command, L146 Iraq_Adnan1,
  L128/153/159-161/172 SUPERWEAPON_Iraqi* / SUPERWEAPON_IraqReconnaissance

This package:
  Drop-in _SPEC_DATA_ONE.big (full Specter content retained)
  Egypt_CommandCenter = USA AmericaCommandCenter donor (Side=Egypt)
  Egypt_CommandCenter SHA {cc_sha}
  BIG SHA {sha}
  Validation: {verdict}

INSTALL:
  1. Backup Data\\_SPEC_DATA_ONE.big
  2. Copy this _SPEC_DATA_ONE.big over Data\\_SPEC_DATA_ONE.big
  3. Keep _SPEC_ART_ONE.big
  4. DELETE every other Specter Data BIG / overlay
"""
    (OUT / "PACKAGE_SUMMARY.txt").write_text(summary, encoding="utf-8")

    verify = [
        "SPECTER EGYPT ROOT CAUSE FIXED — VERIFY REPORT",
        "=" * 60,
        f"VERDICT: {verdict}",
        "BIG: _SPEC_DATA_ONE.big",
        f"SHA256: {sha}",
        f"Egypt_CommandCenter.ini SHA256: {cc_sha}",
        f"Broken vendor CC SHA256: {BROKEN}",
        f"Entries: {len(entries)}",
        f"Size: {len(big)} bytes",
        "",
        "Root cause: vendor SPEC Iraq-donor Egypt_CommandCenter.ini loaded at init.",
        "Fix: full Data BIG replace; Egypt CC USA-donor only; Egypt faction kept.",
        "",
        f"PASS: {len(passes)}  FAIL: {len(fails)}",
        "",
    ]
    for p in passes:
        verify.append("PASS: " + p)
    for f in fails:
        verify.append("FAIL: " + f)
    verify += ["", f"FINAL: {verdict}"]
    (OUT / "VERIFY_REPORT.txt").write_text("\n".join(verify) + "\n", encoding="utf-8")

    (OUT / "README_INSTALL.txt").write_text(
        f"""SPECTER EGYPT ROOT CAUSE FIXED
==============================

File: _SPEC_DATA_ONE.big
SHA256: {sha}
Egypt_CommandCenter SHA256: {cc_sha}
Validation: {verdict}

ROOT CAUSE
----------
Vendor _SPEC_DATA_ONE.big contains broken Egypt_CommandCenter.ini
(sha {BROKEN}):
  L25-26 SelectPortrait/ButtonImage = irq_comndcntr
  L35    Model = Irq_Command
  L146   GunshipTemplateName = Iraq_Adnan1
  L128/153/159-161/172 SUPERWEAPON_Iraqi* / SUPERWEAPON_IraqReconnaissance

Overlays do not help if the broken SPEC Data BIG is what you still run.
You must REPLACE _SPEC_DATA_ONE.big.

INSTALL
-------
1. Backup Data\\_SPEC_DATA_ONE.big
2. Copy this package's _SPEC_DATA_ONE.big over Data\\_SPEC_DATA_ONE.big
3. Keep Data\\_SPEC_ART_ONE.big
4. Delete ALL other Specter Data BIGs (_SPECTER_*.big, old FIXED/CLEAN overlays)

Egypt faction is kept. Object name remains Egypt_CommandCenter.
""",
        encoding="utf-8",
    )

    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        names = [
            "_SPEC_DATA_ONE.big",
            "_SPEC_DATA_ONE.big.sha256",
            "README_INSTALL.txt",
            "VERIFY_REPORT.txt",
            "CRASH_FORENSIC_VERDICT.txt",
            "FORENSIC_01_BIG_COPIES.txt",
            "FORENSIC_02_TO_07.txt",
            "PACKAGE_SUMMARY.txt",
        ]
        for name in names:
            p = OUT / name
            if p.exists():
                zf.write(p, arcname=name)

    print("\n".join(verify))
    print(summary)
    print("ZIP", OUT_ZIP, OUT_ZIP.stat().st_size)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
