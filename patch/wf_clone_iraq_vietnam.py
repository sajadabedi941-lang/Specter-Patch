#!/usr/bin/env python3
"""Clone Iraq/Vietnam WarFactory onto listed factions.

Baseline: SPECTER1_WF_CAMP_UPGRADE_UNLOCK (PR #505 + unlock).
Group 1 (Iraq donor): UAE, Syria, Saudi Arabia, Libya, South Africa.
Group 2 (Vietnam donor): South Korea, Japan, India, Pakistan.

Only WarFactory object INIs and those factions' WarFactory CommandSets.
Camp / MIC / Strategy / CommandCenter / other systems untouched.
ART / Weapon.ini / Upgrade.ini / models unchanged.
Same two BIG names and ZIP-root layout as PR #505.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_WF_CAMP_UPGRADE_UNLOCK/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_WF_CAMP_UPGRADE_UNLOCK/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "cc5e21aafe25c2d9be3e77ee3f4235abd05b25dbf0a72d471a49d8d734899217"
EXPECTED_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"
OUT_DIR = Path("/tmp/SPECTER1_WF_CLONE_IRAQ_VIETNAM")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_WF_CLONE_IRAQ_VIETNAM")

P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_WEAPON = r"Data\INI\Weapon.ini"
P_UPGRADE = r"Data\INI\Upgrade.ini"

IRAQ_WF = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_WarFactory.ini"
VN_WF = r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_WarFactory.ini"
IRAQ_CS = "Iraq_WarFactoryCommandSet_T3"
VN_CS = "Vietnam_WarFactoryCommandSet"

# Identity fields kept so dozers / faction CommandButtons / file paths stay valid.
GROUP1 = [
    {
        "name": "UAE",
        "path": r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_WarFactory.ini",
        "object": "UAE_WarFactory_T",
        "side": "UAE",
        "cs": "UAE_WarFactoryCommandSet",
        "prereq": "UAE_SupplyCenter",
        "construct": "Command_ConstructUAE_WarFactory_T",
    },
    {
        "name": "Syria",
        "path": r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_WarFactory.ini",
        "object": "Syria_WarFactory_T",
        "side": "Syria",
        "cs": "Syria_WarFactoryCommandSet",
        "prereq": "Syria_SupplyCenter",
        "construct": "Command_ConstructSyria_WarFactory_T",
    },
    {
        "name": "Saudi Arabia",
        "path": r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_WarFactory.ini",
        "object": "SaudiArabia_WarFactory_T",
        "side": "SaudiArabia",
        "cs": "SaudiArabia_WarFactoryCommandSet",
        "prereq": "SaudiArabia_SupplyCenter",
        "construct": "Command_ConstructSaudiArabia_WarFactory_T",
    },
    {
        "name": "Libya",
        "path": r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_WarFactory.ini",
        "object": "Libya_WarFactory_T",
        "side": "Libya",
        "cs": "Libya_WarFactoryCommandSet",
        "prereq": "Libya_SupplyCenter",
        "construct": "Command_ConstructLibya_WarFactory_T",
    },
    {
        "name": "South Africa",
        "path": r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_WarFactory.ini",
        "object": "SouthAfrica_WarFactory_T",
        "side": "SouthAfrica",
        "cs": "SouthAfrica_WarFactoryCommandSet",
        "prereq": "SouthAfrica_SupplyCenter",
        "construct": "Command_ConstructSouthAfrica_WarFactory_T",
    },
]

GROUP2 = [
    {
        "name": "South Korea",
        "path": r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\SouthKorea_WarFactory.ini",
        "object": "SouthKorea_WarFactory",
        "side": "SouthKorea",
        "cs": "SouthKorea_WarFactoryCommandSet",
        "prereq": "SouthKorea_SupplyCenter",
        "construct": "Command_ConstructSouthKorea_WarFactory",
    },
    {
        "name": "Japan",
        "path": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_WarFactory.ini",
        "object": "Japan_WarFactory",
        "side": "Japan",
        "cs": "Japan_WarFactoryCommandSet",
        "prereq": "Japan_SupplyCenter",
        "construct": "Command_ConstructJapan_WarFactory",
    },
    {
        "name": "India",
        "path": r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_WarFactory.ini",
        "object": "India_WarFactory_T",
        "side": "India",
        "cs": "India_WarFactoryCommandSet",
        "prereq": "India_SupplyCenter",
        "construct": "Command_ConstructIndia_WarFactory_T",
    },
    {
        "name": "Pakistan",
        "path": r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_WarFactory.ini",
        "object": "Pakistan_WarFactory_T",
        "side": "Pakistan",
        "cs": "Pakistan_WarFactoryCommandSet",
        "prereq": "Pakistan_SupplyCenter",
        "construct": "Command_ConstructPakistan_WarFactory_T",
    },
]

PROTECTED_WF = {
    IRAQ_WF,
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_WarFactory_AI.ini",
    r"Data\INI\Object\Specter\Iraq Army\AI\Iraq_WarFactory.ini",
    VN_WF,
}

SKIP_SYSTEM_RX = re.compile(
    r"(?i)(barracks|commandcenter|command_center|_mic\.ini|strategy|camp)",
)


def object_names(text: str) -> list[str]:
    return re.findall(r"(?im)^Object\s+(\S+)", text)


def field_of(text: str, key: str) -> str | None:
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(\S+)", text)
    return m.group(1) if m else None


def prereq_object(text: str) -> str | None:
    m = re.search(r"(?ims)^\s*Prerequisites\b(.*?)^\s*End", text)
    if not m:
        return None
    m2 = re.search(r"(?im)^\s*Object\s*=\s*(\S+)", m.group(1))
    return m2.group(1) if m2 else None


def display_name(text: str) -> str:
    return field_of(text, "DisplayName") or "OBJECT:WarFactory"


def cs_slot_lines(css: dict[str, str], name: str) -> list[str]:
    body = css.get(name)
    if not body:
        raise SystemExit(f"missing CommandSet {name}")
    lines = []
    for line in body.splitlines():
        if re.match(r"(?i)^\s*\d+\s*=", line):
            lines.append(line.rstrip())
    if not lines:
        raise SystemExit(f"no slots in {name}")
    return lines


def related_commandsets(css: dict[str, str], primary: str) -> list[str]:
    hits = [primary]
    for name in css:
        if name == primary:
            continue
        if name.startswith(primary) and re.match(
            rf"^{re.escape(primary)}\d+$", name
        ):
            hits.append(name)
    return hits


def adapt_donor(
    donor: str,
    src_object: str,
    dest: dict,
    dest_display: str,
) -> str:
    text = donor
    n, err = re.subn(
        rf"(?im)^Object\s+{re.escape(src_object)}\s*$",
        f"Object {dest['object']}",
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"{dest['name']}: object rename failed ({n})")
    text = err
    n, text = _sub_count(text, r"(?im)^(\s*Side\s*=\s*)\S+", rf"\g<1>{dest['side']}")
    if n != 1:
        raise SystemExit(f"{dest['name']}: Side replace {n}")
    n, text = _sub_count(
        text, r"(?im)^(\s*CommandSet\s*=\s*)\S+", rf"\g<1>{dest['cs']}"
    )
    if n != 1:
        raise SystemExit(f"{dest['name']}: CommandSet replace {n}")
    n, text = _sub_count(
        text, r"(?im)^(\s*DisplayName\s*=\s*)\S+", rf"\g<1>{dest_display}"
    )
    if n != 1:
        raise SystemExit(f"{dest['name']}: DisplayName replace {n}")

    def repl_prereq(m: re.Match[str]) -> str:
        block = m.group(0)
        nb, block = _sub_count(
            block, r"(?im)^(\s*Object\s*=\s*)\S+", rf"\g<1>{dest['prereq']}"
        )
        if nb != 1:
            raise SystemExit(f"{dest['name']}: prereq Object replace {nb}")
        return block

    text, n = re.subn(
        r"(?ims)^\s*Prerequisites\b.*?^\s*End",
        repl_prereq,
        text,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"{dest['name']}: Prerequisites block replace {n}")

    header = (
        f"; SPECTER - {dest['name']} WarFactory "
        f"({dest.get('donor_label', 'donor')} clone)\n"
        "; Existing WarFactory object replaced. Object name, Side, CommandSet\n"
        "; name, Prerequisites, and packed path kept for faction identity.\n"
        "; Camp / MIC / Strategy / other systems not modified.\n\n"
    )
    # Drop the donor file header; keep the Object block.
    m = re.search(r"(?im)^Object\s+", text)
    if not m:
        raise SystemExit(f"{dest['name']}: missing Object after adapt")
    return header + text[m.start() :]


def _sub_count(text: str, rx: str, repl: str) -> tuple[int, str]:
    new, n = re.subn(rx, repl, text, count=1)
    return n, new


def collect_objects(entries) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for name, raw in entries:
        n = jf.norm(name)
        if not n.lower().endswith(".ini"):
            continue
        t = raw.decode("latin-1", errors="replace")
        for obj in object_names(t):
            out.setdefault(obj, []).append(n)
    return out


def system_paths(entries) -> list[str]:
    hits = []
    for name, _ in entries:
        n = jf.norm(name)
        if SKIP_SYSTEM_RX.search(n):
            hits.append(n)
    return hits


def button_object(btns: dict[str, str], name: str) -> str | None:
    body = btns.get(name)
    if not body:
        return None
    m = re.search(r"(?im)^\s*Object\s*=\s*(\S+)", body)
    return m.group(1) if m else None


def main() -> int:
    if jf.sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("source DATA SHA mismatch")
    if jf.sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("source ART SHA mismatch")

    entries = jf.read_big_list(SRC_DATA)
    art_entries = jf.read_big_list(SRC_ART)
    if len(entries) != 2880 or len(art_entries) != 4432:
        raise SystemExit(f"packed count {len(entries)}/{len(art_entries)}")

    src_objs = collect_objects(entries)
    src_sys = {p: jf.raw_of(entries, p) for p in system_paths(entries)}
    src_iraq = jf.raw_of(entries, IRAQ_WF)
    src_vn = jf.raw_of(entries, VN_WF)
    src_weapon = jf.raw_of(entries, P_WEAPON)
    src_upgrade = jf.raw_of(entries, P_UPGRADE)
    src_btn = jf.raw_of(entries, P_CMDBTN)

    cmd = jf.text_of(entries, P_CMDSET)
    css = jf.parse_commandsets(cmd)
    iraq_slots = cs_slot_lines(css, IRAQ_CS)
    vn_slots = cs_slot_lines(css, VN_CS)
    iraq_donor = jf.text_of(entries, IRAQ_WF)
    vn_donor = jf.text_of(entries, VN_WF)
    src_obj_name_iraq = object_names(iraq_donor)[0]
    src_obj_name_vn = object_names(vn_donor)[0]
    if src_obj_name_iraq != "Iraq_WarFactory_T":
        raise SystemExit(f"unexpected Iraq WF object {src_obj_name_iraq}")
    if src_obj_name_vn != "Vietnam_WarFactory":
        raise SystemExit(f"unexpected Vietnam WF object {src_obj_name_vn}")

    dest_meta = []
    for dest in GROUP1:
        dest = dict(dest)
        dest["donor_label"] = "Iraq"
        dest["donor_cs"] = IRAQ_CS
        dest["slots"] = iraq_slots
        dest["donor_obj"] = src_obj_name_iraq
        dest_meta.append((dest, iraq_donor))
    for dest in GROUP2:
        dest = dict(dest)
        dest["donor_label"] = "Vietnam"
        dest["donor_cs"] = VN_CS
        dest["slots"] = vn_slots
        dest["donor_obj"] = src_obj_name_vn
        dest_meta.append((dest, vn_donor))

    btns = jf.parse_buttons(jf.text_of(entries, P_CMDBTN))
    for dest, _donor in dest_meta:
        old = jf.text_of(entries, dest["path"])
        objs = object_names(old)
        if dest["object"] not in objs:
            raise SystemExit(f"{dest['name']}: expected object {dest['object']} in {objs}")
        if field_of(old, "Side") != dest["side"]:
            raise SystemExit(f"{dest['name']}: Side {field_of(old, 'Side')}")
        if field_of(old, "CommandSet") != dest["cs"]:
            raise SystemExit(f"{dest['name']}: CS {field_of(old, 'CommandSet')}")
        if prereq_object(old) != dest["prereq"]:
            raise SystemExit(f"{dest['name']}: prereq {prereq_object(old)}")
        dest["display"] = display_name(old)
        dest["old_cs_slots"] = cs_slot_lines(css, dest["cs"])
        if dest["construct"] not in btns:
            raise SystemExit(f"missing construct button {dest['construct']}")
        if button_object(btns, dest["construct"]) != dest["object"]:
            raise SystemExit(
                f"{dest['construct']} -> {button_object(btns, dest['construct'])}"
            )
        dest["related_cs"] = related_commandsets(css, dest["cs"])

    # Replace target WF objects with adapted donor content.
    for dest, donor in dest_meta:
        new_text = adapt_donor(donor, dest["donor_obj"], dest, dest["display"])
        if dest["object"] not in object_names(new_text):
            raise SystemExit(f"{dest['name']}: adapted file missing {dest['object']}")
        if object_names(new_text) != [dest["object"]]:
            raise SystemExit(f"{dest['name']}: extra objects {object_names(new_text)}")
        if field_of(new_text, "Side") != dest["side"]:
            raise SystemExit(f"{dest['name']}: adapted Side wrong")
        if field_of(new_text, "CommandSet") != dest["cs"]:
            raise SystemExit(f"{dest['name']}: adapted CS wrong")
        if prereq_object(new_text) != dest["prereq"]:
            raise SystemExit(f"{dest['name']}: adapted prereq wrong")
        if re.search(r"(?im)^\s*Behavior\s*=\s*CommandSetUpgrade\b", new_text):
            raise SystemExit(f"{dest['name']}: leftover CommandSetUpgrade")
        jf.set_text(entries, dest["path"], new_text)

    # Replace target WarFactory CommandSets (primary + leftover 1/2/3) with donor slots.
    cmd_new = jf.text_of(entries, P_CMDSET)
    for dest, _donor in dest_meta:
        for csname in dest["related_cs"]:
            cmd_new = jf.replace_commandset(cmd_new, csname, dest["slots"])
    jf.set_text(entries, P_CMDSET, cmd_new)

    # ---- validation ----
    if len(entries) != 2880:
        raise SystemExit(f"DATA packed changed {len(entries)}")
    if jf.raw_of(entries, IRAQ_WF) != src_iraq:
        raise SystemExit("Iraq WF file was modified")
    if jf.raw_of(entries, VN_WF) != src_vn:
        raise SystemExit("Vietnam WF file was modified")
    if jf.raw_of(entries, P_WEAPON) != src_weapon:
        raise SystemExit("Weapon.ini changed")
    if jf.raw_of(entries, P_UPGRADE) != src_upgrade:
        raise SystemExit("Upgrade.ini changed")
    if jf.raw_of(entries, P_CMDBTN) != src_btn:
        raise SystemExit("CommandButton.ini changed")
    for p, raw in src_sys.items():
        if jf.raw_of(entries, p) != raw:
            raise SystemExit(f"system file changed: {p}")

    names = [jf.norm(n).lower() for n, _ in entries]
    if len(names) != len(set(names)):
        raise SystemExit("duplicate packed DATA paths")
    if any(n.startswith("art\\") for n in names):
        raise SystemExit("ART leaked into DATA")
    if not any(n.startswith("data\\ini\\") for n in names):
        raise SystemExit("DATA missing Data\\INI")

    new_objs = collect_objects(entries)
    introduced = []
    for obj, paths in new_objs.items():
        if obj not in src_objs:
            introduced.append(obj)
    if introduced:
        raise SystemExit(f"new object names: {introduced}")
    for dest, _ in dest_meta:
        if dest["object"] not in new_objs:
            raise SystemExit(f"lost object {dest['object']}")

    css2 = jf.parse_commandsets(jf.text_of(entries, P_CMDSET))
    btns2 = jf.parse_buttons(jf.text_of(entries, P_CMDBTN))
    broken = []
    for dest, _ in dest_meta:
        slots = cs_slot_lines(css2, dest["cs"])
        if [re.sub(r"\s+", " ", s).strip() for s in slots] != [
            re.sub(r"\s+", " ", s).strip() for s in dest["slots"]
        ]:
            # compare button names only
            got = [re.search(r"=\s*(\S+)", s).group(1) for s in slots]
            exp = [re.search(r"=\s*(\S+)", s).group(1) for s in dest["slots"]]
            if got != exp:
                broken.append(f"{dest['name']} CS slots {got} != {exp}")
        for line in slots:
            btn = re.search(r"=\s*(\S+)", line).group(1)
            if btn not in btns2:
                broken.append(f"{dest['name']} missing button {btn}")
        t = jf.text_of(entries, dest["path"])
        if field_of(t, "Side") != dest["side"]:
            broken.append(f"{dest['name']} Side")
        if field_of(t, "CommandSet") != dest["cs"]:
            broken.append(f"{dest['name']} CS ref")
        if prereq_object(t) != dest["prereq"]:
            broken.append(f"{dest['name']} prereq")
        if dest["prereq"] not in new_objs:
            broken.append(f"{dest['name']} missing {dest['prereq']}")
        if dest["cs"] not in css2:
            broken.append(f"{dest['name']} missing CS def")
        if button_object(btns2, dest["construct"]) != dest["object"]:
            broken.append(f"{dest['construct']} broken")
        if dest["object"] not in new_objs:
            broken.append(f"{dest['name']} object missing")
    if broken:
        raise SystemExit("broken refs:\n  " + "\n  ".join(broken))

    # Donor files and other WF paths unchanged except the 9 targets.
    target_paths = {d["path"] for d, _ in dest_meta}
    src_entries = jf.read_big_list(SRC_DATA)
    src_map = {jf.norm(n).lower(): b for n, b in src_entries}
    for name, raw in entries:
        n = jf.norm(name)
        if n.lower() == jf.norm(P_CMDSET).lower():
            continue
        if n in target_paths or n.lower() in {jf.norm(p).lower() for p in target_paths}:
            continue
        if src_map.get(n.lower()) != raw:
            raise SystemExit(f"unexpected DATA change: {n}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    data_bytes = jf.build_big_ordered(entries)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_bytes)
    shutil.copy2(SRC_ART, OUT_DIR / "_SPEC_ART_ONE.big")
    shutil.copy2(OUT_DIR / "_SPEC_DATA_ONE.big", WS_OUT / "_SPEC_DATA_ONE.big")
    shutil.copy2(OUT_DIR / "_SPEC_ART_ONE.big", WS_OUT / "_SPEC_ART_ONE.big")
    new_sha = jf.sha256_file(WS_OUT / "_SPEC_DATA_ONE.big")
    art_sha = jf.sha256_file(WS_OUT / "_SPEC_ART_ONE.big")
    if art_sha != EXPECTED_ART_SHA:
        raise SystemExit("packed ART SHA changed")
    packed_back = jf.read_big_list(WS_OUT / "_SPEC_DATA_ONE.big")
    if len(packed_back) != 2880:
        raise SystemExit("re-read packed DATA count")
    if jf.read_big_list(WS_OUT / "_SPEC_ART_ONE.big")[0][0] is None:
        raise SystemExit("ART unreadable")

    country_audit = ["", "===== COUNTRY AUDIT =====", ""]
    for dest, _ in dest_meta:
        slots = cs_slot_lines(css2, dest["cs"])
        btns_now = [re.search(r"=\s*(\S+)", s).group(1) for s in slots]
        old = [re.search(r"=\s*(\S+)", s).group(1) for s in dest["old_cs_slots"]]
        country_audit += [
            dest["name"].upper(),
            f"  BIG_PATH = {dest['path']}",
            f"  OBJECT = {dest['object']}  SIDE = {dest['side']}",
            f"  COMMANDSET = {dest['cs']}",
            f"  PREREQ = {dest['prereq']}",
            f"  CONSTRUCT_BUTTON = {dest['construct']} -> {dest['object']}",
            f"  DONOR = {dest['donor_label']} {dest['donor_obj']} / {dest['donor_cs']}",
            f"  RELATED_CS_REPLACED = {', '.join(dest['related_cs'])}",
            f"  PRODUCTION = {' '.join(btns_now)}",
            f"  OLD_PRODUCTION_REMOVED = {' '.join(old)}",
            "  COMMANDSETUPGRADE = NO",
            "  IDENTITY_KEPT = YES",
            "",
        ]

    lines = [
        "SPECTER1 WARFACTORY CLONE  IRAQ + VIETNAM",
        "BASELINE = SPECTER1_WF_CAMP_UPGRADE_UNLOCK / PR #505 + unlock",
        f"BASELINE_DATA_SHA256 = {EXPECTED_DATA_SHA}",
        f"NEW_DATA_SHA256 = {new_sha}",
        f"ART_SHA256 = {EXPECTED_ART_SHA} (unchanged copy)",
        f"PACKED_DATA_FILES = {len(packed_back)}",
        "PACKED_ART_FILES = 4432",
        "DUPLICATE_PACKED_PATHS = NO",
        "NEW_OBJECT_NAMES = NO",
        "BROKEN_INI_REFS_WF = NO",
        "BIG_INTEGRITY = YES",
        "DATA_LAYOUT = Data\\INI\\... inside _SPEC_DATA_ONE.big",
        "ART_LAYOUT = Art\\... inside _SPEC_ART_ONE.big",
        "ART_CHANGED = NO",
        "WEAPON_INI_CHANGED = NO",
        "UPGRADE_INI_CHANGED = NO",
        "COMMANDBUTTON_INI_CHANGED = NO",
        "CAMP_MIC_STRATEGY_CHANGED = NO",
        "IRAQ_WF_UNCHANGED = YES",
        "VIETNAM_WF_UNCHANGED = YES",
        "PACKED_FILE_COUNT_UNCHANGED = YES",
        "NEW_DATA_OR_ART_FOLDERS = NO",
        "NEW_BIG_FILES = NO  (same two archive names as PR #505)",
        "GROUP1 = UAE, Syria, Saudi Arabia, Libya, South Africa  donor=Iraq",
        "GROUP2 = South Korea, Japan, India, Pakistan  donor=Vietnam",
        "",
        "IDENTITY_KEPT = object name, Side, CommandSet name, Prerequisites SupplyCenter, packed path, construct buttons",
        "CONTENT_COPIED = Draw/modules/stats from donor; production bar = donor CommandSet slots",
        "COMMANDSETUPGRADE_REMOVED = South Korea, Japan (Vietnam donor has none)",
        "",
        "INGAME_TESTED = NO",
        "DATA_CHANGED = YES",
        "ART_CHANGED = NO",
    ]
    audit = "\n".join(lines + country_audit) + "\n"

    changelog = """SPECTER1 WarFactory clone: Iraq + Vietnam donors

Continues from SPECTER1_WF_CAMP_UPGRADE_UNLOCK (PR #505 + unlock).
ART, Weapon.ini, Upgrade.ini, Camp, MIC, Strategy Center, CommandCenter,
and other systems are unchanged. Packed file count unchanged.
Same BIG packaging as PR #505.

Group 1 — replace WarFactory of UAE, Syria, Saudi Arabia, Libya, and
South Africa with the Iraq WarFactory structure and production bar
(Iraq_WarFactory_T / Iraq_WarFactoryCommandSet_T3). Existing target
WarFactory objects are removed and rewritten from the Iraq donor.

Group 2 — replace WarFactory of South Korea, Japan, India, and Pakistan
with the Vietnam WarFactory structure and production bar
(Vietnam_WarFactory / Vietnam_WarFactoryCommandSet).

Country IDs stay valid: object name, Side, CommandSet name, SupplyCenter
prerequisite, packed file path, and dozer construct buttons are unchanged.
Leftover WarFactoryCommandSet1/2/3 entries are rewritten to the same
donor bar so stale tier sets cannot restore the old roster.

INGAME_TESTED = NO
"""

    install = f"""SPECTER1_WF_CLONE_IRAQ_VIETNAM
================================

WarFactory clone on the PR #505 + unlock baseline.
UAE / Syria / Saudi Arabia / Libya / South Africa use Iraq's WarFactory.
South Korea / Japan / India / Pakistan use Vietnam's WarFactory.
Camp, MIC, Strategy Center, ART, weapons, and other systems unchanged.
Same GameRoot layout as PR #505: two BIG files, no loose Data/Art.

1. Close Specter / C&C Generals completely.
2. Copy _SPEC_DATA_ONE.big over the current Specter DATA BIG in GameRoot.
3. Copy _SPEC_ART_ONE.big over the current Specter ART BIG in GameRoot.
   ART is an unchanged copy of the PR #505 ART pack.
4. Launch Specter.

Do not mix this DATA with older SPECTER1 roster ZIPs.
Do not extract a Data or Art folder. GameRoot is generals.exe plus the two BIGs.

Checksums:
  DATA SHA256 {new_sha}
  ART  SHA256 {EXPECTED_ART_SHA}

WF_CLONE = YES
INGAME_TESTED = NO
"""

    for dest in (OUT_DIR, WS_OUT):
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "audit.txt").write_text(audit, encoding="utf-8")
        (dest / "changelog.txt").write_text(changelog, encoding="utf-8")
        (dest / "INSTALL.txt").write_text(install, encoding="utf-8")

    zpath = WS_OUT / "SPECTER1_WF_CLONE_IRAQ_VIETNAM.zip"
    sha_docs = (
        f"_SPEC_DATA_ONE.big  SHA256 {new_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {EXPECTED_ART_SHA} (PR #505 ART unchanged)\n"
    )
    (WS_OUT / "SHA256.txt").write_text(sha_docs, encoding="utf-8")
    with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in (
            "_SPEC_DATA_ONE.big",
            "_SPEC_ART_ONE.big",
            "INSTALL.txt",
            "changelog.txt",
            "audit.txt",
            "SHA256.txt",
        ):
            zf.write(WS_OUT / name, name)
        if any(n.startswith(("Data/", "Art/")) for n in zf.namelist()):
            raise SystemExit("zip contains loose Data/Art")
    zip_sha = hashlib.sha256(zpath.read_bytes()).hexdigest()
    sha_txt = (
        f"_SPEC_DATA_ONE.big  SHA256 {new_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {EXPECTED_ART_SHA} (PR #505 ART unchanged)\n"
        f"SPECTER1_WF_CLONE_IRAQ_VIETNAM.zip  SHA256 {zip_sha}  {zpath.stat().st_size} bytes\n"
    )
    for dest in (OUT_DIR, WS_OUT):
        (dest / "SHA256.txt").write_text(sha_txt, encoding="utf-8")
    shutil.copy2(zpath, OUT_DIR / zpath.name)
    print(audit)
    print("WROTE", WS_OUT / "_SPEC_DATA_ONE.big", new_sha)
    print("ZIP", zpath, zpath.stat().st_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
