#!/usr/bin/env python3
"""Enable Vietnam radar minimap using the project's proven RadarUpgrade pattern.

Working radars (Japan_RadarStation, IranRadarStation, Iraq zzzzz overlay,
AmericaRadarStation) all do:

  GrantUpgradeCreate  UpgradeToGrant = Upgrade_AmericaRadar
  RadarUpgrade        TriggeredBy    = Upgrade_AmericaRadar

Vietnam_RadarStation already grants Upgrade_AmericaRadar but both of its
Object definitions omit TriggeredBy on RadarUpgrade, so the minimap never
turns on. This packer inserts the same TriggeredBy line Japan uses.

Does not change CommandSet.ini, CommandButton.ini, Shahed launcher Fire,
radar menus, other countries, or invent Upgrade_VietnamRadar.

Source: radar-shahed-fire-8000 _SPEC_DATA_ONE.big
(SHA 71559b012715a8336cb8b79cefef29cf4e00465825969b500184d95401cc7346).
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/RADAR_SHAHED_FIRE/_SPEC_DATA_ONE.big"
SRC_SHA = "71559b012715a8336cb8b79cefef29cf4e00465825969b500184d95401cc7346"
OUT_DIR = ROOT / "Release/VIETNAM_RADAR_MINIMAP"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"

K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_WPN = r"Data\INI\Weapon.ini"
K_UAV = r"Data\INI\Object\Specter\SpecterRadarUavs.ini"
K_IRAN_SHAHED = r"Data\INI\Object\Specter\Iranian Army\Wheeled\ShahedLauncher.ini"
K_JP = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_RadarStation.ini"
K_VN_DONOR = (
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Iraq_RadarStation.ini"
)
K_VN_OWN = (
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_RadarStation.ini"
)

OLD = (
    "  Behavior        = RadarUpgrade ModuleTag_0d995\r\n"
    "    DisableProof  = No\r\n"
    "  End\r\n"
)
NEW = (
    "  Behavior        = RadarUpgrade ModuleTag_0d995\r\n"
    "    TriggeredBy   = Upgrade_AmericaRadar\r\n"
    "    DisableProof  = No\r\n"
    "  End\r\n"
)
JP_PATTERN = (
    "  Behavior        = RadarUpgrade ModuleTag_0d995\r\n"
    "    TriggeredBy   = Upgrade_AmericaRadar\r\n"
    "    DisableProof  = No\r\n"
    "  End\r\n"
)


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
        name = data[off:end].decode("latin1")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    index, blobs, offset = [], [], header_size
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
        out += name.encode("latin1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def block(text: str, kind: str, name: str) -> str:
    m = re.search(rf"^{kind} {re.escape(name)}\s*\r?\n", text, re.M)
    if not m:
        raise SystemExit(f"missing {kind} {name}")
    n2 = re.search(rf"^{kind} ", text[m.end() :], re.M)
    end = m.end() + n2.start() if n2 else len(text)
    return text[m.start() : end]


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("VALIDATE FAIL: " + msg)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_vn(raw: bytes, key: str) -> bytes:
    text = raw.decode("latin1")
    require(text.count(OLD) == 1, f"{key} RadarUpgrade block count")
    require("Object Vietnam_RadarStation" in text, f"{key} not Vietnam_RadarStation")
    require("UpgradeToGrant    = Upgrade_AmericaRadar" in text, f"{key} missing grant")
    require("TriggeredBy   = Upgrade_AmericaRadar" not in text, f"{key} already has TriggeredBy")
    new_text = text.replace(OLD, NEW, 1)
    require(new_text.count(NEW) == 1, f"{key} patch not applied once")
    require(new_text.count("Object Vietnam_RadarStation") == 1, f"{key} extra object")
    return new_text.encode("latin1")


def radar_upgrade_mod(obj_text: str) -> str:
    m = re.search(r"(?m)^  Behavior\s*=\s*RadarUpgrade[\s\S]*?^  End\r?\n", obj_text)
    require(m is not None, "RadarUpgrade module missing")
    return m.group(0)


def validate(orig: dict[str, bytes], new: dict[str, bytes]) -> None:
    require(orig[K_CS] == new[K_CS], "CommandSet.ini changed")
    require(orig[K_CB] == new[K_CB], "CommandButton.ini changed")
    require(orig[K_WPN] == new[K_WPN], "Weapon.ini changed")
    require(orig[K_UAV] == new[K_UAV], "Shahed UAV file changed")
    require(orig[K_IRAN_SHAHED] == new[K_IRAN_SHAHED], "Iran Shahed launcher changed")
    require(orig[K_JP] == new[K_JP], "Japan radar changed")

    changed = [k for k in orig if orig[k] != new[k]]
    require(set(changed) == {K_VN_DONOR, K_VN_OWN}, f"unexpected files changed: {changed}")

    jp = block(new[K_JP].decode("latin1"), "Object", "Japan_RadarStation")
    require(radar_upgrade_mod(jp) == JP_PATTERN, "Japan pattern drifted")

    for key in (K_VN_DONOR, K_VN_OWN):
        txt = new[key].decode("latin1")
        obj = block(txt, "Object", "Vietnam_RadarStation")
        ru = radar_upgrade_mod(obj)
        require(ru == JP_PATTERN, f"{key} RadarUpgrade != Japan pattern")
        require("UpgradeToGrant    = Upgrade_AmericaRadar" in obj, f"{key} grant lost")
        require("CommandSet          = Vietnam_RadarStationCommandSet" in obj, f"{key} CS")
        require("TriggeredBy   = Upgrade_AmericaRadar" in ru, f"{key} TriggeredBy")
        require(obj.count("Object Vietnam_RadarStation") == 1, f"{key} dup header")

    cs = new[K_CS].decode("latin1")
    vn_cs = block(cs, "CommandSet", "Vietnam_RadarStationCommandSet")
    require("12 = Command_ConstructSpecterRadarShahedLauncher" in vn_cs, "VN radar lost Shahed slot 12")
    require("1  = Command_VietnamRadarSearch" in vn_cs, "VN RadarSearch lost")
    require("Command_ConstructSpecterRadarHeron" in vn_cs, "VN Heron lost")
    uav = block(new[K_UAV].decode("latin1"), "Object", "SpecterRadar_ShahedLauncher")
    require("CommandSet    = IranShahed136FireCommandSet" in uav, "Shahed Fire CS lost")
    require("BuildCost       = 8000" in uav, "Shahed cost not 8000")
    require("Weapon = PRIMARY   Weapon_Iran_Shahed136Launcher" in uav, "Shahed weapon lost")

    defs = [
        k
        for k, v in new.items()
        if b"Object Vietnam_RadarStation" in v
    ]
    require(set(defs) == {K_VN_DONOR, K_VN_OWN}, f"Vietnam object defs: {defs}")


def main() -> None:
    if not SRC_BIG.is_file():
        raise SystemExit(f"missing source BIG {SRC_BIG}")
    blob = SRC_BIG.read_bytes()
    require(sha256(blob) == SRC_SHA, "source BIG sha mismatch")
    orig = read_big(SRC_BIG)
    new = dict(orig)
    new[K_VN_DONOR] = patch_vn(orig[K_VN_DONOR], K_VN_DONOR)
    new[K_VN_OWN] = patch_vn(orig[K_VN_OWN], K_VN_OWN)
    validate(orig, new)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_blob = build_big(new)
    digest = sha256(out_blob)
    OUT_BIG.write_bytes(out_blob)
    (OUT_DIR / "_SPEC_DATA_ONE.big.sha256").write_text(digest + "\n", encoding="ascii")
    lines = [f"{digest}  _SPEC_DATA_ONE.big"]
    for name, key in (("CommandSet.ini", K_CS), ("CommandButton.ini", K_CB)):
        (OUT_DIR / name).write_bytes(new[key])
        h = sha256(new[key])
        (OUT_DIR / f"{name}.sha256").write_text(h + "\n", encoding="ascii")
        lines.append(f"{h}  {name}")
    (OUT_DIR / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="ascii")
    print("wrote", OUT_BIG, "bytes", len(out_blob), "sha256", digest)
    print("CS", sha256(new[K_CS]))
    print("CB", sha256(new[K_CB]))
    print("changed", K_VN_DONOR)
    print("changed", K_VN_OWN)


if __name__ == "__main__":
    main()
