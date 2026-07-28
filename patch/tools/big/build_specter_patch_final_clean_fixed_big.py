#!/usr/bin/env python3
"""Resolve Egypt_CommandCenter BIG conflict by merging SPEC+CLEAN Data.

- Scans _SPEC_DATA_ONE / CLEAN for every egypt_commandcenter.ini
- Deletes all copies in the merge
- Inserts ONE USA-donor Egypt_CommandCenter.ini
- Rebuilds _SPECTER_PATCH_FINAL_CLEAN_FIXED.big from the merged Data folder
- Verifies by reading the FINAL BIG contents only
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import sys
from pathlib import Path

ROOT = Path("patch")
SPEC_DATA = ROOT / "Release/SPECTER_BIG_MERGE/_SPEC_DATA_ONE.big"
CLEAN_BIG = ROOT / "Release/SPECTER_PATCH_FINAL_CLEAN/_SPECTER_PATCH_FINAL_CLEAN.big"
USA_LOOSE = ROOT / (
    "Release/SPECTER_ULTIMATE_LOOSE_FILES_PATCH/Data/INI/Object/Specter/"
    "United States Of America/Buildings/CommandCenter.ini"
)
EGYPT_LIVE = ROOT / (
    "Data/INI/Object/Specter/Egyptian Armed Forces/Buildings/Egypt_CommandCenter.ini"
)
OUT_DIR = ROOT / "Release/SPECTER_PATCH_FINAL_CLEAN_FIXED"
MERGED = OUT_DIR / "_merged_Data"
EGYPT_BIG = (
    r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_CommandCenter.ini"
)


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
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def extract_egypt_specials(text: str) -> str:
    blocks = []
    for m in re.finditer(
        r"^[ \t]*Behavior\s*=\s*(?:OCLSpecialPower|SpectreGunshipDeploymentUpdate)"
        r"\s+ModuleTag_Egypt\w*\n(?:.*?\n)*?^[ \t]*End\s*$",
        text,
        re.M,
    ):
        blocks.append(m.group(0).rstrip() + "\n")
    return "\n".join(blocks)


def build_egypt_cc() -> bytes:
    """Full USA AmericaCommandCenter structure + Egypt identity/specials."""
    usa = USA_LOOSE.read_text(encoding="utf-8", errors="replace")
    live = EGYPT_LIVE.read_text(encoding="utf-8", errors="replace")
    specials = extract_egypt_specials(live)
    if "US_E3G_AWACS" not in specials:
        specials += (
            "\n  Behavior = SpectreGunshipDeploymentUpdate ModuleTag_EgyptAWACS\n"
            "    SpecialPowerTemplate = SuperweaponEgyptAWACS\n"
            "    GunshipTemplateName = US_E3G_AWACS\n"
            "    RequiredScience = SCIENCE_Egypt_AWACS\n"
            "  End\n"
        )

    # Keep USA file intact for ART/structure; rename + identity; remove USA specials; inject Egypt.
    text = usa
    text = re.sub(
        r"^Object\s+AmericaCommandCenter\b",
        "Object Egypt_CommandCenter",
        text,
        count=1,
        flags=re.M,
    )
    text = re.sub(r"(^\s*Side\s*=\s*)\S+", r"\1Egypt", text, count=1, flags=re.M)
    text = re.sub(
        r"(^\s*CommandSet\s*=\s*)\S+",
        r"\1Egypt_CommandCenterCommandSet",
        text,
        count=1,
        flags=re.M,
    )
    text = re.sub(
        r"(^\s*DisplayName\s*=\s*)\S+",
        r"\1OBJECT:Egypt_CommandCenter",
        text,
        count=1,
        flags=re.M,
    )
    text = re.sub(
        r"(^\s*BuildCost\s*=\s*)\S+",
        lambda m: m.group(1) + "2000",
        text,
        count=1,
        flags=re.M,
    )
    text = re.sub(
        r"(^\s*BuildTime\s*=\s*)[^\n;]+",
        lambda m: m.group(1) + "45.0           ",
        text,
        count=1,
        flags=re.M,
    )
    text = re.sub(
        r"(^\s*MaxHealth\s*=\s*)\S+",
        lambda m: m.group(1) + "5000.0",
        text,
        flags=re.M,
    )
    text = re.sub(
        r"(^\s*InitialHealth\s*=\s*)\S+",
        lambda m: m.group(1) + "5000.0",
        text,
        flags=re.M,
    )
    if not re.search(r"^Scale\s*=", text, re.M):
        text = re.sub(
            r"(Object Egypt_CommandCenter\n)",
            r"\1Scale = 0.8\n",
            text,
            count=1,
        )

    # Remove USA special-power / gunship deployment behaviors only.
    text = re.sub(
        r"^[ \t]*Behavior\s*=\s*(?:OCLSpecialPower|SpectreGunshipDeploymentUpdate)"
        r"[^\n]*\n(?:.*?\n)*?^[ \t]*End\s*\n?",
        "",
        text,
        flags=re.M,
    )

    specials_block = (
        "\n  ; --- Egypt specials only ---\n" + specials.rstrip() + "\n\n"
    )
    lines = text.splitlines(keepends=True)
    insert_at = None
    for i, line in enumerate(lines):
        if "PreorderCreate" in line or (
            re.match(r"^\s*KindOf\s*=", line) and "STRUCTURE" in line
        ):
            insert_at = i
            break
    if insert_at is None:
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == "End":
                insert_at = i
                break
    if insert_at is None:
        text = text + specials_block
    else:
        lines.insert(insert_at, specials_block)
        text = "".join(lines)

    # Scrub forbidden tokens from entire file (code + comments)
    text = text.replace("Iraq_Adnan1", "US_E3G_AWACS")
    text = re.sub(r"irq_[A-Za-z0-9_]+", "us_commandcenter", text, flags=re.I)
    text = re.sub(r"SUPERWEAPON_Iraq\w*", "SUPERWEAPON_SpySatellite", text)
    text = re.sub(r"\bIraqi[A-Za-z0-9_]*", "Egypt", text)
    text = re.sub(r"\bIraq\b", "Egypt", text)

    header = (
        "; SPECTER BIG-CONFLICT FIX - Egypt_CommandCenter\n"
        "; ONE file in merged SPEC+CLEAN Data — USA AmericaCommandCenter full donor\n"
        "; ART: us_commandcenter / US_Command / US_COM_Strb\n"
        "; Side=Egypt CommandSet=Egypt_CommandCenterCommandSet\n"
        "; BuildCost=2000 BuildTime=45 MaxHealth=5000\n"
        "; Egypt specials only; GunshipTemplateName=US_E3G_AWACS\n"
        "; Broken SPEC donor identity leftovers removed from this FIXED big\n\n"
    )
    text = header + text

    # Validate required fields
    req = [
        ("Object Egypt_CommandCenter", "Object Egypt_CommandCenter" in text),
        ("Side=Egypt", bool(re.search(r"^\s*Side\s*=\s*Egypt\b", text, re.M))),
        ("CommandSet", "Egypt_CommandCenterCommandSet" in text),
        ("BuildCost", bool(re.search(r"^\s*BuildCost\s*=\s*2000\b", text, re.M))),
        ("BuildTime", bool(re.search(r"^\s*BuildTime\s*=\s*45", text, re.M))),
        ("MaxHealth", bool(re.search(r"^\s*MaxHealth\s*=\s*5000", text, re.M))),
        ("us_commandcenter", "us_commandcenter" in text),
        ("US_Command", "US_Command" in text),
        ("US_COM_Strb", "US_COM_Strb" in text),
        ("US_E3G_AWACS", "US_E3G_AWACS" in text),
        ("no irq_comndcntr", "irq_comndcntr" not in text and "irq_comdcntr" not in text),
        ("no Iraq_Adnan1", "Iraq_Adnan1" not in text),
        ("no SUPERWEAPON_Iraq", "SUPERWEAPON_Iraq" not in text),
    ]
    for label, ok in req:
        if not ok:
            raise SystemExit(f"Egypt CC build failed check: {label}")
    # irq_ leftover in code (ignore comments)
    for i, line in enumerate(text.splitlines(), 1):
        code = line.split(";", 1)[0]
        if re.search(r"\birq_", code, re.I):
            raise SystemExit(f"irq_ leftover line {i}: {line}")
        if re.search(r"\bIraq\b", code) or re.search(r"\bIraqi", code):
            raise SystemExit(f"Iraq leftover line {i}: {line}")
    return text.encode("utf-8")


def egypt_paths(entries: dict[str, bytes]) -> list[str]:
    hits = []
    for name in entries:
        low = name.replace("/", "\\").lower()
        if low.endswith("egypt_commandcenter.ini"):
            hits.append(name)
        elif "egypt" in low and "commandcenter" in low.replace("_", "") and low.endswith(
            ".ini"
        ):
            hits.append(name)
    return sorted(set(hits))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Scanning loaded BIGs...")
    spec = read_big(SPEC_DATA)
    clean = read_big(CLEAN_BIG)
    print("SPEC egypt paths:", egypt_paths(spec))
    print("CLEAN egypt paths:", egypt_paths(clean))
    for label, entries in (("SPEC", spec), ("CLEAN", clean)):
        for p in egypt_paths(entries):
            t = entries[p].decode("utf-8", errors="replace")
            print(
                f"  {label} {p!r} size={len(entries[p])} "
                f"irq={('irq_comndcntr' in t)} adnan={('Iraq_Adnan1' in t)} "
                f"usa={('us_commandcenter' in t)}"
            )

    # Case-insensitive merge SPEC then CLEAN
    merged: dict[str, bytes] = {}
    lower_map: dict[str, str] = {}
    for entries in (spec, clean):
        for name, content in entries.items():
            canon = name.replace("/", "\\")
            key = canon.lower()
            if key in lower_map:
                merged[lower_map[key]] = content
            else:
                lower_map[key] = canon
                merged[canon] = content

    before = egypt_paths(merged)
    print("Merged egypt paths BEFORE delete:", before)
    for p in before:
        del merged[p]
        print("  DELETED", p)

    egypt_bytes = build_egypt_cc()
    merged[EGYPT_BIG] = egypt_bytes
    print(
        "INSERTED ONE",
        EGYPT_BIG,
        "sha",
        hashlib.sha256(egypt_bytes).hexdigest(),
        "size",
        len(egypt_bytes),
    )

    # Sync live patch/Data
    EGYPT_LIVE.parent.mkdir(parents=True, exist_ok=True)
    EGYPT_LIVE.write_bytes(egypt_bytes)

    # Write merged Data folder (Data tree only)
    if MERGED.exists():
        shutil.rmtree(MERGED)
    MERGED.mkdir(parents=True)
    n_files = 0
    for name, content in merged.items():
        norm = name.replace("/", "\\")
        if not norm.lower().startswith("data\\"):
            continue
        parts = [p for p in norm.split("\\") if p]
        if len(parts) < 2 or parts[0].lower() != "data":
            print("SKIP bare Data entry", repr(name))
            continue
        rel = Path(*parts[1:])
        out = MERGED / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(content)
        n_files += 1
    print("Merged Data files:", n_files)
    disk = list(MERGED.rglob("*egypt*commandcenter*.ini")) + list(
        MERGED.rglob("*Egypt*CommandCenter*.ini")
    )
    disk = sorted(set(disk))
    print("Disk egypt cc:", [str(p.relative_to(MERGED)) for p in disk])
    if len(disk) != 1:
        print("FAIL disk count", len(disk))
        return 1

    # Pack FIXED big from merged Data folder
    file_map: dict[str, bytes] = {}
    for path in sorted(MERGED.rglob("*")):
        if path.is_file():
            rel = path.relative_to(MERGED).as_posix()
            file_map["Data\\" + rel.replace("/", "\\")] = path.read_bytes()
    # purge any extra egypt keys
    for k in list(file_map):
        if k == EGYPT_BIG:
            continue
        low = k.lower()
        if low.endswith("egypt_commandcenter.ini") or (
            "egypt" in low and "commandcenter" in low.replace("_", "") and low.endswith(".ini")
        ):
            print("Pack map removing extra", k)
            del file_map[k]
    file_map[EGYPT_BIG] = egypt_bytes

    big = build_big(file_map)
    out_big = OUT_DIR / "_SPECTER_PATCH_FINAL_CLEAN_FIXED.big"
    out_big.write_bytes(big)
    sha = hashlib.sha256(big).hexdigest()
    (OUT_DIR / "_SPECTER_PATCH_FINAL_CLEAN_FIXED.big.sha256").write_text(
        f"{sha}  _SPECTER_PATCH_FINAL_CLEAN_FIXED.big\n"
    )
    print("WROTE", out_big, "entries", len(file_map), "bytes", len(big), "SHA256", sha)

    # ===== VERIFY BY SCANNING FINAL BIG ONLY =====
    verify = read_big(out_big)
    paths = egypt_paths(verify)
    report = [
        "VERIFY BY SCANNING FINAL BIG CONTENTS (not loose INI)",
        f"BIG: _SPECTER_PATCH_FINAL_CLEAN_FIXED.big",
        f"SHA256: {sha}",
        f"Entries: {len(verify)}",
        f"egypt_commandcenter.ini paths: {paths}",
    ]
    ok = True
    if len(paths) != 1:
        report.append(f"FAIL: expected exactly 1 path, got {len(paths)}")
        ok = False
    else:
        content = verify[paths[0]]
        text = content.decode("utf-8", errors="replace")
        report.append(f"PATH: {paths[0]}")
        report.append(f"size={len(content)} content_sha={hashlib.sha256(content).hexdigest()}")
        checks = {
            "Object Egypt_CommandCenter": "Object Egypt_CommandCenter" in text,
            "Side=Egypt": bool(re.search(r"^\s*Side\s*=\s*Egypt\b", text, re.M)),
            "Egypt_CommandCenterCommandSet": "Egypt_CommandCenterCommandSet" in text,
            "BuildCost=2000": bool(re.search(r"^\s*BuildCost\s*=\s*2000\b", text, re.M)),
            "BuildTime=45": bool(re.search(r"^\s*BuildTime\s*=\s*45", text, re.M)),
            "MaxHealth=5000": bool(re.search(r"^\s*MaxHealth\s*=\s*5000", text, re.M)),
            "us_commandcenter": "us_commandcenter" in text,
            "US_Command": "US_Command" in text,
            "US_COM_Strb": "US_COM_Strb" in text,
            "US_E3G_AWACS": "US_E3G_AWACS" in text,
            "NO irq_comndcntr/irq_comdcntr": "irq_comndcntr" not in text
            and "irq_comdcntr" not in text,
            "NO Iraq_Adnan1": "Iraq_Adnan1" not in text,
            "NO SUPERWEAPON_Iraq": "SUPERWEAPON_Iraq" not in text,
            "NOT broken SPEC sha": hashlib.sha256(content).hexdigest()
            != "1b559b9e0d4eb1400e76934196eb71205c1ff21317e610d717c1da1dc7870b61",
        }
        # code-line irq_/Iraq scan
        iraq_code = []
        for i, line in enumerate(text.splitlines(), 1):
            code = line.split(";", 1)[0]
            if re.search(r"\birq_", code, re.I) or re.search(r"\bIraq\b", code) or re.search(
                r"\bIraqi", code
            ):
                iraq_code.append(f"{i}:{code.strip()[:100]}")
        checks["NO irq_/Iraq/Iraqi in code"] = not iraq_code
        for k, v in checks.items():
            report.append(("PASS" if v else "FAIL") + ": " + k)
            if not v:
                ok = False
        if iraq_code:
            report.append("Iraq/irq code hits: " + str(iraq_code[:10]))

    # Confirm FIXED no longer contains broken SPEC bytes anywhere for this path
    report.append(
        "INSTALL: REPLACE _SPEC_DATA_ONE.big with _SPECTER_PATCH_FINAL_CLEAN_FIXED.big "
        "(this is the full merged Data). Keep _SPEC_ART_ONE.big. "
        "Remove old _SPECTER_PATCH_FINAL_CLEAN.big to avoid duplicate Objects."
    )
    report.append("VERDICT: " + ("PASS" if ok else "FAIL"))
    (OUT_DIR / "VERIFY_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT_DIR / "README_INSTALL.txt").write_text(
        "SPECTER PATCH FINAL CLEAN FIXED\n"
        "================================\n\n"
        "The game was still loading the BROKEN Egypt_CommandCenter from _SPEC_DATA_ONE.big.\n"
        "This FIXED big is a FULL merged Data rebuild with that broken copy DELETED and\n"
        "ONE USA-donor Egypt_CommandCenter.ini inserted.\n\n"
        "INSTALL (required):\n"
        "1. Backup _SPEC_DATA_ONE.big\n"
        "2. Copy _SPECTER_PATCH_FINAL_CLEAN_FIXED.big into the Zero Hour folder\n"
        "3. Rename it to _SPEC_DATA_ONE.big (replace the old file)\n"
        "4. Keep _SPEC_ART_ONE.big / EnglishZH.big / AudioZH.big\n"
        "5. DELETE old _SPECTER_PATCH_FINAL_CLEAN.big if present\n\n"
        f"SHA256: {sha}\n"
        f"Validation: {'PASS' if ok else 'FAIL'}\n",
        encoding="utf-8",
    )
    print("\n".join(report))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
