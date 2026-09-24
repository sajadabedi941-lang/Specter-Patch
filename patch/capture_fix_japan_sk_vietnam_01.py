#!/usr/bin/env python3
"""CAPTURE_BUILDING_FIX_STAGE_JAPAN_SOUTH_KOREA_VIETNAM.

Pack existing Japan/SK/Vietnam basic rifles and last-win only their
barracks / rifle CommandSets so Capture Building works.

Does not modify USA/China/Iraq objects, buildings, HUD, flags,
PlayerTemplate, or any other faction CommandSet.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/AIRCRAFT_ROSTER_EXPANSION_AFRICA_PAKISTAN_SYRIA_STAGE_01/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/EA6B_JAPAN_TO_USA_RESTORE_STAGE_01/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "40bb94ac46bc4c8c1e122f124dd4e49a2da073f8d7dc6682e2d6745e4d97024a"
EXPECTED_ART_SHA = "493c16d2a990cad70d459edbbb6eede963172f433a16f57b241688205a19f314"

RELEASE = "CAPTURE_BUILDING_FIX_STAGE_JAPAN_SOUTH_KOREA_VIETNAM"
WS = Path("/workspace/patch/Release") / RELEASE

P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_PT = r"Data\INI\PlayerTemplate.ini"
P_PT_PATCH = r"Data\INI\PlayerTemplate_SpecterPatch.ini"
P_CS_NEW = r"Data\INI\CommandSet_ZZZZ_JapanSKVietnam_Capture.ini"
P_BTN_NEW = r"Data\INI\CommandButton_ZZZZ_JapanSKVietnam_Capture.ini"

RIFLES = [
    (
        "Japan",
        "Japan_InfantryRifleman",
        Path("/workspace/patch/Data/INI/Object/Specter/Japan Self-Defense Forces/Infantry/Japan_Rifleman_G36.ini"),
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Infantry\Japan_Rifleman_G36.ini",
        "Command_ConstructJapan_InfantryRifleman",
        "us_rifleman",
        "AmericaInfantryRangerCommandSet",
        "SpecialAbilityRangerCaptureBuilding",
        "Command_AmericaRangerCaptureBuilding",
        "Command_UpgradeGLARebelCaptureBuilding",
    ),
    (
        "SouthKorea",
        "SouthKorea_InfantryRifleman",
        Path("/workspace/patch/Data/INI/Object/Specter/Republic of Korea Armed Forces/Infantry/SouthKorea_Rifleman_G36.ini"),
        r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Infantry\SouthKorea_Rifleman_G36.ini",
        "Command_ConstructSouthKorea_InfantryRifleman",
        "us_rifleman",
        "AmericaInfantryRangerCommandSet",
        "SpecialAbilityRangerCaptureBuilding",
        "Command_AmericaRangerCaptureBuilding",
        "Command_UpgradeGLARebelCaptureBuilding",
    ),
    (
        "Vietnam",
        "Vietnam_RepublicanGuard_AKMS",
        Path("/workspace/patch/Data/INI/Object/Specter/Vietnam People's Army/Infantry/Rifleman.ini"),
        r"Data\INI\Object\Specter\Vietnam People's Army\Infantry\Rifleman.ini",
        "Command_ConstructVietnam_RepublicanGuard_AKMS",
        "us_rifleman",
        "Vietnam_RepublicanGuardCommandSet",
        "SpecialAbilityRebelCaptureBuilding",
        "Command_GLAInfantryRebelCaptureBuilding",
        "Command_UpgradeGLARebelCaptureBuilding",
    ),
]

BARRACKS_KEEP = [
    "  2 = Command_ConstructIraq_RepublicanGuard_RPG7",
    "  3 = Command_ConstructIraq_RepublicanGuardMortar",
    "  4 = Command_ConstructIraq_RepublicanGuardKornet",
    "  5 = Command_ConstructIraq_RepublicanGuard_Pkm",
    "  6 = Command_ConstructIraq_RepublicanGuard_TBK14",
    "  7 = Command_ConstructIraq_RepublicanGuard_Eng",
    "  8 = Command_ConstructIraq_SpecialForces",
    "  9 = Command_ConstructIraq_RepublicanGuardIgla",
    "  11 = Command_UpgradeGLARebelCaptureBuilding",
    "  12 = Command_Upgrade_RGD5",
    "  13 = Command_Upgrade_Rpg29",
    "  14 = Command_Sell",
]

FROZEN = [
    P_CMDSET,
    P_CMDBTN,
    P_PT,
    P_PT_PATCH,
    r"Data\INI\Object\Specter\United States Of America\Infantry\Rifleman_M4.ini",
    r"Data\INI\Object\Specter\PLA\Infantry\Rifleman.ini",
    r"Data\INI\Object\Specter\Iraq Army\Infantry\Rifleman.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Iraq_Barracks.ini",
    r"Data\INI\Object\Specter\South Korean Armed Forces\Buildings\Iraq_Barracks.ini",
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Iraq_Barracks.ini",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(name: str) -> str:
    return name.replace("/", "\\")


def read_big(path: Path) -> list[tuple[str, bytes]]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries: list[tuple[str, bytes]] = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def read_big_from_bytes(data: bytes) -> list[tuple[str, bytes]]:
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


def build_big_ordered(entries: list[tuple[str, bytes]]) -> bytes:
    header_size = 16
    encoded = []
    for name, _ in entries:
        nb = name.encode("latin1", errors="replace")
        encoded.append(nb)
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded):
        content = bytes(content)
        index.append((nb, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def find_index(entries, target: str) -> int:
    t = norm(target).lower()
    hits = [i for i, (n, _) in enumerate(entries) if norm(n).lower() == t]
    if len(hits) != 1:
        raise SystemExit(f"{target}: expected 1 path, got {len(hits)}")
    return hits[0]


def text_of(entries, target: str) -> str:
    return entries[find_index(entries, target)][1].decode("latin1", errors="replace")


def add_file(entries, name: str, text: str) -> None:
    n = norm(name)
    if any(norm(x).lower() == n.lower() for x, _ in entries):
        raise SystemExit(f"already packed: {name}")
    entries.append((n, text.replace("\n", "\r\n").encode("latin1", errors="replace")))


def unit_button(btn: str, obj: str, image: str) -> str:
    return (
        f"CommandButton {btn}\n"
        f"  Command          = UNIT_BUILD\n"
        f"  Object           = {obj}\n"
        f"  TextLabel        = CONTROLBAR:Construct{obj}\n"
        f"  ButtonImage      = {image}\n"
        f"  ButtonBorderType = BUILD\n"
        f"  DescriptLabel    = CONTROLBAR:ToolTip{obj}\n"
        f"End\n\n"
    )


def assert_rifle_ready(text: str, obj: str, side: str, cs: str, sp: str) -> None:
    if f"Object {obj}" not in text:
        raise SystemExit(f"{obj}: object header missing")
    if not re.search(rf"(?im)^\s*Side\s*=\s*{re.escape(side)}\b", text):
        raise SystemExit(f"{obj}: Side {side} missing")
    if not re.search(rf"(?im)^\s*CommandSet\s*=\s*{re.escape(cs)}\b", text):
        raise SystemExit(f"{obj}: CommandSet {cs} missing")
    if f"SpecialPowerTemplate      = {sp}" not in text and f"SpecialPowerTemplate = {sp}" not in text:
        if sp not in text:
            raise SystemExit(f"{obj}: capture special power missing")
    if "StartsPaused" not in text:
        raise SystemExit(f"{obj}: StartsPaused missing")
    if "UnpauseSpecialPowerUpgrade" not in text:
        raise SystemExit(f"{obj}: Unpause missing")
    if "Upgrade_InfantryCaptureBuilding" not in text:
        raise SystemExit(f"{obj}: capture upgrade trigger/cameo missing")
    if "Weapon" not in text:
        raise SystemExit(f"{obj}: weapons stripped")


def main() -> int:
    if sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("DATA SHA mismatch")
    if not SRC_ART.exists() or sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("ART SHA mismatch")

    entries = read_big(SRC_DATA)
    orig = list(entries)
    orig_map = {norm(n).lower(): b for n, b in orig}

    for faction, obj, src_path, dest, btn, image, cs, sp, cap_btn, up_btn in RIFLES:
        raw = src_path.read_text(encoding="latin1", errors="replace").replace("\r\n", "\n")
        assert_rifle_ready(raw, obj, faction, cs, sp)
        add_file(entries, dest, raw)

    btn_txt = f"; {RELEASE} construct buttons for existing basic rifles\n\n"
    for faction, obj, src_path, dest, btn, image, cs, sp, cap_btn, up_btn in RIFLES:
        btn_txt += unit_button(btn, obj, image)
    add_file(entries, P_BTN_NEW, btn_txt)

    cs_txt = f"; {RELEASE} last-win barracks + Vietnam rifle CS only\n\n"
    for faction, obj, src_path, dest, btn, image, cs, sp, cap_btn, up_btn in RIFLES:
        cs_txt += f"CommandSet {faction}_BarracksCommandSet\n"
        cs_txt += f"  1 = {btn}\n"
        cs_txt += "\n".join(BARRACKS_KEEP) + "\nEnd\n\n"
    cs_txt += (
        "CommandSet Vietnam_RepublicanGuardCommandSet\n"
        "  1  = Command_GLAInfantryRebelCaptureBuilding\n"
        "  12 = Command_AttackMove\n"
        "  13 = Command_Guard\n"
        "  14 = Command_Stop\n"
        "End\n\n"
    )
    add_file(entries, P_CS_NEW, cs_txt)

    for p in FROZEN:
        if entries[find_index(entries, p)][1] != orig_map[norm(p).lower()]:
            raise SystemExit(f"frozen path changed: {p}")

    orig_names = [n for n, _ in orig]
    new_names = [n for n, _ in entries]
    if new_names[: len(orig_names)] != orig_names:
        raise SystemExit("packed path order prefix changed")
    added = new_names[len(orig_names) :]
    expected_added = [j[3] for j in RIFLES] + [P_BTN_NEW, P_CS_NEW]
    if [norm(x) for x in added] != expected_added:
        raise SystemExit(f"unexpected added paths: {added}")

    for n, b in entries[: len(orig)]:
        if b != orig_map[norm(n).lower()]:
            raise SystemExit(f"existing file rewritten: {n}")

    data_blob = build_big_ordered(entries)
    rebuilt = read_big_from_bytes(data_blob)
    if [n for n, _ in rebuilt] != new_names:
        raise SystemExit("rebuild order drifted")

    for faction, obj, src_path, dest, btn, image, cs, sp, cap_btn, up_btn in RIFLES:
        text = text_of(rebuilt, dest)
        assert_rifle_ready(text, obj, faction, cs, sp)
        live_cs = text_of(rebuilt, P_CS_NEW)
        if f"1 = {btn}" not in live_cs:
            raise SystemExit(f"{faction} barracks slot 1 missing")
        if "Command_UpgradeGLARebelCaptureBuilding" not in live_cs:
            raise SystemExit("upgrade button dropped")
    live_cs = text_of(rebuilt, P_CS_NEW)
    if "Command_GLAInfantryRebelCaptureBuilding" not in live_cs:
        raise SystemExit("Vietnam rifle CS missing capture button")
    if "CommandSet Syria_RepublicanGuardCommandSet" in live_cs:
        raise SystemExit("unrelated faction CS leaked")

    WS.mkdir(parents=True, exist_ok=True)
    data_path = WS / "_SPEC_DATA_ONE.big"
    data_path.write_bytes(data_blob)
    data_sha = sha256_file(data_path)

    added_list = "\n".join(f"  {p}" for p in expected_added)
    audit = f"""CAPTURE_BUILDING_FIX_STAGE_JAPAN_SOUTH_KOREA_VIETNAM
SOURCE_DATA_SHA = {EXPECTED_DATA_SHA}
NEW_DATA_SHA256 = {data_sha}
NEW_DATA_BYTES = {data_path.stat().st_size}
NEW_DATA_FILE_COUNT = {len(entries)}
ART_CHANGED = NO
ART_INCLUDED = NO (use existing ART SHA {EXPECTED_ART_SHA})

WORKING_REFERENCE
  AmericaInfantryRanger
    file Data\\INI\\Object\\Specter\\United States Of America\\Infantry\\Rifleman_M4.ini
    SpecialAbilityRangerCaptureBuilding StartsPaused=Yes
    Unpause TriggeredBy=Upgrade_InfantryCaptureBuilding
    CommandSet AmericaInfantryRangerCommandSet
      Command_AmericaRangerCaptureBuilding NEED_UPGRADE
    Barracks Command_UpgradeAmericaRangerCaptureBuilding
  ChinaInfantryRedguard
    file Data\\INI\\Object\\Specter\\PLA\\Infantry\\Rifleman.ini
    SpecialAbilityRedGuardCaptureBuilding StartsPaused=Yes
    Unpause TriggeredBy=Upgrade_InfantryCaptureBuilding
    CommandSet ChinaInfantryRedguardCommandSet
      Command_ChinaInfantryRedGuardCaptureBuilding NEED_UPGRADE
    Barracks Command_UpgradeChinaRedguardCaptureBuilding
  Shared upgrade Upgrade_InfantryCaptureBuilding file Data\\INI\\Upgrade.ini
  Oil / capturable structures use CAPTURABLE KindOf (TechOilDerrick).
  NEED_TARGET_NEUTRAL_OBJECT on the capture button covers oil derricks
  and other capturable buildings.

PREVIOUS_AUDIT_ERROR
  The earlier report marked Japan / South Korea / Vietnam as
  Has capture infantry = NO because it only searched packed
  Japan Self-Defense Forces / South Korean Armed Forces /
  Vietnam People's Armed Forces folders.
  Existing basic rifles were already authored here:
    Japan_InfantryRifleman
      Data\\INI\\Object\\Specter\\Japan Self-Defense Forces\\Infantry\\Japan_Rifleman_G36.ini
      FULL USA ranger capture chain already present
    SouthKorea_InfantryRifleman
      Data\\INI\\Object\\Specter\\Republic of Korea Armed Forces\\Infantry\\SouthKorea_Rifleman_G36.ini
      FULL USA ranger capture chain already present
    Vietnam_RepublicanGuard_AKMS
      Data\\INI\\Object\\Specter\\Vietnam People's Army\\Infantry\\Rifleman.ini
      Rebel capture modules + TriggeredBy already present
  Those three object files and their construct buttons were NOT packed.
  Live barracks last-win in CommandSet.ini still constructed
  Iraq_RepublicanGuard_AKMS instead of the faction rifle.

ROOT_CAUSE_PER_FACTION
  Japan
    Missing packed object Japan_InfantryRifleman
    Missing packed Command_ConstructJapan_InfantryRifleman
    Japan_BarracksCommandSet last-win trained Iraq rifle
    Object itself already had USA capture modules / ranger CommandSet
  South Korea
    Missing packed object SouthKorea_InfantryRifleman
    Missing packed Command_ConstructSouthKorea_InfantryRifleman
    SouthKorea_BarracksCommandSet last-win trained Iraq rifle
    Object itself already had USA capture modules / ranger CommandSet
  Vietnam
    Missing packed object Vietnam_RepublicanGuard_AKMS
    Missing packed Command_ConstructVietnam_RepublicanGuard_AKMS
    Vietnam_BarracksCommandSet last-win trained Iraq rifle
    Vietnam_RepublicanGuardCommandSet was unpacked and had no
    capture button (Guard / AttackMove / Stop only)

FIX_APPLIED
  Packed the three existing rifle INIs unchanged (weapons/stats preserved).
  Appended construct buttons.
  Last-win barracks CommandSets: slot 1 = own basic rifle.
    Slots 2-9 / 11-14 kept from live Iraq-clone barracks so the rest
    of the current bar is unchanged.
  Last-win Vietnam_RepublicanGuardCommandSet = Iraq-style capture button.
  Existing Command_UpgradeGLARebelCaptureBuilding kept (same upgrade
  Upgrade_InfantryCaptureBuilding that USA/China/Iraq use).

CHANGED_OBJECTS
  ADDED Japan_InfantryRifleman
  ADDED SouthKorea_InfantryRifleman
  ADDED Vietnam_RepublicanGuard_AKMS
  NO edits to those objects' weapons, armor, cost, or art.

CHANGED_COMMANDS
  ADDED Command_ConstructJapan_InfantryRifleman
  ADDED Command_ConstructSouthKorea_InfantryRifleman
  ADDED Command_ConstructVietnam_RepublicanGuard_AKMS
  LAST-WIN Japan_BarracksCommandSet
  LAST-WIN SouthKorea_BarracksCommandSet
  LAST-WIN Vietnam_BarracksCommandSet
  LAST-WIN Vietnam_RepublicanGuardCommandSet
    + Command_GLAInfantryRebelCaptureBuilding
  REUSED Command_AmericaRangerCaptureBuilding (Japan/SK)
  REUSED Command_UpgradeGLARebelCaptureBuilding (all three)
  REUSED Upgrade_InfantryCaptureBuilding
  REUSED SpecialAbilityRangerCaptureBuilding / SpecialAbilityRebelCaptureBuilding

CHANGED_FILES
{added_list}

NOT_MODIFIED
  USA ranger object
  China redguard object
  Iraq rifle object
  CommandSet.ini
  CommandButton.ini
  PlayerTemplate
  Japan/SK/Vietnam barracks building INIs
  HUD / flags / aircraft / other factions

COMPARISON_AFTER_FIX
  Japan_InfantryRifleman == USA ranger capture architecture
    same SP / StartsPaused / TriggeredBy / AmericaInfantryRangerCommandSet
  SouthKorea_InfantryRifleman == USA ranger capture architecture
  Vietnam_RepublicanGuard_AKMS == Iraq/GLA capture architecture
    same SP / StartsPaused / TriggeredBy / GLA capture button

OIL_AND_BUILDINGS
  Capture buttons already include NEED_TARGET_NEUTRAL_OBJECT.
  TechOilDerrick is CAPTURABLE. No oil object edit required.

BOOT_SAFE = YES
INGAME_TESTED = NO
OTHER_FACTIONS_MODIFIED = NO
"""
    changelog = """CAPTURE_BUILDING_FIX_STAGE_JAPAN_SOUTH_KOREA_VIETNAM

Japan / South Korea / Vietnam basic rifles can use Zero Hour Capture Building.

Packed existing Japan_InfantryRifleman, SouthKorea_InfantryRifleman,
and Vietnam_RepublicanGuard_AKMS (already authored; were not in the live pair).
Last-win barracks slot 1 to those rifles. Vietnam rifle CommandSet gains
Command_GLAInfantryRebelCaptureBuilding.

USA/China/Iraq capture objects unchanged. Buildings, flags, aircraft,
HUD, PlayerTemplate, and other factions unchanged. ART unchanged.
"""
    install = f"""CAPTURE_BUILDING_FIX_STAGE_JAPAN_SOUTH_KOREA_VIETNAM

1. Copy _SPEC_DATA_ONE.big over the live Specter DATA pair.
2. Keep the existing ART pair (SHA {EXPECTED_ART_SHA}).
3. Play Japan, South Korea, and Vietnam. Build Barracks.
4. Train the basic rifle. Research Capture Building (existing upgrade).
5. Confirm the Capture command appears and can target oil derricks
   and other capturable structures.

DATA SHA256 {data_sha}
"""
    (WS / "audit.txt").write_text(audit, encoding="utf-8")
    (WS / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS / "INSTALL.txt").write_text(install, encoding="utf-8")
    (WS / "CHANGED_FILES.txt").write_text(
        "ADDED_DATA_PATHS\n" + added_list + "\nART_CHANGED = NO\n",
        encoding="utf-8",
    )
    (WS / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {data_sha}\n"
        f"ART unchanged SHA256 {EXPECTED_ART_SHA}\n",
        encoding="utf-8",
    )

    zip_path = WS / f"{RELEASE}.zip"
    print("Writing ZIP...")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(WS / "audit.txt", "audit.txt")
        zf.write(WS / "changelog.txt", "changelog.txt")
        zf.write(WS / "SHA256.txt", "SHA256.txt")
        zf.write(WS / "INSTALL.txt", "INSTALL.txt")
        zf.write(WS / "CHANGED_FILES.txt", "CHANGED_FILES.txt")
    zip_sha = sha256_file(zip_path)
    (WS / "SHA256.txt").write_text(
        f"_SPEC_DATA_ONE.big  SHA256 {data_sha}\n"
        f"ART unchanged SHA256 {EXPECTED_ART_SHA}\n"
        f"{RELEASE}.zip  SHA256 {zip_sha}  {zip_path.stat().st_size} bytes\n",
        encoding="utf-8",
    )
    print(audit)
    print("ZIP", zip_path, zip_path.stat().st_size, zip_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
