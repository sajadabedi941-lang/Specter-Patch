#!/usr/bin/env python3
"""Remove general Spy Satellite from unauthorized live country radar menus.

Live first-win (wf-remove-rs24-df41-khormshar BIG, SHA a41168de...):
  ControlBar opens only Data\\INI\\CommandSet.ini (loose LocalFileSystem
  beats every BIG; archive first-win via game.dat _stricmp, replace=0).

  12 playable radar CommandSets still first-win Command_SpySatelliteScan
  because #710-#718 shipped the full Specter CommandSet.ini descended from
  #657/#666. Merged #682 (0_SPECTER_NoGeneralSpySatellite.big) is not on
  the current install path.

Only those Spy Sat / Fee lines are deleted. Country RadarSearch (NK/SK/JP/VN),
drones 2-8, #666 UAV slots 9-12, Sell, RadarUpgrade objects, Command Center
shortcuts, Missile Factory K/L/M/N, and #710-#718 stay.

CommandSet_ZZZZ_SpySatelliteRadar.ini is unread by ControlBar but still
carries #657 Spy Sat + Fee on 25 radars (including Iran/Iraq). Those Spy
Sat / Fee lines are stripped so a last-win merge cannot put the button back.

Source: wf-remove-rs24-df41-khormshar _SPEC_DATA_ONE.big
(SHA a41168def32528d84d28879e077adcc1eb27ff3a02cc96b20fa15da05b3b465f).
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/WF_REMOVE_RS24_DF41_KHORMSHAR/_SPEC_DATA_ONE.big"
SRC_SHA = "a41168def32528d84d28879e077adcc1eb27ff3a02cc96b20fa15da05b3b465f"
OUT_DIR = ROOT / "Release/RADAR_NO_SPY_SAT"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"

K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_WPN = r"Data\INI\Weapon.ini"
K_ZZZZ = r"Data\INI\CommandSet_ZZZZ_SpySatelliteRadar.ini"
K_IRAQ_RADAR_OBJ = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_RadarStation.ini"
K_IRAN_RADAR_OBJ = r"Data\INI\Object\Specter\Iranian Army\Buildings\RadarStation.ini"
K_USA_RADAR_OBJ = r"Data\INI\Object\Specter\United States Of America\Buildings\AN_FPS117.ini"
K_SHAHED_WPN = r"Data\INI\Object\Specter\SpecterRadarUavs.ini"
K_DF41 = r"Data\INI\Object\Specter\FactoryKLMN\Factory_DF41Once.ini"
K_RS24 = r"Data\INI\Object\Specter\FactoryKLMN\Factory_RS24YarsOnce.ini"

# Live radar CommandSets that first-win Command_SpySatelliteScan.
# Designed replacements from merged #682 (AmericaCountryScan / IsraelCountryScan)
# are NOT added: this change only deletes the general Spy Sat button.
LIVE_RADAR_STRIP = (
    "AmericaRadarStationCommandSet",
    "IsraelRadarStationCommandSet",
    "RussiaRadarStationCommandSet",
    "ChinaRadarStationCommandSet",
    "NatoGM406CommandSet",
    "BritainGM406CommandSet",
    "FranceGM406CommandSet",
    "GermanyGM406CommandSet",
    "ItalyGM406CommandSet",
    "SwedenGM406CommandSet",
    "UkraineGM406CommandSet",
    "TurkeyGM406CommandSet",
)

SPY_BUTTONS = {
    "Command_SpySatelliteScan",
    "Command_SpySatelliteScanFromShortcut",
    "Command_SpecterSpySatelliteFee",
}

# Country recon — not Spy Sat. Leave untouched.
KEEP_RADARSEARCH = {
    "NorthKorea_RadarStationCommandSet": "Command_NorthKoreaRadarSearch",
    "SouthKorea_RadarStationCommandSet": "Command_SouthKoreaRadarSearch",
    "Japan_RadarStationCommandSet": "Command_JapanRadarSearch",
    "Vietnam_RadarStationCommandSet": "Command_VietnamRadarSearch",
}

# Already have no general Spy Sat on the live ControlBar table.
ALREADY_CLEAN = (
    "IranExpandedRadarCommandSet",
    "IranRadarStationCommandSet",
    "Iraq_RadarStationCommandSet",
    "ArabRadarStationCommandSet",
    "India_RadarCommandSet",
    "Libya_RadarCommandSet",
    "Pakistan_RadarCommandSet",
    "SaudiArabia_RadarCommandSet",
    "SouthAfrica_RadarCommandSet",
    "Syria_RadarCommandSet",
    "UAE_RadarCommandSet",
)

# Command Center / general shortcuts — out of radar scope.
LEAVE_SHORTCUT = (
    "SpecialPowerShortcutUSA",
    "AirF_AmericaCommandCenterCommandSet",
    "SupW_SpecialPowerShortcutUSA",
    "SupW_AmericaCommandCenterCommandSet",
    "Lazr_SpecialPowerShortcutUSA",
    "Lazr_AmericaCommandCenterCommandSet",
)

KEEP_FACTORY_SLOTS = (
    "CB_FACTORY_SLOT_K",
    "CB_FACTORY_SLOT_L",
    "CB_FACTORY_SLOT_M",
    "CB_FACTORY_SLOT_N",
)
IRAQ_MF = "Iraq_AlFahdMissileFactoryCommandSet"
MIN_SLOTS_AFTER = 3


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


def strip_spy_lines(body: str) -> tuple[str, int]:
    nl = "\r\n" if "\r\n" in body else "\n"
    kept: list[str] = []
    removed = 0
    for line in body.splitlines():
        m = re.match(r"^[ \t]*(\d+)[ \t]*=[ \t]*(\S+)", line)
        if m and m.group(2) in SPY_BUTTONS:
            removed += 1
            continue
        kept.append(line)
    new_body = nl.join(kept)
    if body.endswith(("\r\n", "\n")) and not new_body.endswith(nl):
        new_body += nl
    return new_body, removed


def patch_commandset_ini(text: str) -> str:
    for name in LIVE_RADAR_STRIP:
        start, end, body = cs_block(text, name)
        new_body, removed = strip_spy_lines(body)
        require(removed >= 1, f"{name} had no Spy Sat button")
        text = text[:start] + new_body + text[end:]
    return text


def patch_zzzz(text: str) -> str:
    names = re.findall(r"^CommandSet (\S+)", text, re.M)
    require(len(names) >= 12, f"ZZZZ too small: {names}")
    for name in names:
        start, end, body = cs_block(text, name)
        new_body, removed = strip_spy_lines(body)
        # every ZZZZ radar block was a Spy Sat overlay
        require(removed >= 1, f"ZZZZ {name} had no Spy Sat/Fee to strip")
        text = text[:start] + new_body + text[end:]
    return text


def validate(orig: dict[str, bytes], new: dict[str, bytes]) -> None:
    require(orig[K_CB] == new[K_CB], "CommandButton.ini changed")
    require(orig[K_WPN] == new[K_WPN], "Weapon.ini changed")
    for key in (K_IRAQ_RADAR_OBJ, K_IRAN_RADAR_OBJ, K_USA_RADAR_OBJ, K_SHAHED_WPN, K_DF41, K_RS24):
        require(orig[key] == new[key], f"object file changed: {key}")

    changed = [k for k in orig if orig[k] != new[k]]
    require(
        set(changed) == {K_CS, K_ZZZZ},
        f"unexpected files changed: {changed}",
    )
    require(set(orig) == set(new), "entry names added/removed")

    old_cs = orig[K_CS].decode("latin1")
    new_cs = new[K_CS].decode("latin1")
    old_names = set(re.findall(r"^CommandSet (\S+)", old_cs, re.M))
    new_names = set(re.findall(r"^CommandSet (\S+)", new_cs, re.M))
    require(old_names == new_names, "CommandSet names added/removed")

    for name in sorted(old_names):
        _, _, ob = cs_block(old_cs, name)
        _, _, nb = cs_block(new_cs, name)
        if name in LIVE_RADAR_STRIP:
            old_btns = {b for _, b in slots(ob)}
            new_btns = {b for _, b in slots(nb)}
            require(SPY_BUTTONS.isdisjoint(new_btns), f"{name} still has Spy Sat")
            require(not SPY_BUTTONS.isdisjoint(old_btns), f"{name} missing Spy Sat in source")
            require(len(slots(nb)) >= MIN_SLOTS_AFTER, f"{name} too empty: {slots(nb)}")
            require("End" in nb or "END" in nb, f"{name} lost End")
            kept_old = [(s, b) for s, b in slots(ob) if b not in SPY_BUTTONS]
            require(slots(nb) == kept_old, f"{name} other slots moved/renumbered")
            require("Command_AmericaCountryScan" not in nb, f"{name} gained CountryScan")
            require("Command_IsraelCountryScan" not in nb, f"{name} gained CountryScan")
        else:
            require(ob == nb, f"unrelated CommandSet changed: {name}")

    for name, btn in KEEP_RADARSEARCH.items():
        _, _, body = cs_block(new_cs, name)
        have = {b for _, b in slots(body)}
        require(btn in have, f"{name} lost {btn}")
        require(SPY_BUTTONS.isdisjoint(have), f"{name} gained Spy Sat")

    for name in ALREADY_CLEAN:
        _, _, body = cs_block(new_cs, name)
        have = {b for _, b in slots(body)}
        require(SPY_BUTTONS.isdisjoint(have), f"{name} gained Spy Sat")

    for name in LEAVE_SHORTCUT:
        _, _, ob = cs_block(old_cs, name)
        _, _, nb = cs_block(new_cs, name)
        require(ob == nb, f"shortcut/CC {name} changed")

    # #666 / #717 radar Shahed slot 12 still on the 18-country copies
    shahed_cs = (
        "Iraq_RadarStationCommandSet",
        "Pakistan_RadarCommandSet",
        "SaudiArabia_RadarCommandSet",
        "UAE_RadarCommandSet",
        "India_RadarCommandSet",
        "Syria_RadarCommandSet",
        "GermanyGM406CommandSet",
        "FranceGM406CommandSet",
        "BritainGM406CommandSet",
        "ItalyGM406CommandSet",
        "SwedenGM406CommandSet",
        "UkraineGM406CommandSet",
        "TurkeyGM406CommandSet",
        "Libya_RadarCommandSet",
        "SouthAfrica_RadarCommandSet",
        "SouthKorea_RadarStationCommandSet",
        "Japan_RadarStationCommandSet",
        "Vietnam_RadarStationCommandSet",
    )
    for name in shahed_cs:
        _, _, body = cs_block(new_cs, name)
        have = {b for _, b in slots(body)}
        require("Command_ConstructSpecterRadarShahedLauncher" in have, f"{name} lost Shahed slot")
        require("Command_ConstructSpecterRadarHeron" in have, f"{name} lost Heron slot")
        require("Command_ConstructSpecterRadarMQ4" in have, f"{name} lost MQ-4 slot")
        require("Command_ConstructSpecterRadarOrlan10" in have, f"{name} lost Orlan slot")

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
        "CB_MISSILE_K",
        "CB_FACTORY_SLOT_L",
        "CB_FACTORY_SLOT_M",
        "CB_FACTORY_SLOT_N",
    ):
        require(btn in iraq_btns, f"{IRAQ_MF} lost {btn}")

    # #718 WF removals still absent
    _, _, ru = cs_block(new_cs, "RussiaWarFactoryCommandSet")
    _, _, cn = cs_block(new_cs, "PLAWarFactoryCommandSet")
    _, _, ir = cs_block(new_cs, "IranWarfactoryCommandSet")
    require("Command_ConstructRussiaVehicleRS24" not in ru, "RS-24 returned to RU WF")
    require("Command_ConstructChinaVehicleDF41" not in cn, "DF-41 returned to CN WF")
    require("Command_ConstructIranVehicleKhormshar" not in ir, "Khormshar returned to IR WF")

    require("CommandSet IranShahed136FireCommandSet" in new_cs, "lost #710 Shahed fire CS")

    # ZZZZ leftover cannot re-add Spy Sat
    zzzz = new[K_ZZZZ].decode("latin1")
    for btn in SPY_BUTTONS:
        require(
            not re.search(rf"^[ \t]*\d+[ \t]*=[ \t]*{re.escape(btn)}\b", zzzz, re.M),
            f"ZZZZ still assigns {btn}",
        )
    # other extra CS files that mentioned Spy Sat must be unchanged
    for key in orig:
        if "commandset" in key.lower() and key not in (K_CS, K_ZZZZ):
            require(orig[key] == new[key], f"extra CS changed: {key}")


def main() -> None:
    if not SRC_BIG.is_file():
        raise SystemExit(f"missing source BIG {SRC_BIG}")
    blob = SRC_BIG.read_bytes()
    if hashlib.sha256(blob).hexdigest() != SRC_SHA:
        raise SystemExit("source BIG sha mismatch")
    orig = read_big(SRC_BIG)
    new = dict(orig)
    new[K_CS] = patch_commandset_ini(orig[K_CS].decode("latin1")).encode("latin1")
    new[K_ZZZZ] = patch_zzzz(orig[K_ZZZZ].decode("latin1")).encode("latin1")
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
    (OUT_DIR / "CommandSet_ZZZZ_SpySatelliteRadar.ini").write_bytes(new[K_ZZZZ])
    (OUT_DIR / "CommandSet_ZZZZ_SpySatelliteRadar.ini.sha256").write_text(
        hashlib.sha256(new[K_ZZZZ]).hexdigest() + "\n", encoding="ascii"
    )
    print("wrote", OUT_BIG, "bytes", len(out_blob), "sha256", digest)
    print("live radar CS stripped:", ", ".join(LIVE_RADAR_STRIP))
    print("ZZZZ Spy Sat lines removed from", K_ZZZZ)


if __name__ == "__main__":
    main()
