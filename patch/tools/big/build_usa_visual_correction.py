#!/usr/bin/env python3
"""USA aircraft visual-only ART pass.

Does not rebuild aircraft DATA gameplay:
  no weapons, CommandSet, AI, unit names, costs, or buttons.

Replaces Draw/model/texture refs only:

  AmericaJetF35C     LSFUSAF35A -> AVF-35 (F-35B JSF donor mesh)
  AmericaJetF-22A_AA US_F22A    -> LSFF22 (AuterF22 donor mesh)
  US_EA18G.W3D       US_EA18G.tga -> US_EA18G.dds (F/A-18G donor texture)

Source of truth: current packed BIGs. Entry order preserved.
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

SRC_DATA = Path("/tmp/japan_korea_reset_c17/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/japan_korea_reset_c17/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/usa_visual_correction")

F35C_PATH = r"Data\INI\Object\Specter\United States Of America\Airforce\F35C.ini"
F22_PATH = r"Data\INI\Object\Specter\United States Of America\Airforce\F22A_AA.ini"
F18_PATH = r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaJetF18Prowler.ini"
EA18_PATH = r"Data\INI\Object\Specter\United States Of America\Airforce\EA18G.ini"
AUTER_PATH = r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaJetAuterF22.ini"

F35C_DRAW = """
  Draw                   = W3DModelDraw ModuleTag_01

    DefaultConditionState
      Model               = AVF-35
      WeaponLaunchBone    = PRIMARY WEAPONA01
    End
    ConditionState        = RIDER1
      Model               = AVF-35
      WeaponLaunchBone    = PRIMARY WEAPONA01
    End
    ConditionState        = RIDER2
      Model               = AVF-35
      WeaponLaunchBone    = PRIMARY WEAPONA01
    End

    ConditionState        = JETEXHAUST
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End
    ConditionState        = RIDER1 JETEXHAUST
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End
    ConditionState        = RIDER2 JETEXHAUST
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End

    ConditionState        = JETEXHAUST JETAFTERBURNER
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
      ParticleSysBone     = Engine01 JetLenzflare
    End
    ConditionState        = RIDER1 JETEXHAUST JETAFTERBURNER
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
      ParticleSysBone     = Engine01 JetLenzflare
    End
    ConditionState        = RIDER2 JETEXHAUST JETAFTERBURNER
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
      ParticleSysBone     = Engine01 JetLenzflare
    End

    ConditionState        = REALLYDAMAGED
      Model               = AVF-35_D
      ParticleSysBone     = Engine01 JetEngineDamagedSmoke
    End

    ConditionState        = REALLYDAMAGED JETEXHAUST
      Model               = AVF-35_D
      ParticleSysBone     = Engine01 JetEngineDamagedSmoke
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End

    ConditionState        = REALLYDAMAGED JETEXHAUST JETAFTERBURNER
      Model               = AVF-35_D
      ParticleSysBone     = Engine01 JetEngineDamagedSmoke
      ParticleSysBone     = Engine01 JetLenzflare
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End

    ConditionState        = RUBBLE
      Model               = AVF-35_E
      HideSubObject       = None
      ShowSubObject       = None
    End

    ConditionState        = RUBBLE JETEXHAUST JETAFTERBURNER
      Model               = AVF-35_E
      HideSubObject       = None
      ShowSubObject       = None
      ParticleSysBone     = Engine01 JetExhaust
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End
    AliasConditionState = RIDER1 REALLYDAMAGED
    AliasConditionState = RIDER1 REALLYDAMAGED JETEXHAUST
    AliasConditionState = RIDER1 REALLYDAMAGED JETEXHAUST JETAFTERBURNER
    AliasConditionState = RIDER1 RUBBLE
    AliasConditionState = RIDER1 RUBBLE JETEXHAUST JETAFTERBURNER
    AliasConditionState = RIDER2 REALLYDAMAGED
    AliasConditionState = RIDER2 REALLYDAMAGED JETEXHAUST
    AliasConditionState = RIDER2 REALLYDAMAGED JETEXHAUST JETAFTERBURNER
    AliasConditionState = RIDER2 RUBBLE
    AliasConditionState = RIDER2 RUBBLE JETEXHAUST JETAFTERBURNER

    OkToChangeModelColor = Yes

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


def nl(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def to_nl(block: str, newline: str) -> str:
    return block.replace("\r\n", "\n").replace("\n", newline).strip("\n") + newline


def object_span(text: str, obj: str):
    m = re.search(rf"(?ms)^Object\s+{re.escape(obj)}\s*\r?\n.*?(?=^Object\s|\Z)", text)
    if not m:
        raise SystemExit(f"Object {obj} missing")
    return m.start(), m.end(), m.group(0)


def replace_draw(obj_text: str, replacement: str) -> str:
    m = re.search(r"(?ms)^  Draw\s*=\s*W3DModelDraw\s+\S+\s*\r?\n.*?^  End\s*$", obj_text)
    if not m:
        raise SystemExit("Draw module missing")
    return obj_text[: m.start()] + to_nl(replacement, nl(obj_text)).rstrip("\r\n") + obj_text[m.end() :]


def replace_art_params(obj_text: str, portrait: str, button: str) -> str:
    obj_text = re.sub(
        r"(?m)^(\s*SelectPortrait\s*=\s*)\S+",
        rf"\1{portrait}",
        obj_text,
        count=1,
    )
    obj_text = re.sub(
        r"(?m)^(\s*ButtonImage\s*=\s*)\S+",
        rf"\1{button}",
        obj_text,
        count=1,
    )
    return obj_text


def gameplay_fingerprint(obj_text: str) -> str:
    """Everything except Draw / portrait / button image."""
    text = re.sub(r"(?ms)^  Draw\s*=\s*W3DModelDraw\s+\S+\s*\r?\n.*?^  End\s*$", "", obj_text)
    text = re.sub(r"(?m)^\s*SelectPortrait\s*=\s*\S+\s*$", "", text)
    text = re.sub(r"(?m)^\s*ButtonImage\s*=\s*\S+\s*$", "", text)
    text = re.sub(r"(?m)^\s*;.*$", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


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

    # --- F-35C: AVF-35 JSF mesh + JSF button/portrait textures ---
    i = data_index[norm(F35C_PATH)]
    name, blob = data_entries[i]
    text = blob.decode("latin1")
    a, b, obj = object_span(text, "AmericaJetF35C")
    before = gameplay_fingerprint(obj)
    obj = replace_draw(obj, F35C_DRAW)
    obj = replace_art_params(obj, "AmericaF35BJSF", "AmericaF35BJSF")
    after = gameplay_fingerprint(obj)
    if before != after:
        raise SystemExit("F-35C gameplay fingerprint changed")
    text = text[:a] + obj + text[b:]
    data_entries[i] = (name, text.encode("latin1"))
    print("F-35C Draw -> AVF-35 / AmericaF35BJSF")

    # --- F-22 AA: AuterF22 Draw (LSFF22) ---
    auter_text = data_entries[data_index[norm(AUTER_PATH)]][1].decode("latin1")
    _, _, auter_obj = object_span(auter_text, "AmericaJetAuterF22")
    auter_draw = re.search(
        r"(?ms)^  Draw\s*=\s*W3DModelDraw\s+\S+\s*\r?\n.*?^  End\s*$", auter_obj
    )
    if not auter_draw:
        raise SystemExit("AuterF22 Draw missing")
    i = data_index[norm(F22_PATH)]
    name, blob = data_entries[i]
    text = blob.decode("latin1")
    a, b, obj = object_span(text, "AmericaJetF-22A_AA")
    before = gameplay_fingerprint(obj)
    obj = replace_draw(obj, auter_draw.group(0))
    after = gameplay_fingerprint(obj)
    if before != after:
        raise SystemExit("F-22 gameplay fingerprint changed")
    if not obj.startswith("Object AmericaJetF-22A_AA"):
        raise SystemExit("F-22 object name changed")
    text = text[:a] + obj + text[b:]
    data_entries[i] = (name, text.encode("latin1"))
    print("F-22 AA Draw -> LSFF22 AuterF22 visual")

    # --- F/A-18G: connect donor texture names on the existing Growler W3D ---
    w3d_key = norm(r"Art\W3D\US_EA18G.W3D")
    i = art_index[w3d_key]
    name, blob = art_entries[i]
    if b"US_EA18G.tga" not in blob:
        raise SystemExit("US_EA18G.W3D has no .tga texture refs to retarget")
    fixed = blob.replace(b"US_EA18G.tga", b"US_EA18G.dds")
    if b"US_EA18G.tga" in fixed:
        raise SystemExit("EA18G tga retarget incomplete")
    if len(fixed) != len(blob):
        raise SystemExit("EA18G W3D size changed")
    art_entries[i] = (name, fixed)
    print("US_EA18G.W3D texture refs -> US_EA18G.dds")

    # Confirm F/A-18 objects still point at US_EA18G (DATA unchanged).
    for path, obj_name in ((F18_PATH, "AmericaJetF18Prowler"), (EA18_PATH, "AmericaJetEA18G")):
        text = data_entries[data_index[norm(path)]][1].decode("latin1")
        _, _, obj = object_span(text, obj_name)
        models = set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", obj))
        if models - {"US_EA18G", "None"}:
            raise SystemExit(f"{obj_name} unexpected models {models}")
        print(obj_name, "keeps", sorted(models))

    if [n for n, _ in data_entries] != original_data_names:
        raise SystemExit("DATA entry order/names changed")
    if [n for n, _ in art_entries] != original_art_names:
        raise SystemExit("ART entry order/names changed")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_data = OUT_DIR / "_SPEC_DATA_ONE.big"
    packed = build_big_ordered(data_entries)
    out_data.write_bytes(packed)
    print("wrote", out_data, "size", len(packed), "files", len(data_entries), "sha", hashlib.sha256(packed).hexdigest())

    out_art = OUT_DIR / "_SPEC_ART_ONE.big"
    packed_art = build_big_ordered(art_entries)
    out_art.write_bytes(packed_art)
    print("wrote", out_art, "size", len(packed_art), "files", len(art_entries), "sha", hashlib.sha256(packed_art).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
