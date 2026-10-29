#!/usr/bin/env python3
"""Strip JP/VN/SK/NK Command Center production to VT72B (+ NK Hwasong15BB).

Live first-win (radar-no-spy-sat BIG, SHA 64835645...):
  Japan_CommandCenter      -> Japan_CommandCenterCommandSet
  Vietnam_CommandCenter    -> Vietnam_CommandCenterCommandSet
  SouthKorea_CommandCenter -> SouthKorea_CommandCenterCommandSet
  NorthKorea_CommandCenter -> NorthKorea_CommandCenterCommandSet

Each CommandSet name is unique (one definition, no extra CommandSet_*.ini
overlay). ControlBar opens only Data\\INI\\CommandSet.ini; loose
LocalFileSystem beats every BIG.

Keep:
  JP/VN/SK slot 1 Command_Construct*_VT72B
  NK      slot 1 Command_ConstructNorthKorea_VT72B
          slot 7 Command_ConstructNorthKorea_Hwasong15BB
            (live menu missile; DF_41 is not on this CommandSet)
  All four: slot 13 SetRallyPoint, slot 14 Sell (not unit production)

Delete every other UNIT_BUILD slot on those four CommandSets only.
Do not add units, do not renumber kept slots, do not touch WF / MF /
radar / other countries / CommandButton.ini / objects.

Source: radar-no-spy-sat _SPEC_DATA_ONE.big
(SHA 64835645cb60fe726b59d8033574823d5de4443aa9dff0f74c1f7978d3d67465).
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/RADAR_NO_SPY_SAT/_SPEC_DATA_ONE.big"
SRC_SHA = "64835645cb60fe726b59d8033574823d5de4443aa9dff0f74c1f7978d3d67465"
OUT_DIR = ROOT / "Release/CC_VT72B_NK_HWASONG"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"

K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_WPN = r"Data\INI\Weapon.ini"
K_JP_CC = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_CommandCenter.ini"
K_VN_CC = r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_CommandCenter.ini"
K_SK_CC = r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\SouthKorea_CommandCenter.ini"
K_NK_CC = r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_CommandCenter.ini"
K_JP_VT = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Tracked\Japan_VT72B.ini"
K_VN_VT = r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Tracked\Vietnam_VT72B.ini"
K_SK_VT = r"Data\INI\Object\Specter\South Korean Armed Forces\Tracked\SouthKorea_VT72B.ini"
K_NK_VT = r"Data\INI\Object\Specter\North Korea\Tracked\NorthKorea_VT72B.ini"
K_NK_HW = r"Data\INI\Object\Specter\North Korea\NorthKorea_Systems.ini"
K_DF41 = r"Data\INI\Object\Specter\FactoryKLMN\Factory_DF41Once.ini"

# Keep these buttons (slot numbers must stay). Everything else on the CS is dropped.
KEEP = {
    "Japan_CommandCenterCommandSet": {
        "Command_ConstructJapan_VT72B",
        "Command_SetRallyPoint",
        "Command_Sell",
    },
    "Vietnam_CommandCenterCommandSet": {
        "Command_ConstructVietnam_VT72B",
        "Command_SetRallyPoint",
        "Command_Sell",
    },
    "SouthKorea_CommandCenterCommandSet": {
        "Command_ConstructSouthKorea_VT72B",
        "Command_SetRallyPoint",
        "Command_Sell",
    },
    "NorthKorea_CommandCenterCommandSet": {
        "Command_ConstructNorthKorea_VT72B",
        "Command_ConstructNorthKorea_Hwasong15BB",
        "Command_SetRallyPoint",
        "Command_Sell",
    },
}

MUST_KEEP_SLOTS = {
    "Japan_CommandCenterCommandSet": {"1": "Command_ConstructJapan_VT72B"},
    "Vietnam_CommandCenterCommandSet": {"1": "Command_ConstructVietnam_VT72B"},
    "SouthKorea_CommandCenterCommandSet": {"1": "Command_ConstructSouthKorea_VT72B"},
    "NorthKorea_CommandCenterCommandSet": {
        "1": "Command_ConstructNorthKorea_VT72B",
        "7": "Command_ConstructNorthKorea_Hwasong15BB",
    },
}

UNTOUCHED_SIBLINGS = (
    "Japan_WarFactoryCommandSet",
    "Vietnam_WarFactoryCommandSet",
    "SouthKorea_WarFactoryCommandSet",
    "NorthKorea_WarFactoryCommandSet",
    "Japan_MissileFactoryCommandSet",
    "Vietnam_MissileFactoryCommandSet",
    "SouthKorea_MissileFactoryCommandSet",
    "NorthKorea_MissileFactoryCommandSet",
    "Japan_RadarStationCommandSet",
    "Vietnam_RadarStationCommandSet",
    "SouthKorea_RadarStationCommandSet",
    "NorthKorea_RadarStationCommandSet",
    "Japan_SupplyCenterCommandSet",
    "Vietnam_SupplyCenterCommandSet",
    "SouthKorea_SupplyCenterCommandSet",
    "NorthKorea_SupplyCenterCommandSet",
    "Japan_VT72BCommandSet",
    "Vietnam_VT72BCommandSet",
    "SouthKorea_VT72BCommandSet",
    "NorthKorea_VT72BCommandSet",
    "Iraq_CommandCenterCommandSet",
    "AmericaRadarStationCommandSet",
)

KEEP_FACTORY_SLOTS = (
    "CB_FACTORY_SLOT_K",
    "CB_FACTORY_SLOT_L",
    "CB_FACTORY_SLOT_M",
    "CB_FACTORY_SLOT_N",
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


def cs_block(text: str, name: str) -> tuple[int, int, str]:
    m = re.search(rf"^CommandSet {re.escape(name)}(?:\s|;|$)", text, re.M)
    if not m:
        raise SystemExit(f"missing CommandSet {name}")
    n2 = re.search(r"^CommandSet ", text[m.end() :], re.M)
    end = m.end() + n2.start() if n2 else len(text)
    return m.start(), end, text[m.start() : end]


def slots(block: str) -> list[tuple[str, str]]:
    return re.findall(r"^[ \t]*(\d+)[ \t]*=[ \t]*(\S+)", block, re.M)


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("VALIDATE FAIL: " + msg)


def patch_cs(text: str) -> str:
    for name, keep in KEEP.items():
        start, end, body = cs_block(text, name)
        nl = "\r\n" if "\r\n" in body else "\n"
        kept_lines: list[str] = []
        removed = 0
        for line in body.splitlines():
            m = re.match(r"^[ \t]*(\d+)[ \t]*=[ \t]*(\S+)", line)
            if m and m.group(2) not in keep:
                removed += 1
                continue
            kept_lines.append(line)
        require(removed >= 1, f"{name} had nothing to strip")
        new_body = nl.join(kept_lines)
        if body.endswith(("\r\n", "\n")) and not new_body.endswith(nl):
            new_body += nl
        text = text[:start] + new_body + text[end:]
    return text


def validate(orig: dict[str, bytes], new: dict[str, bytes]) -> None:
    require(orig[K_CB] == new[K_CB], "CommandButton.ini changed")
    require(orig[K_WPN] == new[K_WPN], "Weapon.ini changed")
    for key in (K_JP_CC, K_VN_CC, K_SK_CC, K_NK_CC, K_JP_VT, K_VN_VT, K_SK_VT, K_NK_VT, K_NK_HW, K_DF41):
        require(orig[key] == new[key], f"object file changed: {key}")
    changed = [k for k in orig if orig[k] != new[k]]
    require(changed == [K_CS], f"unexpected files changed: {changed}")
    require(set(orig) == set(new), "entry names added/removed")

    old_cs = orig[K_CS].decode("latin1")
    new_cs = new[K_CS].decode("latin1")
    old_names = set(re.findall(r"^CommandSet (\S+)", old_cs, re.M))
    new_names = set(re.findall(r"^CommandSet (\S+)", new_cs, re.M))
    require(old_names == new_names, "CommandSet names added/removed")

    for name in sorted(old_names):
        _, _, ob = cs_block(old_cs, name)
        _, _, nb = cs_block(new_cs, name)
        if name in KEEP:
            old_map = dict(slots(ob))
            new_map = dict(slots(nb))
            require("End" in nb or "END" in nb, f"{name} lost End")
            require(set(new_map.values()) == KEEP[name], f"{name} keep mismatch: {new_map}")
            kept_old = [(s, b) for s, b in slots(ob) if b in KEEP[name]]
            require(slots(nb) == kept_old, f"{name} slots moved/renumbered: {slots(nb)}")
            for slot, btn in MUST_KEEP_SLOTS[name].items():
                require(new_map.get(slot) == btn, f"{name} slot {slot} is {new_map.get(slot)} not {btn}")
            require("Command_ConstructChinaVehicleDF41" not in nb, f"{name} gained DF-41")
            require("Factory_DF41" not in nb, f"{name} gained factory DF-41")
        else:
            require(ob == nb, f"unrelated CommandSet changed: {name}")

    for name in UNTOUCHED_SIBLINGS:
        _, _, ob = cs_block(old_cs, name)
        _, _, nb = cs_block(new_cs, name)
        require(ob == nb, f"sibling CS changed: {name}")

    # Hwasong15BB stays on SK/JP/VN objects via buttons, but not on their CC
    for name in (
        "Japan_CommandCenterCommandSet",
        "Vietnam_CommandCenterCommandSet",
        "SouthKorea_CommandCenterCommandSet",
    ):
        _, _, body = cs_block(new_cs, name)
        require("Hwasong15BB" not in body, f"{name} still has Hwasong15BB")
        require("M2020" not in body and "Chonma5" not in body, f"{name} still has tanks")

    _, _, nk = cs_block(new_cs, "NorthKorea_CommandCenterCommandSet")
    require("Command_ConstructNorthKorea_Hwasong15BB" in nk, "NK lost Hwasong15BB")
    require("M2020" not in nk and "Chonma5" not in nk, "NK still has tanks")

    # Spy Sat radar strip from #719 still present
    _, _, usa_radar = cs_block(new_cs, "AmericaRadarStationCommandSet")
    require("Command_SpySatelliteScan" not in usa_radar, "Spy Sat returned to USA radar")

    for name in (
        "Japan_MissileFactoryCommandSet",
        "Vietnam_MissileFactoryCommandSet",
        "SouthKorea_MissileFactoryCommandSet",
        "NorthKorea_MissileFactoryCommandSet",
    ):
        _, _, body = cs_block(new_cs, name)
        have = {b for _, b in slots(body)}
        for slot in KEEP_FACTORY_SLOTS:
            require(slot in have, f"{name} lost {slot}")

    cb = new[K_CB].decode("latin1")
    for btn in (
        "Command_ConstructJapan_VT72B",
        "Command_ConstructVietnam_VT72B",
        "Command_ConstructSouthKorea_VT72B",
        "Command_ConstructNorthKorea_VT72B",
        "Command_ConstructNorthKorea_Hwasong15BB",
        "Command_ConstructJapan_Hwasong15BB",
        "Command_ConstructVietnam_Hwasong15BB",
        "Command_ConstructSouthKorea_Hwasong15BB",
    ):
        require(f"CommandButton {btn}" in cb, f"lost button {btn}")
    require("Object        = Japan_VT72B" in cb, "JP VT72B object ref lost")
    require("Object        = Vietnam_VT72B" in cb, "VN VT72B object ref lost")
    require("Object        = SouthKorea_VT72B" in cb, "SK VT72B object ref lost")
    require("Object           = NorthKorea_VT72B" in cb or "Object        = NorthKorea_VT72B" in cb, "NK VT72B object ref lost")
    require("Object           = NorthKorea_Hwasong15BB" in cb, "NK Hwasong15BB object ref lost")

    require("CommandSet IranShahed136FireCommandSet" in new_cs, "lost #710 Shahed fire CS")
    _, _, ru = cs_block(new_cs, "RussiaWarFactoryCommandSet")
    require("Command_ConstructRussiaVehicleRS24" not in ru, "RS-24 returned to RU WF")


def main() -> None:
    if not SRC_BIG.is_file():
        raise SystemExit(f"missing source BIG {SRC_BIG}")
    blob = SRC_BIG.read_bytes()
    if hashlib.sha256(blob).hexdigest() != SRC_SHA:
        raise SystemExit("source BIG sha mismatch")
    orig = read_big(SRC_BIG)
    new = dict(orig)
    new[K_CS] = patch_cs(orig[K_CS].decode("latin1")).encode("latin1")
    validate(orig, new)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_blob = build_big(new)
    digest = hashlib.sha256(out_blob).hexdigest()
    OUT_BIG.write_bytes(out_blob)
    (OUT_DIR / "_SPEC_DATA_ONE.big.sha256").write_text(digest + "\n", encoding="ascii")
    for name, key in (("CommandSet.ini", K_CS), ("CommandButton.ini", K_CB)):
        (OUT_DIR / name).write_bytes(new[key])
        (OUT_DIR / f"{name}.sha256").write_text(
            hashlib.sha256(new[key]).hexdigest() + "\n", encoding="ascii"
        )
    print("wrote", OUT_BIG, "bytes", len(out_blob), "sha256", digest)
    print("CC CommandSets:", ", ".join(KEEP))


if __name__ == "__main__":
    main()
