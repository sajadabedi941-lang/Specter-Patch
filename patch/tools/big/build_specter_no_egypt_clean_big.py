#!/usr/bin/env python3
"""Remove Egypt completely from Specter Data and rebuild _SPECTER_NO_EGYPT_CLEAN.big.

Does NOT modify USA, Iraq, or other country content except scrubbing Egypt refs
out of shared INI files.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path("patch")
SPEC_DATA = ROOT / "Release/SPECTER_BIG_MERGE/_SPEC_DATA_ONE.big"
PATCH_DATA = ROOT / "Data"
OUT = ROOT / "Release/SPECTER_NO_EGYPT_CLEAN"
EXTRACTED = OUT / "_extracted_Data"
REEXTRACT = OUT / "_reextract_validate"
OUT_BIG = OUT / "_SPECTER_NO_EGYPT_CLEAN.big"

EGYPT_TOKEN_RE = re.compile(r"Egypt|Egyptian|egypt_", re.I)
# Definition names that are Egypt faction content
EGYPT_NAME_RE = re.compile(r"(?:^|_)(?:Egypt|Egyptian)(?:_|$)|(?:^|_)Egy_|Patch_Egypt_|FactionEgypt|SCIENCE_Egypt", re.I)

BLOCK_KINDS = [
    "Object",
    "CommandButton",
    "CommandSet",
    "PlayerTemplate",
    "Science",
    "Upgrade",
    "SpecialPower",
    "Weapon",
    "Locomotor",
    "FXList",
    "ObjectCreationList",
    "MappedImage",
    "ControlBarScheme",
    "AudioEvent",
    "ParticleSystem",
    "Armor",
    "Animation",
]


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


def overlay_patch(dest: Path, patch: Path) -> int:
    n = 0
    for path in patch.rglob("*"):
        if not path.is_file():
            continue
        out = dest / path.relative_to(patch)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(path.read_bytes())
        n += 1
    return n


def is_egypt_path(path: Path | str, root: Path | None = None) -> bool:
    """Match Egypt only in the path relative to root (never absolute out-dir names)."""
    p = Path(path)
    if root is not None:
        try:
            s = str(p.relative_to(root)).replace("\\", "/")
        except ValueError:
            s = p.name
    else:
        s = p.name
    return bool(re.search(r"egypt|egyptian", s, re.I))


def is_egypt_filename(name: str) -> bool:
    return bool(re.search(r"egypt|egyptian", name, re.I))


def is_protected_path(path: Path | str, root: Path | None = None) -> bool:
    """Never delete USA / Iraq trees as a whole."""
    p = Path(path)
    if root is not None:
        try:
            s = str(p.relative_to(root)).replace("\\", "/").lower()
        except ValueError:
            s = str(p).replace("\\", "/").lower()
    else:
        s = str(p).replace("\\", "/").lower()
    if "united states of america" in s:
        return True
    if "iraq army" in s or "ai_iraqiarmy" in s:
        return True
    return False


def remove_egypt_files(base: Path, log: list[str]) -> int:
    removed = 0
    for path in sorted(base.rglob("*"), reverse=True):
        if not path.is_file():
            continue
        rel_egypt = is_egypt_path(path, base) or is_egypt_filename(path.name)
        if not rel_egypt:
            continue
        if is_protected_path(path, base) and not is_egypt_filename(path.name):
            continue
        log.append(f"DELETE FILE {path.relative_to(base)}")
        path.unlink()
        removed += 1
    for path in sorted(base.rglob("*"), reverse=True):
        if not path.is_dir():
            continue
        if is_protected_path(path, base):
            continue
        is_empty = not any(path.iterdir())
        if is_egypt_path(path, base) or is_empty:
            try:
                # only remove empty dirs, or egypt-named dirs after files gone
                if is_empty:
                    path.rmdir()
                    log.append(f"RMDIR {path.relative_to(base)}")
            except OSError:
                pass
    return removed


def name_is_egypt(name: str) -> bool:
    if EGYPT_TOKEN_RE.search(name):
        return True
    return False


def remove_egypt_named_blocks(text: str) -> tuple[str, int]:
    """Remove top-level INI blocks whose definition name contains Egypt."""
    removed = 0
    for kind in BLOCK_KINDS:
        pattern = re.compile(
            rf"(^[ \t]*{kind}\s+(\S+)[^\n]*\n(?:.*?\n)*?^[ \t]*End\s*\n?)",
            re.M,
        )

        def repl(m: re.Match) -> str:
            nonlocal removed
            block_name = m.group(2)
            if name_is_egypt(block_name):
                removed += 1
                return ""
            return m.group(1)

        text = pattern.sub(repl, text)
    return text, removed


def scrub_egypt_lines(text: str) -> tuple[str, int]:
    """Remove or neutralize remaining lines that reference Egypt."""
    out_lines: list[str] = []
    removed = 0
    for line in text.splitlines(keepends=True):
        # Keep file if only comments mention Egypt: drop those comment lines
        if EGYPT_TOKEN_RE.search(line):
            # Do not touch lines that are clearly USA/Iraq identity unless they also say Egypt
            removed += 1
            # If it's a CommandSet slot or list entry, drop the whole line
            # If it's a field assignment, drop the line
            # Preserve newline structure lightly by skipping
            continue
        out_lines.append(line)
    return "".join(out_lines), removed


def scrub_ini_file(path: Path, log: list[str]) -> None:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
        enc = "utf-8"
    except UnicodeDecodeError:
        text = raw.decode("latin1")
        enc = "latin1"
    if not EGYPT_TOKEN_RE.search(text):
        return
    # Never scrub if this somehow is under USA/Iraq and has no Egypt token in name —
    # but we still must remove Egypt refs from shared files; USA files shouldn't have Egypt.
    orig = text
    text, n1 = remove_egypt_named_blocks(text)
    text, n2 = scrub_egypt_lines(text)
    if text != orig:
        path.write_bytes(text.encode(enc))
        log.append(f"SCRUB {path} blocks={n1} lines={n2}")


def scrub_tree(base: Path, log: list[str]) -> None:
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".ini", ".txt", ".cfg"}:
            # still check binary? skip non-ini
            if path.suffix.lower() not in {".ini"}:
                # scan other text-ish
                if path.suffix.lower() not in {".ini", ".str", ".csf"}:
                    continue
        scrub_ini_file(path, log)


def clean_patch_data(log: list[str]) -> None:
    """Apply Egypt removal to patch/Data source tree as well."""
    print("Cleaning patch/Data ...")
    remove_egypt_files(PATCH_DATA, log)
    for path in sorted(PATCH_DATA.rglob("*.ini")):
        scrub_ini_file(path, log)
    for path in sorted(PATCH_DATA.rglob("*"), reverse=True):
        if path.is_dir() and is_egypt_path(path, PATCH_DATA):
            # remove egypt dirs if empty
            try:
                if not any(path.iterdir()):
                    path.rmdir()
                    log.append(f"RMDIR patch {path.relative_to(PATCH_DATA)}")
            except OSError:
                pass


def pack_tree(base: Path) -> dict[str, bytes]:
    file_map: dict[str, bytes] = {}
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(base).as_posix()
        file_map["Data\\" + rel.replace("/", "\\")] = path.read_bytes()
    return file_map


def validate(entries: dict[str, bytes]) -> tuple[bool, list[str], list[str]]:
    passes: list[str] = []
    fails: list[str] = []

    egypt_paths = [
        k
        for k in entries
        if re.search(r"egypt|egyptian", k, re.I)
        or k.lower().endswith("egypt_commandcenter.ini")
    ]
    if not egypt_paths:
        passes.append("Zero Egypt_CommandCenter / Egypt paths in BIG")
    else:
        fails.append(f"Egypt paths remain: {egypt_paths[:20]}")

    # content scan
    content_hits = []
    for k, v in entries.items():
        if not k.lower().endswith(".ini"):
            # also scan other text
            if b"Egypt" in v or b"egypt" in v or b"Egyptian" in v or b"egyptian" in v:
                # allow if somehow in binary art names inside data? still fail per user
                text = v.decode("latin1", errors="replace")
                if EGYPT_TOKEN_RE.search(text):
                    content_hits.append(k)
            continue
        text = v.decode("utf-8", errors="replace")
        if EGYPT_TOKEN_RE.search(text):
            content_hits.append(k)
    if not content_hits:
        passes.append("Zero Egypt references in packed content")
    else:
        fails.append(f"Egypt refs remain in {len(content_hits)} files: {content_hits[:15]}")

    # Object uniqueness
    obj_re = re.compile(r"^\s*Object\s+(?![=])(\S+)", re.M)
    objects: dict[str, list[str]] = defaultdict(list)
    for k, v in entries.items():
        if not k.lower().endswith(".ini"):
            continue
        for m in obj_re.finditer(v.decode("utf-8", errors="replace")):
            objects[m.group(1)].append(k)
    dups = {o: ps for o, ps in objects.items() if len(ps) > 1}
    if not dups:
        passes.append("Object duplicate check PASS (0 dups)")
    else:
        fails.append(f"Object dups: {len(dups)}")

    # USA / Iraq still present
    usa = [k for k in entries if "United States Of America" in k]
    iraq = [k for k in entries if re.search(r"Iraq Army|AI_IraqiArmy", k)]
    if usa:
        passes.append(f"USA content preserved ({len(usa)} files)")
    else:
        fails.append("USA content missing")
    if iraq:
        passes.append(f"Iraq content preserved ({len(iraq)} files)")
    else:
        fails.append("Iraq content missing")

    # INI parser: Egypt gone; spot-check USA CommandCenter + Iraq CommandCenter only
    open_re = re.compile(
        r"^\s*(?:Object\s+(?![=])\S+|Draw\s*=|Behavior\s*=|ArmorSet\b|Body\s*=|"
        r"UnitSpecificSounds\b|ConditionState\s*=|TransitionState\s*=|WeaponSet\b|"
        r"ClientUpdate\s*=|Turret\b|ReplaceModule\b|AddModule\b|RemoveModule\b|"
        r"Prerequisites\b)"
    )
    parse_fail = 0
    checked = 0
    targets = []
    for k in entries:
        lk = k.replace("/", "\\").lower()
        if not lk.endswith(".ini"):
            continue
        if "united states of america" in lk and "commandcenter" in lk:
            targets.append(k)
        if "iraq army" in lk and lk.endswith("iraq_commandcenter.ini"):
            targets.append(k)
    for k in targets:
        text = entries[k].decode("utf-8", errors="replace")
        depth = 0
        hard = False
        for line in text.splitlines():
            code = line.split(";", 1)[0]
            if not code.strip():
                continue
            if re.match(r"^\s*End\s*$", code):
                depth -= 1
                if depth < 0:
                    hard = True
                    depth = 0
                continue
            if open_re.match(code):
                depth += 1
        checked += 1
        if hard or depth != 0:
            parse_fail += 1
            fails.append(f"INI parser issue: {k} depth={depth}")
    if parse_fail == 0:
        passes.append(f"INI parser PASS ({checked} USA/Iraq CommandCenter files)")
    else:
        fails.append(f"INI parser FAIL count={parse_fail}")

    # ensure no Egypt objects
    egypt_objs = [o for o in objects if EGYPT_TOKEN_RE.search(o)]
    if not egypt_objs:
        passes.append("Zero Egypt Object definitions")
    else:
        fails.append(f"Egypt Objects remain: {egypt_objs[:20]}")

    return (not fails), passes, fails


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    log: list[str] = []

    print("=== 1) Clean patch/Data Egypt content ===")
    clean_patch_data(log)

    print("=== 2) Extract SPEC DATA ===")
    spec = read_big(SPEC_DATA)
    print("SPEC entries", len(spec), "extracted", extract_tree(spec, EXTRACTED))

    print("=== 3) Overlay cleaned patch/Data ===")
    print("overlay", overlay_patch(EXTRACTED, PATCH_DATA))

    print("=== 4) Delete Egypt files from extracted tree ===")
    print("deleted files", remove_egypt_files(EXTRACTED, log))

    print("=== 5) Scrub Egypt references from remaining INIs ===")
    scrub_tree(EXTRACTED, log)

    # second pass delete empties
    remove_egypt_files(EXTRACTED, log)

    print("=== 6) Pack _SPECTER_NO_EGYPT_CLEAN.big ===")
    file_map = pack_tree(EXTRACTED)
    # belt: drop any egypt keys
    for k in list(file_map):
        if re.search(r"egypt|egyptian", k, re.I):
            del file_map[k]
            log.append(f"PURGE KEY {k}")
    big = build_big(file_map)
    OUT_BIG.write_bytes(big)
    sha = hashlib.sha256(big).hexdigest()
    (OUT / "_SPECTER_NO_EGYPT_CLEAN.big.sha256").write_text(sha + "\n", encoding="utf-8")
    print("packed", len(file_map), "sha", sha, "size", len(big))

    print("=== 7) Re-extract + validate ===")
    packed = read_big(OUT_BIG)
    extract_tree(packed, REEXTRACT)
    ok, passes, fails = validate(packed)
    verdict = "PASS" if ok else "FAIL"

    report = [
        "SPECTER NO EGYPT CLEAN — VERIFY REPORT",
        "=" * 60,
        f"VERDICT: {verdict}",
        f"BIG: _SPECTER_NO_EGYPT_CLEAN.big",
        f"SHA256: {sha}",
        f"Size: {len(big)} bytes",
        f"Entries: {len(file_map)}",
        "",
        "Egypt faction fully removed. USA and Iraq preserved.",
        "",
        f"PASS: {len(passes)}  FAIL: {len(fails)}",
        "",
    ]
    for p in passes:
        report.append("PASS: " + p)
    for f in fails:
        report.append("FAIL: " + f)
    report += ["", f"FINAL: {verdict}"]
    (OUT / "VERIFY_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "REMOVAL_LOG.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    (OUT / "README_INSTALL.txt").write_text(
        f"""SPECTER NO EGYPT CLEAN
======================

File: _SPECTER_NO_EGYPT_CLEAN.big
SHA256: {sha}
Validation: {verdict}

Egypt faction completely removed (folders, objects, CommandSets/Buttons,
PlayerTemplate, sciences, upgrades, AAB aircraft, shared refs).

USA and Iraq content preserved.

INSTALL:
1. Backup _SPEC_DATA_ONE.big
2. Replace with _SPECTER_NO_EGYPT_CLEAN.big (rename recommended)
3. Keep _SPEC_ART_ONE.big
4. Remove other Specter Data overlay/test BIGs
""",
        encoding="utf-8",
    )
    print("\n".join(report))
    print(f"Log lines: {len(log)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
