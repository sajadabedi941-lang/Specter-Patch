#!/usr/bin/env python3
"""SS2 tunnel loaders as Loose Data files only (no BIG edits).

Live ControlBar files the engine opens:
  Data/INI/CommandSet.ini
  Data/INI/CommandButton.ini

ThingTemplates go in Data/INI/Object/<country folder>/ next to that
country's existing dozer/powerplant, as NEW files.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_turkey_method import (
    FACTIONS,
    GEN_CB,
    GEN_CS,
    GEN_OBJ,
    SRC_CB,
    SRC_CS,
    crlf,
    extract_button_for_object,
    parse_blocks,
    patch_slot,
    sha256,
    slots_of,
    unique_count,
    unique_loader_sets,
)

ROOT = Path("/tmp/ss2/SPECTER FINAL (GeneralsMode.com)")
DATA = ROOT / "Data"
OUT_DIR = Path("patch/Release/SPECTER_SS2_TUNNEL_LOADER_DATA_FOLDER")
BACKUP_DIR = OUT_DIR / "backup"

OBJECT_PATHS = {
    "Iraq": ("Object/Specter/Iraq Army/Tracked/Iraq_VehicleDozerm.ini", "Object/Specter/Iraq Army/Buildings/Iraq_PowerStationm.ini"),
    "NorthKorea": ("Object/Specter/North Korea/Tracked/NorthKorea_VehicleDozerm.ini", "Object/Specter/North Korea/Buildings/NorthKorea_PowerStationm.ini"),
    "America": ("Object/Specter/United States Of America/Wheeled/AmericaVehicleDozerm.ini", "Object/Specter/United States Of America/Buildings/AmericaPowerStationm.ini"),
    "Russia": ("Object/Specter/Armed Forces Of Russian Federation/Tracked/RussiaVehicleDozerm.ini", "Object/Specter/Armed Forces Of Russian Federation/Buildings/RussiaPowerStationm.ini"),
    "China": ("Object/Specter/PLA/Tracked/ChinaVehicleDozerm.ini", "Object/Specter/PLA/Buildings/ChinaPowerStationm.ini"),
    "GLA": ("Object/Specter/Arabic Alliance/Wheeled/GLAVehicleDozerm.ini", "Object/Specter/Arabic Alliance/Buildings/GLAPowerStationm.ini"),
    "Boss": ("Object/Boss_VehicleDozerm.ini", "Object/Boss_PowerStationm.ini"),
    "AmericaAirForceGeneral": ("Object/Specter/Israel Defense Forces/Wheeled/AirF_AmericaVehicleDozerm.ini", "Object/Specter/Israel Defense Forces/Buildings/AirF_AmericaPowerStationm.ini"),
    "Nato": ("Object/Specter/NATO/Wheleed/NatoVehicleDozerm.ini", "Object/Specter/NATO/Buildings/NatoPowerStationm.ini"),
    "Iran": ("Object/Specter/Iranian Army/Tracked/IranVehicleDozerm.ini", "Object/Specter/Iranian Army/Buildings/IranPowerStationm.ini"),
    "Pakistan": ("Object/Specter/Pakistan Armed Forces/Tracked/Pakistan_VehicleDozerm.ini", "Object/Specter/Pakistan Armed Forces/Buildings/Pakistan_PowerStationm.ini"),
    "SaudiArabia": ("Object/Specter/Saudi Arabia Armed Forces/Tracked/SaudiArabia_VehicleDozerm.ini", "Object/Specter/Saudi Arabia Armed Forces/Buildings/SaudiArabia_PowerStationm.ini"),
    "UAE": ("Object/Specter/United Arab Emirates Armed Forces/Tracked/UAE_VehicleDozerm.ini", "Object/Specter/United Arab Emirates Armed Forces/Buildings/UAE_PowerStationm.ini"),
    "India": ("Object/Specter/Indian Armed Forces/Tracked/India_VehicleDozerm.ini", "Object/Specter/Indian Armed Forces/Buildings/India_PowerStationm.ini"),
    "Syria": ("Object/Specter/Syrian Armed Forces/Tracked/Syria_VehicleDozerm.ini", "Object/Specter/Syrian Armed Forces/Buildings/Syria_PowerStationm.ini"),
    "Germany": ("Object/Specter/German Armed Forces/Wheleed/GermanyVehicleDozerm.ini", "Object/Specter/German Armed Forces/Buildings/GermanyPowerStationm.ini"),
    "France": ("Object/Specter/French Armed Forces/Wheleed/FranceVehicleDozerm.ini", "Object/Specter/French Armed Forces/Buildings/FrancePowerStationm.ini"),
    "Britain": ("Object/Specter/British Armed Forces/Wheleed/BritainVehicleDozerm.ini", "Object/Specter/British Armed Forces/Buildings/BritainPowerStationm.ini"),
    "Italy": ("Object/Specter/Italian Armed Forces/Wheleed/ItalyVehicleDozerm.ini", "Object/Specter/Italian Armed Forces/Buildings/ItalyPowerStationm.ini"),
    "Sweden": ("Object/Specter/Swedish Armed Forces/Wheleed/SwedenVehicleDozerm.ini", "Object/Specter/Swedish Armed Forces/Buildings/SwedenPowerStationm.ini"),
    "Ukraine": ("Object/Specter/Ukrainian Armed Forces/Wheleed/UkraineVehicleDozerm.ini", "Object/Specter/Ukrainian Armed Forces/Buildings/UkrainePowerStationm.ini"),
    "Libya": ("Object/Specter/Libyan Armed Forces/Tracked/Libya_VehicleDozerm.ini", "Object/Specter/Libyan Armed Forces/Buildings/Libya_PowerStationm.ini"),
    "SouthAfrica": ("Object/Specter/South African National Defence Force/Tracked/SouthAfrica_VehicleDozerm.ini", "Object/Specter/South African National Defence Force/Buildings/SouthAfrica_PowerStationm.ini"),
    "SouthKorea": ("Object/Specter/South Korean Armed Forces/Tracked/SouthKorea_VehicleDozerm.ini", "Object/Specter/South Korean Armed Forces/Buildings/SouthKorea_PowerStationm.ini"),
    "Japan": ("Object/Specter/Japan Self-Defense Forces/Tracked/Japan_VehicleDozerm.ini", "Object/Specter/Japan Self-Defense Forces/Buildings/Japan_PowerStationm.ini"),
    "Vietnam": ("Object/Specter/Vietnam People's Armed Forces/Tracked/Vietnam_VehicleDozerm.ini", "Object/Specter/Vietnam People's Armed Forces/Buildings/Vietnam_PowerStationm.ini"),
}


def object_block(text: str, name: str) -> str:
    m = re.search(rf"(?ms)^Object {re.escape(name)}\s*\n.*?^(?=Object |\Z)", text)
    if not m:
        raise SystemExit(f"object missing {name}")
    block = m.group(0).rstrip() + "\n"
    return block


def write_audit(out: Path) -> None:
    ini = DATA / "INI"
    lines = []
    lines.append("# SS2 Data folder audit (engine load map)")
    lines.append("")
    lines.append("Source: `/tmp/ss2/SPECTER FINAL (GeneralsMode.com)/Data`")
    lines.append("Engine: stock ZH `game.dat` (6,483,968 bytes). Existence of a Loose file is not a load proof.")
    lines.append("")
    lines.append("## Engine-opened INI paths")
    lines.append("")
    lines.append("ControlBar (exact files only):")
    lines.append("- `Data\\INI\\Default\\CommandButton.ini`")
    lines.append("- `Data\\INI\\CommandButton.ini`  ← Loose wins over every BIG")
    lines.append("- `Data\\INI\\CommandSet.ini`  ← Loose wins over every BIG")
    lines.append("")
    lines.append("ThingFactory directory glob: `Data\\INI\\Object` (recursive `.ini`).")
    lines.append("MappedImages glob: `Data\\INI\\MappedImages\\*.ini`.")
    lines.append("ParticleSystem directory glob: `Data\\INI\\ParticleSystem`.")
    lines.append("Weapons: exact `Data\\INI\\Weapon.ini` only.")
    lines.append("")
    lines.append("Not opened by ControlBar: `CommandSet_*.ini`, `CommandButton_*.ini`.")
    lines.append("Not opened by ThingFactory: `Data\\INI\\Object_ZZZZ_*.ini` (INI **root**, outside Object/).")
    lines.append("Not opened as a weapon glob: `Data\\INI\\Weapon\\*.ini` and `Weapon_*.ini`.")
    lines.append("Duplicate CommandSet names throw `INI_INVALID_DATA` (no last-win).")
    lines.append("")
    lines.append("## Data tree")
    lines.append("")
    lines.append("- `Data/Cursors`, `Data/English/Movies`, `Data/Movies`, `Data/Scripts`, `Data/WaterPlane`")
    lines.append("- `Data/INI` — 211 Loose INI at root + Default, GameData, MappedImages, Object, Weapon")
    lines.append(f"- Object glob: {sum(1 for _ in (ini/'Object').rglob('*.ini'))} `.ini` files")
    lines.append(f"- CommandSet.ini sets: {len(parse_blocks((ini/'CommandSet.ini').read_text('latin1'), 'CommandSet'))}")
    lines.append(f"- CommandButton.ini buttons: {len(parse_blocks((ini/'CommandButton.ini').read_text('latin1'), 'CommandButton'))}")
    lines.append(f"- Extra CommandSet_*.ini files: {len(list(ini.glob('CommandSet_*.ini')))} (not ControlBar-loaded)")
    lines.append(f"- Extra CommandButton_*.ini files: {len(list(ini.glob('CommandButton_*.ini')))} (not ControlBar-loaded)")
    lines.append("")
    lines.append("## Live Command Center bars (26 + Turkey)")
    lines.append("")
    lines.append("| Country | Object file | Live CommandSet (CommandSet.ini) | Slot 1 |")
    lines.append("|---|---|---|---|")
    cs = parse_blocks((ini / "CommandSet.ini").read_text("latin1"), "CommandSet")
    for fac in FACTIONS + [{"side": "Turkey", "cc": "TurkeyCommandCenter", "cs": "TurkeyCommandCenterCommandSet"}]:
        sl = dict(slots_of(cs[fac["cs"]]))
        lines.append(f"| {fac['side']} | `{fac['cc']}` | `{fac['cs']}` | `{sl.get(1)}` |")
    lines.append("")
    lines.append("Iran factory (untouched): `Iran_MissileFactoryCommandSet` in CommandSet.ini, button `CB_IRAN_MISSILE_G` → `Iran_Khorram` in CommandButton.ini, object `Object/Specter/Iranian Army/Wheeled/Iran_Khorram.ini`.")
    lines.append("Turkey loader already live in CommandSet.ini slot 4 + CommandButton.ini + `Turkish Armed Forces/Wheleed/Dozer.ini`.")
    lines.append("Country extras such as `CommandSet_Pakistan.ini` redefine CC sets but are **not** loaded; live Pakistan CC is Dozer from CommandSet.ini.")
    lines.append("")
    lines.append("## Where this patch writes")
    lines.append("")
    lines.append("| Piece | File | Why |")
    lines.append("|---|---|---|")
    lines.append("| CC buttons | `Data/INI/CommandSet.ini` | Only CommandSet file ControlBar opens |")
    lines.append("| Unique loader CommandSets | appended to `Data/INI/CommandSet.ini` | New names only |")
    lines.append("| Unique construct buttons | appended to `Data/INI/CommandButton.ini` | Only CommandButton file ControlBar opens |")
    lines.append("| Loader/tunnel Objects | new files under `Data/INI/Object/Specter/<country>/` | ThingFactory glob |")
    lines.append("")
    lines.append("No BIG members are created or replaced.")
    (out / "DATA_AUDIT_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    bak_ini = BACKUP_DIR / "Data" / "INI"
    bak_ini.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SRC_CS, bak_ini / "CommandSet.ini")
    shutil.copy2(SRC_CB, bak_ini / "CommandButton.ini")
    write_audit(OUT_DIR)

    src_cs = SRC_CS.read_text("latin1")
    src_cb = SRC_CB.read_text("latin1")
    gen_cb = GEN_CB.read_text("latin1")
    gen_cs = GEN_CS.read_text("latin1")
    obj_text = GEN_OBJ.read_text("latin1")
    orig_cs = parse_blocks(src_cs, "CommandSet")
    orig_cb = parse_blocks(src_cb, "CommandButton")
    obj_blocks = parse_blocks(obj_text, "Object")
    loader_sets_text = unique_loader_sets(gen_cs)
    loader_set_blocks = parse_blocks(loader_sets_text, "CommandSet")

    turkey_cc = orig_cs["TurkeyCommandCenterCommandSet"]
    factory = orig_cs["Iran_MissileFactoryCommandSet"]
    gla1 = dict(slots_of(orig_cs["GLACommandCenterCommandSet"]))[1]

    plan = []
    cb_add = []
    for fac in FACTIONS:
        loader_btn, loader_btn_block = extract_button_for_object(gen_cb, fac["loader"])
        tunnel_btn, tunnel_btn_block = extract_button_for_object(gen_cb, fac["tunnel"])
        if loader_btn in orig_cb or tunnel_btn in orig_cb:
            raise SystemExit(f"button already exists {loader_btn}")
        loader_cs = re.search(r"(?m)^\s*CommandSet\s*=\s*(\S+)", obj_blocks[fac["loader"]]).group(1)
        if loader_cs in orig_cs:
            raise SystemExit(f"duplicate CommandSet {loader_cs}")
        if dict(slots_of(loader_set_blocks[loader_cs])).get(1) != tunnel_btn:
            raise SystemExit(f"{loader_cs} slot1 mismatch")
        if fac["loader"] not in obj_blocks or fac["tunnel"] not in obj_blocks:
            raise SystemExit(f"missing object {fac['side']}")
        if "TunnelContain" not in obj_blocks[fac["tunnel"]]:
            raise SystemExit(f"no TunnelContain {fac['tunnel']}")
        orig_slots = dict(slots_of(orig_cs[fac["cs"]]))
        if fac["replace"] and orig_slots.get(9) != "Command_ConstructIranVehicleKhormshar":
            raise SystemExit("Iran slot 9 is not Khormshar")
        if not fac["replace"] and fac["slot"] in orig_slots:
            raise SystemExit(f"{fac['cs']} slot {fac['slot']} occupied")
        loader_rel, tunnel_rel = OBJECT_PATHS[fac["side"]]
        if (DATA / "INI" / loader_rel).exists() or (DATA / "INI" / tunnel_rel).exists():
            raise SystemExit(f"refusing to overwrite existing object file {loader_rel}")
        cb_add.append(loader_btn_block.rstrip() + "\n")
        cb_add.append(tunnel_btn_block.rstrip() + "\n")
        plan.append({**fac, "loader_btn": loader_btn, "tunnel_btn": tunnel_btn, "loader_cs": loader_cs, "slot1": orig_slots[1], "loader_rel": loader_rel, "tunnel_rel": tunnel_rel})

    unique_count([p["loader_btn"] for p in plan], "loader buttons")
    unique_count([p["cs"] for p in plan], "live sets")

    new_cs = src_cs.replace("\r\n", "\n")
    for fac in plan:
        new_cs = patch_slot(new_cs, fac["cs"], fac["slot"], fac["loader_btn"], fac["replace"])
    new_cs = new_cs.rstrip() + "\n\n; SPECTER SS2 tunnel-loader unique CommandSets (Data-folder method).\n; Unique names only.\n\n" + loader_sets_text
    new_cb = src_cb.replace("\r\n", "\n").rstrip() + "\n\n; SPECTER SS2 tunnel-loader unique CommandButtons (Data-folder method).\n; Unique names only.\n\n" + "\n".join(cb_add)

    new_cs_blocks = parse_blocks(new_cs, "CommandSet")
    new_cb_blocks = parse_blocks(new_cb, "CommandButton")
    unique_count(list(new_cs_blocks), "patched CS")
    unique_count(list(new_cb_blocks), "patched CB")
    if new_cs_blocks["TurkeyCommandCenterCommandSet"] != turkey_cc.replace("\r\n", "\n"):
        raise SystemExit("Turkey CC changed")
    if new_cs_blocks["Iran_MissileFactoryCommandSet"] != factory.replace("\r\n", "\n"):
        raise SystemExit("Iran factory changed")
    if dict(slots_of(new_cs_blocks["GLACommandCenterCommandSet"]))[1] != gla1:
        raise SystemExit("GLA worker changed")
    if dict(slots_of(new_cs_blocks["Iran_MissileFactoryCommandSet"])).get(7) != "CB_IRAN_MISSILE_G":
        raise SystemExit("factory Khormshar button lost")

    out_ini = OUT_DIR / "Data" / "INI"
    out_ini.mkdir(parents=True, exist_ok=True)
    (out_ini / "CommandSet.ini").write_bytes(crlf(new_cs))
    (out_ini / "CommandButton.ini").write_bytes(crlf(new_cb))

    zip_names = ["Data/INI/CommandButton.ini", "Data/INI/CommandSet.ini"]
    for fac in plan:
        for rel, obj_name in ((fac["loader_rel"], fac["loader"]), (fac["tunnel_rel"], fac["tunnel"])):
            dest = out_ini / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            header = f"; SPECTER SS2 tunnel-loader object. New file under Data/INI/{rel}\n"
            dest.write_bytes(crlf(header + object_block(obj_text.replace("\r\n", "\n"), obj_name)))
            zip_names.append("Data/INI/" + rel)

    zip_path = OUT_DIR / "SPECTER_SS2_TUNNEL_LOADER_DATA_FOLDER.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        mapping = {
            "Data/INI/CommandButton.ini": out_ini / "CommandButton.ini",
            "Data/INI/CommandSet.ini": out_ini / "CommandSet.ini",
        }
        for fac in plan:
            mapping["Data/INI/" + fac["loader_rel"]] = out_ini / fac["loader_rel"]
            mapping["Data/INI/" + fac["tunnel_rel"]] = out_ini / fac["tunnel_rel"]
        for name in zip_names:
            zf.write(mapping[name], name)
        if zf.namelist() != zip_names:
            raise SystemExit(f"ZIP {zf.namelist()}")

    report = [
        "SS2 tunnel loaders as Data-folder Loose files (no BIG)",
        f"backup CommandSet.ini     {sha256(bak_ini / 'CommandSet.ini')}",
        f"backup CommandButton.ini  {sha256(bak_ini / 'CommandButton.ini')}",
        f"SHA-256 CommandSet.ini    {sha256(out_ini / 'CommandSet.ini')}",
        f"SHA-256 CommandButton.ini {sha256(out_ini / 'CommandButton.ini')}",
        f"SHA-256 ZIP               {sha256(zip_path)}",
        f"ZIP {zip_path} {zip_path.stat().st_size} members={len(zip_names)}",
        "No BIG files were written.",
        "In-game test was not run.",
        "",
        f"{'Side':24s} {'CS file':20s} {'slot':4s} object path",
    ]
    for fac in plan:
        report.append(f"{fac['side']:24s} CommandSet.ini        {fac['slot']:<4d} {fac['loader_rel']}")
    (OUT_DIR / "BUILD_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT_DIR / "SPECTER_SS2_TUNNEL_LOADER_DATA_FOLDER.zip.sha256").write_text(
        f"{sha256(zip_path)}  SPECTER_SS2_TUNNEL_LOADER_DATA_FOLDER.zip\n", encoding="ascii"
    )
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
