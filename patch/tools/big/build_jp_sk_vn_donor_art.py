#!/usr/bin/env python3
"""Replace Japan / South Korea / Vietnam aircraft visuals only.

Uses packed ART donor meshes already in _SPEC_ART_ONE.big.
Does not touch PlayerTemplate, Faction, CommandCenter, VT72B, or CommandSet.
Does not change weapons, AI, locomotor, costs, or other gameplay DATA.
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

SRC_DATA = Path("/tmp/country_air_roster/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/country_air_roster/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/jp_sk_vn_donor_art")

# path -> model map, bone map, optional portrait
# model map is exact Model= token replacement.
VISUALS = {
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF35A.ini": {
        "models": {"LSFUSAF35A": "JPF35A", "LSFUSAF35Ad": "JPF35Ad", "LSFUSAF35Ak": "JPF35Ak"},
        "bones": {},  # already MISSILEA01
        "why": "unique Japan F-35A stem JPF35A",
    },
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF35B.ini": {
        "models": {"LSFUSAF35A": "AVF-35", "LSFUSAF35Ad": "AVF-35_D", "LSFUSAF35Ak": "AVF-35_E"},
        "bones": {"MISSILEA01": "WEAPONA01"},
        "why": "JSF AVF-35; do not use invisible JP_F35B",
    },
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF15J.ini": {
        "models": {},
        "bones": {"WeaponA": "MISSILEA01"},
        "why": "keep LSFJPF15J; launch bone matches mesh",
    },
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF2A.ini": {
        "models": {},
        "bones": {"WeaponA": "MISSILEA01"},
        "why": "keep JPF2; launch bone matches mesh",
    },
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF2B.ini": {
        "models": {},
        "bones": {"WeaponA": "WEAPONA01"},
        "why": "keep AGMZJPF2G two-seater F-2; launch bone matches mesh",
    },
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF2Kai.ini": {
        "models": {"LSF02TJ": "JPF2", "LSF02TJd": "JPF2D", "LSF02TJk": "JPF2K"},
        "bones": {"WeaponA": "MISSILEA01"},
        "why": "LSF02TJ is a ZBD/IFV turret mesh; replace with JPF2",
    },
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF4EJKai.ini": {
        "models": {},
        "bones": {"WeaponA": "MISSILEA01"},
        "why": "keep JPF4; launch bone matches mesh",
    },
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetX2Shinshin.ini": {
        "models": {},
        "bones": {"WeaponA": "MISSILEA"},
        "why": "keep LSFSX2; launch bone matches mesh (not J-20 JP_X2Shinshin)",
    },
    r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF35A.ini": {
        "models": {"LSFUSAF35A": "AVF-35", "LSFUSAF35Ad": "AVF-35_D", "LSFUSAF35Ak": "AVF-35_E"},
        "bones": {"MISSILEA01": "WEAPONA01"},
        "why": "JSF AVF-35 visual cleanup",
    },
    r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF35B.ini": {
        "models": {"LSFUSAF35A": "AVF-35", "LSFUSAF35Ad": "AVF-35_D", "LSFUSAF35Ak": "AVF-35_E"},
        "bones": {"MISSILEA01": "WEAPONA01"},
        "why": "JSF AVF-35 visual cleanup",
    },
    r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetKF21.ini": {
        "models": {},
        "bones": {"WeaponA": "MISSILEA01"},
        "why": "keep LSFJ31 (only packed KF-21-class mesh); launch bone matches",
    },
    r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF15KSlam.ini": {
        "models": {},
        "bones": {"WeaponA": "WEAPONA01"},
        "why": "keep LSFF15K; launch bone matches mesh",
    },
    r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF16C.ini": {
        "models": {},
        "bones": {"WeaponA": "MISSILEA01"},
        "why": "keep LSFKF16; launch bone matches mesh",
    },
    r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetF16D.ini": {
        "models": {},
        "bones": {"WeaponA": "MISSILEA01"},
        "why": "keep LSFKF16; launch bone matches mesh",
    },
    r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce\SouthKoreaJetFA50.ini": {
        "models": {},
        "bones": {"Weapon01": "MISSILE01"},
        "why": "keep LSFT50; launch bone matches mesh",
    },
    r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu30.ini": {
        "models": {},
        "bones": {},
        "why": "keep RUS_SU30SM2; ART tga->dds so packed texture loads",
    },
    r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu27.ini": {
        "models": {},
        "bones": {"Weapon01": "MISSILEB01", "Weapon02": "MISSILEB02"},
        "why": "keep LSFRUSU27SK; launch bones match mesh",
    },
    r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetMig29S.ini": {
        "models": {},
        "bones": {"Weapon01": "MISSILEA01", "Weapon02": "MISSILEB01"},
        "portrait": "LSFRUMIG29",
        "why": "keep LSFruMiG29; drop irq_ portrait; bones match mesh",
    },
    r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetSu22.ini": {
        "models": {"Irq_SU22M3": "Irn_SU22M2"},
        "bones": {"Weapon01": "WEAPONB01", "Weapon02": "WEAPONB02"},
        "why": "replace Iraq Irq_SU22M3 with packed Irn_SU22M2",
    },
    r"Data\INI\Object\Specter\Vietnam People's Army\Airforce\VietnamJetF5E.ini": {
        "models": {"AVHawk_P": "LSFKoreaF5", "AVHawk_D": "LSFKoreaF5k"},
        "bones": {"Weapon01": "MISSILEA01", "Weapon02": "MISSILEB01"},
        "damaged": "LSFKoreaF5d",
        "why": "AVHawk_P is E-2 Hawkeye; replace with LSFKoreaF5",
    },
}

LOCKED = (
    r"Data\INI\PlayerTemplate.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\Science.ini",
    r"Data\INI\CommandButton.ini",
)

LOCKED_SUBSTR = (
    "commandcenter",
    "vt72b",
    "playertemplate",
)

ART_TGA_TO_DDS = (
    (r"Art\W3D\RUS_SU30SM2.W3D", b"RUS_SU30SM2.tga", b"RUS_SU30SM2.dds"),
    (r"Art\W3D\AGMZJPF2G.W3D", b"JapF2FIM.tga", b"JapF2FIM.dds"),
)


def parse_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    nfiles = struct.unpack(">I", data[8:12])[0]
    off = 16
    entries = []
    for _ in range(nfiles):
        eoff, esz = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries.append((name, data[eoff : eoff + esz]))
    return entries


def build_big_ordered(entries: list[tuple[str, bytes]]) -> bytes:
    header_size = 16
    encoded = [(n.encode("latin1"), b) for n, b in entries]
    for nb, _blob in encoded:
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for nb, blob in encoded:
        index.append((nb, offset, len(blob)))
        blobs.append(blob)
        offset += len(blob)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(encoded))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def norm(name: str) -> str:
    return name.replace("/", "\\").lower()


def gameplay_fingerprint(text: str) -> str:
    text = re.sub(r"(?ms)^\s*Draw\s*=\s*W3DModelDraw.*?^\s*End\s*$", "", text, count=1)
    text = re.sub(r"(?m)^\s*SelectPortrait\s*=\s*\S+\s*$", "", text)
    text = re.sub(r"(?m)^\s*ButtonImage\s*=\s*\S+\s*$", "", text)
    return text


def patch_visual(text: str, spec: dict) -> str:
    models = spec.get("models") or {}
    bones = spec.get("bones") or {}
    portrait = spec.get("portrait")

    def model_sub(m):
        val = m.group(2)
        return m.group(1) + models.get(val, val)

    text = re.sub(r"(?m)^(\s*Model\s*=\s*)(\S+)", model_sub, text)

    def bone_sub(m):
        bone = m.group(3)
        return m.group(1) + m.group(2) + bones.get(bone, bone)

    text = re.sub(r"(?m)^(\s*WeaponLaunchBone\s*=\s*\S+\s+)(\s*)(\S+)", bone_sub, text)
    if portrait:
        text = re.sub(r"(?m)^(\s*SelectPortrait\s*=\s*)\S+", rf"\1{portrait}", text)
        text = re.sub(r"(?m)^(\s*ButtonImage\s*=\s*)\S+", rf"\1{portrait}", text)
    damaged = spec.get("damaged")
    if damaged:
        text = re.sub(
            r"(?m)(^(\s*)ConditionState\s*=\s*REALLYDAMAGED.*\r?\n\s*Model\s*=\s*)\S+",
            rf"\1{damaged}",
            text,
        )
    return text


def art_stems(entries) -> set[str]:
    stems = set()
    for n, _ in entries:
        base = n.replace("/", "\\").split("\\")[-1]
        if base.lower().endswith(".w3d"):
            stems.add(base[:-4])
    return stems


def main() -> int:
    if not SRC_DATA.is_file() or not SRC_ART.is_file():
        print("missing source BIGs", file=sys.stderr)
        return 1

    data_entries = parse_big(SRC_DATA)
    art_entries = parse_big(SRC_ART)
    data_index = {norm(n): i for i, (n, _) in enumerate(data_entries)}
    art_index = {norm(n): i for i, (n, _) in enumerate(art_entries)}
    original_data_names = [n for n, _ in data_entries]
    original_art_names = [n for n, _ in art_entries]
    stems = art_stems(art_entries)

    locked_before = {norm(p): data_entries[data_index[norm(p)]][1] for p in LOCKED}

    for path, spec in VISUALS.items():
        key = norm(path)
        if any(s in key for s in LOCKED_SUBSTR):
            raise SystemExit(f"refusing locked path {path}")
        i = data_index[key]
        name, blob = data_entries[i]
        old = blob.decode("latin1")
        new = patch_visual(old, spec)
        if gameplay_fingerprint(old) != gameplay_fingerprint(new):
            raise SystemExit(f"gameplay DATA changed {path}")
        models = re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", new)
        missing = [m for m in models if m not in stems]
        if missing:
            raise SystemExit(f"Model= not in packed ART {path}: {missing}")
        if "Iraq_" in " ".join(models) or any(m.startswith("Irq_") for m in models):
            raise SystemExit(f"Iraq model still used {path}: {models}")
        if new == old and not spec.get("models") and not spec.get("bones") and not spec.get("portrait"):
            print("visual-ready", path, spec["why"])
        elif new == old:
            raise SystemExit(f"no visual change {path}")
        else:
            data_entries[i] = (name, new.encode("latin1"))
            print("patched", path, "models", sorted(set(models)), spec["why"])

    for art_path, old, new in ART_TGA_TO_DDS:
        if len(old) != len(new):
            raise SystemExit(f"tga/dds length mismatch {old} {new}")
        key = norm(art_path)
        i = art_index[key]
        name, blob = art_entries[i]
        if old not in blob:
            print("no tga ref", art_path, old)
            continue
        art_entries[i] = (name, blob.replace(old, new))
        print("hex-fixed", art_path, old, "->", new)

    for (n, old), (_, new) in zip(parse_big(SRC_DATA), data_entries):
        key = norm(n)
        if key in {norm(p) for p in LOCKED} and old != new:
            raise SystemExit(f"locked file changed {n}")
        if any(s in key for s in LOCKED_SUBSTR) and old != new:
            raise SystemExit(f"faction-chain file changed {n}")
        if key not in {norm(p) for p in VISUALS} and old != new:
            raise SystemExit(f"unexpected DATA mutation {n}")

    if [n for n, _ in data_entries] != original_data_names:
        raise SystemExit("DATA entry order changed")
    if [n for n, _ in art_entries] != original_art_names:
        raise SystemExit("ART entry order changed")
    for p, before in locked_before.items():
        if data_entries[data_index[p]][1] != before:
            raise SystemExit(f"locked blob changed {p}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    packed_data = build_big_ordered(data_entries)
    packed_art = build_big_ordered(art_entries)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(packed_data)
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(packed_art)
    print("wrote DATA", len(packed_data), hashlib.sha256(packed_data).hexdigest())
    print("wrote ART", len(packed_art), hashlib.sha256(packed_art).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
