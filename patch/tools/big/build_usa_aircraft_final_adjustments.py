#!/usr/bin/env python3
"""Surgical USA aircraft final adjustments into packed _SPEC_DATA_ONE.big.

Preserves entry order. Does not rebuild ART. Does not pack overlay CommandSet
as a whole file — slot/button/weapon edits are applied inside the live packed
INI copies.
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

SRC_DATA = Path("/tmp/usa_airforce_overhaul/_SPEC_DATA_ONE.big")
OUT_DIR = Path("/tmp/usa_aircraft_final_adj")
PATCH = Path("/workspace/patch/Data/INI")

OBJECT_REPLACEMENTS = {
    r"Data\INI\Object\Specter\United States Of America\AmericaJetF117Clean.ini":
        PATCH / "Object/Specter/United States Of America/AmericaJetF117Clean.ini",
    r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaJetAuterF22.ini":
        PATCH / "Object/Specter/United States Of America/Airforce/AmericaJetAuterF22.ini",
    r"Data\INI\Object\Specter\United States Of America\AmericaJetC17Visual.ini":
        PATCH / "Object/Specter/United States Of America/AmericaJetC17Visual.ini",
}

NEW_OBJECTS = {
    r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaJetF18Prowler.ini":
        PATCH / "Object/Specter/United States Of America/Airforce/AmericaJetF18Prowler.ini",
}

B52_WEAPON = """Weapon AmericaB52FifteenBombLineWeapon
  ; Star General AirF_SUPERWEAPON_CarpetBomb transfer:
  ; 12x Mk82_B52H (CarpetBombWeapon) dropped sequentially, DropDelay 130.
  PrimaryDamage = 1.0
  PrimaryDamageRadius = 1.0
  AttackRange = 500.0
  MinimumAttackRange = 0
  AcceptableAimDelta = 45
  DamageType = EXPLOSION
  DeathType = EXPLODED
  WeaponSpeed = 999999.0
  ProjectileObject = NONE
  FireOCL = OCL_AmericaB52StarGeneralMk82
  FireFX = FX_AuroraBombLaunch
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 130
  ClipSize = 12
  ClipReloadTime = 600000
  AutoReloadsClip = RETURN_TO_BASE
  ShowsAmmoPips = Yes
  AntiGround = Yes
  AntiAirborneVehicle = No
  AntiAirborneInfantry = No
  LeechRangeWeapon = Yes
End
"""

B52_OCL = """
ObjectCreationList OCL_AmericaB52StarGeneralMk82
  CreateObject
    Offset = X:0 Y:0 Z:-2
    ObjectNames = Mk82_B52H
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Count = 1
  End
End
"""

PROWLER_BUTTONS = """
CommandButton Command_ConstructAmericaJetF18Prowler
  Command       = UNIT_BUILD
  Object        = AmericaJetF18Prowler
  TextLabel     = CONTROLBAR:ConstructAmericaJetF18Prowler
  ButtonImage   = EA18G
  ButtonBorderType        = BUILD
  DescriptLabel           = CONTROLBAR:ToolTipAmericaJetF18Prowler
End
"""


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
    encoded = []
    for name, blob in entries:
        nb = name.encode("latin1")
        encoded.append((nb, blob))
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


def replace_block(text: str, start_pat: str, end_pat: str, replacement: str) -> str:
    m = re.search(start_pat, text)
    if not m:
        raise SystemExit(f"start not found: {start_pat}")
    start = m.start()
    m2 = re.search(end_pat, text[m.end() :])
    if not m2:
        raise SystemExit(f"end not found after {start_pat}")
    end = m.end() + m2.end()
    return text[:start] + replacement + text[end:]


def patch_commandset(text: str) -> str:
    m = re.search(
        r"CommandSet America_LargeAirBaseCommandSet\s*.*?^End",
        text,
        re.S | re.M,
    )
    if not m:
        raise SystemExit("America_LargeAirBaseCommandSet not found")
    block = m.group(0)
    new_block, n = re.subn(
        r"9\s*=\s*Command_ConstructAmericaVehicleUH60",
        "9  = Command_ConstructAmericaJetF18Prowler",
        block,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"UH-60 slot 9 not replaced ({n})")
    if "Command_ConstructAmericaVehicleUH60" in new_block:
        raise SystemExit("UH-60 still present on LargeAirBase")
    if "Command_ConstructAmericaJetF18Prowler" not in new_block:
        raise SystemExit("Prowler construct missing on LargeAirBase")
    return text[: m.start()] + new_block + text[m.end() :]


def patch_weapon(text: str) -> str:
    m = re.search(
        r"^Weapon AmericaB52FifteenBombLineWeapon\s*.*?^End\s*",
        text,
        re.S | re.M,
    )
    if not m:
        raise SystemExit("AmericaB52FifteenBombLineWeapon not found")
    return text[: m.start()] + B52_WEAPON + "\n" + text[m.end() :]


def patch_ocl(text: str) -> str:
    if "OCL_AmericaB52StarGeneralMk82" in text:
        return text
    return text.rstrip() + "\n" + B52_OCL + "\n"


def patch_commandbutton(text: str) -> str:
    if "Command_ConstructAmericaJetF18Prowler" in text:
        return text
    m = re.search(r"CommandButton Command_ConstructAmericaJetEA18\s*\r?\n", text)
    if not m:
        raise SystemExit("EA18 construct button not found")
    m_end = re.search(r"\r?\nEnd\r?\n", text[m.end() :])
    if not m_end:
        raise SystemExit("EA18 button end not found")
    insert_at = m.end() + m_end.end()
    return text[:insert_at] + PROWLER_BUTTONS + text[insert_at:]


def xor_csf_utf16(s: str) -> bytes:
    raw = s.encode("utf-16-le")
    return bytes(b ^ 0xFF for b in raw)


def append_csf_labels(blob: bytes, labels: dict[str, str]) -> bytes:
    if blob[:4] != b" FSC":
        raise SystemExit("generals.csf is not CSF")
    version, nlabels, nstrings = struct.unpack_from("<III", blob, 4)
    # skip unused + language (header is 24 bytes)
    pos = 24
    # walk existing labels to validate
    for _ in range(nlabels):
        if blob[pos : pos + 4] != b" LBL":
            raise SystemExit(f"bad LBL at {pos}")
        nstr, namelen = struct.unpack_from("<II", blob, pos + 4)
        pos += 12 + namelen
        for _s in range(nstr):
            mag = blob[pos : pos + 4]
            slen = struct.unpack_from("<I", blob, pos + 4)[0]
            pos += 8 + slen * 2
            if mag == b"WRTS":
                elen = struct.unpack_from("<I", blob, pos)[0]
                pos += 4 + elen
    if pos != len(blob):
        # some CSFs have trailing padding; keep it by appending after real end
        pass
    extra = bytearray()
    add_labels = 0
    add_strings = 0
    existing = blob.upper()
    for name, value in labels.items():
        key = name.encode("latin1")
        if key.upper() in existing:
            continue
        extra += b" LBL"
        extra += struct.pack("<II", 1, len(key))
        extra += key
        extra += b" RTS"
        encoded = xor_csf_utf16(value)
        extra += struct.pack("<I", len(value))
        extra += encoded
        add_labels += 1
        add_strings += 1
    if add_labels == 0:
        return blob
    out = bytearray(blob)
    struct.pack_into("<I", out, 8, nlabels + add_labels)
    struct.pack_into("<I", out, 12, nstrings + add_strings)
    out += extra
    return bytes(out)


def main() -> int:
    if not SRC_DATA.is_file():
        print("missing source DATA BIG", SRC_DATA, file=sys.stderr)
        return 1
    entries = parse_big(SRC_DATA)
    index = {norm(n): i for i, (n, _) in enumerate(entries)}
    original_count = len(entries)

    # replace object INIs
    for big_name, src in OBJECT_REPLACEMENTS.items():
        key = norm(big_name)
        if key not in index:
            raise SystemExit(f"missing packed file {big_name}")
        entries[index[key]] = (entries[index[key]][0], src.read_bytes())
        print("replaced", big_name, "bytes", len(entries[index[key]][1]))

    for big_name, src in NEW_OBJECTS.items():
        key = norm(big_name)
        blob = src.read_bytes()
        if key in index:
            entries[index[key]] = (entries[index[key]][0], blob)
            print("replaced existing", big_name)
        else:
            entries.append((big_name, blob))
            index[key] = len(entries) - 1
            print("appended", big_name, "bytes", len(blob))

    def mut(path: str, fn):
        key = norm(path)
        i = index[key]
        name, blob = entries[i]
        text = blob.decode("latin1")
        new = fn(text)
        if new == text:
            raise SystemExit(f"no change applied to {path}")
        entries[i] = (name, new.encode("latin1"))
        print("patched", path, "delta", len(new) - len(text))

    mut(r"Data\INI\CommandSet.ini", patch_commandset)
    mut(r"Data\INI\CommandButton.ini", patch_commandbutton)
    mut(r"Data\INI\Weapon.ini", patch_weapon)
    mut(r"Data\INI\ObjectCreationList.ini", patch_ocl)

    csf_key = norm(r"Data\English\generals.csf")
    i = index[csf_key]
    name, blob = entries[i]
    new_csf = append_csf_labels(
        blob,
        {
            "OBJECT:AmericaJetF18Prowler": "F-18 Prowler",
            "CONTROLBAR:ConstructAmericaJetF18Prowler": "F-18 Prowler",
            "CONTROLBAR:ToolTipAmericaJetF18Prowler": "Build F-18 Prowler strike/support fighter",
        },
    )
    entries[i] = (name, new_csf)
    print("patched CSF", len(new_csf) - len(blob))

    # never drop files
    if len(entries) < original_count:
        raise SystemExit("entry count shrank")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_big = OUT_DIR / "_SPEC_DATA_ONE.big"
    packed = build_big_ordered(entries)
    out_big.write_bytes(packed)
    sha = hashlib.sha256(packed).hexdigest()
    print("wrote", out_big, "size", len(packed), "files", len(entries), "sha", sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
