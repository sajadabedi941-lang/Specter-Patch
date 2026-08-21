#!/usr/bin/env python3
"""Fix Global Starting Radar crash: Specter factions only.

Reverts the previous GLOBAL_STARTING_RADAR patch by starting from the
healthy pre-radar DATA BIG (russia-ui-airbase-update) and re-applying
RadarUpgrade StartsActive=Yes ONLY on the 26 Specter factions.

Never modifies GLA, Taiwan, UN, Boss, America Air Force General, or
other unused Zero Hour templates/objects. Never invents missing HQs.

Output: GLOBAL_STARTING_RADAR_FIX.zip containing only _SPEC_DATA_ONE.big
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = Path("/tmp/radar_fix_src/_SPEC_DATA_ONE.big")
EXPECTED_SRC_SHA = "273acc1b411261669c66ae9b8aea95e21d280a68136f804007c05dd67cea8f92"
OUT_DIR = Path("/tmp/global_starting_radar_fix")
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"
OUT_ZIP = OUT_DIR / "GLOBAL_STARTING_RADAR_FIX.zip"
REPORT = ROOT / "patch/Release/DATA_GLOBAL_STARTING_RADAR_FIX_REPORT.txt"

MODULE_TAG = "ModuleTag_SpecterGlobalStartingRadar"

# Exact runtime PlayerTemplate names for the 26 Specter factions.
ALLOWED_TEMPLATES = (
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
)

# Objects / path tokens that must remain byte-identical to source.
FORBIDDEN_OBJECT_NAMES = (
    "GLACommandCenter",
    "FakeGLACommandCenter",
    "Slth_GLACommandCenter",
    "Slth_FakeGLACommandCenter",
    "Boss_CommandCenter",
    "AirF_AmericaCommandCenter",
    "Infa_ChinaCommandCenter",
    "Taiwan_CommandCenter",
    "Taiwan_MilitaryHQ",
    "UN_CommandCenter",
    "UN_MilitaryHQ",
)
FORBIDDEN_PATH_RE = re.compile(
    r"(Arabic Alliance|GLACommandCenter|Taiwan|United Nations|"
    r"\\UN_|/UN_|Boss_CommandCenter|AirF_America|InfantryGeneral|"
    r"StealthGeneral|SuperWeaponGeneral|FactionBuilding\.ini)",
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


def parse_named_templates(files: dict[str, bytes], names: tuple[str, ...]) -> dict[str, dict[str, str]]:
    """Look up only the requested PlayerTemplates. Does not iterate unused sides."""
    wanted = set(names)
    found: dict[str, dict[str, str]] = {}
    for key, raw in files.items():
        if "PlayerTemplate" not in key.replace("\\", "/"):
            continue
        text = raw.decode("utf-8", errors="replace")
        for match in PT_RE.finditer(text):
            name = match.group(1)
            if name not in wanted:
                continue
            fields: dict[str, str] = {"Template": name, "Source": key}
            for line in match.group(2).splitlines():
                if "=" not in line or line.lstrip().startswith(";"):
                    continue
                left, right = line.split("=", 1)
                fields[left.strip()] = right.strip()
            found[name] = fields
    missing = [n for n in names if n not in found]
    if missing:
        raise SystemExit("missing allowed PlayerTemplates: " + ", ".join(missing))
    return found


def object_spans(text: str) -> list[tuple[str, int, int]]:
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
    if MODULE_TAG in block:
        return block, "already_tagged"
    module = radar_module(nl)
    kindof = re.search(r"(?m)^[ \t]*KindOf[ \t]*=[^\n]*\n", block)
    if kindof:
        insert_at = kindof.end()
        return block[:insert_at] + module + block[insert_at:], "inserted_after_kindof"
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
            if name in FORBIDDEN_OBJECT_NAMES:
                raise SystemExit(f"refusing to patch forbidden object {name}")
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
    templates = parse_named_templates(files, ALLOWED_TEMPLATES)

    modified_files: dict[str, list[str]] = defaultdict(list)
    faction_rows: list[str] = []

    for tmpl_name in ALLOWED_TEMPLATES:
        tmpl = templates[tmpl_name]
        building = tmpl.get("StartingBuilding", "")
        if not building:
            raise SystemExit(f"{tmpl_name} has no StartingBuilding")
        if building in FORBIDDEN_OBJECT_NAMES:
            raise SystemExit(f"{tmpl_name} StartingBuilding is forbidden: {building}")
        hits = find_object_files(files, building)
        if not hits:
            raise SystemExit(
                f"{tmpl_name} StartingBuilding {building} has no Object definition "
                "(will not invent an HQ)"
            )
        for key in hits:
            if FORBIDDEN_PATH_RE.search(key):
                raise SystemExit(f"refusing forbidden path {key} for {building}")
            new_raw, actions = patch_object_in_file(files[key], building)
            files[key] = new_raw
            modified_files[key].append(f"{building}:{'/'.join(actions)}")
        faction_rows.append(
            f"{tmpl_name}\tside={tmpl.get('Side', '?')}\t{building}\tfiles={len(hits)}"
        )

    # Every allowed HQ must now carry the module.
    verify_fail: list[str] = []
    for tmpl_name in ALLOWED_TEMPLATES:
        building = templates[tmpl_name]["StartingBuilding"]
        for key in find_object_files(files, building):
            text = files[key].decode("utf-8", errors="replace")
            ok = False
            for name, start, end in object_spans(text):
                if name != building:
                    continue
                block = text[start:end]
                if MODULE_TAG in block and re.search(r"StartsActive\s*=\s*Yes", block):
                    ok = True
            if not ok:
                verify_fail.append(f"{tmpl_name}:{building}:{key}")
    if verify_fail:
        raise SystemExit("verify failed:\n" + "\n".join(verify_fail))

    changed_keys = sorted(k for k, v in files.items() if v != original[k])

    # Crash-cause freeze: GLA / Taiwan / UN / unused vanilla must be untouched.
    forbidden_changed = []
    for key in changed_keys:
        if FORBIDDEN_PATH_RE.search(key):
            forbidden_changed.append(key)
        text = files[key].decode("utf-8", errors="replace")
        for obj in FORBIDDEN_OBJECT_NAMES:
            if re.search(rf"(?m)^Object(?:\s+Reskin)?\s+{re.escape(obj)}\b", text):
                # File contains a forbidden object AND was modified — only OK if
                # we did not alter that object's span. Compare original spans.
                orig_text = original[key].decode("utf-8", errors="replace")
                for name, start, end in object_spans(text):
                    if name != obj:
                        continue
                    orig_spans = {n: orig_text[s:e] for n, s, e in object_spans(orig_text)}
                    if orig_spans.get(obj) != text[start:end]:
                        forbidden_changed.append(f"{key}::{obj}")
    if forbidden_changed:
        raise SystemExit("forbidden files/objects changed:\n" + "\n".join(forbidden_changed))

    hard_freeze = []
    for key in changed_keys:
        lower = key.lower().replace("\\", "/")
        if any(
            token in lower
            for token in (
                "/weapon.ini",
                "objectcreationlist",
                "specialpower.ini",
                "radarstation",
                "radarvan",
                "/airforce/",
                "playertemplate",
                "commandbutton.ini",
                "commandset.ini",
            )
        ):
            hard_freeze.append(key)
    if hard_freeze:
        raise SystemExit("hard freeze violated:\n" + "\n".join(hard_freeze))

    # Explicit identity checks for GLA / Taiwan / UN objects vs source.
    identity_ok = []
    identity_missing = []
    for obj in FORBIDDEN_OBJECT_NAMES:
        hits = find_object_files(original, obj)
        if not hits:
            identity_missing.append(obj)
            continue
        for key in hits:
            if files[key] != original[key]:
                raise SystemExit(f"forbidden object file drifted: {key} ({obj})")
        identity_ok.append(f"{obj} unchanged in {len(hits)} file(s)")

    packed = build_big(files)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_BIG.write_bytes(packed)
    zip_stored(OUT_ZIP, "_SPEC_DATA_ONE.big", packed)

    with zipfile.ZipFile(OUT_ZIP) as zf:
        names = zf.namelist()
        if names != ["_SPEC_DATA_ONE.big"]:
            raise SystemExit(f"ZIP contents wrong: {names}")
        if zf.read("_SPEC_DATA_ONE.big") != packed:
            raise SystemExit("ZIP payload mismatch")

    # Round-trip: GLA/Taiwan/UN still absent from changed set.
    rt = read_big(OUT_BIG)
    for key in changed_keys:
        if MODULE_TAG.encode() not in rt[key]:
            raise SystemExit(f"round-trip missing module in {key}")
        for token in (b"GLACommandCenter", b"Taiwan_", b"UN_MilitaryHQ", b"UN_CommandCenter"):
            if token in Path(key).name.encode() or FORBIDDEN_PATH_RE.search(key):
                raise SystemExit(f"changed key looks forbidden: {key}")

    lines = [
        "GLOBAL STARTING RADAR FIX",
        "Crash cause: previous pack patched unused Zero Hour playable templates",
        "  (FactionGLA / GLACommandCenter, FactionAmericaAirForceGeneral /",
        "  AirF_AmericaCommandCenter). Boss was scanned but had no HQ object.",
        "This pack restores pre-radar DATA and applies StartsActive radar only",
        "to the 26 Specter factions.",
        "",
        f"Source DATA SHA256: {src_sha}",
        f"Output DATA SHA256: {sha256(packed)}",
        f"ZIP: {OUT_ZIP.name}",
        f"ZIP SHA256: {sha256(OUT_ZIP)}",
        "",
        "Mechanism (Specter HQs only):",
        "  Behavior = RadarUpgrade ModuleTag_SpecterGlobalStartingRadar",
        "    StartsActive = Yes",
        "  End",
        "",
        f"Specter factions patched: {len(ALLOWED_TEMPLATES)}",
        *faction_rows,
        "",
        f"Modified files ({len(changed_keys)}):",
        *[f"  {k} :: {'; '.join(modified_files[k])}" for k in changed_keys],
        "",
        "Forbidden objects confirmed unchanged or absent:",
        *[f"  {x}" for x in identity_ok],
        *[f"  {x} (not present in packed DATA)" for x in identity_missing],
        "",
        "Not modified: GLA, Taiwan, UN, Boss, Air Force General, vanilla ZH unused,",
        "PlayerTemplate.ini, weapons, aircraft, ART, CSF, radar stations.",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nWrote {OUT_BIG}")
    print(f"Wrote {OUT_ZIP}")
    print(f"Wrote {REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
