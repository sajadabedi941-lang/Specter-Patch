#!/usr/bin/env python3
"""Clone Iraq/Vietnam Camp (Barracks) onto listed factions.

Baseline: SPECTER1_WF_CLONE_IRAQ_VIETNAM (PR #505 + unlock + WF clone).
Group 1 (Iraq donor): UAE, Syria, Saudi Arabia, Libya, South Africa.
Group 2 (Vietnam donor): South Korea, Japan, India, Pakistan.

Only Camp/Barracks object INIs and those factions' Barracks CommandSets.
WarFactory / MIC / Strategy / CommandCenter untouched.
ART / Weapon.ini / Upgrade.ini / CommandButton.ini / models unchanged.
Same two BIG names and ZIP-root layout as PR #505.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_WF_CLONE_IRAQ_VIETNAM/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/SPECTER1_WF_CLONE_IRAQ_VIETNAM/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "5e6ef407c7f18ac1af1daa47d8be319c5cacaeb5fe0c59bd3b5d4d012eca78ca"
EXPECTED_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"
OUT_DIR = Path("/tmp/SPECTER1_CAMP_CLONE_IRAQ_VIETNAM")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_CAMP_CLONE_IRAQ_VIETNAM")

P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_WEAPON = r"Data\INI\Weapon.ini"
P_UPGRADE = r"Data\INI\Upgrade.ini"

IRAQ_CAMP = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_Barracks.ini"
VN_CAMP = r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Iraq_Barracks.ini"
IRAQ_CS = "Iraq_BarracksCommandSet"
VN_CS = "Vietnam_BarracksCommandSet"

GROUP1 = [
    {
        "name": "UAE",
        "path": r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_Barracks.ini",
        "object": "UAE_Barracks",
        "side": "UAE",
        "cs": "UAE_BarracksCommandSet",
        "construct": "Command_ConstructUAE_Barracks",
    },
    {
        "name": "Syria",
        "path": r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_Barracks.ini",
        "object": "Syria_Barracks",
        "side": "Syria",
        "cs": "Syria_BarracksCommandSet",
        "construct": "Command_ConstructSyria_Barracks",
    },
    {
        "name": "Saudi Arabia",
        "path": r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_Barracks.ini",
        "object": "SaudiArabia_Barracks",
        "side": "SaudiArabia",
        "cs": "SaudiArabia_BarracksCommandSet",
        "construct": "Command_ConstructSaudiArabia_Barracks",
    },
    {
        "name": "Libya",
        "path": r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_Barracks.ini",
        "object": "Libya_Barracks",
        "side": "Libya",
        "cs": "Libya_BarracksCommandSet",
        "construct": "Command_ConstructLibya_Barracks",
    },
    {
        "name": "South Africa",
        "path": r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_Barracks.ini",
        "object": "SouthAfrica_Barracks",
        "side": "SouthAfrica",
        "cs": "SouthAfrica_BarracksCommandSet",
        "construct": "Command_ConstructSouthAfrica_Barracks",
    },
]

GROUP2 = [
    {
        "name": "South Korea",
        "path": r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\Iraq_Barracks.ini",
        "object": "SouthKorea_Barracks",
        "side": "SouthKorea",
        "cs": "SouthKorea_BarracksCommandSet",
        "construct": "Command_ConstructSouthKorea_Barracks_SAFE",
    },
    {
        "name": "Japan",
        "path": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Iraq_Barracks.ini",
        "object": "Japan_Barracks",
        "side": "Japan",
        "cs": "Japan_BarracksCommandSet",
        "construct": "Command_ConstructJapan_Barracks_SAFE",
    },
    {
        "name": "India",
        "path": r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_Barracks.ini",
        "object": "India_Barracks",
        "side": "India",
        "cs": "India_BarracksCommandSet",
        "construct": "Command_ConstructIndia_Barracks",
    },
    {
        "name": "Pakistan",
        "path": r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_Barracks.ini",
        "object": "Pakistan_Barracks",
        "side": "Pakistan",
        "cs": "Pakistan_BarracksCommandSet",
        "construct": "Command_ConstructPakistan_Barracks",
    },
]

PROTECTED_RX = re.compile(
    r"(?i)(warfactory|war_factory|_mic\.ini|strategy|commandcenter|command_center)"
)


def object_names(text: str) -> list[str]:
    return re.findall(r"(?im)^Object\s+(\S+)", text)


def field_of(text: str, key: str) -> str | None:
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(\S+)", text)
    return m.group(1) if m else None


def display_name(text: str) -> str:
    return field_of(text, "DisplayName") or "OBJECT:Barracks"


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


def slot_buttons(lines: list[str]) -> list[str]:
    return [re.search(r"=\s*(\S+)", s).group(1) for s in lines]


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


def button_object(btns: dict[str, str], name: str) -> str | None:
    body = btns.get(name)
    if not body:
        return None
    m = re.search(r"(?im)^\s*Object\s*=\s*(\S+)", body)
    return m.group(1) if m else None


def adapt_donor(donor: str, src_object: str, dest: dict, dest_display: str) -> str:
    text, n = re.subn(
        rf"(?im)^Object\s+{re.escape(src_object)}\s*$",
        f"Object {dest['object']}",
        donor,
        count=1,
    )
    if n != 1:
        raise SystemExit(f"{dest['name']}: object rename failed ({n})")
    text, n = re.subn(r"(?im)^(\s*Side\s*=\s*)\S+", rf"\g<1>{dest['side']}", text, count=1)
    if n != 1:
        raise SystemExit(f"{dest['name']}: Side replace {n}")
    text, n = re.subn(
        r"(?im)^(\s*CommandSet\s*=\s*)\S+", rf"\g<1>{dest['cs']}", text, count=1
    )
    if n != 1:
        raise SystemExit(f"{dest['name']}: CommandSet replace {n}")
    text, n = re.subn(
        r"(?im)^(\s*DisplayName\s*=\s*)\S+", rf"\g<1>{dest_display}", text, count=1
    )
    if n != 1:
        raise SystemExit(f"{dest['name']}: DisplayName replace {n}")
    if re.search(r"(?im)^\s*Behavior\s*=\s*CommandSetUpgrade\b", text):
        raise SystemExit(f"{dest['name']}: leftover CommandSetUpgrade")
    header = (
        f"; SPECTER - {dest['name']} Camp/Barracks "
        f"({dest['donor_label']} clone)\n"
        "; Existing Camp infantry/unit entries removed. Object name, Side,\n"
        "; CommandSet name, and packed path kept for faction identity.\n"
        "; WarFactory / MIC / Strategy / CommandCenter not modified.\n\n"
    )
    m = re.search(r"(?im)^Object\s+", text)
    if not m:
        raise SystemExit(f"{dest['name']}: missing Object after adapt")
    return header + text[m.start() :]


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
    src_iraq = jf.raw_of(entries, IRAQ_CAMP)
    src_vn = jf.raw_of(entries, VN_CAMP)
    src_weapon = jf.raw_of(entries, P_WEAPON)
    src_upgrade = jf.raw_of(entries, P_UPGRADE)
    src_btn = jf.raw_of(entries, P_CMDBTN)
    src_map = {jf.norm(n).lower(): b for n, b in entries}
    src_cmd = jf.text_of(entries, P_CMDSET)
    src_css = jf.parse_commandsets(src_cmd)

    iraq_slots = cs_slot_lines(src_css, IRAQ_CS)
    vn_slots = cs_slot_lines(src_css, VN_CS)
    iraq_donor = jf.text_of(entries, IRAQ_CAMP)
    vn_donor = jf.text_of(entries, VN_CAMP)
    src_obj_iraq = object_names(iraq_donor)[0]
    src_obj_vn = object_names(vn_donor)[0]
    if src_obj_iraq != "Iraq_Barracks":
        raise SystemExit(f"unexpected Iraq Camp object {src_obj_iraq}")
    if src_obj_vn != "Vietnam_Barracks":
        raise SystemExit(f"unexpected Vietnam Camp object {src_obj_vn}")

    dest_meta = []
    for dest in GROUP1:
        dest = dict(dest)
        dest["donor_label"] = "Iraq"
        dest["donor_cs"] = IRAQ_CS
        dest["slots"] = iraq_slots
        dest["donor_obj"] = src_obj_iraq
        dest_meta.append((dest, iraq_donor))
    for dest in GROUP2:
        dest = dict(dest)
        dest["donor_label"] = "Vietnam"
        dest["donor_cs"] = VN_CS
        dest["slots"] = vn_slots
        dest["donor_obj"] = src_obj_vn
        dest_meta.append((dest, vn_donor))

    btns = jf.parse_buttons(jf.text_of(entries, P_CMDBTN))
    target_paths = set()
    changed_cs = set()
    for dest, _donor in dest_meta:
        old = jf.text_of(entries, dest["path"])
        objs = object_names(old)
        if dest["object"] not in objs:
            raise SystemExit(f"{dest['name']}: expected {dest['object']} in {objs}")
        if field_of(old, "Side") != dest["side"]:
            raise SystemExit(f"{dest['name']}: Side {field_of(old, 'Side')}")
        if field_of(old, "CommandSet") != dest["cs"]:
            raise SystemExit(f"{dest['name']}: CS {field_of(old, 'CommandSet')}")
        dest["display"] = display_name(old)
        dest["old_cs_slots"] = cs_slot_lines(src_css, dest["cs"])
        if dest["construct"] not in btns:
            raise SystemExit(f"missing construct button {dest['construct']}")
        if button_object(btns, dest["construct"]) != dest["object"]:
            raise SystemExit(
                f"{dest['construct']} -> {button_object(btns, dest['construct'])}"
            )
        target_paths.add(jf.norm(dest["path"]).lower())
        changed_cs.add(dest["cs"])

    for dest, donor in dest_meta:
        new_text = adapt_donor(donor, dest["donor_obj"], dest, dest["display"])
        if object_names(new_text) != [dest["object"]]:
            raise SystemExit(f"{dest['name']}: extra objects {object_names(new_text)}")
        if field_of(new_text, "Side") != dest["side"]:
            raise SystemExit(f"{dest['name']}: adapted Side wrong")
        if field_of(new_text, "CommandSet") != dest["cs"]:
            raise SystemExit(f"{dest['name']}: adapted CS wrong")
        jf.set_text(entries, dest["path"], new_text)

    cmd_new = jf.text_of(entries, P_CMDSET)
    for dest, _donor in dest_meta:
        cmd_new = jf.replace_commandset(cmd_new, dest["cs"], dest["slots"])
    jf.set_text(entries, P_CMDSET, cmd_new)

    if len(entries) != 2880:
        raise SystemExit(f"DATA packed changed {len(entries)}")
    if jf.raw_of(entries, IRAQ_CAMP) != src_iraq:
        raise SystemExit("Iraq Camp file was modified")
    if jf.raw_of(entries, VN_CAMP) != src_vn:
        raise SystemExit("Vietnam Camp file was modified")
    if jf.raw_of(entries, P_WEAPON) != src_weapon:
        raise SystemExit("Weapon.ini changed")
    if jf.raw_of(entries, P_UPGRADE) != src_upgrade:
        raise SystemExit("Upgrade.ini changed")
    if jf.raw_of(entries, P_CMDBTN) != src_btn:
        raise SystemExit("CommandButton.ini changed")

    names = [jf.norm(n).lower() for n, _ in entries]
    if len(names) != len(set(names)):
        raise SystemExit("duplicate packed DATA paths")
    if any(n.startswith("art\\") for n in names):
        raise SystemExit("ART leaked into DATA")
    if not any(n.startswith("data\\ini\\") for n in names):
        raise SystemExit("DATA missing Data\\INI")

    new_objs = collect_objects(entries)
    introduced = [obj for obj in new_objs if obj not in src_objs]
    if introduced:
        raise SystemExit(f"new object names: {introduced}")

    css2 = jf.parse_commandsets(jf.text_of(entries, P_CMDSET))
    btns2 = jf.parse_buttons(jf.text_of(entries, P_CMDBTN))
    broken = []
    for dest, _ in dest_meta:
        got = slot_buttons(cs_slot_lines(css2, dest["cs"]))
        exp = slot_buttons(dest["slots"])
        if got != exp:
            broken.append(f"{dest['name']} CS slots {got} != {exp}")
        for btn in got:
            if btn not in btns2:
                broken.append(f"{dest['name']} missing button {btn}")
        t = jf.text_of(entries, dest["path"])
        if field_of(t, "Side") != dest["side"]:
            broken.append(f"{dest['name']} Side")
        if field_of(t, "CommandSet") != dest["cs"]:
            broken.append(f"{dest['name']} CS ref")
        if dest["cs"] not in css2:
            broken.append(f"{dest['name']} missing CS def")
        if button_object(btns2, dest["construct"]) != dest["object"]:
            broken.append(f"{dest['construct']} broken")
        if dest["object"] not in new_objs:
            broken.append(f"{dest['name']} object missing")
    if broken:
        raise SystemExit("broken Camp refs:\n  " + "\n  ".join(broken))

    for name in src_css:
        if name in changed_cs:
            continue
        if slot_buttons(cs_slot_lines(css2, name)) != slot_buttons(
            cs_slot_lines(src_css, name)
        ):
            raise SystemExit(f"unexpected CommandSet change: {name}")

    for name, raw in entries:
        n = jf.norm(name).lower()
        if n == jf.norm(P_CMDSET).lower():
            continue
        if n in target_paths:
            continue
        if src_map.get(n) != raw:
            raise SystemExit(f"unexpected DATA change: {jf.norm(name)}")
        if PROTECTED_RX.search(n):
            if src_map.get(n) != raw:
                raise SystemExit(f"protected system changed: {jf.norm(name)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(jf.build_big_ordered(entries))
    shutil.copy2(SRC_ART, OUT_DIR / "_SPEC_ART_ONE.big")
    shutil.copy2(OUT_DIR / "_SPEC_DATA_ONE.big", WS_OUT / "_SPEC_DATA_ONE.big")
    shutil.copy2(OUT_DIR / "_SPEC_ART_ONE.big", WS_OUT / "_SPEC_ART_ONE.big")
    new_sha = jf.sha256_file(WS_OUT / "_SPEC_DATA_ONE.big")
    if jf.sha256_file(WS_OUT / "_SPEC_ART_ONE.big") != EXPECTED_ART_SHA:
        raise SystemExit("packed ART SHA changed")
    packed_back = jf.read_big_list(WS_OUT / "_SPEC_DATA_ONE.big")
    if len(packed_back) != 2880:
        raise SystemExit("re-read packed DATA count")

    country_audit = ["", "===== COUNTRY AUDIT =====", ""]
    for dest, _ in dest_meta:
        now = slot_buttons(cs_slot_lines(css2, dest["cs"]))
        old = slot_buttons(dest["old_cs_slots"])
        country_audit += [
            dest["name"].upper(),
            f"  BIG_PATH = {dest['path']}",
            f"  OBJECT = {dest['object']}  SIDE = {dest['side']}",
            f"  COMMANDSET = {dest['cs']}",
            f"  CONSTRUCT_BUTTON = {dest['construct']} -> {dest['object']}",
            f"  DONOR = {dest['donor_label']} {dest['donor_obj']} / {dest['donor_cs']}",
            f"  PRODUCTION = {' '.join(now)}",
            f"  OLD_PRODUCTION_REMOVED = {' '.join(old)}",
            "  CAMP_UPGRADES = Command_UpgradeGLARebelCaptureBuilding Command_Upgrade_RGD5 Command_Upgrade_Rpg29",
            "  IDENTITY_KEPT = YES",
            "",
        ]

    lines = [
        "SPECTER1 CAMP CLONE  IRAQ + VIETNAM",
        "BASELINE = SPECTER1_WF_CLONE_IRAQ_VIETNAM / PR #505 + unlock + WF clone",
        f"BASELINE_DATA_SHA256 = {EXPECTED_DATA_SHA}",
        f"NEW_DATA_SHA256 = {new_sha}",
        f"ART_SHA256 = {EXPECTED_ART_SHA} (unchanged copy)",
        f"PACKED_DATA_FILES = {len(packed_back)}",
        "PACKED_ART_FILES = 4432",
        "DUPLICATE_PACKED_PATHS = NO",
        "NEW_OBJECT_NAMES = NO",
        "BROKEN_INI_REFS_CAMP = NO",
        "BIG_INTEGRITY = YES",
        "DATA_LAYOUT = Data\\INI\\... inside _SPEC_DATA_ONE.big",
        "ART_LAYOUT = Art\\... inside _SPEC_ART_ONE.big",
        "ART_CHANGED = NO",
        "WEAPON_INI_CHANGED = NO",
        "UPGRADE_INI_CHANGED = NO",
        "COMMANDBUTTON_INI_CHANGED = NO",
        "WARFACTORY_CHANGED = NO",
        "MIC_STRATEGY_COMMANDCENTER_CHANGED = NO",
        "IRAQ_CAMP_UNCHANGED = YES",
        "VIETNAM_CAMP_UNCHANGED = YES",
        "PACKED_FILE_COUNT_UNCHANGED = YES",
        "NEW_DATA_OR_ART_FOLDERS = NO",
        "NEW_BIG_FILES = NO  (same two archive names as PR #505)",
        "GROUP1 = UAE, Syria, Saudi Arabia, Libya, South Africa  donor=Iraq Camp",
        "GROUP2 = South Korea, Japan, India, Pakistan  donor=Vietnam Camp",
        "",
        "IDENTITY_KEPT = object name, Side, CommandSet name, packed path, construct buttons",
        "CONTENT_COPIED = Draw/modules/stats from donor; production bar = donor Camp infantry + Capture/RGD5/RPG29",
        "",
        "INGAME_TESTED = NO",
        "DATA_CHANGED = YES",
        "ART_CHANGED = NO",
    ]
    audit = "\n".join(lines + country_audit) + "\n"

    changelog = """SPECTER1 Camp clone: Iraq + Vietnam donors

Continues from SPECTER1_WF_CLONE_IRAQ_VIETNAM (PR #505 + unlock + WF clone).
WarFactory, MIC, Strategy Center, CommandCenter, ART, Weapon.ini,
Upgrade.ini, and CommandButton.ini are unchanged. Packed file count
unchanged. Same BIG packaging as PR #505.

Group 1 — replace Camp of UAE, Syria, Saudi Arabia, Libya, and
South Africa with the Iraq Camp structure and infantry bar
(Iraq_Barracks / Iraq_BarracksCommandSet). Existing target Camp
infantry/unit entries are removed and rewritten from the Iraq donor.

Group 2 — replace Camp of South Korea, Japan, India, and Pakistan
with the Vietnam Camp structure and infantry bar
(Vietnam_Barracks / Vietnam_BarracksCommandSet).

Country IDs stay valid: object name, Side, CommandSet name, packed
file path, and dozer construct buttons are unchanged.

INGAME_TESTED = NO
"""

    install = f"""SPECTER1_CAMP_CLONE_IRAQ_VIETNAM
================================

Camp/Barracks clone on the PR #505 + unlock + WF-clone baseline.
UAE / Syria / Saudi Arabia / Libya / South Africa use Iraq's Camp.
South Korea / Japan / India / Pakistan use Vietnam's Camp.
WarFactory, MIC, Strategy Center, CommandCenter, ART, weapons unchanged.
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

CAMP_CLONE = YES
INGAME_TESTED = NO
"""

    for dest in (OUT_DIR, WS_OUT):
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "audit.txt").write_text(audit, encoding="utf-8")
        (dest / "changelog.txt").write_text(changelog, encoding="utf-8")
        (dest / "INSTALL.txt").write_text(install, encoding="utf-8")

    zpath = WS_OUT / "SPECTER1_CAMP_CLONE_IRAQ_VIETNAM.zip"
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
        f"SPECTER1_CAMP_CLONE_IRAQ_VIETNAM.zip  SHA256 {zip_sha}  {zpath.stat().st_size} bytes\n"
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
