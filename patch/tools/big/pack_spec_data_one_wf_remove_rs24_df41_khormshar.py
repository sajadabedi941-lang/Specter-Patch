#!/usr/bin/env python3
"""Remove RS-24 / DF-41 / Khorramshahr only from live RU/CN/IR War Factory menus.

Live first-win WF objects (from radar-shahed-range BIG):
  RussiaWarFactory  -> RussiaWarFactoryCommandSet
      slot 13 Command_ConstructRussiaVehicleRS24
  ChinaWarFactory   -> PLAWarFactoryCommandSet
      slots 4, 7 Command_ConstructChinaVehicleDF41
      slot 15 Command_ConstructChinaVehicleDF41_AI
  IranWarFactory    -> IranWarfactoryCommandSet
      slot 9 Command_ConstructIranVehicleKhormshar
      slot 15 Command_ConstructIranVehicleKhormshar_AI

Only those slot lines are deleted. Other WF buttons, Sell, HQ, Missile Factory
K/L/M/N, Iraq A-J, CommandButton.ini, weapons, and objects stay.

Source: radar-shahed-range _SPEC_DATA_ONE.big
(SHA e2b326824c774609f5e16d9c8a2b17f26f8f0edef5feb351a97ada5e1de4bdbf).
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/RADAR_SHAHED_RANGE/_SPEC_DATA_ONE.big"
SRC_SHA = "e2b326824c774609f5e16d9c8a2b17f26f8f0edef5feb351a97ada5e1de4bdbf"
OUT_DIR = ROOT / "Release/WF_REMOVE_RS24_DF41_KHORMSHAR"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"

K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_WPN = r"Data\INI\Weapon.ini"
K_IRAN_WF_OBJ = r"Data\INI\Object\Specter\Iranian Army\Buildings\Warfactory.ini"
K_RU_WF_OBJ = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\Warfactory.ini"
K_CN_WF_OBJ = r"Data\INI\Object\Specter\PLA\Buildings\Warfactory.ini"
K_IRAN_TEL = r"Data\INI\Object\Specter\Iranian Army\Wheeled\ShahedLauncher.ini"
K_DF41 = r"Data\INI\Object\Specter\FactoryKLMN\Factory_DF41Once.ini"
K_RS24 = r"Data\INI\Object\Specter\FactoryKLMN\Factory_RS24YarsOnce.ini"
K_KHOR = r"Data\INI\Object\Specter\FactoryKLMN\Factory_KhormsharOnce.ini"

# Live WF CommandSet -> buttons to strip (player + AI construct of the same missile).
REMOVE = {
    "RussiaWarFactoryCommandSet": {
        "Command_ConstructRussiaVehicleRS24",
    },
    "PLAWarFactoryCommandSet": {
        "Command_ConstructChinaVehicleDF41",
        "Command_ConstructChinaVehicleDF41_AI",
    },
    "IranWarfactoryCommandSet": {
        "Command_ConstructIranVehicleKhormshar",
        "Command_ConstructIranVehicleKhormshar_AI",
    },
}

KEEP_FACTORY_SLOTS = (
    "CB_FACTORY_SLOT_K",
    "CB_FACTORY_SLOT_L",
    "CB_FACTORY_SLOT_M",
    "CB_FACTORY_SLOT_N",
)

IRAQ_MF = "Iraq_AlFahdMissileFactoryCommandSet"
MIN_SLOTS_AFTER = 8


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
    for name, buttons in REMOVE.items():
        start, end, body = cs_block(text, name)
        nl = "\r\n" if "\r\n" in body else "\n"
        kept: list[str] = []
        removed = 0
        for line in body.splitlines():
            m = re.match(r"^[ \t]*(\d+)[ \t]*=[ \t]*(\S+)", line)
            if m and m.group(2) in buttons:
                removed += 1
                continue
            kept.append(line)
        require(removed >= 1, f"{name} had no target buttons")
        new_body = nl.join(kept)
        if not new_body.endswith(nl):
            new_body += nl
        text = text[:start] + new_body + text[end:]
    return text


def validate(orig: dict[str, bytes], new: dict[str, bytes]) -> None:
    require(orig[K_CB] == new[K_CB], "CommandButton.ini changed")
    require(orig[K_WPN] == new[K_WPN], "Weapon.ini changed")
    for key in (K_IRAN_WF_OBJ, K_RU_WF_OBJ, K_CN_WF_OBJ, K_IRAN_TEL, K_DF41, K_RS24, K_KHOR):
        require(orig[key] == new[key], f"object file changed: {key}")
    changed = [k for k in orig if orig[k] != new[k]]
    require(changed == [K_CS], f"unexpected files changed: {changed}")

    old_cs = orig[K_CS].decode("latin1")
    new_cs = new[K_CS].decode("latin1")

    # only the three live WF sets may differ
    old_names = set(re.findall(r"^CommandSet (\S+)", old_cs, re.M))
    new_names = set(re.findall(r"^CommandSet (\S+)", new_cs, re.M))
    require(old_names == new_names, "CommandSet names added/removed")
    for name in sorted(old_names):
        _, _, ob = cs_block(old_cs, name)
        _, _, nb = cs_block(new_cs, name)
        if name in REMOVE:
            old_btns = {b for _, b in slots(ob)}
            new_btns = {b for _, b in slots(nb)}
            require(REMOVE[name].isdisjoint(new_btns), f"{name} still has a removed button")
            require(REMOVE[name] <= old_btns, f"{name} missing expected button in source")
            require(len(slots(nb)) >= MIN_SLOTS_AFTER, f"{name} too empty: {slots(nb)}")
            require("End" in nb, f"{name} lost End")
            kept_old = [(s, b) for s, b in slots(ob) if b not in REMOVE[name]]
            require(slots(nb) == kept_old, f"{name} other slots moved/renumbered")
        else:
            require(ob == nb, f"unrelated CommandSet changed: {name}")

    # missile factory K/L/M/N still present
    for name in (
        "Russia_MissileFactoryCommandSet",
        "China_MissileFactoryCommandSet",
        "Iran_MissileFactoryCommandSet",
    ):
        _, _, body = cs_block(new_cs, name)
        have = {b for _, b in slots(body)}
        for slot in KEEP_FACTORY_SLOTS:
            require(slot in have, f"{name} lost {slot}")
    _, _, iraq = cs_block(new_cs, IRAQ_MF)
    iraq_btns = {b for _, b in slots(iraq)}
    for btn in (
        "CB_MISSILE_A",
        "CB_MISSILE_B",
        "CB_MISSILE_C",
        "CB_MISSILE_D",
        "CB_MISSILE_E",
        "CB_MISSILE_F",
        "CB_MISSILE_G",
        "CB_MISSILE_H",
        "CB_MISSILE_I",
        "CB_MISSILE_J",
        "CB_MISSILE_K",
        "CB_FACTORY_SLOT_L",
        "CB_FACTORY_SLOT_M",
        "CB_FACTORY_SLOT_N",
    ):
        require(btn in iraq_btns, f"{IRAQ_MF} lost {btn}")
    # Iraq A-K buttons not leaked into RU/CN/IR WF
    for name in REMOVE:
        _, _, body = cs_block(new_cs, name)
        require("CB_MISSILE_" not in body, f"{name} gained Iraq CB_MISSILE")
        require("Iraq_Alhussaien" not in body, f"{name} gained Iraq K")

    # construct buttons still exist (missiles not deleted)
    cb = new[K_CB].decode("latin1")
    for btn in (
        "Command_ConstructRussiaVehicleRS24",
        "Command_ConstructChinaVehicleDF41",
        "Command_ConstructIranVehicleKhormshar",
        "CB_FACTORY_SLOT_L",
        "CB_FACTORY_SLOT_M",
        "CB_FACTORY_SLOT_N",
    ):
        require(f"CommandButton {btn}" in cb, f"lost button {btn}")

    # Iran fire / radar Shahed overlays still present
    require("CommandSet IranShahed136FireCommandSet" in new_cs, "lost #710 Shahed fire CS")
    require("Command_ConstructSpecterRadarShahedLauncher" in new_cs, "lost #666 radar Shahed")


def main() -> None:
    if not SRC_BIG.is_file():
        raise SystemExit(f"missing source BIG {SRC_BIG}")
    blob = SRC_BIG.read_bytes()
    if hashlib.sha256(blob).hexdigest() != SRC_SHA:
        raise SystemExit("source BIG sha mismatch")
    orig = read_big(SRC_BIG)
    new = dict(orig)
    patched = patch_cs(orig[K_CS].decode("latin1"))
    new[K_CS] = patched.encode("latin1")
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
    print("CommandSets edited:", ", ".join(REMOVE))


if __name__ == "__main__":
    main()
