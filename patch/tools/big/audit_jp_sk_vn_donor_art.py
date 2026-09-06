#!/usr/bin/env python3
"""Audit every Model= on priority JP/SK/VN aircraft against packed ART."""

from __future__ import annotations

import io
import re
import struct
import sys
from pathlib import Path

DATA = Path("/tmp/jp_sk_vn_donor_art/_SPEC_DATA_ONE.big")
ART = Path("/tmp/jp_sk_vn_donor_art/_SPEC_ART_ONE.big")
SRC_DATA = Path("/tmp/country_air_roster/_SPEC_DATA_ONE.big")
REPORT = Path("/opt/cursor/artifacts/jp_sk_vn_donor_art_audit.txt")

OBJECTS = [
    "JapanJetF35A",
    "JapanJetF35B",
    "JapanJetF15J",
    "JapanJetF2A",
    "JapanJetF2B",
    "JapanJetF2Kai",
    "JapanJetF4EJKai",
    "JapanJetX2Shinshin",
    "SouthKoreaJetF35A",
    "SouthKoreaJetF35B",
    "SouthKoreaJetKF21",
    "SouthKoreaJetF15KSlam",
    "SouthKoreaJetF16C",
    "SouthKoreaJetF16D",
    "SouthKoreaJetFA50",
    "VietnamJetSu30",
    "VietnamJetSu27",
    "VietnamJetMig29S",
    "VietnamJetSu22",
    "VietnamJetF5E",
]

FORBIDDEN_MODELS = ("Irq_", "Iraq_", "AVHawk", "LSF02TJ", "JP_F35B", "ENF35A")
LOCKED_NAMES = ("playertemplate.ini", "commandset.ini", "commandbutton.ini", "science.ini")


def parse_big(path: Path):
    data = path.read_bytes()
    nfiles = struct.unpack(">I", data[8:12])[0]
    off = 16
    entries = []
    for i in range(nfiles):
        eoff, esz = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries.append((i, name, data[eoff : eoff + esz]))
    return entries


def last_object(entries, obj: str):
    hits = []
    for i, n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", "replace")
        if re.search(rf"(?m)^Object\s+{re.escape(obj)}\s*$", t):
            m = re.search(rf"(?ms)^Object\s+{re.escape(obj)}\s*\r?\n.*?(?=^Object\s|\Z)", t)
            hits.append((i, n, m.group(0) if m else t))
    return hits[-1] if hits else None


def gameplay(text: str) -> str:
    text = re.sub(r"(?ms)^\s*Draw\s*=\s*W3DModelDraw.*?^\s*End\s*$", "", text, count=1)
    text = re.sub(r"(?m)^\s*SelectPortrait\s*=\s*\S+\s*$", "", text)
    text = re.sub(r"(?m)^\s*ButtonImage\s*=\s*\S+\s*$", "", text)
    return text


def named(text, kind, name):
    m = re.search(rf"(?ms)^{kind}\s+{re.escape(name)}\s*\r?\n.*?^End\s*$", text)
    return m.group(0) if m else None


def main() -> int:
    if not DATA.is_file() or not ART.is_file():
        print("missing packed BIGs", file=sys.stderr)
        return 1
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


def _run() -> int:
    data = parse_big(DATA)
    art = parse_big(ART)
    src = parse_big(SRC_DATA)
    errors = []
    stems = set()
    art_idx = {}
    for i, n, b in art:
        art_idx[n.replace("/", "\\").lower()] = b
        base = n.replace("/", "\\").split("\\")[-1]
        if base.lower().endswith(".w3d"):
            stems.add(base[:-4])

    print("PACKED DATA", DATA, "files", len(data))
    print("PACKED ART", ART, "files", len(art), "w3d", len(stems))
    print()

    src_idx = {n.replace("/", "\\").lower(): b for i, n, b in src}
    new_idx = {n.replace("/", "\\").lower(): b for i, n, b in data}
    for locked in LOCKED_NAMES:
        sk = [k for k in src_idx if k.endswith(locked)]
        nk = [k for k in new_idx if k.endswith(locked)]
        if not sk or src_idx[sk[0]] != new_idx[nk[0]]:
            errors.append(f"locked file changed {locked}")
        else:
            print("LOCKED unchanged", locked)

    for i, n, b in data:
        ln = n.lower()
        if any(x in ln for x in ("commandcenter", "vt72b")) and src_idx[n.replace("/", "\\").lower()] != b:
            errors.append(f"faction-chain file changed {n}")

    print()
    print("MODEL AUDIT")
    for obj in OBJECTS:
        hit = last_object(data, obj)
        src_hit = last_object(src, obj)
        print("=" * 72)
        print(obj)
        if not hit:
            errors.append(f"{obj} missing")
            continue
        i, n, block = hit
        models = re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", block)
        bones = re.findall(r"(?m)^\s*WeaponLaunchBone\s*=\s*(\S+)\s+(\S+)", block)
        portrait = re.search(r"(?m)^\s*SelectPortrait\s*=\s*(\S+)", block)
        print("  file", n)
        print("  models", models)
        print("  bones", bones)
        print("  portrait", portrait.group(1) if portrait else None)
        for model in models:
            if model not in stems:
                errors.append(f"{obj} Model={model} NOT in packed ART")
                print("  FAIL missing W3D", model)
            else:
                print("  OK W3D", model)
            if any(model.startswith(bad) or bad in model for bad in FORBIDDEN_MODELS):
                errors.append(f"{obj} forbidden model {model}")
        if src_hit and gameplay(src_hit[2]) != gameplay(block):
            errors.append(f"{obj} gameplay DATA changed")
            print("  FAIL gameplay changed")
        else:
            print("  OK gameplay fingerprint unchanged")
        if "Iraq" in n or "\\Iraq_" in n:
            errors.append(f"{obj} still defined in Iraq file {n}")

    su30 = art_idx.get(r"art\w3d\rus_su30sm2.w3d", b"")
    if b"RUS_SU30SM2.tga" in su30:
        errors.append("RUS_SU30SM2.W3D still references .tga")
    else:
        print("OK RUS_SU30SM2.W3D uses .dds")

    print()
    print("=" * 72)
    if errors:
        print("AUDIT_FAIL")
        for e in errors:
            print("ERROR", e)
        return 1
    print("AUDIT_OK every priority Model= exists in packed ART")
    print("AUDIT_OK gameplay DATA / CommandSet / faction chain unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
