#!/usr/bin/env python3
"""Iran / America / Israel missile-factory construction access only.

Baseline: packed SPECTER_CHINA_RUSSIA_MISSILES_AJ (PR #651 on #650).

Packed last-wins audit:
  FactionIran StartingUnit0=IranVehicleDozer CommandSet=IranDozerCommandSet
    slot 10 = Command_ConstructIranBavarSiteAI (CSF: Bavar-373 SAM Site)
  FactionAmerica StartingUnit0=AmericaVehicleDozer CommandSet=AmericaDozerCommandSet
    slot 14 = Command_DisarmMinesAtPosition (Clear Mines)
  FactionIsrael StartingUnit0=Israel_VehicleDozer (object ABSENT in packed DATA).
    Packed Israel dozer file last-wins Object AirF_AmericaVehicleDozer Side=Israel
    CommandSet=AirF_AmericaDozerCommandSet slot 14 = Command_DisarmMinesAtPosition.
    FactionAmericaAirForceGeneral shares that same packed dozer object.

This pack replaces those three live MENU ENTRIES only. Bavar-373 objects,
Command_ConstructIranBavarSiteAI / Command_ConstructIran_Bavar definitions,
and Command_DisarmMinesAtPosition remain. No A-J rosters, weapons, or
projectiles. Factories are Rally/Sell shells. ART is unchanged from #651.
No ZZZZ. No faction conversion.
"""
from __future__ import annotations

import gzip
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
sys.path.insert(0, str(ROOT / "patch/tools/big"))
import pack_s_sk_missiles_aj as sk  # noqa: E402
import pack_s_turkey_spain_missiles_aj as ts  # noqa: E402
import pack_s_sweden_ukraine_missiles_aj as su  # noqa: E402
import pack_s_britain_france_missiles_aj as bf  # noqa: E402
import pack_s_germany_italy_missiles_aj as gi  # noqa: E402
import pack_s_china_russia_missiles_aj as cr  # noqa: E402

SRC_DATA = ROOT / "patch/Release/SPECTER_CHINA_RUSSIA_MISSILES_AJ/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_CHINA_RUSSIA_MISSILES_AJ/_SPEC_ART_ONE.big"
SRC_ART_GZ = ROOT / "patch/Release/SPECTER_CHINA_RUSSIA_MISSILES_AJ/_SPEC_ART_ONE.big.gz"
OUT = ROOT / "patch/Release/SPECTER_IRAN_US_ISRAEL_FACTORY_BTNS"
LOOSE = ROOT / "patch/Data/INI"

SHA_DATA_SRC = "ad40fe44269bc5dc7a139077a0b8656215e723fc8df8fbbfd67499d930492cc6"
SIZE_DATA_SRC = 370212639
SHA_ART_SRC = "cf83e8cfedff3b3cf3ef5ff890d2ee79dd551dc68d9c6ae3f6295b36935f6d35"
SIZE_ART_SRC = 2308008528

CB_KEY = sk.CB_KEY
CS_KEY = sk.CS_KEY
CSF_KEY = sk.CSF_KEY
WEAPON_KEY = sk.WEAPON_KEY

COUNTRIES = [
    {
        "code": "IR",
        "label": "Iran",
        "side": "Iran",
        "prefix": "Iran",
        "builder": "IranDozerCommandSet",
        "replace": "Command_ConstructIranBavarSiteAI",
        "replace_slot": "10",
        "replace_why": "Bavar-373 SAM Site construction entry",
        "fac_obj": "Iran_MissileFactory",
        "fac_cs": "Iran_MissileFactoryCommandSet",
        "fac_btn": "Command_ConstructIran_MissileFactory",
        "fac_key": r"Data\INI\Object\Specter\Iranian Army\Buildings\Iran_MissileFactory.ini",
        "cb_key": r"Data\INI\CommandButton_IranMissileFactory.ini",
        "cs_key": r"Data\INI\CommandSet_IranMissileFactory.ini",
        "supply": "IranSupplyCenter",
        "keep": (
            "Command_ConstructIranPowerplant",
            "Command_ConstructIranIndustrialComplex",
            "Command_ConstructIranSupplyCenter",
            "Command_ConstructIranCommandCenter",
            "Command_ConstructIranBarracks",
            "Command_ConstructIranSejjilSilo",
            "Command_ConstructIranD30Post",
            "Command_ConstructIranKhordad15SamSite",
            "Command_ConstructIranRadarStation",
            "Command_ConstructIranWarFactory",
            "Command_ConstructIranFalaqTrench",
            "Command_ConstructIranAirfield",
            "Command_ConstructIran_HeavyAirBase",
        ),
    },
    {
        "code": "US",
        "label": "America",
        "side": "America",
        "prefix": "America",
        "builder": "AmericaDozerCommandSet",
        "replace": "Command_DisarmMinesAtPosition",
        "replace_slot": "14",
        "replace_why": "Clear Mines construction entry",
        "fac_obj": "America_MissileFactory",
        "fac_cs": "America_MissileFactoryCommandSet",
        "fac_btn": "Command_ConstructAmerica_MissileFactory",
        "fac_key": (
            r"Data\INI\Object\Specter\United States Of America"
            r"\Buildings\America_MissileFactory.ini"
        ),
        "cb_key": r"Data\INI\CommandButton_AmericaMissileFactory.ini",
        "cs_key": r"Data\INI\CommandSet_AmericaMissileFactory.ini",
        "supply": "AmericaSupplyCenter",
        "keep": (
            "Command_ConstructAmericaPowerPlant",
            "Command_ConstructAmericaStrategyCenter_T",
            "Command_ConstructAmericaBarracks",
            "Command_ConstructAmerica_HeavyAirBase",
            "Command_ConstructAmericaSupplyCenter",
            "Command_ConstructAmericaRadarStation",
            "Command_ConstructAmericaPatriotBattery",
            "Command_ConstructAmericaCommandCenter",
            "Command_ConstructAmericaFireBase",
            "Command_ConstructAmerica_MIM104F",
            "Command_ConstructAmericaWarFactory_T",
            "Command_ConstructAmericaLgm30",
            "Command_ConstructAmericaAirfield_T",
            "Command_ConstructAmericaStrategyCenter",
            "Command_ConstructAmericaVehicleTHAAD_AI",
            "Command_ConstructAmericaWarFactory",
            "Command_ConstructAmericaAirfield",
        ),
    },
    {
        "code": "IL",
        "label": "Israel",
        "side": "Israel",
        "prefix": "Israel",
        "builder": "AirF_AmericaDozerCommandSet",
        "replace": "Command_DisarmMinesAtPosition",
        "replace_slot": "14",
        "replace_why": "Clear Mines construction entry on packed Israel dozer",
        "fac_obj": "Israel_MissileFactory",
        "fac_cs": "Israel_MissileFactoryCommandSet",
        "fac_btn": "Command_ConstructIsrael_MissileFactory",
        "fac_key": (
            r"Data\INI\Object\Specter\Israel Defense Forces"
            r"\Buildings\Israel_MissileFactory.ini"
        ),
        "cb_key": r"Data\INI\CommandButton_IsraelMissileFactory.ini",
        "cs_key": r"Data\INI\CommandSet_IsraelMissileFactory.ini",
        "supply": "AirF_AmericaSupplyCenter Israel_SupplyCenter",
        "keep": (
            "AirF_Command_ConstructAmericaPowerPlant",
            "AirF_Command_ConstructAmericaStrategyCenter",
            "AirF_Command_ConstructAmericaBarracks",
            "Command_ConstructIsrael_HeavyAirBase",
            "AirF_Command_ConstructAmericaSupplyCenter",
            "AirF_Command_ConstructAmericaParticleCannonUplink",
            "AirF_Command_ConstructAmericaPatriotBattery",
            "AirF_Command_ConstructAmericaCommandCenter",
            "AirF_Command_ConstructAmericaFireBase",
            "Command_ConstructIsraelBuildingC-RAM",
            "AirF_Command_ConstructAmericaWarFactory",
            "Command_ConstructIsraelBuildingRadarStation",
            "AirF_Command_ConstructAmericaAirfield",
            "Command_ConstructAmericaVehicleTHAAD_AI",
        ),
    },
]


def factory_ini(c: dict) -> str:
    text = sk.factory_ini()
    text = text.replace("; South Korea missile factory.", f"; {c['label']} missile factory (construction shell).")
    text = text.replace(
        "with a SouthKorea-only CommandSet (A-J).",
        f"with a {c['side']}-only Rally/Sell CommandSet. No A-J roster in this pack.",
    )
    text = text.replace("Object SouthKorea_MissileFactory", f"Object {c['fac_obj']}")
    text = text.replace(
        "DisplayName      = OBJECT:SouthKoreaMissileFactory",
        f"DisplayName      = OBJECT:{c['prefix']}MissileFactory",
    )
    text = text.replace("Side             = SouthKorea", f"Side             = {c['side']}")
    text = text.replace(
        "CommandSet       = SouthKorea_MissileFactoryCommandSet",
        f"CommandSet       = {c['fac_cs']}",
    )
    text = text.replace(
        "Object = SouthKorea_SupplyCenter",
        f"Object = {c['supply']} SouthKorea_SupplyCenter",
    )
    return text


def factory_commandset(c: dict) -> str:
    return (
        f"CommandSet {c['fac_cs']}\r\n"
        "  13 = Command_SetRallyPoint\r\n"
        "  14 = Command_Sell\r\n"
        "End"
    )


def construct_button(c: dict) -> str:
    return "\n".join(
        [
            f"; {c['label']} missile factory construction button. No A-J production buttons.",
            f"CommandButton {c['fac_btn']}",
            "  Command          = DOZER_CONSTRUCT",
            f"  Object           = {c['fac_obj']}",
            f"  TextLabel        = CONTROLBAR:Construct{c['prefix']}MissileFactory",
            "  ButtonImage      = Button_MissileFactory",
            "  ButtonBorderType = BUILD",
            f"  DescriptLabel    = CONTROLBAR:ToolTip{c['prefix']}MissileFactory",
            "End",
            "",
        ]
    )


def with_factory(block: str, c: dict) -> str:
    if c["replace"] not in block:
        raise SystemExit(f"expected {c['replace']} in {c['builder']}:\n{block}")
    if c["fac_btn"] in block:
        raise SystemExit(f"{c['label']} factory already on {c['builder']}")
    # Replace only the construction-menu token, not a substring of another command.
    return block.replace(c["replace"], c["fac_btn"])


def commandset_file(c: dict, builder_block: str) -> str:
    return builder_block + "\r\n\r\n" + factory_commandset(c) + "\r\n"


def csf_map() -> dict[str, str]:
    mapping = {}
    for c in COUNTRIES:
        mapping[f"OBJECT:{c['prefix']}MissileFactory"] = "Missile Factory"
        mapping[f"CONTROLBAR:Construct{c['prefix']}MissileFactory"] = "Missile Factory"
        mapping[f"CONTROLBAR:ToolTip{c['prefix']}MissileFactory"] = (
            f"Missile Factory\nConstruction access for {c['label']}\nPrice: $1800"
        )
    return mapping


def mapping_report() -> list[str]:
    return [
        "IRAN / AMERICA / ISRAEL MISSILE FACTORY CONSTRUCTION ACCESS",
        "",
        "Baseline packed last-wins: SPECTER_CHINA_RUSSIA_MISSILES_AJ (PR #651).",
        "Construction menus only. No A-J launchers, weapons, or projectiles.",
        "Factories are Rally/Sell shells using Irq_FahdFac / Button_MissileFactory.",
        "ART is byte-identical to PR #651.",
        "",
        "IRAN  live builder IranDozerCommandSet (IranVehicleDozer)",
        "  slot 10 Command_ConstructIranBavarSiteAI -> Command_ConstructIran_MissileFactory",
        "  Bavar-373 objects and Command_ConstructIranBavarSiteAI definition kept.",
        "  IranHQCommandSet still builds Iran_Bavar via Command_ConstructIran_Bavar.",
        "",
        "AMERICA live builder AmericaDozerCommandSet (AmericaVehicleDozer)",
        "  slot 14 Command_DisarmMinesAtPosition -> Command_ConstructAmerica_MissileFactory",
        "  Command_DisarmMinesAtPosition definition kept for other menus.",
        "",
        "ISRAEL packed live builder AirF_AmericaDozerCommandSet",
        "  (AirF_AmericaVehicleDozer Side=Israel in Israel Defense Forces Dozer.ini)",
        "  slot 14 Command_DisarmMinesAtPosition -> Command_ConstructIsrael_MissileFactory",
        "  FactionIsrael StartingUnit0=Israel_VehicleDozer remains absent in packed DATA",
        "  (pre-existing). FactionAmericaAirForceGeneral shares this packed dozer object.",
        "",
        "China/Russia #651, Turkey/Spain #650, SE/UA #649, GB/FR #648, DE/IT #647 kept.",
    ]


def validate(data, src_data, order) -> list[str]:
    fails: list[str] = []
    frozen_data = [
        cr.CN_DOZER_KEY, cr.CN_WF_KEY, cr.CN_SC_KEY, cr.CN_FAC_KEY, cr.CN_WEP_KEY,
        cr.CN_CS_KEY, cr.CN_CB_KEY, cr.RU_DOZER_KEY, cr.RU_WF_KEY, cr.RU_SC_KEY,
        cr.RU_FAC_KEY, cr.RU_WEP_KEY, cr.RU_CS_KEY, cr.RU_CB_KEY,
        ts.TR_DOZER_KEY, ts.TR_WF_KEY, ts.TR_SC_KEY, ts.TR_FAC_KEY, ts.TR_WEP_KEY,
        ts.TR_CS_KEY, ts.TR_CB_KEY, ts.ES_CS_KEY, ts.ES_CB_KEY, ts.ES_FAC_KEY, ts.ES_WEP_KEY,
        su.SE_FAC_KEY, su.UA_FAC_KEY, bf.GB_FAC_KEY, bf.FR_FAC_KEY, gi.DE_FAC_KEY, gi.IT_FAC_KEY,
        sk.R11_KEY,
        r"Data\INI\Object\Specter\Iranian Army\AirDefense\Bavar.ini",
        r"Data\INI\Object\Specter\Iranian Army\SamSites\BavarAI.ini",
        r"Data\INI\Object\Specter\Iranian Army\Tracked\Dozer.ini",
        r"Data\INI\Object\Specter\United States Of America\Wheeled\Dozer.ini",
        r"Data\INI\Object\Specter\Israel Defense Forces\Wheeled\Dozer.ini",
        WEAPON_KEY,
    ]
    for key in frozen_data:
        if key in src_data and data.get(key) != src_data.get(key):
            fails.append(f"frozen DATA mutated {key}")

    cs_text = data[CS_KEY].decode("latin1")
    src_cs = src_data[CS_KEY].decode("latin1")
    cb_text = data[CB_KEY].decode("latin1")
    src_cb = src_data[CB_KEY].decode("latin1")

    for frozen_cs in (
        "PLADozerCommandSet",
        "RussiaDozerCommandSet",
        "ChinaDozerCommandSet",
        "TurkeyDozerCommandSet",
        "NatoDozerCommandSet",
        "SwedenDozerCommandSet",
        "UkraineDozerCommandSet",
        "BritainDozerCommandSet",
        "FranceDozerCommandSet",
        "GermanyDozerCommandSet",
        "ItalyDozerCommandSet",
        "Iraq_VT72BCommandSet",
        "IranHQCommandSet",
        "China_MissileFactoryCommandSet",
        "Russia_MissileFactoryCommandSet",
        "Turkey_MissileFactoryCommandSet",
        "Spain_MissileFactoryCommandSet",
    ):
        if sk.last_block(cs_text, "CommandSet", frozen_cs) != sk.last_block(src_cs, "CommandSet", frozen_cs):
            fails.append(f"{frozen_cs} mutated in CommandSet.ini")

    for name, btn in (
        ("PLADozerCommandSet", "Command_ConstructChina_MissileFactory"),
        ("RussiaDozerCommandSet", "Command_ConstructRussia_MissileFactory"),
        ("TurkeyDozerCommandSet", "Command_ConstructTurkey_MissileFactory"),
        ("NatoDozerCommandSet", "Command_ConstructSpain_MissileFactory"),
        ("Iraq_VT72BCommandSet", "Command_ConstructIraq_AlFahdMissileFactory"),
        ("IranHQCommandSet", "Command_ConstructIran_Bavar"),
        ("Iraq_WorkerCommandSet", "Command_DisarmMinesAtPosition"),
    ):
        _k, lw = sk.last_block_from_files(order, data, "CommandSet", name)
        if not lw or btn not in lw:
            fails.append(f"preserved menu lost {name} {btn}")

    bavar_btn = sk.last_block(cb_text, "CommandButton", "Command_ConstructIranBavarSiteAI")
    src_bavar = sk.last_block(src_cb, "CommandButton", "Command_ConstructIranBavarSiteAI")
    if bavar_btn != src_bavar:
        fails.append("Command_ConstructIranBavarSiteAI mutated")
    mines_btn = sk.last_block(cb_text, "CommandButton", "Command_DisarmMinesAtPosition")
    src_mines = sk.last_block(src_cb, "CommandButton", "Command_DisarmMinesAtPosition")
    if mines_btn != src_mines:
        fails.append("Command_DisarmMinesAtPosition mutated")

    for obj in (
        "IranBavarSiteAI", "Iran_Bavar", "Iran_Bavar_CombatMode", "BavarMissile",
        "China_YJ18", "Russia_Kalibr", "Turkey_Atmaca", "Spain_Albatros",
    ):
        if not sk.last_block_from_files(order, data, "Object", obj)[1]:
            fails.append(f"lost object {obj}")

    aj_needles = (
        "CB_IRAN_MISSILE_", "CB_AMERICA_MISSILE_", "CB_ISRAEL_MISSILE_",
        "Weapon_Iran_", "Weapon_America_", "Weapon_Israel_",
        "Projectile_Iran_", "Projectile_America_", "Projectile_Israel_",
    )
    joined = "\n".join(
        data[k].decode("latin1", "ignore")
        for k in data
        if k.endswith(".ini") or k.endswith(".INI")
    )
    for n in aj_needles:
        if n in joined:
            fails.append(f"A-J content leaked {n}")

    for c in COUNTRIES:
        if "ZZZZ" in c["cs_key"] or "ZZZZ" in c["cb_key"]:
            fails.append(f"ZZZZ {c['code']}")
        new_b = sk.last_block(cs_text, "CommandSet", c["builder"])
        if c["fac_btn"] not in new_b:
            fails.append(f"{c['builder']} catalog missing factory")
        if c["replace"] in new_b:
            fails.append(f"{c['builder']} still has {c['replace']}")
        for keep in c["keep"]:
            if keep not in new_b:
                fails.append(f"{c['builder']} lost {keep}")
        _k, lw = sk.last_block_from_files(order, data, "CommandSet", c["builder"])
        if c["fac_btn"] not in lw:
            fails.append(f"last-wins {c['builder']} from {_k} missing factory")
        if c["replace"] in lw:
            fails.append(f"last-wins {c['builder']} still {c['replace']}")

        fac = sk.last_block_from_files(order, data, "CommandSet", c["fac_cs"])[1]
        if "Command_Sell" not in fac or "Command_SetRallyPoint" not in fac:
            fails.append(f"{c['code']} factory missing Rally/Sell")
        if "CB_" in fac and "MISSILE_" in fac:
            fails.append(f"{c['code']} factory has A-J buttons")

        construct = sk.last_block(cb_text, "CommandButton", c["fac_btn"])
        if sk.field(construct, "Object") != c["fac_obj"]:
            fails.append(f"{c['code']} construct Object")
        if sk.field(construct, "Command") != "DOZER_CONSTRUCT":
            fails.append(f"{c['code']} construct Command")
        if sk.field(construct, "ButtonImage") != "Button_MissileFactory":
            fails.append(f"{c['code']} construct image")

        fac_obj = sk.last_block(data[c["fac_key"]].decode("latin1"), "Object", c["fac_obj"])
        if sk.field(fac_obj, "Side") != c["side"]:
            fails.append(f"{c['code']} factory Side")
        if sk.field(fac_obj, "CommandSet") != c["fac_cs"]:
            fails.append(f"{c['code']} factory CommandSet")
        if c["supply"].split()[0] not in fac_obj:
            fails.append(f"{c['code']} factory missing supply prereq")
        cap = sk.csf_get(data[CSF_KEY], f"CONTROLBAR:Construct{c['prefix']}MissileFactory")
        tip = sk.csf_get(data[CSF_KEY], f"CONTROLBAR:ToolTip{c['prefix']}MissileFactory")
        if cap != "Missile Factory":
            fails.append(f"{c['code']} CSF caption")
        if not tip or "A-J" in tip:
            fails.append(f"{c['code']} CSF tooltip")

    for key, expect in (
        ("CONTROLBAR:ConstructIranBavarSiteAI", "Bavar-373"),
        ("CONTROLBAR:ChinaMissileA", "A YJ18"),
        ("CONTROLBAR:RussiaMissileA", "A Kalibr"),
        ("CONTROLBAR:TurkeyMissileA", "A Atmaca"),
        ("CONTROLBAR:SpainMissileA", "A Albatros"),
    ):
        got = sk.csf_get(data[CSF_KEY], key)
        if not got or expect not in got:
            fails.append(f"frozen CSF lost {key}")
    return fails


def write_loose(builders: dict[str, str]) -> None:
    for c in COUNTRIES:
        fac_path = LOOSE / c["fac_key"].replace("Data\\INI\\", "").replace("\\", "/")
        fac_path.parent.mkdir(parents=True, exist_ok=True)
        fac_path.write_text(factory_ini(c), encoding="utf-8")
        (LOOSE / Path(c["cb_key"].replace("\\", "/")).name).write_text(construct_button(c), encoding="utf-8")
        (LOOSE / Path(c["cs_key"].replace("\\", "/")).name).write_text(
            commandset_file(c, builders[c["builder"]]), encoding="utf-8"
        )


def main() -> None:
    if sk.sha256_path(SRC_DATA) != SHA_DATA_SRC or SRC_DATA.stat().st_size != SIZE_DATA_SRC:
        raise SystemExit("DATA baseline is not SPECTER_CHINA_RUSSIA_MISSILES_AJ")
    if sk.sha256_path(SRC_ART) != SHA_ART_SRC or SRC_ART.stat().st_size != SIZE_ART_SRC:
        raise SystemExit("ART baseline is not SPECTER_CHINA_RUSSIA_MISSILES_AJ")

    src_data, _ = sk.parse_big_ordered(SRC_DATA.read_bytes())
    data = dict(src_data)
    cs = src_data[CS_KEY].decode("latin1")
    cb = src_data[CB_KEY].decode("latin1")
    builders = {}
    for c in COUNTRIES:
        data[c["fac_key"]] = sk.to_crlf(factory_ini(c))
        data[c["cb_key"]] = sk.to_crlf(construct_button(c))
        old = sk.last_block(cs, "CommandSet", c["builder"])
        new = with_factory(old, c)
        builders[c["builder"]] = new
        cs = sk.replace_last(cs, "CommandSet", c["builder"], new)
        if sk.last_block(cs, "CommandSet", c["fac_cs"]):
            cs = sk.replace_last(cs, "CommandSet", c["fac_cs"], factory_commandset(c))
        else:
            cs = cs.rstrip("\r\n") + "\r\n\r\n" + factory_commandset(c) + "\r\n"
        data[c["cs_key"]] = sk.to_crlf(commandset_file(c, new))
        if c["fac_btn"] in cb:
            raise SystemExit(f"CommandButton.ini already had {c['fac_btn']}")
        cb = cb.rstrip("\r\n") + "\r\n\r\n" + construct_button(c).replace("\n", "\r\n")
    data[CS_KEY] = cs.encode("latin1")
    data[CB_KEY] = cb.encode("latin1")
    data[CSF_KEY] = sk.csf_upsert(src_data[CSF_KEY], csf_map())
    write_loose(builders)

    data_big = sk.build_big(data)
    packed_data, order = sk.parse_big_ordered(data_big)
    fails = validate(packed_data, src_data, order)
    fails.extend(f"DATA {x}" for x in sk.big_structure_ok(data_big))
    if fails:
        raise SystemExit("VALIDATION FAILED\n" + "\n".join(fails))

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    data_path = OUT / "_SPEC_DATA_ONE.big"
    art_path = OUT / "_SPEC_ART_ONE.big"
    art_gz_path = OUT / "_SPEC_ART_ONE.big.gz"
    data_path.write_bytes(data_big)
    shutil.copy2(SRC_ART, art_path)
    if SRC_ART_GZ.exists():
        shutil.copy2(SRC_ART_GZ, art_gz_path)
    else:
        with art_path.open("rb") as src, gzip.open(art_gz_path, "wb", compresslevel=6) as dst:
            shutil.copyfileobj(src, dst, 1024 * 1024)
    if sk.sha256_path(art_path) != SHA_ART_SRC:
        raise SystemExit("ART copy is not identical to PR #651")

    ext = OUT / "LAST_WINS_EXTRACT" / "DATA"
    ext.mkdir(parents=True)
    packed_cs = packed_data[CS_KEY].decode("latin1")
    parts = []
    for c in COUNTRIES:
        parts.append(sk.last_block(packed_cs, "CommandSet", c["builder"]))
        parts.append(sk.last_block(packed_cs, "CommandSet", c["fac_cs"]))
        (ext / f"{c['fac_obj']}.ini").write_text(factory_ini(c), encoding="utf-8")
    (ext / "CommandSets.txt").write_text("\r\n\r\n".join(parts) + "\r\n", encoding="utf-8")
    map_lines = mapping_report()
    (ext / "GAMEPLAY_MAPPING.txt").write_text("\n".join(map_lines) + "\n", encoding="utf-8")

    data_sha = sk.sha256_path(data_path)
    art_sha = sk.sha256_path(art_path)
    art_gz_sha = sk.sha256_path(art_gz_path)
    zip_path = ROOT / "patch/Release/SPECTER_IRAN_US_ISRAEL_FACTORY_BTNS.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
    zip_sha = sk.sha256_path(zip_path)
    tag = "s-iran-us-israel-factory-btns"
    rel_base = (
        "https://github.com/sajadabedi941-lang/Specter-Patch/releases/download/" + tag
    )

    report = [
        "STATIC VALIDATION: PASS",
        "RUNTIME TEST: NOT RUN",
        "BASELINE: PR #651 s-china-russia-missiles-aj + #650 + #649 + #648 + #647",
        f"DATA_SIZE={data_path.stat().st_size}",
        f"DATA_SHA256={data_sha}",
        f"ART_SIZE={art_path.stat().st_size}",
        f"ART_SHA256={art_sha}",
        "ART_CHANGED=NO",
        f"ART_GZ_SIZE={art_gz_path.stat().st_size}",
        f"ART_GZ_SHA256={art_gz_sha}",
        "IRAN_SLOT10=Command_ConstructIran_MissileFactory",
        "AMERICA_SLOT14=Command_ConstructAmerica_MissileFactory",
        "ISRAEL_AIRF_SLOT14=Command_ConstructIsrael_MissileFactory",
        "BAVAR373_OBJECTS_KEPT=YES",
        "DISARM_MINES_DEFINITION_KEPT=YES",
        "NO_AJ_ROSTER=YES",
        "CN_RU_TR_ES_SE_UA_GB_FR_DE_IT_KEPT=YES",
        "",
        *map_lines,
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    hashes = "\n".join(
        [
            "DATA_CHANGED=YES",
            "ART_CHANGED=NO",
            f"DATA_SIZE={data_path.stat().st_size}",
            f"DATA_SHA256={data_sha}",
            f"ART_SIZE={art_path.stat().st_size}",
            f"ART_SHA256={art_sha}",
            f"ART_GZ_SIZE={art_gz_path.stat().st_size}",
            f"ART_GZ_SHA256={art_gz_sha}",
            "ZIP_FILE=SPECTER_IRAN_US_ISRAEL_FACTORY_BTNS.zip",
            f"ZIP_SIZE={zip_path.stat().st_size}",
            f"ZIP_SHA256={zip_sha}",
            "BASELINE=PR #651",
            "STATIC_VALIDATION=PASS",
            "RUNTIME_TEST=NOT RUN",
            "",
        ]
    )
    (OUT / "HASHES.txt").write_text(hashes)
    (OUT / "DOWNLOAD.txt").write_text(
        "\n".join(
            [
                "DATA replacement:",
                f"  {rel_base}/_SPEC_DATA_ONE.big",
                f"  SIZE={data_path.stat().st_size}",
                f"  SHA256={data_sha}",
                "",
                "ART replacement (unchanged from PR #651; gzipped for GitHub 2 GiB limit):",
                f"  {rel_base}/_SPEC_ART_ONE.big.gz",
                f"  GZ_SIZE={art_gz_path.stat().st_size}",
                f"  GZ_SHA256={art_gz_sha}",
                f"  UNCOMPRESSED_SIZE={art_path.stat().st_size}",
                f"  UNCOMPRESSED_SHA256={art_sha}",
                "  gunzip -k _SPEC_ART_ONE.big.gz",
                "",
                "ZIP (complete uncompressed DATA + ART BIGs):",
                f"  {rel_base}/SPECTER_IRAN_US_ISRAEL_FACTORY_BTNS.zip",
                f"  SIZE={zip_path.stat().st_size}",
                f"  SHA256={zip_sha}",
                "",
                "Place both uncompressed BIGs in the SPECTER folder.",
                f"TAG={tag}",
                "RELEASE=https://github.com/sajadabedi941-lang/Specter-Patch/releases/tag/" + tag,
                "STATIC_VALIDATION=PASS",
                "RUNTIME_TEST=NOT RUN",
                "",
            ]
        )
    )
    (OUT / "README.txt").write_text(
        "Iran, America, and Israel missile-factory construction access only.\n"
        "Iran dozer slot 10 Bavar-373 entry replaced. USA and packed Israel Clear Mines\n"
        "slot 14 replaced. Bavar-373 system and Clear Mines definitions kept.\n"
        "No A-J missile rosters. ART unchanged from PR #651.\n"
        "Static validation only. The game was not launched.\n"
    )
    (OUT / "RELEASE_NOTES.md").write_text(
        "# Iran / USA / Israel missile factory construction buttons\n\n"
        "- IranDozerCommandSet slot 10: Bavar-373 construct -> Iran_MissileFactory.\n"
        "- AmericaDozerCommandSet slot 14: Clear Mines -> America_MissileFactory.\n"
        "- AirF_AmericaDozerCommandSet slot 14: Clear Mines -> Israel_MissileFactory.\n"
        "- Factories are Rally/Sell construction shells. No A-J rosters.\n"
        "- Bavar-373 objects and Clear Mines command definition preserved.\n"
        "- ART unchanged from PR #651. Static validation only. Not in-game tested.\n"
    )
    (OUT / "CONFLICTS.txt").write_text(
        "CommandSet_IranMissileFactory.ini last-wins IranDozerCommandSet.\n"
        "CommandSet_AmericaMissileFactory.ini last-wins AmericaDozerCommandSet.\n"
        "CommandSet_IsraelMissileFactory.ini last-wins AirF_AmericaDozerCommandSet.\n"
        "Command_ConstructIranBavarSiteAI and Command_DisarmMinesAtPosition definitions stay.\n"
        "IranHQCommandSet still has Command_ConstructIran_Bavar.\n"
        "FactionAmericaAirForceGeneral shares packed AirF_AmericaVehicleDozer / AirF_AmericaDozerCommandSet.\n"
        "China/Russia #651, Turkey/Spain #650, and earlier A-J factories stay frozen.\n"
    )
    print("PACKED")
    print(hashes)
    print("\n".join(report))


if __name__ == "__main__":
    main()
