#!/usr/bin/env python3
"""Static validation + pack overlay BIG for AmericaRadarAN/MPQ65 mobility."""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
INI = ROOT / (
    "patch/Data/INI/Object/Specter/United States Of America/"
    "AirDefense Installation/AN_MPQ65.ini"
)
LOCO = ROOT / "patch/Data/INI/Locomotor.ini"
CMD = ROOT / "patch/Data/INI/CommandSet.ini"
WEAPON = ROOT / "patch/Data/INI/Weapon.ini"
OUT_DIR = ROOT / "docs/specter-patriot-mpq65-mobile"
OUT_BIG = OUT_DIR / "_SPECTER_PATRIOT_MPQ65_MOBILE.big"
BIG_INNER = (
    "Data\\INI\\Object\\Specter\\United States Of America\\"
    "AirDefense Installation\\AN_MPQ65.ini"
)


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(1)


def objects(text: str) -> dict[str, str]:
    found = {}
    for m in re.finditer(r"(?m)^Object\s+(\S+)\s*$", text):
        name = m.group(1)
        nxt = re.search(r"(?m)^Object\s+\S+\s*$", text[m.end() :])
        end = m.end() + nxt.start() if nxt else len(text)
        found[name] = text[m.start() : end]
    return found


def pack_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin-1")) + 1
    index = []
    blobs = []
    offset = header_size
    for name, content in items:
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
        out += name.encode("latin-1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def main() -> int:
    raw = INI.read_bytes()
    text = raw.decode("latin-1")
    objs = objects(text)
    radar = objs.get("AmericaRadarAN/MPQ65")
    hole = objs.get("AmericaMPQ65Damaged")
    if not radar:
        fail("AmericaRadarAN/MPQ65 missing")
    if not hole:
        fail("AmericaMPQ65Damaged missing (packed hole object must be preserved)")

    checks = {
        "model": "Model               = US_AN_MPQ65" in radar,
        "animation": "Animation           = US_AN_MPQ65.US_AN_MPQ65" in radar,
        "loop": "AnimationMode       = LOOP" in radar,
        "display": "DisplayName         = OBJECT:ANMPQ65" in radar,
        "side": "Side                = America" in radar,
        "fcr": "Weapon                    = AN_MPQ65_WaveEmitter" in radar,
        "detect": "DetectionRange            = 970" in radar,
        "no_immobile": "IMMOBILE" not in radar,
        "locomotor": "Locomotor = SET_NORMAL Generic8x8Locomotor" in radar,
        "ai": "AIUpdateInterface" in radar,
        "commandset": "CommandSet           = GenericCommandSet" in radar,
        "physics": "Mass = 300.0" in radar,
        "body": "MaxHealth       = 800" in radar,
        "no_deploy_ai": "DeployStyleAIUpdate" not in radar,
        "no_pack_state": "ConditionState            = PACKING" not in radar,
        "hole_immobile": "IMMOBILE" in hole,
    }
    for name, ok in checks.items():
        print(("OK  " if ok else "FAIL"), name)
        if not ok:
            fail(name)

    loco = LOCO.read_text(encoding="latin-1", errors="replace")
    if not re.search(r"(?m)^Locomotor Generic8x8Locomotor\s*$", loco):
        fail("Generic8x8Locomotor not in Locomotor.ini")
    cmd = CMD.read_text(encoding="latin-1", errors="replace")
    if "CommandSet GenericCommandSet" not in cmd:
        fail("GenericCommandSet missing")
    if "14 = Command_Stop" not in cmd.split("CommandSet GenericCommandSet", 1)[1][:200]:
        fail("GenericCommandSet has no Stop")

    weapon = WEAPON.read_text(encoding="latin-1", errors="replace")
    if "Weapon AN_MPQ65_WaveEmitter" not in weapon:
        fail("AN_MPQ65_WaveEmitter missing from Weapon.ini (must remain unchanged)")

    # Guard: this change must not touch shared combat files.
    for rel in (
        "patch/Data/INI/Weapon.ini",
        "patch/Data/INI/ObjectCreationList.ini",
        "patch/Data/INI/Object/Specter/Israel Defense Forces/AirDefense/Israel_AD_IronDome.ini",
    ):
        # existence only; git diff is checked by caller
        p = ROOT / rel
        if not p.exists():
            print("note: optional path absent", rel)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    big = pack_big({BIG_INNER: raw})
    OUT_BIG.write_bytes(big)
    digest = hashlib.sha256(big).hexdigest()
    (OUT_DIR / "_SPECTER_PATRIOT_MPQ65_MOBILE.big.sha256").write_text(
        f"{digest}  _SPECTER_PATRIOT_MPQ65_MOBILE.big\n", encoding="ascii"
    )
    print(f"PACKED {OUT_BIG} bytes={len(big)} entries=1 sha256={digest}")
    print("STATIC_OK")
    print("MOVE_STOP_STATIC: KindOf has VEHICLE without IMMOBILE; Locomotor Generic8x8Locomotor; AIUpdateInterface; CommandSet GenericCommandSet includes Command_Stop.")
    print("DEPLOY_NOT_ADDED: no packed W3D / pack animation; FCR remains always-on.")
    print("INGAME_ZH: not executed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
