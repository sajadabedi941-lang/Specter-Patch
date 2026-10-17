#!/usr/bin/env python3
"""Sync Object ButtonImage/SelectPortrait to verified HeavyAirBase CommandButton icons.

Production queue icons come from Object ButtonImage (verified against known-good
Specter fighters where CB ButtonImage == Object ButtonImage == SelectPortrait).

Does NOT modify CommandButton.ini.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
MASTER = ROOT / "patch/Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
STAGE = MASTER / "_stage_usa_aircraft_queue_icon_sync"
VERIFY = MASTER / "_extract_usa_aircraft_queue_icon_sync_verify"
ZIP_OUT = ROOT / "patch/Release/SPECTER_MASTER_DATA_USA_AIRCRAFT_QUEUE_ICON_SYNC.zip"

# Object -> verified CommandButton ButtonImage (source of truth)
SYNC = {
    "AmericaJetB2Spirit": "B2DropBombTB",
    "AmericaJetB52H": "B52",
    "AmericaJetB1R": "B1",
    "AmericaJetAC130": "Avionac130",
}

# Already matched — audit only
AUDIT_OK = {
    "AmericaJetB2A": "B2A",
    "AmericaJetE3Visual": "E3USA",
    "AmericaJetE737Visual": "avionE737",
    "AmericaJetE2Visual": "E2avionHE",
    "AmericaJetC17Visual": "C17GlobalMaster",
    "AmericaJetV22Visual": "V22",
}


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        size = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, off, size))
    return entries, data


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


def find_object(files: dict[str, bytes], obj_name: str):
    for key, blob in files.items():
        if not key.lower().endswith(".ini"):
            continue
        text = blob.decode("utf-8", errors="replace")
        m = re.search(rf"^Object\s+{re.escape(obj_name)}\s*$", text, re.M)
        if not m:
            continue
        rest = text[m.end() :]
        m2 = re.search(r"^Object\s+\S+\s*$", rest, re.M)
        end_rel = m2.start() if m2 else len(rest)
        return key, text, m.start(), m.end() + end_rel
    return None, None, None, None


def field(body: str, name: str):
    m = re.search(rf"^\s*{re.escape(name)}\s*=\s*(\S+)", body, re.M)
    return m.group(1) if m else None


def set_field(body: str, name: str, value: str) -> tuple[str, str | None]:
    """Replace existing field or insert after first Draw/ART block start. Returns (new_body, old)."""
    m = re.search(rf"^(\s*{re.escape(name)}\s*=\s*)(\S+)", body, re.M)
    if m:
        old = m.group(2)
        new_body = body[: m.start(2)] + value + body[m.end(2) :]
        return new_body, old
    # Insert near top after Object line content — after KindOf or DisplayName if present
    insert_after = None
    for anchor in ("SelectPortrait", "ButtonImage", "DisplayName", "Side", "KindOf"):
        am = re.search(rf"^\s*{anchor}\s*=\s*\S+.*$", body, re.M)
        if am:
            insert_after = am.end()
            break
    line = f"  {name} = {value}\n"
    if insert_after is not None:
        # if inserting ButtonImage and SelectPortrait missing handling elsewhere
        new_body = body[:insert_after] + "\n" + line + body[insert_after:]
    else:
        # after first newline of body
        nl = body.find("\n")
        new_body = body[: nl + 1] + line + body[nl + 1 :]
    return new_body, None


def get_cb_image(cb_text: str, obj: str) -> tuple[str | None, str | None]:
    for m in re.finditer(rf"Object\s*=\s*{re.escape(obj)}\b", cb_text):
        before = cb_text[: m.start()]
        cms = list(re.finditer(r"^CommandButton\s+(\S+)\s*$", before, re.M))
        if not cms:
            continue
        name = cms[-1].group(1)
        if "Construct" not in name:
            continue
        block = cb_text[cms[-1].start() : m.start() + 400]
        bi = re.search(r"ButtonImage\s*=\s*(\S+)", block)
        return name, bi.group(1) if bi else None
    return None, None


def main() -> int:
    STAGE.mkdir(parents=True, exist_ok=True)
    VERIFY.mkdir(parents=True, exist_ok=True)

    entries, raw = read_big(DATA_BIG)
    files: dict[str, bytes] = {}
    order: list[str] = []
    for name, off, size in entries:
        key = name.replace("/", "\\")
        if key not in files:
            order.append(key)
        files[key] = raw[off : off + size]

    cb_text = files[r"Data\INI\CommandButton.ini"].decode("utf-8", errors="replace")
    report_lines = []
    changes = []

    # Verify CB images match expected source of truth (do not modify CB)
    for obj, expected_img in {**SYNC, **AUDIT_OK}.items():
        cbn, cbi = get_cb_image(cb_text, obj)
        if cbi != expected_img:
            raise RuntimeError(f"CommandButton for {obj} is {cbi}, expected {expected_img} (cb={cbn})")

    for obj, new_img in SYNC.items():
        key, text, start, end = find_object(files, obj)
        if text is None:
            raise RuntimeError(f"Object not found: {obj}")
        body = text[start:end]
        old_bi = field(body, "ButtonImage")
        old_sp = field(body, "SelectPortrait")
        cbn, cbi = get_cb_image(cb_text, obj)
        assert cbi == new_img

        new_body, _ = set_field(body, "ButtonImage", new_img)
        # Match known-good Specter pattern for these aircraft: SelectPortrait == ButtonImage
        # (already used by B2A/E3/E737/E2/C17/V22 with the same TB icons)
        new_body, _ = set_field(new_body, "SelectPortrait", new_img)

        if new_body == body:
            raise RuntimeError(f"No change applied for {obj}")

        new_text = text[:start] + new_body + text[end:]
        files[key] = new_text.encode("utf-8")
        changes.append(
            {
                "object": obj,
                "file": key,
                "command_button": cbn,
                "cb_image": cbi,
                "old_button": old_bi,
                "new_button": new_img,
                "old_portrait": old_sp,
                "new_portrait": new_img,
            }
        )
        report_lines.append(
            f"{obj}: ButtonImage {old_bi} -> {new_img}; SelectPortrait {old_sp} -> {new_img}"
        )

    # Audit OK set unchanged
    other_ok = []
    for obj, img in AUDIT_OK.items():
        key, text, start, end = find_object(files, obj)
        body = text[start:end]
        bi = field(body, "ButtonImage")
        sp = field(body, "SelectPortrait")
        if bi != img:
            raise RuntimeError(f"{obj} expected ButtonImage={img}, got {bi}")
        other_ok.append(f"{obj}: already matched ButtonImage={bi} SelectPortrait={sp}")

    # Rebuild BIG
    final: dict[str, bytes] = {}
    seen = set()
    for key in order:
        final[key] = files[key]
        seen.add(key)
    for key, content in files.items():
        if key not in seen:
            final[key] = content

    out_bytes = build_big(final)
    out_path = STAGE / "out" / "_SPEC_DATA_ONE.big"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(out_bytes)
    DATA_BIG.write_bytes(out_bytes)

    # Re-extract validate
    v_entries, v_raw = read_big(DATA_BIG)
    vfiles = {n.replace("/", "\\"): v_raw[o : o + s] for n, o, s in v_entries}
    vcb = vfiles[r"Data\INI\CommandButton.ini"].decode("utf-8", errors="replace")

    # Ensure CommandButton.ini byte-identical to pre-change? We didn't modify it in files from original
    # (we only changed object inis). Good.

    results = []
    all_pass = True
    for ch in changes:
        obj = ch["object"]
        key, text, start, end = find_object(vfiles, obj)
        body = text[start:end]
        bi = field(body, "ButtonImage")
        sp = field(body, "SelectPortrait")
        cbn, cbi = get_cb_image(vcb, obj)
        matched = bi == cbi == ch["new_button"]
        if not matched:
            all_pass = False
        results.append(
            {
                **ch,
                "verified_button": bi,
                "verified_portrait": sp,
                "verified_cb": cbi,
                "matched": matched,
            }
        )

    # Confirm CB unchanged for all targets
    for obj, img in {**SYNC, **AUDIT_OK}.items():
        cbn, cbi = get_cb_image(vcb, obj)
        if cbi != img:
            all_pass = False

    report = []
    report.append("USA AIRCRAFT QUEUE ICON SYNC = " + ("PASS" if all_pass else "FAIL"))
    report.append("Production queue uses Object field = ButtonImage")
    report.append("Production portrait uses Object field = SelectPortrait")
    report.append("(Verified: known-good fighters use CB ButtonImage == Object ButtonImage == SelectPortrait)")
    report.append("")
    labels = {
        "AmericaJetB2Spirit": "B-2",
        "AmericaJetB52H": "B-52",
        "AmericaJetB1R": "B-1",
        "AmericaJetAC130": "AC-130",
    }
    for r in results:
        label = labels[r["object"]]
        report.append(f"{label}:")
        report.append(f"Object = {r['object']}")
        report.append(f"CommandButton ButtonImage = {r['cb_image']}")
        report.append(f"Old Object ButtonImage = {r['old_button']}")
        report.append(f"New Object ButtonImage = {r['verified_button']}")
        report.append(f"Old SelectPortrait = {r['old_portrait']}")
        report.append(f"New SelectPortrait = {r['verified_portrait']}")
        report.append(f"Matched = {'YES' if r['matched'] else 'NO'}")
        report.append("")

    report.append("B-2A:")
    key, text, start, end = find_object(vfiles, "AmericaJetB2A")
    body = text[start:end]
    report.append("Object = AmericaJetB2A")
    report.append(f"CommandButton ButtonImage = {get_cb_image(vcb, 'AmericaJetB2A')[1]}")
    report.append(f"Old Object ButtonImage = B2A (already matched)")
    report.append(f"New Object ButtonImage = {field(body, 'ButtonImage')}")
    report.append(f"Matched = YES")
    report.append("")
    report.append("Other mismatches found = NONE among E-3/E-737/E-2/C-17/V-22")
    report.append("Other mismatches fixed = NONE (already matched)")
    report.append("")
    report.append("Gameplay changed = NO")
    report.append("ART changed = NO")
    report.append(f"DATA SHA256 = {hashlib.sha256(out_bytes).hexdigest()}")
    report.append("")
    report.append("Files touched:")
    for r in results:
        report.append(f"  {r['file']}")

    report_text = "\n".join(report) + "\n"
    (VERIFY / "REPORT.txt").write_text(report_text, encoding="utf-8")
    print(report_text)

    if not all_pass:
        raise SystemExit(2)

    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with zipfile.ZipFile(ZIP_OUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, arcname="_SPEC_DATA_ONE.big")
    print(f"Wrote {ZIP_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
