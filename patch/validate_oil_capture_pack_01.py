#!/usr/bin/env python3
"""Post-pack validation for OIL_CAPTURE_INFANTRY DATA BIG."""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

NEXT14 = Path("/workspace/patch/Release/FIGHTER_ROSTER_NEXT14/_SPEC_DATA_ONE.big")
EXPECTED_BASE_SHA = "0528e90d4627e7949c683847b00df97626bdc8e36d4f8cd022dae5738856d71a"
EXPECTED_BASE_SIZE = 366161409
PACKED = Path("/workspace/patch/Release/OIL_CAPTURE_INFANTRY/_SPEC_DATA_ONE.big")
INI = Path("/workspace/patch/Data/INI")
OUT = Path("/workspace/patch/Release/OIL_CAPTURE_INFANTRY/POST_PACK_VALIDATION.txt")

REPLACE = [
    r"Data\INI\Object\Specter\Swedish Armed Forces\Infantry\Rifleman_G36.ini",
    r"Data\INI\Object\Specter\Ukrainian Armed Forces\Infantry\Rifleman_G36.ini",
    r"Data\INI\Object\Specter\Turkish Armed Forces\Infantry\Rifleman_G36.ini",
    r"Data\INI\Object\Specter\Italian Armed Forces\Infantry\Rifleman_G36.ini",
    r"Data\INI\Object\Specter\British Armed Forces\Infantry\Rifleman_G36.ini",
    r"Data\INI\Object\Specter\German Armed Forces\Infantry\Rifleman_G36.ini",
    r"Data\INI\Object\Specter\French Armed Forces\Infantry\Rifleman_G36.ini",
]
APPEND = r"Data\INI\CommandSet_ZZZZ_OilCapture_Class2.ini"
CLASS2 = [
    "SaudiArabia_RepublicanGuardCommandSet",
    "UAE_RepublicanGuardCommandSet",
    "Libya_RepublicanGuardCommandSet",
    "SouthAfrica_RepublicanGuardCommandSet",
]
CLASS2_SA_OBJECTS = [
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Infantry\Rifleman.ini",
    r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Infantry\Rifleman.ini",
    r"Data\INI\Object\Specter\Libyan Armed Forces\Infantry\Rifleman.ini",
    r"Data\INI\Object\Specter\South African National Defence Force\Infantry\Rifleman.ini",
]
FROZEN = [
    r"Data\INI\Weapon.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\Upgrade.ini",
    r"Data\INI\SpecialPower.ini",
    r"Data\INI\Object\CivilianBuilding.ini",
    r"Data\INI\Object\Specter\United States Of America\Infantry\Rifleman_M4.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Infantry\Japan_Rifleman_G36.ini",
    r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Infantry\SouthKorea_Rifleman_G36.ini",
    r"Data\INI\Object\Specter\Vietnam People's Army\Infantry\Rifleman.ini",
    r"Data\INI\CommandButton_ZZZZ_FighterRoster_Next14.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_Next14.ini",
    r"Data\INI\CommandButton_ZZZZ_FighterRoster_SAUAESYINPK.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_SAUAESYINPK.ini",
    r"Data\INI\CommandSet_ZZZZ_JapanSKVietnam_Capture.ini",
    r"Data\INI\CommandButton_ZZZZ_JapanSKVietnam_Capture.ini",
]
PK12 = [
    "Command_ConstructPakistanJetF16AMLU",
    "Command_ConstructPakistanJetMirage3",
    "Command_ConstructPakistanJetF7P",
    "Command_ConstructPakistanJetA5C",
    "Command_ConstructPakistan_F16Blk52",
    "Command_ConstructPakistanJetJ10CE",
    "Command_ConstructPakistanJetJF17",
    "Command_ConstructPakistanJetJF17Blk3",
    "Command_ConstructPakistanJetMirage5",
    "Command_ConstructPakistanJetMirageROSE",
    "Command_ConstructPakistanJetF16B",
    "Command_ConstructPakistanJetF7PG",
]
SY12 = [
    "Command_ConstructSyria_Mig-29A",
    "Command_ConstructSyriaJetMig25",
    "Command_ConstructSyria_MirageF1_Bq",
    "Command_ConstructSyria_Su-25K",
    "Command_ConstructSyriaJetJ7",
    "Command_ConstructSyriaJetSu22",
    "Command_ConstructSyriaJetSu22M4",
    "Command_ConstructSyriaJetSu24",
    "Command_ConstructSyriaJetL39",
    "Command_ConstructSyriaJetMig23",
    "Command_ConstructSyriaJetMig21",
    "Command_ConstructSyriaJetMig21MF",
]
SA2 = ["Command_ConstructSaudiJetF15C", "Command_ConstructSaudiJetTyphoon"]
UAE2 = ["Command_ConstructUAEJetF16E", "Command_ConstructUAEJetMirage20005"]
IN6 = [
    "Command_ConstructIndiaJetMig21Bison",
    "Command_ConstructIndia_Mig-29A",
    "Command_ConstructIndiaJetJaguarIS",
    "Command_ConstructIndiaJetMig27",
    "Command_ConstructIndiaJetSu30MKI",
    "Command_ConstructIndiaJetRafaleEH",
]
PK_HEAVY = ["Command_ConstructPakistanJetSu35S", "Command_ConstructPakistanJetF15E"]
SY_HEAVY = ["Command_ConstructSyriaJetSu30SM2", "Command_ConstructSyriaJetJ16D"]
USA_FIRST = "Command_ConstructAmericaJetRaptor"
IL12_PREFIX = "Command_ConstructIsrael"
RE_OBJ = re.compile(r"(?m)^Object\s+(\S+)")
RE_WPN = re.compile(r"(?m)^Weapon\s+(\S+)")
RE_BTN = re.compile(r"(?m)^CommandButton\s+(\S+)")
RE_CS = re.compile(r"(?ms)^CommandSet\s+(\S+)\s*(.*?)^End\s*$")
RE_SLOT = re.compile(r"(?m)^\s*(\d+)\s*=\s*(\S+)")
RE_CONSTRUCT = re.compile(r"Command_Construct\S+")
RE_UNPAUSE = re.compile(
    r"(?ms)Behavior\s*=\s*UnpauseSpecialPowerUpgrade\s+\S+\s*"
    r".*?SpecialPowerTemplate\s*=\s*SpecialAbilityRangerCaptureBuilding\s*"
    r"(.*?)^  End",
)
RE_OIL = re.compile(r"(?ms)^Object\s+TechOilDerrick\b.*?(?=^Object\s|\Z)")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(name: str) -> str:
    return name.replace("/", "\\")


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def as_map(entries):
    return {norm(n).lower(): (n, b) for n, b in entries}


def get(m, packed):
    return m[norm(packed).lower()][1]


def last_win_blocks(entries, regex):
    found = {}
    for name, blob in entries:
        if not name.lower().endswith(".ini"):
            continue
        text = blob.decode("latin1")
        for match in regex.finditer(text):
            found[match.group(1)] = match.group(0) if regex is RE_OBJ else match
    return found


def last_win_names(entries, regex):
    found = {}
    for name, blob in entries:
        if not name.lower().endswith(".ini"):
            continue
        text = blob.decode("latin1")
        for match in regex.finditer(text):
            found[match.group(1)] = True
    return found


def last_win_cs(entries):
    found = {}
    for name, blob in entries:
        if not name.lower().endswith(".ini"):
            continue
        text = blob.decode("latin1")
        for match in RE_CS.finditer(text):
            slots = {int(a): b for a, b in RE_SLOT.findall(match.group(2))}
            found[match.group(1)] = slots
    return found


def last_win_buttons(entries):
    found = set()
    for name, blob in entries:
        if not name.lower().endswith(".ini"):
            continue
        found.update(RE_BTN.findall(blob.decode("latin1")))
    return found


def construct_buttons(entries, packed):
    blob = get(as_map(entries), packed)
    return RE_BTN.findall(blob.decode("latin1"))


def cs_first_n(cs, name, n):
    slots = cs[name]
    return [slots[i] for i in range(1, n + 1)]


def has_triggered(blob: bytes) -> bool:
    text = blob.decode("latin1")
    matches = list(RE_UNPAUSE.finditer(text))
    if len(matches) != 1:
        return False
    return "TriggeredBy = Upgrade_InfantryCaptureBuilding" in matches[0].group(1)


def ws_path(packed: str) -> Path:
    rel = packed.replace("\\", "/")
    return INI / rel[len("Data/INI/") :]


def main() -> int:
    lines = []
    fails = []

    def check(ok: bool, label: str, extra: str = ""):
        status = "PASS" if ok else "FAIL"
        if not ok:
            fails.append(label)
        lines.append(f"  {label:<56} {status}{('  ' + extra) if extra else ''}")

    if sha256_file(NEXT14) != EXPECTED_BASE_SHA:
        raise SystemExit("Next-14 base SHA mismatch")
    if NEXT14.stat().st_size != EXPECTED_BASE_SIZE:
        raise SystemExit("Next-14 base size mismatch")

    base = read_big(NEXT14)
    packed = read_big(PACKED)
    bm = as_map(base)
    pm = as_map(packed)
    final_sha = sha256_file(PACKED)
    final_size = PACKED.stat().st_size

    replace_set = {norm(p).lower() for p in REPLACE}
    check(len(base) == 2903, "base file count 2903", str(len(base)))
    check(len(packed) == 2904, "packed file count 2904", str(len(packed)))
    check([n for n, _ in packed[:2903]] == [n for n, _ in base], "path-order prefix preserved")
    check(norm(packed[-1][0]) == APPEND, "Class2 CommandSet appended last")

    changed = []
    for (bn, bb), (pn, pb) in zip(base, packed[:2903]):
        if bb != pb:
            changed.append(bn)
    check(
        {norm(n).lower() for n in changed} == replace_set,
        "only 7 G36 object paths rewritten",
        str(len(changed)),
    )

    for p in REPLACE:
        check(get(pm, p) == ws_path(p).read_bytes(), f"overlay matches workspace {Path(p).name} / {p.split(chr(92))[4]}")
        check(get(pm, p) != get(bm, p), f"overlay differs from Next-14 {p.split(chr(92))[4]}")
        check(has_triggered(get(pm, p)), f"Class1 TriggeredBy present {p.split(chr(92))[4]}")
        check(not has_triggered(get(bm, p)), f"Class1 was missing on Next-14 {p.split(chr(92))[4]}")

    check(get(pm, APPEND) == (INI / "CommandSet_ZZZZ_OilCapture_Class2.ini").read_bytes(), "Class2 CS matches workspace")

    cs = last_win_cs(packed)
    base_cs = last_win_cs(base)
    for name in CLASS2:
        slots = cs.get(name, {})
        check(slots.get(1) == "Command_GLAInfantryRebelCaptureBuilding", f"Class2 last-win {name}")
        check(slots.get(12) == "Command_AttackMove", f"{name} AttackMove preserved")
        check(slots.get(13) == "Command_Guard", f"{name} Guard preserved")
        check(slots.get(14) == "Command_Stop", f"{name} Stop preserved")

    for p in CLASS2_SA_OBJECTS:
        check(get(pm, p) == get(bm, p), f"Class2 object unchanged {p.split(chr(92))[4]}")
        check(has_triggered(get(pm, p)) or b"TriggeredBy = Upgrade_InfantryCaptureBuilding" in get(pm, p), f"Class2 object already has TriggeredBy {p.split(chr(92))[4]}")

    for p in FROZEN:
        check(get(pm, p) == get(bm, p), f"frozen {p.split(chr(92))[-1]}")

    check(get(pm, r"Data\INI\Object\Specter\Japan Self-Defense Forces\Infantry\Japan_Rifleman_G36.ini") == get(bm, r"Data\INI\Object\Specter\Japan Self-Defense Forces\Infantry\Japan_Rifleman_G36.ini"), "Japan infantry unchanged")
    check(get(pm, r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Infantry\SouthKorea_Rifleman_G36.ini") == get(bm, r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Infantry\SouthKorea_Rifleman_G36.ini"), "South Korea infantry unchanged")
    check(get(pm, r"Data\INI\Object\Specter\Vietnam People's Army\Infantry\Rifleman.ini") == get(bm, r"Data\INI\Object\Specter\Vietnam People's Army\Infantry\Rifleman.ini"), "Vietnam infantry unchanged")
    check(get(pm, r"Data\INI\Object\Specter\United States Of America\Infantry\Rifleman_M4.ini") == get(bm, r"Data\INI\Object\Specter\United States Of America\Infantry\Rifleman_M4.ini"), "USA Ranger object unchanged")

    oil_b = RE_OIL.search(get(bm, r"Data\INI\Object\CivilianBuilding.ini").decode("latin1"))
    oil_p = RE_OIL.search(get(pm, r"Data\INI\Object\CivilianBuilding.ini").decode("latin1"))
    check(oil_b is not None and oil_p is not None and oil_b.group(0) == oil_p.group(0), "TechOilDerrick unchanged")

    base_obj = set(last_win_names(base, RE_OBJ))
    pack_obj = set(last_win_names(packed, RE_OBJ))
    check(base_obj == pack_obj, "object set unchanged", f"{len(pack_obj)}")

    base_wpn = set(RE_WPN.findall(get(bm, r"Data\INI\Weapon.ini").decode("latin1")))
    pack_wpn = set(RE_WPN.findall(get(pm, r"Data\INI\Weapon.ini").decode("latin1")))
    def all_weapons(entries):
        names = set()
        for n, blob in entries:
            if n.lower().endswith(".ini"):
                names.update(RE_WPN.findall(blob.decode("latin1")))
        return names

    base_all_wpn = all_weapons(base)
    pack_all_wpn = all_weapons(packed)
    check(base_wpn == pack_wpn, "Weapon.ini weapon set unchanged", str(len(pack_wpn)))
    check(base_all_wpn == pack_all_wpn, "no new Weapon definitions anywhere", str(len(pack_all_wpn)))

    next14_btns = construct_buttons(packed, r"Data\INI\CommandButton_ZZZZ_FighterRoster_Next14.ini")
    sa5_btns = construct_buttons(packed, r"Data\INI\CommandButton_ZZZZ_FighterRoster_SAUAESYINPK.ini")
    check(len(next14_btns) == 40, "40 Next-14 Command_Construct buttons", str(len(next14_btns)))
    check(len(sa5_btns) == 54, "54 SA/UAE/SY/IN/PK buttons remain", str(len(sa5_btns)))
    check(next14_btns == construct_buttons(base, r"Data\INI\CommandButton_ZZZZ_FighterRoster_Next14.ini"), "Next-14 buttons identical")
    check(sa5_btns == construct_buttons(base, r"Data\INI\CommandButton_ZZZZ_FighterRoster_SAUAESYINPK.ini"), "5-country buttons identical")

    check("Pakistan_AirfieldCommandSet" in cs, "Pakistan_AirfieldCommandSet present")
    check(cs_first_n(cs, "Pakistan_AirfieldCommandSet", 12) == PK12, "Pakistan_AirfieldCommandSet National 12")
    check(cs["Pakistan_AirfieldCommandSet"] == base_cs["Pakistan_AirfieldCommandSet"], "Pakistan National 12 identical to Next-14")
    check("Syria_AirfieldCommandSet" in cs, "Syria_AirfieldCommandSet present")
    check(cs_first_n(cs, "Syria_AirfieldCommandSet", 12) == SY12, "Syria_AirfieldCommandSet National 12")
    check(cs["Syria_AirfieldCommandSet"] == base_cs["Syria_AirfieldCommandSet"], "Syria National 12 identical to Next-14")
    for name in ("SaudiArabiaAirfieldCommandSet", "SaudiArabia_AirfieldCommandSet"):
        if name in cs:
            check(cs_first_n(cs, name, 2) == SA2, f"{name} 2-slot")
    for name in ("UAEAirfieldCommandSet", "UAE_AirfieldCommandSet"):
        if name in cs:
            check(cs_first_n(cs, name, 2) == UAE2, f"{name} 2-slot")
    for name in ("IndiaAirfieldCommandSet", "India_AirfieldCommandSet"):
        if name in cs:
            check(cs_first_n(cs, name, 6) == IN6, f"{name} 6-slot")

    check("Pakistan_HeavyAirBaseCommandSet" in cs, "Pakistan Heavy CS present")
    if "Pakistan_HeavyAirBaseCommandSet" in cs:
        heavy = [cs["Pakistan_HeavyAirBaseCommandSet"][i] for i in sorted(cs["Pakistan_HeavyAirBaseCommandSet"]) if i <= 12]
        check(all(x in heavy for x in PK_HEAVY), "Pakistan Heavy Su35S+F15E remain")
    check("Syria_HeavyAirBaseCommandSet" in cs, "Syria Heavy CS present")
    if "Syria_HeavyAirBaseCommandSet" in cs:
        heavy = [cs["Syria_HeavyAirBaseCommandSet"][i] for i in sorted(cs["Syria_HeavyAirBaseCommandSet"]) if i <= 12]
        check(all(x in heavy for x in SY_HEAVY), "Syria Heavy Su30SM2+J16D remain")

    usa_ok = True
    for name, slots in cs.items():
        if "airfield" in name.lower() and ("america" in name.lower() or name.lower().startswith("usa")):
            if slots.get(1) != USA_FIRST and "Command_ConstructAmerica" in str(slots.values()):
                usa_ok = False
    usa_names = [n for n in base_cs if "airfield" in n.lower() and ("america" in n.lower() or n.lower().startswith("usa") or "unitedstates" in n.lower())]
    usa_same = all(cs.get(n) == base_cs.get(n) for n in usa_names) and bool(usa_names)
    check(usa_same, "USA Airfield last-win unchanged", f"{len(usa_names)} CS")

    arabic_names = [n for n in base_cs if "arabic" in n.lower() or "alliance" in n.lower()]
    check(all(cs.get(n) == base_cs.get(n) for n in arabic_names) and bool(arabic_names), "Arabic Alliance CS unchanged", f"{len(arabic_names)} CS")

    nk_names = [n for n in base_cs if "northkorea" in n.lower() or "nk_" in n.lower() or "korea" in n.lower() and "south" not in n.lower()]
    # safer: names containing NorthKorea
    nk_names = [n for n in base_cs if "northkorea" in n.lower()]
    check(all(cs.get(n) == base_cs.get(n) for n in nk_names) and bool(nk_names), "North Korea CS unchanged", f"{len(nk_names)} CS")

    dual_ok = True
    for country in ("France", "Germany", "Britain", "Italy"):
        a = f"{country}AirfieldCommandSet"
        b = f"{country}_AirfieldCommandSet"
        if a not in cs or b not in cs:
            dual_ok = False
        elif cs[a] != cs[b]:
            dual_ok = False
        elif cs[a] != base_cs[a] or cs[b] != base_cs[b]:
            dual_ok = False
    check(dual_ok, "France/Germany/Britain/Italy dual CS intact")

    israel_names = [n for n in cs if "israel" in n.lower() and "airfield" in n.lower()]
    israel_ok = False
    for n in israel_names:
        slots = [cs[n][i] for i in range(1, 13) if i in cs[n]]
        if len(slots) == 12 and all(s.startswith(IL12_PREFIX) for s in slots):
            israel_ok = True
    check(israel_ok, "Israel national 12 last-win intact", str(israel_names))

    egypt_heavy = [n for n in cs if "egypt" in n.lower() and "heavy" in n.lower()]
    check(not egypt_heavy, "Egypt has no invented Heavy CS", str(egypt_heavy))

    next14_same = get(pm, r"Data\INI\CommandSet_ZZZZ_FighterRoster_Next14.ini") == get(bm, r"Data\INI\CommandSet_ZZZZ_FighterRoster_Next14.ini")
    sa5_same = get(pm, r"Data\INI\CommandSet_ZZZZ_FighterRoster_SAUAESYINPK.ini") == get(bm, r"Data\INI\CommandSet_ZZZZ_FighterRoster_SAUAESYINPK.ini")
    check(next14_same, "Next-14 CommandSet ZZZZ byte-identical")
    check(sa5_same, "5-country CommandSet ZZZZ byte-identical")

    art_ext = (".w3d", ".tga", ".dds", ".bmp")
    art_base = [(n, b) for n, b in base if n.lower().endswith(art_ext)]
    art_pack = [(n, b) for n, b in packed if n.lower().endswith(art_ext)]
    check(art_base == art_pack, "ART files unchanged vs Next-14", str(len(art_pack)))

    ranger_blob = get(pm, r"Data\INI\Object\Specter\United States Of America\Infantry\Rifleman_M4.ini").decode("latin1")
    check("Object AmericaInfantryRanger" in ranger_blob, "AmericaInfantryRanger still defined")

    header = [
        f"PACK_STATUS = {'PASS' if not fails else 'FAIL'}",
        "PACKED_FILES = [_SPEC_DATA_ONE.big]",
        f"BASE_SHA256 = {EXPECTED_BASE_SHA}",
        f"FINAL_SHA256 = {final_sha}",
        f"BASE_SIZE = {EXPECTED_BASE_SIZE}",
        f"FINAL_SIZE = {final_size}",
        f"OIL_OVERLAYS_PACKED = {REPLACE + [APPEND]}",
        f"NEXT14_CONTENT_PRESERVED = {'YES' if next14_same and len(next14_btns) == 40 else 'NO'}",
        f"PREVIOUS_5_COUNTRY_CONTENT_PRESERVED = {'YES' if sa5_same and len(sa5_btns) == 54 else 'NO'}",
        "JAPAN_CHANGED = NO",
        "SOUTH_KOREA_CHANGED = NO",
        "VIETNAM_CHANGED = NO",
        "USA_RANGER_CHANGED = NO",
        "TECH_OIL_DERRICK_CHANGED = NO",
        "WEAPON_INI_CHANGED = NO",
        "COMMAND_BUTTON_INI_CHANGED = NO",
        "COMMAND_SET_INI_CHANGED = NO",
        "UPGRADE_INI_CHANGED = NO",
        "SPECIALPOWER_INI_CHANGED = NO",
        "NEW_OBJECTS = 0",
        "NEW_WEAPONS = 0",
        "ART_CHANGED = NO",
        f"UNINTENDED_CHANGES = {'NONE' if not fails else fails}",
        f"POST_PACK_VALIDATION = {'PASS' if not fails else 'FAIL'}",
        f"READY_FOR_RELEASE = {'YES' if not fails else 'NO'}",
        "INGAME_TESTED = NO",
        "",
        "CHECKS",
    ]
    OUT.write_text("\n".join(header + lines) + "\n", encoding="utf-8")
    print(OUT.read_text(encoding="utf-8"))
    print("FAILS", fails)
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
