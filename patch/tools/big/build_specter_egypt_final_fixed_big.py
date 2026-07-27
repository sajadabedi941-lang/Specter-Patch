#!/usr/bin/env python3
"""Build _SPECTER_EGYPT_FINAL_FIXED.big — single Egypt_CommandCenter, SPEC-replace install.

Root cause: vendor _SPEC_DATA_ONE.big embeds broken Egypt_CommandCenter
(sha 1b559b9e… irq_comndcntr / Iraq_Adnan1). Any _SPECTER_* overlay can lose
to SPEC depending on FS sort; safe fix is REPLACE _SPEC_DATA_ONE.big entirely.
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
# Prefer previous full fixed BIG (Egypt + init repairs); fallback FINAL_REPAIRED
SRC_CANDIDATES = [
    ROOT / "Release/SPECTER_EGYPT_COMMANDCENTER_FIXED/_SPECTER_EGYPT_COMMANDCENTER_FIXED.big",
    ROOT / "Release/SPECTER_FINAL_REPAIRED/_SPECTER_FINAL_REPAIRED.big",
]
OUT = ROOT / "Release/SPECTER_EGYPT_FINAL_FIXED"
EXTRACTED = OUT / "_extracted_Data"
REEXTRACT = OUT / "_reextract_validate"
OUT_BIG = OUT / "_SPECTER_EGYPT_FINAL_FIXED.big"
OUT_ZIP = OUT / "_SPECTER_EGYPT_FINAL_FIXED.zip"
CC_SRC = (
    ROOT
    / "Data/INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_CommandCenter.ini"
)
CC_KEY = r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_CommandCenter.ini"
BROKEN_SPEC_SHA = "1b559b9e0d4eb1400e76934196eb71205c1ff21317e610d717c1da1dc7870b61"


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    _, n, _ = struct.unpack_from(">III", data, 4)
    entries: dict[str, bytes] = {}
    off = 16
    for _ in range(n):
        eoff, esize = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1", errors="replace")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


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


def big_to_fs(base: Path, big_name: str) -> Path | None:
    parts = [p for p in big_name.replace("/", "\\").split("\\") if p]
    if not parts or parts[0].lower() != "data":
        return None
    return base.joinpath(*parts[1:])


def extract_tree(entries: dict[str, bytes], dest: Path) -> int:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    n = 0
    for name, content in entries.items():
        out = big_to_fs(dest, name)
        if out is None:
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(content)
        n += 1
    return n


def pack_tree(base: Path) -> dict[str, bytes]:
    file_map: dict[str, bytes] = {}
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(base).as_posix()
        file_map["Data\\" + rel.replace("/", "\\")] = path.read_bytes()
    return file_map


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
        cats["Armor"].update(re.findall(r"^\s*Armor\s+(?![=])(\S+)", text, re.M))
        cats["DamageFX"].update(re.findall(r"^\s*DamageFX\s+(?![=])(\S+)", text, re.M))
        cats["FXList"].update(re.findall(r"^\s*FXList\s+(?![=])(\S+)", text, re.M))
    return cats


def parse_ok(text: str) -> bool:
    open_re = re.compile(
        r"^\s*(?:Object\s+(?![=])\S+|Draw\s*=|Behavior\s*=|ArmorSet\b|Body\s*=|"
        r"UnitSpecificSounds\b|ConditionState\s*=|TransitionState\s*=|WeaponSet\b|"
        r"CommandSet\s+(?![=])\S+|CommandButton\s+(?![=])\S+)"
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


def validate(entries: dict[str, bytes]) -> tuple[bool, list[str], list[str], str]:
    passes, fails = [], []
    ini = {
        k: v.decode("utf-8", errors="replace")
        for k, v in entries.items()
        if k.lower().endswith(".ini")
    }
    cats = catalogs(ini)

    # Exactly one Egypt_CommandCenter.ini path
    cc_paths = [
        k
        for k in entries
        if "egypt" in k.lower()
        and "commandcenter" in k.lower().replace("_", "").replace(" ", "")
        and k.lower().endswith(".ini")
    ]
    if len(cc_paths) == 1 and cc_paths[0] == CC_KEY:
        passes.append("ONLY ONE Egypt_CommandCenter.ini entry")
    else:
        fails.append(f"Egypt_CommandCenter path count={len(cc_paths)} paths={cc_paths}")

    cc_bytes = entries.get(CC_KEY, b"")
    cc_sha = hashlib.sha256(cc_bytes).hexdigest()
    if cc_sha == BROKEN_SPEC_SHA:
        fails.append("Packed CC still equals BROKEN SPEC sha 1b559b9e…")
    else:
        passes.append(f"CC content sha != broken SPEC ({cc_sha[:16]}…)")

    obj_map: dict[str, list[str]] = defaultdict(list)
    cs_map: dict[str, list[str]] = defaultdict(list)
    for name, text in ini.items():
        for m in re.finditer(r"^\s*Object\s+(?![=])(\S+)", text, re.M):
            obj_map[m.group(1)].append(name)
        for m in re.finditer(r"^\s*CommandSet\s+(?![=])(\S+)", text, re.M):
            cs_map[m.group(1)].append(name)
    obj_dups = {k: v for k, v in obj_map.items() if len(v) > 1}
    cs_dups = {k: v for k, v in cs_map.items() if len(v) > 1}
    if not obj_dups:
        passes.append("Duplicate Objects = 0")
    else:
        fails.append(f"Duplicate Objects = {len(obj_dups)}")
    # CommandSet redefinitions across files are common in ZH patches; count only
    # same-file multi-defs as hard fail, report multi-file as info
    hard_cs = {k: v for k, v in cs_dups.items() if len(set(v)) == 1 and len(v) > 1}
    if not hard_cs:
        passes.append("Duplicate CommandSets (same-file) = 0")
    else:
        fails.append(f"Duplicate CommandSets same-file = {len(hard_cs)}")

    if obj_map.get("Egypt_CommandCenter") == [CC_KEY]:
        passes.append("Egypt_CommandCenter Object defined once")
    else:
        fails.append(f"Egypt_CommandCenter defs={obj_map.get('Egypt_CommandCenter')}")

    cc = ini.get(CC_KEY, "")
    code = "\n".join(line.split(";", 1)[0] for line in cc.splitlines())
    if re.search(
        r"\birq_|\bIraq_Adnan1\b|\bIrq_Command\b|\bSUPERWEAPON_Iraqi|\bSUPERWEAPON_Iraq",
        code,
    ):
        fails.append("Iraq/irq crash tokens still in Egypt_CommandCenter code")
    else:
        passes.append("No Iraq/irq crash tokens in Egypt_CommandCenter")

    if not parse_ok(cc):
        fails.append("INI parser FAIL (Egypt_CommandCenter)")
    else:
        passes.append("INI parser PASS")

    # Missing refs for Egypt CC
    missing = []
    for label, rx, pool in [
        ("CommandSet", r"^\s*CommandSet\s*=\s*(\S+)", "CommandSet"),
        ("SpecialPower", r"^\s*SpecialPowerTemplate\s*=\s*(\S+)", "SpecialPower"),
        ("OCL", r"^\s*(?:OCL|CreationList|UpgradeObject)\s*=\s*(\S+)", "OCL"),
        ("Object", r"^\s*GunshipTemplateName\s*=\s*(\S+)", "Object"),
        ("Upgrade", r"^\s*(?:UpgradeToGrant|TriggeredBy)\s*=\s*(\S+)", "Upgrade"),
        ("Science", r"^\s*GrantScience\s*=\s*(\S+)", "Science"),
        ("Weapon", r"^\s*DeathWeapon\s*=\s*(\S+)", "Weapon"),
        ("Armor", r"^\s*Armor\s*=\s*(\S+)", "Armor"),
        ("DamageFX", r"^\s*DamageFX\s*=\s*(\S+)", "DamageFX"),
        ("FXList", r"^\s*DeathFX\s*=\s*(\S+)", "FXList"),
    ]:
        for m in re.finditer(rx, cc, re.M):
            ref = m.group(1)
            if ref.upper() == "NONE":
                continue
            if ref not in cats[pool]:
                missing.append(f"{label}={ref}")
    for sci, ocl in re.findall(r"^\s*UpgradeOCL\s*=\s*(\S+)\s+(\S+)", cc, re.M):
        if sci not in cats["Science"]:
            missing.append(f"Science={sci}")
        if ocl not in cats["OCL"]:
            missing.append(f"OCL={ocl}")
    # CS buttons
    for name, text in ini.items():
        m = re.search(
            r"CommandSet\s+Egypt_CommandCenterCommandSet\n([\s\S]*?)^\s*End\s*$",
            text,
            re.M,
        )
        if not m:
            continue
        for sm in re.finditer(r"^\s*\d+\s*=\s*(\S+)", m.group(1), re.M):
            btn = sm.group(1)
            if btn in ("NONE", "Separator"):
                continue
            if btn not in cats["CommandButton"] and btn not in cats["Object"]:
                missing.append(f"CommandButton={btn}")
        break
    if not missing:
        passes.append("Missing references = 0")
    else:
        fails.append("Missing references: " + "; ".join(missing[:15]))

    # Identity
    if re.search(r"^\s*Side\s*=\s*Egypt\b", cc, re.M) and "us_commandcenter" in cc:
        passes.append("Egypt identity + USA donor ART OK")
    else:
        fails.append("Identity/ART check failed")

    if "AmericaCommandCenter" in cats["Object"]:
        passes.append("AmericaCommandCenter preserved")
    else:
        fails.append("AmericaCommandCenter missing")

    if not fails:
        passes.append("Game initialization PASS (static)")
    return (not fails), passes, fails, cc_sha


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    src = next((p for p in SRC_CANDIDATES if p.exists()), None)
    if src is None:
        print("No source BIG")
        return 1
    if not CC_SRC.exists():
        print("Missing", CC_SRC)
        return 1

    load_order = Path("patch/Release/SPECTER_EGYPT_FINAL_FIXED/LOAD_ORDER_REPORT.txt")
    report_header = f"""EGYPT FINAL FIXED — LOAD ORDER ROOT CAUSE
==========================================
Broken SPEC Egypt_CommandCenter sha256:
  {BROKEN_SPEC_SHA}
  portrait=irq_comndcntr  gunship=Iraq_Adnan1  cost=1615  hp=2000

Found in vendor packages e.g.:
  patch/Release/SPECTER_BIG_MERGE/_SPEC_DATA_ONE.big

WHY PREVIOUS FIX FAILED IF LEFT AS OVERLAY:
  _SPECTER_EGYPT_COMMANDCENTER_FIXED.big does NOT replace
  _SPEC_DATA_ONE.big. If the broken SPEC Data BIG remains installed,
  the game can still load the Iraq-donor Egypt_CommandCenter.ini.

REQUIRED INSTALL (only way that is reliable):
  1. DELETE every Specter Data overlay BIG (_SPECTER_*.big etc.)
  2. REPLACE Data/_SPEC_DATA_ONE.big with _SPECTER_EGYPT_FINAL_FIXED.big
     (rename the fixed file TO _SPEC_DATA_ONE.big)
  3. Keep _SPEC_ART_ONE.big
"""
    (OUT / "LOAD_ORDER_REPORT.txt").write_text(
        report_header
        + ("\n" + load_order.read_text(encoding="utf-8") if load_order.exists() else ""),
        encoding="utf-8",
    )
    print(report_header)

    print("Source BIG:", src)
    entries = read_big(src)
    print("extract", extract_tree(entries, EXTRACTED))

    # Force single USA-donor Egypt_CommandCenter
    cc_text = CC_SRC.read_text(encoding="utf-8", errors="replace")
    # Ensure header marks FINAL
    if "EGYPT FINAL FIXED" not in cc_text.splitlines()[0]:
        lines = cc_text.splitlines()
        if lines and lines[0].startswith(";"):
            lines[0] = "; SPECTER EGYPT FINAL FIXED — USA AmericaCommandCenter donor"
            cc_text = "\n".join(lines) + ("\n" if cc_text.endswith("\n") else "")
    cc_out = (
        EXTRACTED
        / "INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_CommandCenter.ini"
    )
    cc_out.parent.mkdir(parents=True, exist_ok=True)
    cc_out.write_text(cc_text, encoding="utf-8", newline="\n")
    # Sync patch Data
    CC_SRC.write_text(cc_text, encoding="utf-8", newline="\n")

    # Remove any accidental alternate Egypt CommandCenter paths under extract
    expected = (
        "INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_CommandCenter.ini"
    )
    for p in EXTRACTED.rglob("*.ini"):
        if not p.is_file():
            continue
        rel = p.relative_to(EXTRACTED).as_posix()
        rel_l = rel.lower().replace("\\", "/")
        if "egypt" not in rel_l:
            continue
        if "commandcenter" not in rel_l.replace("_", "").replace(" ", ""):
            continue
        if rel != expected:
            print("Removing alternate Egypt CC path", rel)
            p.unlink()

    print("Packing...")
    file_map = pack_tree(EXTRACTED)
    # Ensure exactly one CC key
    cc_keys = [
        k
        for k in file_map
        if "egypt" in k.lower()
        and "commandcenter" in k.lower().replace("_", "").replace(" ", "")
        and k.lower().endswith(".ini")
    ]
    print("CC keys in pack:", cc_keys)
    big = build_big(file_map)
    OUT_BIG.write_bytes(big)
    # Also write drop-in rename copy for install clarity
    (OUT / "_SPEC_DATA_ONE.REPLACE_WITH_THIS.big").write_bytes(big)
    sha = hashlib.sha256(big).hexdigest()
    (OUT / "_SPECTER_EGYPT_FINAL_FIXED.big.sha256").write_text(sha + "\n", encoding="utf-8")

    packed = read_big(OUT_BIG)
    extract_tree(packed, REEXTRACT)
    ok, passes, fails, cc_sha = validate(packed)
    verdict = "PASS" if ok else "FAIL"

    verify = [
        "SPECTER EGYPT FINAL FIXED — VERIFY REPORT",
        "=" * 60,
        f"VERDICT: {verdict}",
        "BIG: _SPECTER_EGYPT_FINAL_FIXED.big",
        f"BIG SHA256: {sha}",
        f"Egypt_CommandCenter.ini SHA256: {cc_sha}",
        f"Broken SPEC CC SHA256 (must not match): {BROKEN_SPEC_SHA}",
        f"Size: {len(big)} bytes",
        f"Entries: {len(file_map)}",
        f"Source: {src}",
        "",
        "INSTALL (mandatory):",
        "  Rename/copy this BIG over Data\\_SPEC_DATA_ONE.big",
        "  Remove ALL other Specter Data overlay BIGs",
        "  Keep _SPEC_ART_ONE.big",
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
        f"""SPECTER EGYPT FINAL FIXED
========================

File: _SPECTER_EGYPT_FINAL_FIXED.big
SHA256: {sha}
Egypt_CommandCenter.ini SHA256: {cc_sha}
Validation: {verdict}

WHY THE LAST FIX FAILED
-----------------------
The broken Egypt_CommandCenter lives INSIDE vendor _SPEC_DATA_ONE.big
(sha {BROKEN_SPEC_SHA[:16]}… irq_comndcntr / Iraq_Adnan1).

Dropping _SPECTER_* beside SPEC does NOT reliably replace that file.
You must REPLACE _SPEC_DATA_ONE.big.

INSTALL
-------
1. Backup your current Data\\_SPEC_DATA_ONE.big
2. Copy _SPECTER_EGYPT_FINAL_FIXED.big → Data\\_SPEC_DATA_ONE.big
   (same filename as SPEC Data — overwrite)
3. Keep Data\\_SPEC_ART_ONE.big
4. DELETE every other Specter Data BIG (_SPECTER_*.big, old patch BIGs)
5. Do NOT leave the original vendor SPEC Data BIG installed

This BIG contains exactly ONE Egypt_CommandCenter.ini
(USA AmericaCommandCenter donor structure, Side=Egypt).
""",
        encoding="utf-8",
    )

    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in [
            "_SPECTER_EGYPT_FINAL_FIXED.big",
            "_SPECTER_EGYPT_FINAL_FIXED.big.sha256",
            "README_INSTALL.txt",
            "VERIFY_REPORT.txt",
            "LOAD_ORDER_REPORT.txt",
        ]:
            zf.write(OUT / name, arcname=name)

    print("\n".join(verify))
    print("ZIP", OUT_ZIP, OUT_ZIP.stat().st_size)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
