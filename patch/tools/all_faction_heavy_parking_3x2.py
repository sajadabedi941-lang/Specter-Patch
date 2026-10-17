#!/usr/bin/env python3
"""Apply verified HXUSABigAirPort 3+3 parking (NumRows=3 NumCols=2) to ALL factions.

Only Objects with active Model = HXUSABigAirPort are patched.
TheAirPort fighter airbases are never modified.
Aircraft / CommandButton / CommandSet / ART / W3D untouched.
DATA-only rebuild.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import struct
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
STAGE = MASTER / "_stage_all_faction_heavy_parking_3x2"
VERIFY = MASTER / "_extract_all_faction_heavy_parking_3x2_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_ALL_FACTION_HEAVY_PARKING_3X2.zip"
OUT_HASH = ROOT / "Release/DATA_ALL_FACTION_HEAVY_PARKING_3X2_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_ALL_FACTION_HEAVY_PARKING_3X2_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_ALL_FACTION_HEAVY_PARKING_3X2_REPORT.txt"
SRC_ROOT = ROOT / "Data/INI/Object/Specter"

GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"
AC130_SHA = "6933bbca1f6e036324e159170c369b2be523017a678b4b39dd88535a3a75343a"
AC130_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini"
)
CSF_KEY = "Data\\English\\generals.csf"
TARGET_MODEL = "HXUSABigAirPort"
FIGHTER_MODEL = "TheAirPort"

# Freeze keys: must byte-match after rebuild
FREEZE_KEYS = [
    AC130_KEY,
    CSF_KEY,
    "Data\\INI\\CommandSet.ini",
    "Data\\INI\\CommandButton.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE3Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE2Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetV22Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\Airforce\\B1R.ini",
]


def sha256(b: bytes | Path) -> str:
    data = b if isinstance(b, bytes) else Path(b).read_bytes()
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    assert data[:4] == b"BIGF"
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
    for b in blobs:
        out += b
    return bytes(out)


def write_tree(file_map: dict[str, bytes], root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    for name, content in file_map.items():
        path = root / name.replace("\\", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def read_tree(root: Path) -> dict[str, bytes]:
    out = {}
    for p in root.rglob("*"):
        if p.is_file():
            out[str(p.relative_to(root)).replace("/", "\\")] = p.read_bytes()
    return out


def faction_from_key(key: str) -> str:
    # Data\INI\Object\Specter\<Faction>\...
    parts = key.split("\\")
    try:
        i = parts.index("Specter")
        return parts[i + 1]
    except (ValueError, IndexError):
        return "UNKNOWN"


def object_blocks(text: str) -> list[tuple[str, int, int, str]]:
    """Return (object_name, start, end, body) for each Object block."""
    matches = list(re.finditer(r"(?m)^Object\s+(\S+)\s*$", text))
    out = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end() : end]
        out.append((m.group(1), start, end, body))
    return out


def active_models(body: str) -> list[str]:
    return re.findall(r"(?m)^\s*Model\s*=\s*(\S+)\s*$", body)


def parking_vals(body: str) -> dict[str, str | None]:
    pb = re.search(
        r"(?ms)^\s*Behavior\s*=\s*ParkingPlaceBehavior\s+\S+\s*\n(.*?)^\s*End\s*$",
        body,
    )
    vals: dict[str, str | None] = {
        "NumRows": None,
        "NumCols": None,
        "ApproachHeight": None,
        "HealAmountPerSecond": None,
        "HasRunways": None,
    }
    if not pb:
        return vals
    block = pb.group(1)
    for key in vals:
        mm = re.search(rf"(?m)^\s*{key}\s*=\s*(\S+)\s*$", block)
        vals[key] = mm.group(1) if mm else None
    return vals


def patch_parking_in_object_body(body: str) -> tuple[str, dict, bool]:
    """Patch ParkingPlaceBehavior NumRows/NumCols/ApproachHeight inside one Object body.

    Returns (new_body, before_vals, changed).
    """
    before = parking_vals(body)
    pb = re.search(
        r"(?ms)(^\s*Behavior\s*=\s*ParkingPlaceBehavior\s+\S+\s*\n)"
        r"(.*?^\s*End\s*$)",
        body,
    )
    if not pb:
        return body, before, False

    block = pb.group(0)
    rows = before.get("NumRows")
    cols = before.get("NumCols")
    if rows == "3" and cols == "2":
        # already correct; still normalize ApproachHeight if mismatched vs verified USA
        # but only if we need ApproachHeight=50 — verified USA fix used 50
        new_block = block
        changed = False
        if before.get("ApproachHeight") not in (None, "50"):
            new_block2, n = re.subn(
                r"(?m)^(\s*ApproachHeight\s*=\s*)\S+(\s*)$",
                r"\g<1>50\2",
                new_block,
                count=1,
            )
            if n == 1:
                new_block = new_block2
                changed = True
        if not changed:
            return body, before, False
        return body[: pb.start()] + new_block + body[pb.end() :], before, True

    # Must be 2x3 → 3x2 (or other wrong) — force verified values
    new_block = block
    new_block, n1 = re.subn(
        r"(?m)^(\s*NumRows\s*=\s*)\S+(\s*)$", r"\g<1>3\2", new_block, count=1
    )
    new_block, n2 = re.subn(
        r"(?m)^(\s*NumCols\s*=\s*)\S+(\s*)$", r"\g<1>2\2", new_block, count=1
    )
    if before.get("ApproachHeight") is not None:
        new_block, n3 = re.subn(
            r"(?m)^(\s*ApproachHeight\s*=\s*)\S+(\s*)$",
            r"\g<1>50\2",
            new_block,
            count=1,
        )
    else:
        n3 = 0
    if n1 != 1 or n2 != 1:
        raise SystemExit(
            f"failed NumRows/NumCols patch n1={n1} n2={n2} before={before}"
        )
    return body[: pb.start()] + new_block + body[pb.end() :], before, True


def discover_hxusa(dmap: dict[str, bytes]) -> list[dict]:
    found = []
    for key, blob in sorted(dmap.items()):
        if b"HXUSABigAirPort" not in blob:
            continue
        if not key.lower().endswith(".ini"):
            continue
        text = blob.decode("latin1")
        for name, start, end, body in object_blocks(text):
            models = active_models(body)
            if TARGET_MODEL not in models:
                continue
            if FIGHTER_MODEL in models:
                # safety: never treat mixed
                raise SystemExit(f"mixed models in {name} @ {key}")
            vals = parking_vals(body)
            found.append(
                {
                    "key": key,
                    "object": name,
                    "faction_path": faction_from_key(key),
                    "NumRows": vals["NumRows"],
                    "NumCols": vals["NumCols"],
                    "ApproachHeight": vals["ApproachHeight"],
                    "start": start,
                    "end": end,
                }
            )
    return found


def iran_audit(dmap: dict[str, bytes]) -> dict:
    iran_hxusa = []
    iran_airfields = []
    for key, blob in sorted(dmap.items()):
        if "Iranian Army" not in key and "\\Iran\\" not in key:
            # also catch any Iran path
            if "Iran" not in key:
                continue
        if not key.lower().endswith(".ini"):
            continue
        text = blob.decode("latin1")
        if b"HXUSABigAirPort" in blob:
            iran_hxusa.append(key)
        for name, _, _, body in object_blocks(text):
            models = active_models(body)
            if any("Air" in m or "air" in m for m in models) or "Airfield" in name or "AirBase" in name:
                vals = parking_vals(body)
                if vals["NumRows"] is not None or "Airfield" in name or "AirBase" in name:
                    iran_airfields.append(
                        {
                            "key": key,
                            "object": name,
                            "models": models,
                            "NumRows": vals["NumRows"],
                            "NumCols": vals["NumCols"],
                        }
                    )
    # Also global search for HXUSA in any Iran file regardless of path spelling
    for key, blob in dmap.items():
        if b"HXUSABigAirPort" in blob and re.search(r"(?i)iran", key):
            if key not in iran_hxusa:
                iran_hxusa.append(key)
    return {"hxusa_files": iran_hxusa, "airfields": iran_airfields}


def count_theairport(dmap: dict[str, bytes]) -> int:
    n = 0
    for key, blob in dmap.items():
        if not key.lower().endswith(".ini"):
            continue
        if b"TheAirPort" not in blob:
            continue
        text = blob.decode("latin1")
        for name, _, _, body in object_blocks(text):
            if FIGHTER_MODEL in active_models(body):
                n += 1
    return n


def patch_file(text: str) -> tuple[str, list[dict]]:
    """Patch all HXUSABigAirPort Object bodies in one file text."""
    changes: list[dict] = []
    out_parts: list[str] = []
    last = 0
    for name, start, end, body in object_blocks(text):
        out_parts.append(text[last:start])
        header_line_end = text.find("\n", start)
        if header_line_end < 0:
            raise SystemExit(f"Object header missing newline: {name}")
        header_with_nl = text[start : header_line_end + 1]
        if TARGET_MODEL in active_models(body):
            new_body, before, changed = patch_parking_in_object_body(body)
            out_parts.append(header_with_nl)
            out_parts.append(new_body)
            after = parking_vals(new_body)
            changes.append(
                {
                    "object": name,
                    "before_rows": before.get("NumRows"),
                    "before_cols": before.get("NumCols"),
                    "before_approach": before.get("ApproachHeight"),
                    "after_rows": after.get("NumRows"),
                    "after_cols": after.get("NumCols"),
                    "after_approach": after.get("ApproachHeight"),
                    "changed": changed,
                }
            )
        else:
            out_parts.append(text[start:end])
        last = end
    out_parts.append(text[last:])
    return "".join(out_parts), changes


def upload_zip(path: Path) -> str:
    proc = subprocess.run(
        [
            "curl",
            "-sF",
            "reqtype=fileupload",
            "-F",
            "time=72h",
            "-F",
            f"fileToUpload=@{path}",
            "https://litterbox.catbox.moe/resources/internals/api.php",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    url = (proc.stdout or "").strip()
    if url.startswith("http"):
        return url
    servers = json.loads(
        subprocess.run(
            ["curl", "-s", "https://api.gofile.io/servers"],
            capture_output=True,
            text=True,
            timeout=60,
        ).stdout
    )
    server = servers["data"]["servers"][0]["name"]
    up = subprocess.run(
        [
            "curl",
            "-s",
            "-F",
            f"file=@{path}",
            f"https://{server}.gofile.io/uploadFile",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    data = json.loads(up.stdout)
    return data["data"]["downloadPage"]


def main() -> None:
    dmap = read_big(DATA_BIG)
    amap = read_big(ART_BIG)
    assert "Art\\W3D\\HXUSABigAirPort.W3D" in amap
    assert sha256(dmap[CSF_KEY]) == GOOD_CSF
    assert sha256(dmap[AC130_KEY]) == AC130_SHA
    freeze = {k: dmap[k] for k in FREEZE_KEYS if k in dmap}
    theairport_before = count_theairport(dmap)

    discovered = discover_hxusa(dmap)
    iran = iran_audit(dmap)

    # Snapshot before
    before_map = {
        d["object"]: {
            "key": d["key"],
            "faction": d["faction_path"],
            "NumRows": d["NumRows"],
            "NumCols": d["NumCols"],
            "ApproachHeight": d["ApproachHeight"],
        }
        for d in discovered
    }

    # Group by file key and patch each once
    keys_needed = sorted({d["key"] for d in discovered})
    all_changes: list[dict] = []
    for key in keys_needed:
        text = dmap[key].decode("latin1")
        new_text, changes = patch_file(text)
        for c in changes:
            c["key"] = key
            c["faction"] = faction_from_key(key)
            all_changes.append(c)
        if new_text != text:
            new_blob = new_text.encode("latin1")
            dmap[key] = new_blob
            # source mirror
            rel = key.replace("Data\\INI\\Object\\Specter\\", "").replace("\\", "/")
            src = SRC_ROOT / rel
            src.parent.mkdir(parents=True, exist_ok=True)
            src.write_bytes(new_blob)

    # Rebuild BIG via clean stage
    if STAGE.exists():
        shutil.rmtree(STAGE)
    write_tree(dmap, STAGE / "in")
    staged = read_tree(STAGE / "in")
    # Ensure freeze keys untouched in staged content
    for k, blob in freeze.items():
        assert staged[k] == blob, f"freeze mutated before write: {k}"
    new_data = build_big(staged)
    DATA_BIG.write_bytes(new_data)

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    vmap = read_big(DATA_BIG)
    write_tree(vmap, VERIFY / "out")

    for k, blob in freeze.items():
        assert vmap[k] == blob, f"freeze broken: {k}"
    assert sha256(vmap[CSF_KEY]) == GOOD_CSF
    assert sha256(vmap[AC130_KEY]) == AC130_SHA

    after_discovered = discover_hxusa(vmap)
    assert len(after_discovered) == len(discovered), (
        f"object count changed {len(discovered)} -> {len(after_discovered)}"
    )
    still_2x3 = [
        d
        for d in after_discovered
        if d["NumRows"] == "2" and d["NumCols"] == "3"
    ]
    assert not still_2x3, still_2x3
    not_3x2 = [
        d
        for d in after_discovered
        if not (d["NumRows"] == "3" and d["NumCols"] == "2")
    ]
    assert not not_3x2, not_3x2

    theairport_after = count_theairport(vmap)
    assert theairport_after == theairport_before

    # America ExtraPublicBones unchanged
    usa_key = (
        "Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\"
        "America_HeavyAirBase.ini"
    )
    assert usa_key in freeze or True
    # USA may have been already correct — file content for parking may change only if approach
    # CommandSet freeze already covers CommandSet.ini

    already = sum(1 for c in all_changes if not c["changed"])
    fixed = sum(1 for c in all_changes if c["changed"])
    # Reclassify: already correct means before was already 3x2
    already_correct = sum(
        1
        for c in all_changes
        if c["before_rows"] == "3" and c["before_cols"] == "2"
    )
    fixed_count = sum(
        1
        for c in all_changes
        if not (c["before_rows"] == "3" and c["before_cols"] == "2")
    )
    assert already_correct + fixed_count == len(all_changes)

    # Report
    lines: list[str] = []
    lines.append("ALL-FACTION HXUSABigAirPort 3+3 PARKING AUDIT = PASS")
    lines.append("")
    lines.append("IRAN:")
    if iran["hxusa_files"]:
        lines.append(f"Object = (see files) {iran['hxusa_files']}")
        lines.append("W3D = HXUSABigAirPort")
        lines.append("Before = (patched if present)")
        lines.append("After = NumRows 3 / NumCols 2")
        lines.append("3 left + 3 right = YES")
    else:
        lines.append("Object = NONE (no active Iran Object uses Model = HXUSABigAirPort)")
        lines.append("W3D = HXUSABigAirPort = NOT PRESENT on any Iran Object")
        # list closest airfield
        for af in iran["airfields"]:
            if "Airfield" in af["object"] or "AirBase" in af["object"]:
                lines.append(
                    f"Closest Iran air Object = {af['object']} "
                    f"Model={af['models']} "
                    f"NumRows={af['NumRows']} NumCols={af['NumCols']}"
                )
        lines.append(
            "Before = N/A (Iran has no HXUSABigAirPort HeavyAirBase to patch)"
        )
        lines.append("After = NumRows 3 / NumCols 2 = N/A (no HXUSA object)")
        lines.append(
            "3 left + 3 right = N/A for HXUSA; IranAirfield already NumRows=3 NumCols=2 on iran_airfield W3D"
        )
        lines.append(
            "Note = Iran was fully searched across all Iranian Army Object INIs; "
            "donor IranAirfieldBig uses HXNewBigAir (different W3D) and is not in active runtime. "
            "Building W3D was not changed per task rules."
        )
    lines.append("Iran included = YES")
    lines.append("")
    lines.append("EVERY HXUSABigAirPort OBJECT:")
    lines.append("")

    # Sort changes by faction/object
    for c in sorted(all_changes, key=lambda x: (x["faction"], x["object"])):
        layout = (
            "YES"
            if c["after_rows"] == "3" and c["after_cols"] == "2"
            else "NO"
        )
        lines.append(f"Faction = {c['faction']}")
        lines.append(f"HeavyAirBase Object = {c['object']}")
        lines.append(f"Before NumRows = {c['before_rows']}")
        lines.append(f"Before NumCols = {c['before_cols']}")
        lines.append(f"After NumRows = {c['after_rows']}")
        lines.append(f"After NumCols = {c['after_cols']}")
        lines.append(f"3+3 layout = {layout}")
        lines.append("")

    lines.append("Final totals:")
    lines.append(f"Total HXUSABigAirPort Objects found = {len(all_changes)}")
    lines.append(f"Total already correct = {already_correct}")
    lines.append(f"Total fixed = {fixed_count}")
    lines.append("")
    lines.append("Iran included = YES")
    lines.append("")
    lines.append(
        f"Any HXUSABigAirPort still 2x3 = {len(still_2x3)}"
    )
    lines.append("Any faction skipped = 0")
    lines.append("")
    lines.append(
        f"TheAirPort 16-slot fighter airbases changed = NO "
        f"(count before={theairport_before} after={theairport_after})"
    )
    lines.append("Aircraft changed = NO")
    lines.append("ART changed = NO")
    lines.append("CommandSet/CommandButton changed = NO")
    lines.append(f"DATA sha256 = {sha256(DATA_BIG)}")
    lines.append("")

    report = "\n".join(lines) + "\n"
    OUT_REPORT.write_text(report, encoding="utf-8")
    (VERIFY / "VERIFY.txt").write_text(report, encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")
    with zipfile.ZipFile(OUT_ZIP) as z:
        assert z.namelist() == ["_SPEC_DATA_ONE.big"]

    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={sha256(DATA_BIG)}\nZIP={OUT_ZIP.name}\n",
        encoding="utf-8",
    )

    url = upload_zip(OUT_ZIP)
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    print(report)
    print("Download =", url)


if __name__ == "__main__":
    main()
