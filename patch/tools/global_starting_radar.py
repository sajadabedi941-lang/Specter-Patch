#!/usr/bin/env python3
"""Enable radar vision from match start for every playable faction.

Source of truth: current healthy DATA BIG (russia-ui-airbase-update /
uploaded ART+DATA lineage). DATA only.

Mechanism: add an engine RadarUpgrade module with StartsActive = Yes on each
playable faction's StartingBuilding (Command Center / HQ). Radar stations,
AWACS, spy satellite, special powers, vision ranges, weapons, aircraft, AI,
economy, and ART are not modified.

Output: GLOBAL_STARTING_RADAR.zip containing only _SPEC_DATA_ONE.big
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = Path("/tmp/ui_extracted/_SPEC_DATA_ONE.big")
EXPECTED_SRC_SHA = "273acc1b411261669c66ae9b8aea95e21d280a68136f804007c05dd67cea8f92"
OUT_DIR = Path("/tmp/global_starting_radar")
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"
OUT_ZIP = OUT_DIR / "GLOBAL_STARTING_RADAR.zip"
REPORT = ROOT / "patch/Release/DATA_GLOBAL_STARTING_RADAR_REPORT.txt"

MODULE_TAG = "ModuleTag_SpecterGlobalStartingRadar"
USER_FACTIONS = [
    "Iran",
    "Israel",
    "South Korea",
    "USA",
    "Russia",
    "China",
    "Iraq",
    "North Korea",
    "Japan",
    "Vietnam",
    "India",
    "Pakistan",
    "Saudi Arabia",
    "UAE",
    "Syria",
    "Turkey",
    "Ukraine",
    "Germany",
    "France",
    "Britain",
    "Egypt",
    "Italy",
    "Libya",
    "South Africa",
    "Sweden",
    "NATO",
]

# Files that must remain byte-identical (gameplay systems out of scope).
FREEZE_NAME_RE = re.compile(
    r"(Weapon\.ini|ObjectCreationList|SpecialPower\.ini|Upgrade\.ini|"
    r"RadarStation|RadarVan|CommandButton\.ini|CommandSet\.ini|"
    r"PlayerTemplate|Airforce|Aircraft|Science\.ini)",
    re.I,
)
PT_RE = re.compile(r"(?ms)^PlayerTemplate\s+(\S+)\s*\n(.*?)(?=^PlayerTemplate\s|\Z)")
OBJECT_START_RE = re.compile(r"(?m)^(Object(?:\s+Reskin)?)\s+(\S+)")


def sha256(p: Path | bytes) -> str:
    return hashlib.sha256(p if isinstance(p, bytes) else Path(p).read_bytes()).hexdigest()


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    assert data[:4] == b"BIGF", path
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    out: dict[str, bytes] = {}
    for _ in range(n):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        out[name.replace("/", "\\")] = data[off : off + size]
    return out


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16 + sum(8 + len(n.encode("latin1")) + 1 for n, _ in items)
    offset = header_size
    index, blobs = [], []
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">III", offset, len(items), header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def newline_for(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def parse_player_templates(files: dict[str, bytes]) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    for key, raw in files.items():
        if "PlayerTemplate" not in key.replace("\\", "/"):
            continue
        text = raw.decode("utf-8", errors="replace")
        for match in PT_RE.finditer(text):
            name, body = match.group(1), match.group(2)
            fields: dict[str, str] = {"Template": name, "Source": key}
            for line in body.splitlines():
                if "=" not in line or line.lstrip().startswith(";"):
                    continue
                left, right = line.split("=", 1)
                fields[left.strip()] = right.strip()
            found.append(fields)
    return found


def object_spans(text: str) -> list[tuple[str, int, int]]:
    """Return (object_name, start, end) for top-level Object blocks."""
    starts = [(m.group(2), m.start()) for m in OBJECT_START_RE.finditer(text)]
    spans = []
    for i, (name, start) in enumerate(starts):
        end = starts[i + 1][1] if i + 1 < len(starts) else len(text)
        spans.append((name, start, end))
    return spans


def radar_module(nl: str) -> str:
    return (
        f"  Behavior = RadarUpgrade {MODULE_TAG}{nl}"
        f"    StartsActive = Yes{nl}"
        f"  End{nl}"
    )


def inject_starting_radar(block: str, nl: str) -> tuple[str, str]:
    """Insert StartsActive RadarUpgrade into one Object block. Returns (text, action)."""
    if MODULE_TAG in block:
        return block, "already_tagged"
    if re.search(
        r"Behavior\s*=\s*RadarUpgrade[\s\S]{0,400}?StartsActive\s*=\s*Yes",
        block,
        re.I,
    ):
        return block, "already_starts_active"

    module = radar_module(nl)
    kindof = re.search(r"(?m)^[ \t]*KindOf[ \t]*=[^\n]*\n", block)
    if kindof:
        insert_at = kindof.end()
        return block[:insert_at] + module + block[insert_at:], "inserted_after_kindof"

    # Fall back: after the Object header line.
    header = re.search(r"(?m)^Object(?:\s+Reskin)?[ \t]+\S+[^\n]*\n", block)
    if header:
        insert_at = header.end()
        return block[:insert_at] + module + block[insert_at:], "inserted_after_header"
    return block, "no_insert_point"


def find_object_files(files: dict[str, bytes], obj_name: str) -> list[str]:
    pat = re.compile(rf"(?m)^Object(?:\s+Reskin)?\s+{re.escape(obj_name)}\b")
    needle = obj_name.encode("latin1")
    hits = []
    for key, raw in files.items():
        if not key.lower().endswith(".ini"):
            continue
        if needle not in raw:
            continue
        text = raw.decode("utf-8", errors="replace")
        if pat.search(text):
            hits.append(key)
    return hits


def patch_object_in_file(raw: bytes, obj_name: str) -> tuple[bytes, list[str]]:
    text = raw.decode("utf-8", errors="replace")
    nl = newline_for(text)
    actions: list[str] = []
    out = []
    cursor = 0
    changed = False
    for name, start, end in object_spans(text):
        out.append(text[cursor:start])
        block = text[start:end]
        if name == obj_name:
            new_block, action = inject_starting_radar(block, nl)
            actions.append(action)
            if new_block != block:
                changed = True
            out.append(new_block)
        else:
            out.append(block)
        cursor = end
    out.append(text[cursor:])
    if not changed:
        return raw, actions
    return "".join(out).encode("utf-8"), actions


def zip_stored(zip_path: Path, arcname: str, data: bytes) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr(arcname, data)


def main() -> int:
    if not SRC_DATA.is_file():
        raise SystemExit(f"missing source DATA BIG: {SRC_DATA}")
    src_sha = sha256(SRC_DATA)
    if src_sha != EXPECTED_SRC_SHA:
        raise SystemExit(f"source DATA SHA mismatch: {src_sha} != {EXPECTED_SRC_SHA}")

    files = read_big(SRC_DATA)
    original = dict(files)
    templates = parse_player_templates(files)
    playable = [t for t in templates if t.get("PlayableSide", "").lower() == "yes"]

    modified_files: dict[str, list[str]] = defaultdict(list)
    faction_rows: list[str] = []
    missing_objects: list[str] = []

    for tmpl in playable:
        name = tmpl["Template"]
        side = tmpl.get("Side", "?")
        building = tmpl.get("StartingBuilding", "")
        if not building:
            faction_rows.append(f"{name}\tside={side}\tNO StartingBuilding")
            missing_objects.append(name)
            continue
        hits = find_object_files(files, building)
        if not hits:
            faction_rows.append(f"{name}\tside={side}\t{building}\tOBJECT MISSING")
            missing_objects.append(f"{name}:{building}")
            continue
        for key in hits:
            new_raw, actions = patch_object_in_file(files[key], building)
            files[key] = new_raw
            modified_files[key].append(f"{building}:{'/'.join(actions)}")
        faction_rows.append(
            f"{name}\tside={side}\t{building}\tfiles={len(hits)}\t{';'.join(hits)}"
        )

    # Verify playable HQs (except known-missing objects) now have the module.
    verify_fail: list[str] = []
    for tmpl in playable:
        building = tmpl.get("StartingBuilding", "")
        if not building:
            continue
        hits = find_object_files(files, building)
        if not hits:
            continue
        for key in hits:
            text = files[key].decode("utf-8", errors="replace")
            ok = False
            for name, start, end in object_spans(text):
                if name != building:
                    continue
                block = text[start:end]
                if MODULE_TAG in block and re.search(
                    r"StartsActive\s*=\s*Yes", block
                ):
                    ok = True
            if not ok:
                verify_fail.append(f"{tmpl['Template']}:{building}:{key}")

    # Freeze: every non-targeted file must be identical.
    changed_keys = sorted(k for k, v in files.items() if v != original[k])
    freeze_violations = []
    for key in files:
        if files[key] == original[key]:
            continue
        if FREEZE_NAME_RE.search(key) and "CommandCenter" not in key and "MilitaryHQ" not in key and not key.endswith("HQ.ini") and not key.endswith("Command.ini"):
            freeze_violations.append(key)

    # Extra freeze: weapons / OCL / special power / radar stations / aircraft always.
    hard_freeze = []
    for key in files:
        lower = key.lower().replace("\\", "/")
        if files[key] == original[key]:
            continue
        if any(
            token in lower
            for token in (
                "/weapon.ini",
                "objectcreationlist",
                "specialpower.ini",
                "radarstation",
                "radarvan",
                "/airforce/",
            )
        ):
            hard_freeze.append(key)

    if verify_fail:
        raise SystemExit("verify failed:\n" + "\n".join(verify_fail))
    if hard_freeze:
        raise SystemExit("hard freeze violated:\n" + "\n".join(hard_freeze))

    # Parser sanity: every modified file still has matching Object headers.
    for key in changed_keys:
        text = files[key].decode("utf-8", errors="replace")
        if MODULE_TAG not in text:
            raise SystemExit(f"modified file missing module: {key}")
        if text.count("Behavior = RadarUpgrade " + MODULE_TAG) < 1:
            raise SystemExit(f"module header missing: {key}")

    packed = build_big(files)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_BIG.write_bytes(packed)
    zip_stored(OUT_ZIP, "_SPEC_DATA_ONE.big", packed)

    # Round-trip verify ZIP + BIG.
    with zipfile.ZipFile(OUT_ZIP) as zf:
        names = zf.namelist()
        if names != ["_SPEC_DATA_ONE.big"]:
            raise SystemExit(f"ZIP contents wrong: {names}")
        zdata = zf.read("_SPEC_DATA_ONE.big")
    if zdata != packed:
        raise SystemExit("ZIP payload mismatch")
    rt = read_big(OUT_BIG)
    if set(rt) != set(files):
        raise SystemExit("round-trip file set mismatch")
    for key in changed_keys:
        if MODULE_TAG.encode() not in rt[key]:
            raise SystemExit(f"round-trip missing module in {key}")

    lines = [
        "GLOBAL STARTING RADAR",
        f"Source DATA SHA256: {src_sha}",
        f"Output DATA SHA256: {sha256(packed)}",
        f"ZIP: {OUT_ZIP.name}",
        f"ZIP SHA256: {sha256(OUT_ZIP)}",
        "",
        "Mechanism:",
        "  Behavior = RadarUpgrade ModuleTag_SpecterGlobalStartingRadar",
        "    StartsActive = Yes",
        "  End",
        "  Inserted on each playable faction StartingBuilding (HQ / Command Center).",
        "  Existing RadarUpgrade TriggeredBy blocks on radar stations were not changed.",
        "  RadarUpdate (dish animation) was not changed.",
        "",
        f"Playable PlayerTemplates detected: {len(playable)}",
        *faction_rows,
        "",
        f"Modified files ({len(changed_keys)}):",
        *[f"  {k} :: {'; '.join(modified_files[k])}" for k in changed_keys],
        "",
        "Missing StartingBuilding objects (not invented):",
        *([f"  {x}" for x in missing_objects] or ["  (none)"]),
        "",
        "User faction coverage:",
    ]
    packed_sides = {t.get("Side", "") for t in playable}
    packed_templates = {t["Template"] for t in playable}
    for label in USER_FACTIONS:
        needle = label.replace(" ", "")
        hit = any(
            needle.lower() == s.lower()
            or label.lower() == s.lower()
            or needle.lower() in t.lower()
            or label.replace(" ", "").lower() in t.lower()
            for s, t in ((x.get("Side", ""), x["Template"]) for x in playable)
        )
        # USA is FactionAmerica / Side=America
        if label == "USA":
            hit = "FactionAmerica" in packed_templates or "America" in packed_sides
        if label == "NATO":
            hit = "FactionNato" in packed_templates or "Nato" in packed_sides
        if label == "UAE":
            hit = "FactionUAE" in packed_templates or "UAE" in packed_sides
        lines.append(f"  {label}: {'FOUND' if hit else 'MISSING'}")

    extra = sorted(
        t["Template"]
        for t in playable
        if t["Template"]
        not in {
            "FactionIran",
            "FactionIsrael",
            "FactionSouthKorea",
            "FactionAmerica",
            "FactionRussia",
            "FactionChina",
            "FactionIraq",
            "FactionNorthKorea",
            "FactionJapan",
            "FactionVietnam",
            "FactionIndia",
            "FactionPakistan",
            "FactionSaudiArabia",
            "FactionUAE",
            "FactionSyria",
            "FactionTurkey",
            "FactionUkraine",
            "FactionGermany",
            "FactionFrance",
            "FactionBritain",
            "FactionEgypt",
            "FactionItaly",
            "FactionLibya",
            "FactionSouthAfrica",
            "FactionSweden",
            "FactionNato",
        }
    )
    lines.append("")
    lines.append("Additional playable custom sides patched:")
    lines.extend(f"  {x}" for x in extra)
    if freeze_violations:
        lines.append("")
        lines.append("WARNING freeze-name hits (still allowed if HQ path matched):")
        lines.extend(f"  {x}" for x in freeze_violations)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nWrote {OUT_BIG}")
    print(f"Wrote {OUT_ZIP}")
    print(f"Wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
