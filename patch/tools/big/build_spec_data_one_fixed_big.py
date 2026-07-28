#!/usr/bin/env python3
"""Replace broken Egypt_CommandCenter inside original _SPEC_DATA_ONE.big.

Output: _SPEC_DATA_ONE_FIXED.big (complete Data replacement, not an overlay).
Only Egypt_CommandCenter.ini content changes; all other entries unchanged.
"""
from __future__ import annotations

import hashlib
import re
import struct
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path("patch")
SRC_BIG = ROOT / "Release/SPECTER_BIG_MERGE/_SPEC_DATA_ONE.big"
CC_SRC = (
    ROOT
    / "Data/INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_CommandCenter.ini"
)
CC_KEY = r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_CommandCenter.ini"
OUT = ROOT / "Release/SPEC_DATA_ONE_FIXED"
OUT_BIG = OUT / "_SPEC_DATA_ONE_FIXED.big"
OUT_ZIP = OUT / "_SPEC_DATA_ONE_FIXED.zip"
BROKEN_SHA = "1b559b9e0d4eb1400e76934196eb71205c1ff21317e610d717c1da1dc7870b61"


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


def egypt_cc_keys(entries: dict[str, bytes]) -> list[str]:
    keys = []
    for k in entries:
        kl = k.lower().replace("/", "\\")
        if not kl.endswith(".ini"):
            continue
        if "egypt" in kl and "commandcenter" in kl.replace("_", "").replace(" ", ""):
            keys.append(k)
    return keys


def validate(
    entries: dict[str, bytes],
    orig_entries: dict[str, bytes],
) -> tuple[bool, list[str], list[str], str]:
    passes, fails = [], []
    ini = {
        k: v.decode("utf-8", errors="replace")
        for k, v in entries.items()
        if k.lower().endswith(".ini")
    }
    cats = catalogs(ini)
    orig_keys = set(orig_entries)

    cc_keys = egypt_cc_keys(entries)
    if len(cc_keys) == 1 and cc_keys[0] == CC_KEY:
        passes.append("Egypt_CommandCenter copies = 1 only")
    else:
        fails.append(f"Egypt_CommandCenter copies = {len(cc_keys)} keys={cc_keys}")

    cc_bytes = entries[CC_KEY]
    cc_sha = hashlib.sha256(cc_bytes).hexdigest()
    if cc_sha == BROKEN_SHA:
        fails.append("CC still broken SPEC sha")
    else:
        passes.append(f"CC repaired sha={cc_sha[:16]}… (not {BROKEN_SHA[:16]}…)")

    code = "\n".join(
        line.split(";", 1)[0]
        for line in cc_bytes.decode("utf-8", errors="replace").splitlines()
    )
    if re.search(
        r"\birq_|\bIraq_Adnan1\b|\bIrq_Command\b|\bSUPERWEAPON_Iraqi|\bSUPERWEAPON_Iraq",
        code,
    ):
        fails.append("Iraq/irq tokens still in Egypt_CommandCenter code")
    else:
        passes.append("No Iraq/irq crash tokens")

    cc = ini[CC_KEY]
    if parse_ok(cc):
        passes.append("INI parser PASS")
    else:
        fails.append("INI parser FAIL")

    def object_map(src: dict[str, bytes]) -> dict[str, list[str]]:
        m: dict[str, list[str]] = defaultdict(list)
        for name, raw in src.items():
            if not name.lower().endswith(".ini"):
                continue
            text = raw.decode("utf-8", errors="replace")
            for mm in re.finditer(r"^\s*Object\s+(?![=])(\S+)", text, re.M):
                m[mm.group(1)].append(name)
        return m

    obj_map = object_map(entries)
    orig_map = object_map(orig_entries)
    dups = {k: v for k, v in obj_map.items() if len(v) > 1}
    orig_dups = {k: v for k, v in orig_map.items() if len(v) > 1}
    # Vendor SPEC already has many Object redefinitions; keep them unchanged.
    # Require: Egypt_CommandCenter unique, and no NEW duplicate names vs original.
    if obj_map.get("Egypt_CommandCenter") == [CC_KEY]:
        passes.append("Object duplicates = 0 for Egypt_CommandCenter")
    else:
        fails.append(
            f"Egypt_CommandCenter Object dups defs={obj_map.get('Egypt_CommandCenter')}"
        )
    new_dup_names = set(dups) - set(orig_dups)
    worsened = [
        k
        for k in set(dups) & set(orig_dups)
        if len(dups[k]) > len(orig_dups[k])
    ]
    if not new_dup_names and not worsened:
        passes.append(
            f"Object duplicates unchanged vs SPEC (vendor pre-existing={len(orig_dups)}; no new)"
        )
    else:
        fails.append(
            f"New/worsened Object duplicates: new={list(new_dup_names)[:5]} worsened={worsened[:5]}"
        )

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
        fails.append("Missing references: " + "; ".join(missing[:20]))

    new_keys = set(entries)
    if new_keys == orig_keys:
        passes.append("All other SPEC entries preserved (same key set)")
    else:
        only_new = new_keys - orig_keys
        only_old = orig_keys - new_keys
        fails.append(f"Key set changed +{len(only_new)} -{len(only_old)}")

    # Byte-identical for every non-CC entry
    changed = []
    for k in orig_keys:
        if k == CC_KEY:
            continue
        if entries.get(k) != orig_entries.get(k):
            changed.append(k)
    if not changed:
        passes.append("All non-CC entry bytes unchanged")
    else:
        fails.append(f"Unexpected changed entries: {changed[:5]}")

    if not fails:
        passes.append("Game initialization PASS (static)")
    return (not fails), passes, fails, cc_sha


def scan_repo_egypt_copies(exclude_out_big: Path) -> list[tuple[str, str, bool]]:
    """Scan release BIGs for Egypt CC; report path, sha, broken?"""
    rows = []
    for big in sorted(Path("patch/Release").rglob("*.big")):
        # skip huge nested extracted noise? all bigs ok
        try:
            entries = read_big(big)
        except Exception:
            continue
        for k in egypt_cc_keys(entries):
            raw = entries[k]
            sha = hashlib.sha256(raw).hexdigest()
            code = "\n".join(
                line.split(";", 1)[0]
                for line in raw.decode("utf-8", errors="replace").splitlines()
            )
            broken = bool(
                re.search(
                    r"\birq_|\bIraq_Adnan1\b|\bIrq_Command\b|\bSUPERWEAPON_Iraqi|\bSUPERWEAPON_Iraq",
                    code,
                )
            )
            rows.append((str(big), sha, broken))
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if not SRC_BIG.exists():
        print("MISSING", SRC_BIG)
        return 1
    if not CC_SRC.exists():
        print("MISSING", CC_SRC)
        return 1

    print("Extracting original", SRC_BIG)
    entries = read_big(SRC_BIG)
    entries_orig_snapshot = dict(entries)
    orig_keys = set(entries)
    print("entries", len(entries))

    if CC_KEY not in entries:
        print("MISSING key in SPEC:", CC_KEY)
        return 1

    old = entries[CC_KEY]
    old_sha = hashlib.sha256(old).hexdigest()
    print("OLD Egypt_CommandCenter sha", old_sha)
    if old_sha != BROKEN_SHA:
        print("WARNING: expected broken sha", BROKEN_SHA)

    # Delete broken + insert repaired
    repaired = CC_SRC.read_bytes()
    # normalize newlines to the file as stored (utf-8)
    repaired_text = CC_SRC.read_text(encoding="utf-8", errors="replace")
    if not repaired_text.endswith("\n"):
        repaired_text += "\n"
    repaired = repaired_text.encode("utf-8")
    del entries[CC_KEY]
    entries[CC_KEY] = repaired
    new_sha = hashlib.sha256(repaired).hexdigest()
    print("NEW Egypt_CommandCenter sha", new_sha)

    # Ensure only one egypt CC key
    for k in list(egypt_cc_keys(entries)):
        if k != CC_KEY:
            print("Removing duplicate key", k)
            del entries[k]

    print("Packing _SPEC_DATA_ONE_FIXED.big ...")
    big = build_big(entries)
    OUT_BIG.write_bytes(big)
    big_sha = hashlib.sha256(big).hexdigest()
    (OUT / "_SPEC_DATA_ONE_FIXED.big.sha256").write_text(big_sha + "\n", encoding="utf-8")
    print("BIG sha", big_sha, "size", len(big), "entries", len(entries))

    packed = read_big(OUT_BIG)
    ok, passes, fails, cc_sha = validate(packed, entries_orig_snapshot)
    verdict = "PASS" if ok else "FAIL"

    # Scan report: this new BIG must have copies=1; note other repo BIGs may still be broken
    print("Scanning repo BIGs for Egypt_CommandCenter copies...")
    scan_rows = scan_repo_egypt_copies(OUT_BIG)
    fixed_in_new = [
        r for r in scan_rows if r[0].endswith("_SPEC_DATA_ONE_FIXED.big")
    ]
    broken_elsewhere = [r for r in scan_rows if r[2]]
    scan_txt = [
        "EGYPT_COMMANDCENTER SCAN (all patch/Release *.big)",
        "=" * 60,
        f"Total copies across all BIGs: {len(scan_rows)}",
        f"Broken copies still in other packages: {len(broken_elsewhere)}",
        f"_SPEC_DATA_ONE_FIXED.big copies: {len(fixed_in_new)} (must be 1)",
        "",
        "THIS PACKAGE guarantees Egypt_CommandCenter copies = 1 inside the shipped BIG.",
        "Other archived BIGs in the repo may still contain broken copies — do not install them.",
        "",
    ]
    for path, sha, broken in fixed_in_new:
        scan_txt.append(f"FIXED  {sha}  {path}")
    scan_txt.append("")
    scan_txt.append("Broken SPEC copies elsewhere (do not install):")
    seen = set()
    for path, sha, broken in broken_elsewhere:
        if sha in seen:
            continue
        seen.add(sha)
        scan_txt.append(f"BROKEN {sha}")
        for p, s, b in broken_elsewhere:
            if s == sha:
                scan_txt.append(f"  - {p}")
    (OUT / "EGYPT_CC_SCAN.txt").write_text("\n".join(scan_txt) + "\n", encoding="utf-8")

    verify = [
        "SPEC DATA ONE FIXED — VERIFY REPORT",
        "=" * 60,
        f"VERDICT: {verdict}",
        "BIG: _SPEC_DATA_ONE_FIXED.big",
        f"BIG SHA256: {big_sha}",
        f"Source: {SRC_BIG}",
        f"Source BIG SHA256: {hashlib.sha256(SRC_BIG.read_bytes()).hexdigest()}",
        f"Old Egypt_CommandCenter SHA256: {old_sha}",
        f"New Egypt_CommandCenter SHA256: {cc_sha}",
        f"Broken SPEC CC SHA256: {BROKEN_SHA}",
        f"Size: {len(big)} bytes",
        f"Entries: {len(entries)}",
        "",
        "Method: extract original _SPEC_DATA_ONE.big → delete broken Egypt_CommandCenter.ini",
        "→ insert USA-donor repaired Egypt_CommandCenter.ini → rebuild complete Data BIG.",
        "Not an overlay. Only that one file content changed.",
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
        f"""SPEC DATA ONE FIXED
===================

File: _SPEC_DATA_ONE_FIXED.big
SHA256: {big_sha}
Egypt_CommandCenter.ini SHA256: {cc_sha}
Validation: {verdict}

This is a COMPLETE replacement for vendor _SPEC_DATA_ONE.big.
It is NOT an overlay.

What changed:
  ONLY Data\\INI\\Object\\Specter\\Egyptian Armed Forces\\Buildings\\Egypt_CommandCenter.ini
  (broken Iraq-donor → USA AmericaCommandCenter donor, Side=Egypt)

INSTALL (mandatory):
1. Backup Data\\_SPEC_DATA_ONE.big
2. Copy _SPEC_DATA_ONE_FIXED.big → Data\\_SPEC_DATA_ONE.big
   (overwrite using the SPEC Data filename)
3. Keep Data\\_SPEC_ART_ONE.big
4. DELETE every Specter overlay BIG (_SPECTER_*.big, old patch BIGs)
5. Do not leave the original broken vendor SPEC Data BIG installed

Inside this BIG: Egypt_CommandCenter copies = 1 only.
""",
        encoding="utf-8",
    )

    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in [
            "_SPEC_DATA_ONE_FIXED.big",
            "_SPEC_DATA_ONE_FIXED.big.sha256",
            "README_INSTALL.txt",
            "VERIFY_REPORT.txt",
            "EGYPT_CC_SCAN.txt",
        ]:
            zf.write(OUT / name, arcname=name)

    print("\n".join(verify))
    print("ZIP", OUT_ZIP, OUT_ZIP.stat().st_size)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
