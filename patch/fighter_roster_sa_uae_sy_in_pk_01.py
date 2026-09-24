#!/usr/bin/env python3
"""FIGHTER_ROSTER_SA_UAE_SY_IN_PK — implement approved 2/2/6 plan.

Writes last-win CommandButton/CommandSet and rebinds only the five
countries' approved fighter Objects to existing donor/shared weapons.

Does NOT write a BIG. Does NOT modify Weapon.ini or unrelated factions.
"""
from __future__ import annotations

import re
import struct
from pathlib import Path

BIG = Path("/workspace/patch/Release/CAPTURE_BUILDING_FIX_STAGE_JAPAN_SOUTH_KOREA_VIETNAM/_SPEC_DATA_ONE.big")
ROOT = Path("/workspace/patch")
INI = ROOT / "Data" / "INI"

BTN_OUT = INI / "CommandButton_ZZZZ_FighterRoster_SAUAESYINPK.ini"
CS_OUT = INI / "CommandSet_ZZZZ_FighterRoster_SAUAESYINPK.ini"

# --- approved WeaponSet replacements (existing Weapon.ini names only) ---

WS_F15C_AA = """  WeaponSet
    Conditions = None
    Weapon            = PRIMARY   6x_MRAAM_AIM120C_F15C
    Weapon            = SECONDARY AN/APG63V3_AESA_Radar_AAMode
    Weapon            = TERTIARY  2x_AIM-9X
  End
"""

WS_F16_AA = """  WeaponSet
    Conditions = None
    Weapon            = PRIMARY   AIM-9X_F16C
    Weapon            = SECONDARY AN/APG68V9_AESA_Radar_AAMode
  End
"""

WS_AGM65_AT = """  WeaponSet
    Conditions = None
    Weapon              = PRIMARY    2x_AGM65F_F16CMB50
    PreferredAgainst    = PRIMARY    VEHICLE
    AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI
  End
"""

WS_KH29_AT = """  WeaponSet
    Conditions = None
    Weapon            = PRIMARY     2x_KH29L_AGM_F1EQ
    PreferredAgainst    = PRIMARY    VEHICLE STRUCTURE
    AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI
  End
"""

WS_HARM = """  WeaponSet
    Conditions = None
    Weapon            = PRIMARY    2x_AGM88G_AARGM-ER_F16CJ
  End
"""

WS_KH31 = """  WeaponSet
    Conditions = None
    Weapon              = PRIMARY    2x_ARM_KH31P_SU30SM2
  End
"""

WS_J10C = """  WeaponSet
    Conditions = None
    Weapon              = PRIMARY    3x_1000LB_LT3_PGM_J10C
  End
"""

WS_SU24 = """  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY     2x_TVG_Kab1500Kr_Su24M2
    Weapon            = SECONDARY   SVP-24_AMTS_SU24M2
  End
"""

WS_AURORA = """  WeaponSet
    Conditions = None
    Weapon              = PRIMARY    GBU_31V2_JDAM_F15E
  End
  WeaponSet
    Conditions = PLAYER_UPGRADE
    Weapon              = PRIMARY    GBU_31V2_JDAM_F15EX
    Weapon              = SECONDARY  AN/AAQ33_SniperXR_ATP_EX
    Weapon              = TERTIARY   AGM184H_K_ER_F15EX
  End
  WeaponSet
    Conditions          = WEAPON_RIDER2
    Weapon              = PRIMARY   AIM-120C_F15E
    Weapon              = SECONDARY AN/APG82_AESA_Radar_AAMode
    Weapon              = TERTIARY  2x_AIM-9X
  End
"""

WS_MIG29_AA = """  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY     4x_R27_MRBVR_Mig29A
  End
"""

WS_MIRAGE_F1_AT = """  WeaponSet
    Conditions        = None
    Weapon            = PRIMARY     2x_KH29L_AGM_F1EQ
  End
"""

WS_JF17 = """  WeaponSet
    Conditions = None
    Weapon              = PRIMARY    China_Weapon_LT2_JF17
    Weapon              = SECONDARY  China_Weapon_CM802_JF17
    Weapon              = TERTIARY   China_Weapon_MK82_JF17
  End
"""

WS_MIG35_STRIKE = """  WeaponSet
    Weapon              = PRIMARY    Kab500_LeaserGuidedBomb_Mig29k
  End
"""


def ws_keep_aa(primary: str, secondary: str | None = None) -> str:
    lines = [
        "  WeaponSet",
        "    Conditions = None",
        f"    Weapon              = PRIMARY    {primary}",
        "    PreferredAgainst    = PRIMARY    AIRCRAFT",
        "    AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI",
    ]
    if secondary:
        lines += [
            f"    Weapon              = SECONDARY  {secondary}",
            "    PreferredAgainst    = SECONDARY  AIRCRAFT",
            "    AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI",
        ]
    lines.append("  End\n")
    return "\n".join(lines)


def ws_strike(primary: str, secondary: str | None = None) -> str:
    lines = [
        "  WeaponSet",
        "    Conditions = None",
        f"    Weapon              = PRIMARY    {primary}",
        "    PreferredAgainst    = PRIMARY    VEHICLE STRUCTURE",
        "    AutoChooseSources   = PRIMARY    FROM_PLAYER FROM_SCRIPT FROM_AI",
    ]
    if secondary:
        lines += [
            f"    Weapon              = SECONDARY  {secondary}",
            "    PreferredAgainst    = SECONDARY  VEHICLE STRUCTURE",
            "    AutoChooseSources   = SECONDARY  FROM_PLAYER FROM_SCRIPT FROM_AI",
        ]
    lines.append("  End\n")
    return "\n".join(lines)


# object -> new WeaponSet text
REBINDS: dict[str, str] = {
    # Saudi
    "SaudiJetF15C": WS_F15C_AA,
    "SaudiJetTyphoon": ws_keep_aa("SaudiJetTyphoon_WpnRadar", "SaudiJetTyphoon_WpnIR"),
    "SaudiJetF15S": WS_AGM65_AT,
    "SaudiJetF5E": WS_AGM65_AT,
    "SaudiJetTornadoECR": WS_HARM,
    "SaudiJetTornadoIDS": ws_strike("GBU38_JDAM_F16C"),
    "SaudiJetF15EX": ws_strike("GBU_31V2_JDAM_F15E"),
    "SaudiJetF15SA": ws_strike("GBU_31V2_JDAM_F15E"),
    "SaudiJetTyphoonT3": ws_strike("Paveway_IV_EF2000"),
    "SaudiJetLightning": ws_strike("Kab2500_LeaserGuidedBomb"),
    "SaudiJetHawk65": ws_strike("Fab-250"),
    "SaudiJetTornadoADV": ws_strike("GBU-39_SDB_F22A"),
    # UAE
    "UAEJetF16E": WS_F16_AA,
    "UAEJetMirage20005": ws_keep_aa("UAEJetMirage20005_WpnRadar", "UAEJetMirage20005_WpnIR"),
    "UAEJetMirage2000DAD": WS_AGM65_AT,
    "UAEJetF15EA": WS_AGM65_AT,
    "UAEJetF15E": WS_AURORA,
    "UAEJetF16F": ws_strike("Kab500_LeaserGuidedBomb"),
    "UAEJetF16ECegy": ws_strike("6_MK-82"),
    "UAEJetMirage20009": ws_strike("Gbu-12II_Paveway"),
    "UAEJetMirage20009E": ws_strike("GBU38_JDAM_F16C"),
    "UAEJetF15SA": ws_strike("Fab-250"),
    "UAEJetHawk102": ws_strike("Kab2500_LeaserGuidedBomb"),
    # Syria
    "Syria_Mig-29A": WS_MIG29_AA,
    "SyriaJetMig25": ws_keep_aa("SyriaJetMig25_WpnRadar", "SyriaJetMig25_WpnIR"),
    "Syria_MirageF1_Bq": WS_MIRAGE_F1_AT,
    "SyriaJetSu22": ws_strike("Kab1500_LeaserGuidedBomb"),
    "SyriaJetSu22M4": ws_strike("ODAB_500_PMV_SU39"),
    "SyriaJetSu24": WS_SU24,
    "SyriaJetL39": ws_strike("GBU38_JDAM_F16C"),
    "SyriaJetMig23": ws_strike("GBU_31V2_JDAM_F15E"),
    "SyriaJetMig21": ws_strike("Kab500_LeaserGuidedBomb"),
    "SyriaJetMig21MF": ws_strike("6_MK-82"),
    # India
    "IndiaJetMig21Bison": ws_keep_aa("IndiaJetMig21Bison_WpnIR"),
    "India_Mig-29A": WS_MIG29_AA,
    "IndiaJetJaguarIS": WS_KH29_AT,
    "IndiaJetMig27": WS_KH29_AT,
    "IndiaJetSu30MKI": WS_KH31,
    "IndiaJetRafaleEH": ws_strike("Paveway_IV_EF2000"),
    "IndiaJetRafaleDH": ws_strike("AGM-154C_JSOW_F16C"),
    "IndiaJetMirage2000H": ws_strike("6_MK-82"),
    "IndiaJetMirage2000I": ws_strike("GBU38_JDAM_F16C"),
    "IndiaJetTejas": ws_strike("GBU-39_SDB_F22A"),
    "IndiaJetAMCA": ws_strike("Kab2500_LeaserGuidedBomb"),
    "IndiaJetMig29K": WS_MIG35_STRIKE,
    # Pakistan national 12
    "PakistanJetF16AMLU": WS_F16_AA,
    "PakistanJetMirage3": ws_keep_aa("PakistanJetMirage3_WpnRadar", "PakistanJetMirage3_WpnIR"),
    "PakistanJetF7P": WS_KH29_AT,
    "PakistanJetA5C": WS_KH29_AT,
    "PakistanJetJ10CE": WS_J10C,
    "PakistanJetJF17": WS_JF17,
    "PakistanJetJF17Blk3": WS_JF17,
    "PakistanJetMirage5": ws_strike("PakistanJetMirage5_WpnBomb", "PakistanJetMirage5_WpnStandoff"),
    "PakistanJetMirageROSE": ws_strike("PakistanJetMirageROSE_WpnBomb", "PakistanJetMirageROSE_WpnStandoff"),
    "PakistanJetF16B": ws_strike("PakistanJetF16B_WpnStrike"),
    "PakistanJetF7PG": ws_strike("3x_ODAB_500_PMV_SU24"),
}

# KEEP (do not rewrite Object): donor-MATCH or Iraq-chain already correct
KEEP_OBJECTS = {
    "UAE_F16Blk52",
    "Pakistan_F16Blk52",
    "SyriaJetJ7",
    "Syria_Su-25K",
    "SyriaJetSu30SM2",
    "SyriaJetJ16D",
    "PakistanJetSu35S",
    "PakistanJetF15E",
}

AIRFIELD = {
    "SaudiArabia": [
        ("Command_ConstructSaudiJetF15C", "SaudiJetF15C"),
        ("Command_ConstructSaudiJetTyphoon", "SaudiJetTyphoon"),
        ("Command_ConstructSaudiJetF15S", "SaudiJetF15S"),
        ("Command_ConstructSaudiJetF5E", "SaudiJetF5E"),
        ("Command_ConstructSaudiJetTornadoECR", "SaudiJetTornadoECR"),
        ("Command_ConstructSaudiJetTornadoIDS", "SaudiJetTornadoIDS"),
        ("Command_ConstructSaudiJetF15EX", "SaudiJetF15EX"),
        ("Command_ConstructSaudiJetF15SA", "SaudiJetF15SA"),
        ("Command_ConstructSaudiJetTyphoonT3", "SaudiJetTyphoonT3"),
        ("Command_ConstructSaudiJetLightning", "SaudiJetLightning"),
        ("Command_ConstructSaudiJetHawk65", "SaudiJetHawk65"),
        ("Command_ConstructSaudiJetTornadoADV", "SaudiJetTornadoADV"),
    ],
    "UAE": [
        ("Command_ConstructUAEJetF16E", "UAEJetF16E"),
        ("Command_ConstructUAEJetMirage20005", "UAEJetMirage20005"),
        ("Command_ConstructUAEJetMirage2000DAD", "UAEJetMirage2000DAD"),
        ("Command_ConstructUAEJetF15EA", "UAEJetF15EA"),
        ("Command_ConstructUAE_F16Blk52", "UAE_F16Blk52"),
        ("Command_ConstructUAEJetF15E", "UAEJetF15E"),
        ("Command_ConstructUAEJetF16F", "UAEJetF16F"),
        ("Command_ConstructUAEJetF16ECegy", "UAEJetF16ECegy"),
        ("Command_ConstructUAEJetMirage20009", "UAEJetMirage20009"),
        ("Command_ConstructUAEJetMirage20009E", "UAEJetMirage20009E"),
        ("Command_ConstructUAEJetF15SA", "UAEJetF15SA"),
        ("Command_ConstructUAEJetHawk102", "UAEJetHawk102"),
    ],
    "Syria": [
        ("Command_ConstructSyria_Mig-29A", "Syria_Mig-29A"),
        ("Command_ConstructSyriaJetMig25", "SyriaJetMig25"),
        ("Command_ConstructSyria_MirageF1_Bq", "Syria_MirageF1_Bq"),
        ("Command_ConstructSyria_Su-25K", "Syria_Su-25K"),
        ("Command_ConstructSyriaJetJ7", "SyriaJetJ7"),
        ("Command_ConstructSyriaJetSu22", "SyriaJetSu22"),
        ("Command_ConstructSyriaJetSu22M4", "SyriaJetSu22M4"),
        ("Command_ConstructSyriaJetSu24", "SyriaJetSu24"),
        ("Command_ConstructSyriaJetL39", "SyriaJetL39"),
        ("Command_ConstructSyriaJetMig23", "SyriaJetMig23"),
        ("Command_ConstructSyriaJetMig21", "SyriaJetMig21"),
        ("Command_ConstructSyriaJetMig21MF", "SyriaJetMig21MF"),
    ],
    "India": [
        ("Command_ConstructIndiaJetMig21Bison", "IndiaJetMig21Bison"),
        ("Command_ConstructIndia_Mig-29A", "India_Mig-29A"),
        ("Command_ConstructIndiaJetJaguarIS", "IndiaJetJaguarIS"),
        ("Command_ConstructIndiaJetMig27", "IndiaJetMig27"),
        ("Command_ConstructIndiaJetSu30MKI", "IndiaJetSu30MKI"),
        ("Command_ConstructIndiaJetRafaleEH", "IndiaJetRafaleEH"),
        ("Command_ConstructIndiaJetRafaleDH", "IndiaJetRafaleDH"),
        ("Command_ConstructIndiaJetMirage2000H", "IndiaJetMirage2000H"),
        ("Command_ConstructIndiaJetMirage2000I", "IndiaJetMirage2000I"),
        ("Command_ConstructIndiaJetTejas", "IndiaJetTejas"),
        ("Command_ConstructIndiaJetAMCA", "IndiaJetAMCA"),
        ("Command_ConstructIndiaJetMig29K", "IndiaJetMig29K"),
    ],
    "Pakistan": [
        ("Command_ConstructPakistanJetF16AMLU", "PakistanJetF16AMLU"),
        ("Command_ConstructPakistanJetMirage3", "PakistanJetMirage3"),
        ("Command_ConstructPakistanJetF7P", "PakistanJetF7P"),
        ("Command_ConstructPakistanJetA5C", "PakistanJetA5C"),
        ("Command_ConstructPakistan_F16Blk52", "Pakistan_F16Blk52"),
        ("Command_ConstructPakistanJetJ10CE", "PakistanJetJ10CE"),
        ("Command_ConstructPakistanJetJF17", "PakistanJetJF17"),
        ("Command_ConstructPakistanJetJF17Blk3", "PakistanJetJF17Blk3"),
        ("Command_ConstructPakistanJetMirage5", "PakistanJetMirage5"),
        ("Command_ConstructPakistanJetMirageROSE", "PakistanJetMirageROSE"),
        ("Command_ConstructPakistanJetF16B", "PakistanJetF16B"),
        ("Command_ConstructPakistanJetF7PG", "PakistanJetF7PG"),
    ],
}

EXISTING_BUTTONS = {
    "Command_ConstructUAE_F16Blk52",
    "Command_ConstructSyria_Mig-29A",
    "Command_ConstructSyria_MirageF1_Bq",
    "Command_ConstructSyria_Su-25K",
    "Command_ConstructIndia_Mig-29A",
    "Command_ConstructPakistan_F16Blk52",
}


def read_big(path: Path):
    data = path.read_bytes()
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def first_val(body: str, key: str):
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(\S+)", body)
    return m.group(1) if m else None


def replace_weaponsets(body: str, new_ws: str) -> str:
    m = re.search(r"(?im)^\s*WeaponSet\b", body)
    if not m:
        raise SystemExit("WeaponSet missing")
    rest = body[m.start() :]
    armor = re.search(r"(?im)^\s*ArmorSet\b", rest)
    if not armor:
        raise SystemExit("ArmorSet missing after WeaponSet")
    return body[: m.start()] + new_ws.rstrip() + "\n\n" + rest[armor.start() :]


def big_path_to_ws(packed: str) -> Path:
    rel = packed.replace("\\", "/")
    if rel.lower().startswith("data/"):
        rel = rel[5:]
    return INI / rel[len("INI/") :] if rel.startswith("INI/") else ROOT / rel


def main() -> int:
    entries = read_big(BIG)
    file_by_name = {n.replace("/", "\\"): b for n, b in entries}

    OBJ_RE = re.compile(r"(?m)^Object\s+(\S+)\s*\n(.*?)(?=^Object\s|\Z)", re.S)
    WPN_RE = re.compile(r"(?m)^Weapon\s+(\S+)\s*\n", re.S)
    BTN_RE = re.compile(r"(?m)^CommandButton\s+(\S+)\s*\n", re.S)

    obj_src: dict[str, str] = {}
    obj_body: dict[str, str] = {}
    obj_file: dict[str, bytes] = {}
    weapons: set[str] = set()
    live_buttons: set[str] = set()

    for n, b in entries:
        t = b.decode("latin1", errors="replace").replace("\r\n", "\n")
        if n.lower().endswith(".ini") and ("commandbutton" in n.lower()):
            live_buttons.update(BTN_RE.findall(t))
        if n.lower().endswith(".ini"):
            for m in WPN_RE.finditer(t):
                weapons.add(m.group(1))
            if "Object " in t:
                for m in OBJ_RE.finditer(t):
                    obj_src[m.group(1)] = n
                    obj_body[m.group(1)] = m.group(2)
                    obj_file[m.group(1)] = b

    # sanity: every rebound weapon exists
    needed = set()
    for ws in REBINDS.values():
        needed.update(re.findall(r"Weapon\s*=\s*(?:PRIMARY|SECONDARY|TERTIARY)\s+(\S+)", ws))
    missing_w = sorted(w for w in needed if w not in weapons)
    if missing_w:
        raise SystemExit(f"missing weapons in live BIG: {missing_w}")

    written: list[str] = []

    # write rebound object files (extract whole packed file, replace WS of that object)
    for obj, ws in REBINDS.items():
        if obj not in obj_src:
            raise SystemExit(f"object missing from BIG: {obj}")
        packed = obj_src[obj]
        raw = file_by_name[packed.replace("/", "\\")].decode("latin1").replace("\r\n", "\n")
        # file may be single-object; replace WS inside this object only
        om = re.search(rf"(?m)^Object {re.escape(obj)}\b\n(.*?)(?=^Object |\Z)", raw, re.S)
        if not om:
            raise SystemExit(f"cannot isolate {obj} in {packed}")
        new_body = replace_weaponsets(om.group(1), ws)
        new_raw = raw[: om.start()] + f"Object {obj}\n" + new_body
        dest = big_path_to_ws(packed)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(new_raw.replace("\n", "\r\n"), encoding="latin1", newline="")
        written.append(str(dest.relative_to(ROOT)))

    # CommandButtons for missing construct buttons only
    btn_lines = [
        "; FIGHTER_ROSTER_SA_UAE_SY_IN_PK missing UNIT_BUILD buttons\n",
        "; Last-win append. Does not rewrite CommandButton.ini\n\n",
    ]
    all_btns = []
    for country, slots in AIRFIELD.items():
        for btn, obj in slots:
            all_btns.append((btn, obj))
            if btn in EXISTING_BUTTONS or btn in live_buttons:
                continue
            if obj not in obj_body:
                raise SystemExit(f"button object missing: {obj}")
            image = first_val(obj_body[obj], "ButtonImage") or first_val(obj_body[obj], "SelectPortrait") or "us_airfield"
            btn_lines.append(
                f"CommandButton {btn}\n"
                f"  Command          = UNIT_BUILD\n"
                f"  Object           = {obj}\n"
                f"  TextLabel        = CONTROLBAR:Construct{obj}\n"
                f"  ButtonImage      = {image}\n"
                f"  ButtonBorderType = BUILD\n"
                f"  DescriptLabel    = CONTROLBAR:ToolTipConstruct{obj}\n"
                f"End\n\n"
            )
    BTN_OUT.write_text("".join(btn_lines).replace("\n", "\r\n"), encoding="latin1", newline="")
    written.append(str(BTN_OUT.relative_to(ROOT)))

    # CommandSets last-win airfield + numbered variants only
    cs_lines = [
        "; FIGHTER_ROSTER_SA_UAE_SY_IN_PK last-win airfield CommandSets\n",
        "; 2 A2A / 2 AT / 6 strike + 2 overflow. Pakistan = national 12.\n",
        "; HeavyAirBase CommandSets are NOT touched.\n\n",
    ]
    for country, slots in AIRFIELD.items():
        names = [f"{country}_AirfieldCommandSet"] + [f"{country}_AirfieldCommandSet{i}" for i in (1, 2, 3)]
        for cs_name in names:
            cs_lines.append(f"CommandSet {cs_name}\n")
            for i, (btn, _obj) in enumerate(slots, start=1):
                cs_lines.append(f"  {i} = {btn}\n")
            cs_lines.append("  13 = Command_SetRallyPoint\n")
            cs_lines.append("  14 = Command_Sell\n")
            cs_lines.append("End\n\n")
    CS_OUT.write_text("".join(cs_lines).replace("\n", "\r\n"), encoding="latin1", newline="")
    written.append(str(CS_OUT.relative_to(ROOT)))

    print("WROTE", len(written), "files")
    for p in written:
        print(" ", p)
    print("REBIND_OBJECTS", len(REBINDS))
    print("KEEP_OBJECTS", sorted(KEEP_OBJECTS))
    print("NEEDED_WEAPONS", len(needed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
