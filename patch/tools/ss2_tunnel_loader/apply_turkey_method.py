#!/usr/bin/env python3
"""Add Turkey-style tunnel-loader buttons to the 26 SS2 Command Centers.

Edits only the two ControlBar files the engine actually opens:

  Data/INI/CommandButton.ini
  Data/INI/CommandSet.ini

Loader/tunnel ThingTemplates stay in the ThingFactory Object glob as a Loose file:

  Data/INI/Object/zzzzzzzzzz_SPECTER_SS2_TunnelLoader.ini

Does not create CommandSet_*.ini / CommandButton_*.ini extras.
Does not redefine existing CommandSet names.
Does not edit Turkey CC/Dozerm, missile-factory sets, ART, or SS1.
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

ROOT = Path("/tmp/ss2/SPECTER FINAL (GeneralsMode.com)")
SRC_CS = ROOT / "Data/INI/CommandSet.ini"
SRC_CB = ROOT / "Data/INI/CommandButton.ini"
GEN_DIR = Path("patch/tools/ss2_tunnel_loader/generated")
GEN_CB = GEN_DIR / "CommandButton_zzzzzzzzzz_SPECTER_SS2_TunnelLoader.ini"
GEN_CS = GEN_DIR / "CommandSet_zzzzzzzzzz_SPECTER_SS2_TunnelLoader.ini"
GEN_OBJ = GEN_DIR / "Object_zzzzzzzzzz_SPECTER_SS2_TunnelLoader.ini"
OUT_DIR = Path("patch/Release/SPECTER_SS2_TUNNEL_LOADER_TURKEY_METHOD")

FACTIONS = [
    {"side": "Iraq", "cc": "Iraq_CommandCenter", "cs": "Iraq_CommandCenterCommandSet", "loader": "Iraq_VehicleDozerm", "tunnel": "Iraq_PowerStationm", "slot": 4, "replace": False},
    {"side": "NorthKorea", "cc": "NorthKorea_CommandCenter", "cs": "NorthKorea_CommandCenterCommandSet", "loader": "NorthKorea_VehicleDozerm", "tunnel": "NorthKorea_PowerStationm", "slot": 4, "replace": False},
    {"side": "America", "cc": "AmericaCommandCenter", "cs": "AmericaCommandCenterCommandSet", "loader": "AmericaVehicleDozerm", "tunnel": "AmericaPowerStationm", "slot": 4, "replace": False},
    {"side": "Russia", "cc": "RussiaCommandCenter", "cs": "RussiaCommandCenterCommandSet", "loader": "RussiaVehicleDozerm", "tunnel": "RussiaPowerStationm", "slot": 8, "replace": False},
    {"side": "China", "cc": "ChinaCommandCenter", "cs": "ChinaCommandCenterCommandSet", "loader": "ChinaVehicleDozerm", "tunnel": "ChinaPowerStationm", "slot": 4, "replace": False},
    {"side": "GLA", "cc": "GLACommandCenter", "cs": "GLACommandCenterCommandSet", "loader": "GLAVehicleDozerm", "tunnel": "GLAPowerStationm", "slot": 8, "replace": False},
    {"side": "Boss", "cc": "Boss_CommandCenter", "cs": "Boss_ChinaCommandCenterCommandSet", "loader": "Boss_VehicleDozerm", "tunnel": "Boss_PowerStationm", "slot": 4, "replace": False},
    {"side": "AmericaAirForceGeneral", "cc": "AirF_AmericaCommandCenter", "cs": "AirF_AmericaCommandCenterCommandSet", "loader": "AirF_AmericaVehicleDozerm", "tunnel": "AirF_AmericaPowerStationm", "slot": 3, "replace": False},
    {"side": "Nato", "cc": "NatoCommandCenter", "cs": "NatoCommandCenterCommandSet", "loader": "NatoVehicleDozerm", "tunnel": "NatoPowerStationm", "slot": 4, "replace": False},
    {"side": "Iran", "cc": "IranCommandCenter", "cs": "IranExpandedHQCommandSet", "loader": "IranVehicleDozerm", "tunnel": "IranPowerStationm", "slot": 9, "replace": True},
    {"side": "Pakistan", "cc": "Pakistan_CommandCenter", "cs": "Pakistan_CommandCenterCommandSet", "loader": "Pakistan_VehicleDozerm", "tunnel": "Pakistan_PowerStationm", "slot": 4, "replace": False},
    {"side": "SaudiArabia", "cc": "SaudiArabia_CommandCenter", "cs": "SaudiArabia_CommandCenterCommandSet", "loader": "SaudiArabia_VehicleDozerm", "tunnel": "SaudiArabia_PowerStationm", "slot": 4, "replace": False},
    {"side": "UAE", "cc": "UAE_CommandCenter", "cs": "UAE_CommandCenterCommandSet", "loader": "UAE_VehicleDozerm", "tunnel": "UAE_PowerStationm", "slot": 4, "replace": False},
    {"side": "India", "cc": "India_CommandCenter", "cs": "India_CommandCenterCommandSet", "loader": "India_VehicleDozerm", "tunnel": "India_PowerStationm", "slot": 4, "replace": False},
    {"side": "Syria", "cc": "Syria_CommandCenter", "cs": "Syria_CommandCenterCommandSet", "loader": "Syria_VehicleDozerm", "tunnel": "Syria_PowerStationm", "slot": 4, "replace": False},
    {"side": "Germany", "cc": "GermanyCommandCenter", "cs": "GermanyCommandCenterCommandSet", "loader": "GermanyVehicleDozerm", "tunnel": "GermanyPowerStationm", "slot": 4, "replace": False},
    {"side": "France", "cc": "FranceCommandCenter", "cs": "FranceCommandCenterCommandSet", "loader": "FranceVehicleDozerm", "tunnel": "FrancePowerStationm", "slot": 4, "replace": False},
    {"side": "Britain", "cc": "BritainCommandCenter", "cs": "BritainCommandCenterCommandSet", "loader": "BritainVehicleDozerm", "tunnel": "BritainPowerStationm", "slot": 4, "replace": False},
    {"side": "Italy", "cc": "ItalyCommandCenter", "cs": "ItalyCommandCenterCommandSet", "loader": "ItalyVehicleDozerm", "tunnel": "ItalyPowerStationm", "slot": 4, "replace": False},
    {"side": "Sweden", "cc": "SwedenCommandCenter", "cs": "SwedenCommandCenterCommandSet", "loader": "SwedenVehicleDozerm", "tunnel": "SwedenPowerStationm", "slot": 4, "replace": False},
    {"side": "Ukraine", "cc": "UkraineCommandCenter", "cs": "UkraineCommandCenterCommandSet", "loader": "UkraineVehicleDozerm", "tunnel": "UkrainePowerStationm", "slot": 4, "replace": False},
    {"side": "Libya", "cc": "Libya_CommandCenter", "cs": "Libya_CommandCenterCommandSet", "loader": "Libya_VehicleDozerm", "tunnel": "Libya_PowerStationm", "slot": 4, "replace": False},
    {"side": "SouthAfrica", "cc": "SouthAfrica_CommandCenter", "cs": "SouthAfrica_CommandCenterCommandSet", "loader": "SouthAfrica_VehicleDozerm", "tunnel": "SouthAfrica_PowerStationm", "slot": 4, "replace": False},
    {"side": "SouthKorea", "cc": "SouthKorea_CommandCenter", "cs": "SouthKorea_CommandCenterCommandSet", "loader": "SouthKorea_VehicleDozerm", "tunnel": "SouthKorea_PowerStationm", "slot": 4, "replace": False},
    {"side": "Japan", "cc": "Japan_CommandCenter", "cs": "Japan_CommandCenterCommandSet", "loader": "Japan_VehicleDozerm", "tunnel": "Japan_PowerStationm", "slot": 4, "replace": False},
    {"side": "Vietnam", "cc": "Vietnam_CommandCenter", "cs": "Vietnam_CommandCenterCommandSet", "loader": "Vietnam_VehicleDozerm", "tunnel": "Vietnam_PowerStationm", "slot": 4, "replace": False},
]

PROTECTED_CS = {
    "TurkeyCommandCenterCommandSet",
    "TurkeyDozermCommandSet",
    "TurkeyDozerCommandSet",
    "Iran_MissileFactoryCommandSet",
    "AmericaMissileFactoryCommandSet",
    "Israel_MissileFactoryCommandSet",
}


def crlf(text: str) -> bytes:
    return text.replace("\r\n", "\n").replace("\n", "\r\n").encode("latin1")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_blocks(text: str, kind: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(rf"(?m)^{kind}\s+(\S+)\s*$", text):
        name = m.group(1)
        start = m.start()
        nxt = text.find(f"\n{kind} ", start + 1)
        out[name] = text[start : nxt if nxt > 0 else None]
    return out


def slots_of(block: str) -> list[tuple[int, str]]:
    return [(int(a), b) for a, b in re.findall(r"(?m)^\s*(\d+)\s*=\s*(\S+)", block)]


def unique_count(names: list[str], label: str) -> None:
    if len(names) != len(set(names)):
        dups = [n for n in set(names) if names.count(n) > 1]
        raise SystemExit(f"duplicate {label}: {dups}")


def extract_button_for_object(cb_text: str, obj: str) -> tuple[str, str]:
    hits = []
    for name, block in parse_blocks(cb_text, "CommandButton").items():
        m = re.search(r"(?m)^\s*Object\s*=\s*(\S+)", block)
        cmd = re.search(r"(?m)^\s*Command\s*=\s*(\S+)", block)
        if m and m.group(1) == obj:
            hits.append((name, cmd.group(1) if cmd else "", block))
    if len(hits) != 1:
        raise SystemExit(f"expected 1 CommandButton for Object {obj}, got {hits}")
    return hits[0][0], hits[0][2]


def patch_slot(cs_text: str, set_name: str, slot: int, button: str, replace: bool) -> str:
    m = re.search(rf"(?ms)^CommandSet {re.escape(set_name)}\s*\n.*?^End\s*$", cs_text)
    if not m:
        raise SystemExit(f"live CommandSet missing: {set_name}")
    block = m.group(0)
    occupied = dict(slots_of(block))
    if occupied.get(slot) == button:
        return cs_text
    if replace:
        if slot not in occupied:
            raise SystemExit(f"{set_name} has no slot {slot} to replace")
        new_block, n = re.subn(
            rf"(?m)^(\s*{slot}\s*=\s*)\S+",
            rf"\g<1>{button}",
            block,
            count=1,
        )
        if n != 1:
            raise SystemExit(f"failed to replace slot {slot} on {set_name}")
    else:
        if slot in occupied:
            raise SystemExit(f"{set_name} slot {slot} occupied by {occupied[slot]}")
        lines = block.splitlines()
        if lines[-1].strip() != "End":
            raise SystemExit(f"{set_name} does not end with End")
        lines.insert(-1, f"  {slot} = {button}")
        new_block = "\n".join(lines) + ("\n" if block.endswith("\n") else "")
    return cs_text[: m.start()] + new_block + cs_text[m.end() :]


def unique_loader_sets(gen_cs: str) -> str:
    keep = []
    for name, block in parse_blocks(gen_cs, "CommandSet").items():
        if name == "SpecterSS2TunnelNetworkCommandSet" or name.endswith("DozermCommandSet"):
            if "CommandCenter" in name or name in PROTECTED_CS or name == "IranExpandedHQCommandSet":
                raise SystemExit(f"refused to copy live/protected set {name}")
            keep.append(block.rstrip() + "\n")
    if len(keep) != 27:
        raise SystemExit(f"expected 26 loader sets + tunnel network, got {len(keep)}")
    return "\n".join(keep).rstrip() + "\n"


def main() -> int:
    src_cs = SRC_CS.read_text("latin1")
    src_cb = SRC_CB.read_text("latin1")
    gen_cb = GEN_CB.read_text("latin1")
    gen_cs = GEN_CS.read_text("latin1")
    obj_text = GEN_OBJ.read_text("latin1")

    orig_cs_blocks = parse_blocks(src_cs, "CommandSet")
    orig_cb_blocks = parse_blocks(src_cb, "CommandButton")
    unique_count(list(orig_cs_blocks), "CommandSet.ini")
    unique_count(list(orig_cb_blocks), "CommandButton.ini")

    turkey_before = orig_cs_blocks["TurkeyCommandCenterCommandSet"]
    turkey_dozerm_before = orig_cs_blocks["TurkeyDozermCommandSet"]
    factory_before = orig_cs_blocks["Iran_MissileFactoryCommandSet"]
    gla_worker_before = dict(slots_of(orig_cs_blocks["GLACommandCenterCommandSet"]))[1]

    gen_buttons = parse_blocks(gen_cb, "CommandButton")
    obj_blocks = parse_blocks(obj_text, "Object")
    if any(n.endswith("CommandCenter") or n == "IranCommandCenter" for n in obj_blocks):
        raise SystemExit("Object source still has CommandCenter stubs")
    if len(obj_blocks) != 52:
        raise SystemExit(f"expected 52 objects, got {len(obj_blocks)}")

    loader_sets_text = unique_loader_sets(gen_cs)
    loader_set_blocks = parse_blocks(loader_sets_text, "CommandSet")

    cb_add: list[str] = []
    plan = []
    for fac in FACTIONS:
        if fac["cs"] not in orig_cs_blocks:
            raise SystemExit(f"live CommandSet missing {fac['cs']}")
        if fac["loader"] not in obj_blocks or fac["tunnel"] not in obj_blocks:
            raise SystemExit(f"missing loader/tunnel object {fac['side']}")
        loader_btn, loader_btn_block = extract_button_for_object(gen_cb, fac["loader"])
        tunnel_btn, tunnel_btn_block = extract_button_for_object(gen_cb, fac["tunnel"])
        if loader_btn in orig_cb_blocks or tunnel_btn in orig_cb_blocks:
            raise SystemExit(f"button already in CommandButton.ini: {loader_btn}/{tunnel_btn}")
        if loader_btn in gen_buttons and gen_buttons[loader_btn].count("CommandButton") != 1:
            raise SystemExit(f"generated button malformed {loader_btn}")
        loader_cs = re.search(r"(?m)^\s*CommandSet\s*=\s*(\S+)", obj_blocks[fac["loader"]])
        if not loader_cs:
            raise SystemExit(f"loader object missing CommandSet {fac['loader']}")
        loader_cs_name = loader_cs.group(1)
        if loader_cs_name not in loader_set_blocks:
            raise SystemExit(f"unique loader CommandSet missing {loader_cs_name}")
        if loader_cs_name in orig_cs_blocks:
            raise SystemExit(f"loader CommandSet would duplicate {loader_cs_name}")
        tun_slots = dict(slots_of(loader_set_blocks[loader_cs_name]))
        if tun_slots.get(1) != tunnel_btn:
            raise SystemExit(f"{loader_cs_name} slot 1 is not {tunnel_btn}")
        if "TunnelContain" not in obj_blocks[fac["tunnel"]]:
            raise SystemExit(f"tunnel missing TunnelContain {fac['tunnel']}")
        orig_slots = dict(slots_of(orig_cs_blocks[fac["cs"]]))
        slot1 = orig_slots.get(1)
        if not slot1:
            raise SystemExit(f"{fac['cs']} has no slot 1")
        if fac["replace"] and orig_slots.get(9) != "Command_ConstructIranVehicleKhormshar":
            raise SystemExit("Iran slot 9 is not Khormshar on the live CC set")
        if not fac["replace"] and fac["slot"] in orig_slots:
            raise SystemExit(f"{fac['cs']} slot {fac['slot']} is occupied")
        cb_add.append(loader_btn_block.rstrip() + "\n")
        cb_add.append(tunnel_btn_block.rstrip() + "\n")
        plan.append({**fac, "loader_btn": loader_btn, "tunnel_btn": tunnel_btn, "loader_cs": loader_cs_name, "slot1": slot1})

    unique_count([p["loader_btn"] for p in plan], "loader buttons")
    unique_count([p["tunnel_btn"] for p in plan], "tunnel buttons")
    unique_count([p["cs"] for p in plan], "live CC sets")

    new_cs = src_cs.replace("\r\n", "\n")
    for fac in plan:
        new_cs = patch_slot(new_cs, fac["cs"], fac["slot"], fac["loader_btn"], fac["replace"])
    if "SpecterSS2TunnelNetworkCommandSet" in parse_blocks(new_cs, "CommandSet"):
        raise SystemExit("tunnel network CommandSet already present")
    new_cs = new_cs.rstrip() + "\n\n; SPECTER SS2 tunnel-loader unique CommandSets (Turkey method).\n; Unique names only. Live CC CommandSets were edited in-place above.\n\n" + loader_sets_text
    if not new_cs.endswith("\n"):
        new_cs += "\n"

    new_cb = src_cb.replace("\r\n", "\n").rstrip() + "\n\n; SPECTER SS2 tunnel-loader unique CommandButtons (Turkey method).\n; Unique names only. One definition each.\n\n" + "\n".join(cb_add)
    if not new_cb.endswith("\n"):
        new_cb += "\n"

    new_cs_blocks = parse_blocks(new_cs, "CommandSet")
    new_cb_blocks = parse_blocks(new_cb, "CommandButton")
    unique_count(list(new_cs_blocks), "patched CommandSet.ini")
    unique_count(list(new_cb_blocks), "patched CommandButton.ini")

    if new_cs_blocks["TurkeyCommandCenterCommandSet"] != turkey_before.replace("\r\n", "\n"):
        raise SystemExit("Turkey Command Center CommandSet changed")
    if new_cs_blocks["TurkeyDozermCommandSet"] != turkey_dozerm_before.replace("\r\n", "\n"):
        raise SystemExit("Turkey Dozerm CommandSet changed")
    if new_cs_blocks["Iran_MissileFactoryCommandSet"] != factory_before.replace("\r\n", "\n"):
        raise SystemExit("Iran missile factory CommandSet changed")
    if dict(slots_of(new_cs_blocks["GLACommandCenterCommandSet"]))[1] != gla_worker_before:
        raise SystemExit("GLA worker slot 1 changed")

    for fac in plan:
        won = dict(slots_of(new_cs_blocks[fac["cs"]]))
        if won.get(fac["slot"]) != fac["loader_btn"]:
            raise SystemExit(f"{fac['side']} slot {fac['slot']} is {won.get(fac['slot'])}")
        if won.get(1) != fac["slot1"]:
            raise SystemExit(f"{fac['side']} lost slot 1 {fac['slot1']}")
        if fac["loader_btn"] not in new_cb_blocks or fac["tunnel_btn"] not in new_cb_blocks:
            raise SystemExit(f"patched CommandButton.ini missing {fac['loader_btn']}")
        if new_cb_blocks[fac["loader_btn"]].count("CommandButton") != 1:
            raise SystemExit(f"loader button not unique {fac['loader_btn']}")
        if "Command_ConstructIranVehicleKhormshar" in won.values() and fac["side"] == "Iran":
            raise SystemExit("Iran CC still has Khormshar")

    factory_slots = dict(slots_of(new_cs_blocks["Iran_MissileFactoryCommandSet"]))
    if factory_slots.get(7) != "CB_IRAN_MISSILE_G":
        raise SystemExit(f"Iran factory slot 7 is {factory_slots.get(7)}")
    if "CB_IRAN_MISSILE_G" not in new_cb_blocks:
        raise SystemExit("CB_IRAN_MISSILE_G missing")
    if not re.search(r"(?m)^\s*Object\s*=\s*Iran_Khorram\s*$", new_cb_blocks["CB_IRAN_MISSILE_G"]):
        raise SystemExit("CB_IRAN_MISSILE_G is not Iran_Khorram")

    for name in ("Command_ConstructTurkeyVehicleDozerm", "Command_ConstructTurkeyPowerStationm"):
        if new_cb_blocks[name] != orig_cb_blocks[name].replace("\r\n", "\n"):
            raise SystemExit(f"Turkey button changed {name}")

    if "Command_ConstructGLAWorker" not in dict(slots_of(new_cs_blocks["GLACommandCenterCommandSet"])).values():
        raise SystemExit("GLA worker button dropped")

    out_ini = OUT_DIR / "Data" / "INI"
    out_obj = out_ini / "Object"
    out_ini.mkdir(parents=True, exist_ok=True)
    out_obj.mkdir(parents=True, exist_ok=True)
    out_cs = out_ini / "CommandSet.ini"
    out_cb = out_ini / "CommandButton.ini"
    out_obj_file = out_obj / "zzzzzzzzzz_SPECTER_SS2_TunnelLoader.ini"
    out_cs.write_bytes(crlf(new_cs))
    out_cb.write_bytes(crlf(new_cb))
    out_obj_file.write_bytes(crlf(obj_text.replace("\r\n", "\n")))

    zip_names = [
        "Data/INI/CommandButton.ini",
        "Data/INI/CommandSet.ini",
        "Data/INI/Object/zzzzzzzzzz_SPECTER_SS2_TunnelLoader.ini",
    ]
    zip_path = OUT_DIR / "SPECTER_SS2_TUNNEL_LOADER_TURKEY_METHOD.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_cb, zip_names[0])
        zf.write(out_cs, zip_names[1])
        zf.write(out_obj_file, zip_names[2])
        if zf.namelist() != zip_names:
            raise SystemExit(f"ZIP contents {zf.namelist()}")

    hashes = {
        "CommandButton.ini": sha256(out_cb),
        "CommandSet.ini": sha256(out_cs),
        "Object": sha256(out_obj_file),
        "ZIP": sha256(zip_path),
    }
    for name, digest in (
        ("CommandButton.ini", hashes["CommandButton.ini"]),
        ("CommandSet.ini", hashes["CommandSet.ini"]),
        ("zzzzzzzzzz_SPECTER_SS2_TunnelLoader.ini", hashes["Object"]),
        ("SPECTER_SS2_TUNNEL_LOADER_TURKEY_METHOD.zip", hashes["ZIP"]),
    ):
        (OUT_DIR / f"{name}.sha256").write_text(f"{digest}  {name}\n", encoding="ascii")

    report = [
        "SS2 tunnel loaders via Turkey method (live CommandSet.ini / CommandButton.ini)",
        f"source CommandSet.ini:    {SRC_CS}  {sha256(SRC_CS)}",
        f"source CommandButton.ini: {SRC_CB}  {sha256(SRC_CB)}",
        f"out CommandSet.ini:       {out_cs}  {hashes['CommandSet.ini']}",
        f"out CommandButton.ini:    {out_cb}  {hashes['CommandButton.ini']}",
        f"out Object glob:          {out_obj_file}  {hashes['Object']}",
        f"SHA-256 ZIP: {hashes['ZIP']}",
        f"ZIP: {zip_path}  {zip_path.stat().st_size}",
        "ZIP members: " + ", ".join(zip_names),
        "",
        "Backup the original Loose Data/INI/CommandSet.ini and CommandButton.ini before unzip.",
        "Turkey CC, GLA worker slot 1, Iran missile factory, ART, SS1 were not edited.",
        "No extra CommandSet_*.ini / CommandButton_*.ini files were created.",
        "In-game test was not run.",
        "",
        f"{'Side':24s} {'live CS':42s} {'slot':4s} {'slot1 kept':42s} loader button",
    ]
    for fac in plan:
        report.append(
            f"{fac['side']:24s} {fac['cs']:42s} {fac['slot']:<4d} {fac['slot1']:42s} {fac['loader_btn']}"
        )
    (OUT_DIR / "BUILD_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
