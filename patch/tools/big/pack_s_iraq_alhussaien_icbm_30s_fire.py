#!/usr/bin/env python3
"""Screenshot Al Abbas ICBM Launcher (Iraq_Alhussaien): 30s + fire after deploy.

Starts from packed PR #590 _SPEC_DATA_ONE.big
  SHA256 8f4a7e1950b44638cf77d91f6da50eca695d9e053784894e42f6cf1e3d399bca

Screenshot mapping (CSF last-wins):
  Iraq_WarFactoryCommandSet_T3 slot 10 = Command_ConstructIraq_Alhussaien
  between SA-6 (2K12 KUB, slot 8) and BM-21 Grad (slot 12)
  TextLabel CONTROLBAR:ConstructAlhussaiengls = "Al Abbas ICBM Launcher"
  DescriptLabel = Iraqi-made mobile ICBM with HEB warhead and 5 decoys
  Object Iraq_Alhussaien  BuildCost 20000  BuildTime 1200
  File Data\\INI\\Object\\Specter\\Iraq Army\\Wheeled\\AbbasLauncher.ini

PR #590 edited missile-factory Iraq_AlAbbas (CB_MISSILE_D, cost 2600).
That object is NOT the screenshot unit. PR #590 changes are preserved.

Fire locks on Iraq_Alhussaien:
  1. InitialPayload GenericFakeRider1 -> WEAPON_RIDER1 SECONDARY=NONE (unarmed)
     Rearm upgrade Upgrade_AlhussaienWarheadRearm takes 500s before first load.
  2. Command_TacticalStrike has NEED_SPECIAL_POWER_SCIENCE and SpecialPower
     Iraq_AlhussainMissile (missing from SpecialPower.ini). Shared with Iskander.
  3. Command_AlAbidMissileStrike (Iraq-only) has the same science lock.

Fix (Iraq_Alhussaien only; Iskander button unchanged):
  BuildTime 1200 -> 30.0
  Start armed: InitialPayload GenericFakeRider2 + ArmedCommandSet
  New Command_IraqAlAbbasICBMFire = FIRE_WEAPON SECONDARY, no science
  Strip science from Iraq-only Command_AlAbidMissileStrike
  Wire ObjectCreationUpgrade TriggeredBy = Upgrade_AlhussaienWarheadRearm
    so post-shot rearm still works (500s reload UNCHANGED)
  Keep Command_IraqDeployUnitWeapon + DeployStyleAIUpdate
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_ALABBAS_WF_30S_FIRE/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_MISSILE_DATA_BCDHIJ/_SPEC_ART_ONE.big"
OUT = ROOT / "patch/Release/SPECTER_IRAQ_ALHUSSAIEN_ICBM_30S_FIRE"

BASE_DATA_SHA = "8f4a7e1950b44638cf77d91f6da50eca695d9e053784894e42f6cf1e3d399bca"
BASE_DATA_SIZE = 366514412
BASE_ART_SHA = "e2024ec0e3130076b29c52beae3c495193e4c95136e64170724e082d40a856e4"
BASE_ART_SIZE = 1292294758

CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"
PT_KEY = r"Data\INI\PlayerTemplate.ini"
WEAPON_KEY = r"Data\INI\Weapon.ini"
UPGRADE_KEY = r"Data\INI\Upgrade.ini"
LOCO_KEY = r"Data\INI\Locomotor.ini"
R11_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini"
FACTORY_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini"
UNIT_A_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini"
UNIT_D_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlAbbas.ini"
UNLOCK_KEY = r"Data\INI\Object\Specter\EU5Unlock\Specter_EU5WFUnlock.ini"
IRAQ_WF_KEY = r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_WarFactory.ini"
LAUNCHER_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\AbbasLauncher.ini"
LAUNCHER_AI_KEY = r"Data\INI\Object\Specter\Iraq Army\Wheeled\AbbasLauncher_AI.ini"

NEW_FIRE_BTN = "Command_IraqAlAbbasICBMFire"

IRAQ_WF_SLOTS = {
    1: "Command_ConstructIraq_T-72",
    2: "Command_ConstructIraq_BMP-1",
    3: "Command_ConstructIraq_BMP-2",
    4: "Command_ConstructIraq_BTR-90",
    5: "Command_ConstructIraq_2S1",
    6: "Command_ConstructIraq_Sam8",
    7: "Command_ConstructIraq_AssadBabel-2",
    8: "Command_ConstructIraq_SA-6",
    9: "Command_ConstructIraq_Sarab7",
    10: "Command_ConstructIraq_Alhussaien",
    11: "Command_ConstructIraqVehicleRoland3K",
    12: "Command_ConstructIraq_BM-21",
    13: "Command_ConstructIraq_R11ScudB",
    14: "Command_Sell",
}

FACTORY_SLOTS = {
    1: "CB_MISSILE_A",
    2: "CB_MISSILE_B",
    3: "CB_MISSILE_C",
    4: "CB_MISSILE_D",
    8: "CB_MISSILE_H",
    9: "CB_MISSILE_I",
    10: "CB_MISSILE_J",
    13: "Command_SetRallyPoint",
    14: "Command_Sell",
}

NEW_FIRE_BUTTON = (
    "CommandButton Command_IraqAlAbbasICBMFire\r\n"
    "  Command             = FIRE_WEAPON\r\n"
    "  WeaponSlot          = SECONDARY\r\n"
    "  Options             = OK_FOR_MULTI_SELECT NEED_TARGET_POS CONTEXTMODE_COMMAND\r\n"
    "  TextLabel           = CONTROLBAR:TacticalThermoNuclearStrike\r\n"
    "  ButtonImage         = sys_fire\r\n"
    "  ButtonBorderType    = ACTION\r\n"
    "  DescriptLabel       = CONTROLBAR:ToolTipTacticalThermoNuclearStrike\r\n"
    "  CursorName          = LaserGuidedMissiles\r\n"
    "  RadiusCursorType    = NUCLEARMISSILE\r\n"
    "End"
)


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_big(data: bytes) -> dict[str, bytes]:
    if data[:4] != b"BIGF":
        raise ValueError("not BIGF")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files: dict[str, bytes] = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name.replace("/", "\\")] = data[off : off + size]
    return files


def parse_index(data: bytes):
    archive_size = struct.unpack(">I", data[4:8])[0]
    count = struct.unpack(">I", data[8:12])[0]
    header_size = struct.unpack(">I", data[12:16])[0]
    pos = 16
    files = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files.append((name, off, size))
    return archive_size, count, header_size, pos, files


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    index = []
    blobs = []
    offset = header_size
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


def big_structure_ok(blob: bytes) -> list[str]:
    issues = []
    arch, count, header, index_end, files = parse_index(blob)
    if arch != len(blob):
        issues.append("archive size field mismatch")
    if header != index_end:
        issues.append("header size mismatch")
    if count != len(files):
        issues.append("count mismatch")
    expected = header
    for name, off, size in sorted(files, key=lambda x: x[1]):
        if off != expected:
            issues.append(f"overlap/gap {name}")
            break
        expected = off + size
    if expected != len(blob):
        issues.append("trailing gap/overflow")
    lows = [n.replace("/", "\\").lower() for n, _, _ in files]
    if len(lows) != len(set(lows)):
        issues.append("duplicate paths")
    return issues


def command_block(text: str, kind: str, name: str) -> str | None:
    matches = list(re.finditer(rf"(?ms)^{kind} {re.escape(name)}\r?\n.*?^End", text))
    return matches[-1].group(0) if matches else None


def slot_map(block: str | None) -> dict[int, str]:
    out: dict[int, str] = {}
    if not block:
        return out
    for m in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", block, re.M):
        out[int(m.group(1))] = m.group(2)
    return out


def field(block: str | None, key: str) -> str:
    if not block:
        return ""
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block, re.M)
    return m.group(1).strip() if m else ""


def first_object(text: str, name: str) -> str:
    m = re.search(rf"(?ms)^Object {re.escape(name)}\r?\n.*?(?=^Object |\Z)", text)
    if not m:
        raise SystemExit(f"missing Object {name}")
    return m.group(0)


def splice_block(text: str, old: str, new: str) -> str:
    idx = text.rfind(old)
    if idx < 0:
        raise SystemExit("splice target not found")
    return text[:idx] + new + text[idx + len(old) :]


def patch_launcher(text: str) -> str:
    obj = first_object(text, "Iraq_Alhussaien")
    if field(obj, "BuildTime") != "1200":
        raise SystemExit(f"unexpected BuildTime {field(obj, 'BuildTime')}")
    if field(obj, "BuildCost") != "20000":
        raise SystemExit(f"unexpected BuildCost {field(obj, 'BuildCost')}")
    new = obj
    new, n = re.subn(r"^(\s*BuildTime\s*=\s*)1200\s*$", r"\g<1>30.0", new, count=1, flags=re.M)
    if n != 1:
        raise SystemExit("BuildTime replace failed")
    new, n = re.subn(
        r"^(\s*CommandSet\s*=\s*)Iraq_AlhussaienCommandSet\s*$",
        r"\1Iraq_AlhussaienArmedCommandSet",
        new,
        count=1,
        flags=re.M,
    )
    if n != 1:
        raise SystemExit("CommandSet replace failed")
    new, n = re.subn(
        r"^(\s*InitialPayload\s*=\s*)GenericFakeRider1_Default_Rank 1\s*$",
        r"\1GenericFakeRider2_Default_Rank 1",
        new,
        count=1,
        flags=re.M,
    )
    if n != 1:
        raise SystemExit("InitialPayload replace failed")
    ocu = (
        "  Behavior = ObjectCreationUpgrade ModuleTag_Rearm\r\n"
        "    UpgradeObject = OCL_HussienWareheadRearm\r\n"
        "  End"
    )
    ocu_new = (
        "  Behavior = ObjectCreationUpgrade ModuleTag_Rearm\r\n"
        "    TriggeredBy    = Upgrade_AlhussaienWarheadRearm\r\n"
        "    UpgradeObject  = OCL_HussienWareheadRearm\r\n"
        "  End"
    )
    if ocu not in new:
        raise SystemExit("ObjectCreationUpgrade block missing")
    new = new.replace(ocu, ocu_new, 1)
    if "PackTime = 6700" not in new or "UnpackTime = 6735" not in new:
        raise SystemExit("deploy timings lost")
    if "Command_IraqDeployUnitWeapon" in new:
        pass
    return splice_block(text, obj, new)


def patch_commandbuttons(cb: str) -> str:
    old_t = command_block(cb, "CommandButton", "Command_TacticalStrike")
    if not old_t:
        raise SystemExit("missing Command_TacticalStrike")
    if command_block(cb, "CommandButton", NEW_FIRE_BTN):
        raise SystemExit("new fire button already present")
    if "NEED_SPECIAL_POWER_SCIENCE" not in old_t:
        raise SystemExit("baseline TacticalStrike missing science lock")
    cb = splice_block(cb, old_t, old_t + "\r\n\r\n" + NEW_FIRE_BUTTON)
    old_a = command_block(cb, "CommandButton", "Command_AlAbidMissileStrike")
    if not old_a:
        raise SystemExit("missing Command_AlAbidMissileStrike")
    new_a = old_a.replace(
        "  Options             = OK_FOR_MULTI_SELECT NEED_TARGET_POS CONTEXTMODE_COMMAND NEED_SPECIAL_POWER_SCIENCE\r\n",
        "  Options             = OK_FOR_MULTI_SELECT NEED_TARGET_POS CONTEXTMODE_COMMAND\r\n",
        1,
    )
    new_a = re.sub(r"^  SpecialPower        = Iraq_AlhussainMissile\r\n", "", new_a, count=1, flags=re.M)
    if "NEED_SPECIAL_POWER_SCIENCE" in new_a or "SpecialPower" in new_a:
        raise SystemExit("AlAbid science lock not stripped")
    if field(new_a, "Command") != "FIRE_WEAPON" or field(new_a, "WeaponSlot") != "PRIMARY":
        raise SystemExit("AlAbid fire path changed")
    return splice_block(cb, old_a, new_a)


def patch_commandsets(cs: str) -> str:
    old = command_block(cs, "CommandSet", "Iraq_AlhussaienArmedCommandSet")
    if not old:
        raise SystemExit("missing armed CommandSet")
    if "1 = Command_TacticalStrike" not in old:
        raise SystemExit("armed set missing TacticalStrike")
    new = old.replace("1 = Command_TacticalStrike", f"1 = {NEW_FIRE_BTN}", 1)
    sl = slot_map(new)
    if sl.get(1) != NEW_FIRE_BTN:
        raise SystemExit("armed slot 1 not retargeted")
    if sl.get(5) != "Command_AlAbidMissileStrike":
        raise SystemExit("armed slot 5 lost")
    if sl.get(12) != "Command_IraqDeployUnitWeapon":
        raise SystemExit("deploy button lost")
    return splice_block(cs, old, new)


def validate(data: dict[str, bytes], src: dict[str, bytes]) -> list[str]:
    fails: list[str] = []
    changed = sorted(k for k in set(src) | set(data) if src.get(k) != data.get(k))
    allowed = {LAUNCHER_KEY, CB_KEY, CS_KEY}
    unexpected = [k for k in changed if k not in allowed]
    if unexpected:
        fails.append(f"unexpected mutated files: {unexpected[:8]}")
    if set(data) != set(src):
        fails.append("packed file set changed")

    obj = first_object(data[LAUNCHER_KEY].decode("latin1"), "Iraq_Alhussaien")
    src_obj = first_object(src[LAUNCHER_KEY].decode("latin1"), "Iraq_Alhussaien")
    if field(obj, "BuildTime") != "30.0":
        fails.append(f"BuildTime {field(obj, 'BuildTime')}")
    if field(src_obj, "BuildTime") != "1200":
        fails.append("baseline BuildTime not 1200")
    if field(obj, "BuildCost") != "20000" or field(obj, "BuildCost") != field(src_obj, "BuildCost"):
        fails.append("BuildCost changed")
    if field(obj, "CommandSet") != "Iraq_AlhussaienArmedCommandSet":
        fails.append("default CommandSet not armed")
    if "InitialPayload        = GenericFakeRider2_Default_Rank 1" not in obj:
        fails.append("not starting as Rider2")
    if "TriggeredBy    = Upgrade_AlhussaienWarheadRearm" not in obj:
        fails.append("Rearm TriggeredBy missing")
    if "PackTime = 6700" not in obj or "UnpackTime = 6735" not in obj:
        fails.append("deploy timings changed")
    if "Weapon            = SECONDARY  HussieanMissileWeapon" not in obj:
        fails.append("HussieanMissileWeapon lost")
    if "Weapon            = PRIMARY    AlAbidMissileWeapon" not in obj:
        fails.append("AlAbidMissileWeapon lost")
    if re.search(r"^\s*Prerequisites\b", obj, re.M):
        fails.append("gained Prerequisites")

    cb = data[CB_KEY].decode("latin1")
    src_cb = src[CB_KEY].decode("latin1")
    prod = command_block(cb, "CommandButton", "Command_ConstructIraq_Alhussaien")
    src_prod = command_block(src_cb, "CommandButton", "Command_ConstructIraq_Alhussaien")
    if prod != src_prod:
        fails.append("production button mutated")
    if field(prod, "Object") != "Iraq_Alhussaien" or field(prod, "Command") != "UNIT_BUILD":
        fails.append("production mapping broken")
    fire = command_block(cb, "CommandButton", NEW_FIRE_BTN)
    if not fire:
        fails.append("new fire button missing")
    if "NEED_SPECIAL_POWER_SCIENCE" in (fire or "") or re.search(r"^\s*SpecialPower\s*=", fire or "", re.M):
        fails.append("new fire button still science-locked")
    if field(fire, "Command") != "FIRE_WEAPON" or field(fire, "WeaponSlot") != "SECONDARY":
        fails.append("new fire button not FIRE_WEAPON SECONDARY")
    shared = command_block(cb, "CommandButton", "Command_TacticalStrike")
    src_shared = command_block(src_cb, "CommandButton", "Command_TacticalStrike")
    if shared != src_shared:
        fails.append("shared Command_TacticalStrike mutated")
    if "NEED_SPECIAL_POWER_SCIENCE" not in (shared or ""):
        fails.append("Iskander science lock stripped")
    alabid = command_block(cb, "CommandButton", "Command_AlAbidMissileStrike")
    if "NEED_SPECIAL_POWER_SCIENCE" in (alabid or "") or re.search(r"^\s*SpecialPower\s*=", alabid or "", re.M):
        fails.append("AlAbid still science-locked")
    if field(alabid, "WeaponSlot") != "PRIMARY":
        fails.append("AlAbid slot changed")
    deploy = command_block(cb, "CommandButton", "Command_IraqDeployUnitWeapon")
    src_deploy = command_block(src_cb, "CommandButton", "Command_IraqDeployUnitWeapon")
    if deploy != src_deploy:
        fails.append("deploy button mutated")

    cs = data[CS_KEY].decode("latin1")
    src_cs = src[CS_KEY].decode("latin1")
    armed = slot_map(command_block(cs, "CommandSet", "Iraq_AlhussaienArmedCommandSet"))
    if armed.get(1) != NEW_FIRE_BTN:
        fails.append(f"armed slot 1 {armed.get(1)}")
    if armed.get(12) != "Command_IraqDeployUnitWeapon":
        fails.append("armed deploy lost")
    unarmed = command_block(cs, "CommandSet", "Iraq_AlhussaienCommandSet")
    src_unarmed = command_block(src_cs, "CommandSet", "Iraq_AlhussaienCommandSet")
    if unarmed != src_unarmed:
        fails.append("unarmed CommandSet mutated")
    isk = command_block(cs, "CommandSet", "IskanderCommandSet_Armed")
    src_isk = command_block(src_cs, "CommandSet", "IskanderCommandSet_Armed")
    if isk != src_isk:
        fails.append("Iskander CommandSet mutated")
    wf = slot_map(command_block(cs, "CommandSet", "Iraq_WarFactoryCommandSet_T3"))
    if wf != IRAQ_WF_SLOTS:
        fails.append("Iraq WF T3 slots changed")
    factory = slot_map(command_block(cs, "CommandSet", "Iraq_AlFahdMissileFactoryCommandSet"))
    if factory != FACTORY_SLOTS:
        fails.append("missile factory slots changed")

    # PR #590 preserved
    d = first_object(data[UNIT_D_KEY].decode("latin1"), "Iraq_AlAbbas")
    if field(d, "BuildTime") != "30.0":
        fails.append("PR #590 Iraq_AlAbbas BuildTime lost")
    weap = data[WEAPON_KEY].decode("latin1")
    src_weap = src[WEAPON_KEY].decode("latin1")
    if weap != src_weap:
        fails.append("Weapon.ini mutated")
    w_abbas = command_block(weap, "Weapon", "Weapon_Iraq_AlAbbas")
    if w_abbas and re.search(r"AutoReloadsClip", w_abbas):
        fails.append("PR #590 AutoReloadsClip reverted")
    for name in ("HussieanMissileWeapon", "AlAbidMissileWeapon"):
        if command_block(weap, "Weapon", name) != command_block(src_weap, "Weapon", name):
            fails.append(f"{name} mutated")
        w = command_block(weap, "Weapon", name)
        if field(w, "ClipReloadTime") != "4000":
            fails.append(f"{name} ClipReloadTime changed")

    up = data[UPGRADE_KEY].decode("latin1")
    src_up = src[UPGRADE_KEY].decode("latin1")
    if up != src_up:
        fails.append("Upgrade.ini mutated")
    rearm = command_block(up, "Upgrade", "Upgrade_AlhussaienWarheadRearm")
    if field(rearm, "BuildTime") != "500.0":
        fails.append("post-shot rearm time changed")

    if data[LAUNCHER_AI_KEY] != src[LAUNCHER_AI_KEY]:
        fails.append("Iraq_Alhussaien_AI mutated")
    ai = first_object(data[LAUNCHER_AI_KEY].decode("latin1"), "Iraq_Alhussaien_AI")
    if not field(ai, "BuildTime").startswith("20.0"):
        fails.append("AI BuildTime changed")
    if data[UNIT_A_KEY] != src[UNIT_A_KEY]:
        fails.append("Missile A mutated")
    if data[UNIT_D_KEY] != src[UNIT_D_KEY]:
        fails.append("PR #590 Iraq_AlAbbas object mutated")
    if data[UNLOCK_KEY] != src[UNLOCK_KEY]:
        fails.append("PR #589 EU5 unlock mutated")
    if data[R11_KEY] != src[R11_KEY]:
        fails.append("9P117 mutated")
    if data[FACTORY_KEY] != src[FACTORY_KEY]:
        fails.append("missile factory mutated")
    if data[PT_KEY] != src[PT_KEY]:
        fails.append("PlayerTemplate mutated")
    if data[LOCO_KEY] != src[LOCO_KEY]:
        fails.append("Locomotor mutated")
    return fails


def dump_extract(extracted: dict[str, bytes]) -> None:
    stage = OUT / "LAST_WINS_EXTRACT/DATA"
    keys = [LAUNCHER_KEY, CB_KEY, CS_KEY, UNIT_D_KEY, UNLOCK_KEY]
    for rel in keys:
        p = stage / rel.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(extracted[rel])


def independent_extract_audit(packed: bytes) -> list[str]:
    fails: list[str] = []
    clean = OUT / "CLEAN_EXTRACT"
    if clean.exists():
        shutil.rmtree(clean)
    extracted = parse_big(packed)
    for name, blob in extracted.items():
        p = clean / name.replace("\\", "/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(blob)
    launcher = (clean / "Data/INI/Object/Specter/Iraq Army/Wheeled/AbbasLauncher.ini").read_text(encoding="latin1")
    obj = first_object(launcher, "Iraq_Alhussaien")
    cb = (clean / "Data/INI/CommandButton.ini").read_text(encoding="latin1")
    cs = (clean / "Data/INI/CommandSet.ini").read_text(encoding="latin1")
    if field(obj, "BuildTime") != "30.0":
        fails.append(f"clean BuildTime {field(obj, 'BuildTime')}")
    if field(obj, "BuildCost") != "20000":
        fails.append("clean BuildCost")
    if "GenericFakeRider2_Default_Rank 1" not in obj:
        fails.append("clean not Rider2")
    prod = command_block(cb, "CommandButton", "Command_ConstructIraq_Alhussaien")
    if field(prod, "Object") != "Iraq_Alhussaien":
        fails.append("clean production mapping")
    fire = command_block(cb, "CommandButton", NEW_FIRE_BTN)
    if not fire or "NEED_SPECIAL_POWER_SCIENCE" in fire:
        fails.append("clean fire button")
    armed = slot_map(command_block(cs, "CommandSet", "Iraq_AlhussaienArmedCommandSet"))
    if armed.get(1) != NEW_FIRE_BTN or armed.get(12) != "Command_IraqDeployUnitWeapon":
        fails.append("clean armed CommandSet")
    wf = slot_map(command_block(cs, "CommandSet", "Iraq_WarFactoryCommandSet_T3"))
    if wf.get(10) != "Command_ConstructIraq_Alhussaien" or wf.get(8) != "Command_ConstructIraq_SA-6" or wf.get(12) != "Command_ConstructIraq_BM-21":
        fails.append("clean WF neighbors")
    d = first_object(
        (clean / "Data/INI/Object/Specter/Iraq Army/Wheeled/Iraq_AlAbbas.ini").read_text(encoding="latin1"),
        "Iraq_AlAbbas",
    )
    if field(d, "BuildTime") != "30.0":
        fails.append("clean PR #590 AlAbbas lost")
    file_count = sum(1 for p in clean.rglob("*") if p.is_file())
    if file_count != len(extracted):
        fails.append(f"clean file count {file_count} != {len(extracted)}")
    return fails


def main() -> int:
    if not SRC_DATA.is_file():
        raise SystemExit(f"missing PR #590 DATA BIG at {SRC_DATA}")
    if SRC_DATA.stat().st_size != BASE_DATA_SIZE or sha256_path(SRC_DATA) != BASE_DATA_SHA:
        raise SystemExit("PR #590 DATA baseline mismatch")
    if SRC_ART.is_file():
        if SRC_ART.stat().st_size != BASE_ART_SIZE or sha256_path(SRC_ART) != BASE_ART_SHA:
            raise SystemExit("ART baseline mismatch")

    src = parse_big(SRC_DATA.read_bytes())
    data = dict(src)
    data[LAUNCHER_KEY] = patch_launcher(data[LAUNCHER_KEY].decode("latin1")).encode("latin1")
    data[CB_KEY] = patch_commandbuttons(data[CB_KEY].decode("latin1")).encode("latin1")
    data[CS_KEY] = patch_commandsets(data[CS_KEY].decode("latin1")).encode("latin1")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    packed_data = build_big(data)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_data.write_bytes(packed_data)
    extracted = parse_big(out_data.read_bytes())
    dump_extract(extracted)

    fails = validate(extracted, src)
    fails.extend(f"DATA {x}" for x in big_structure_ok(packed_data))
    fails.extend(f"CLEAN {x}" for x in independent_extract_audit(out_data.read_bytes()))

    data_sha = sha256_path(out_data)
    changed = sorted(k for k in extracted if src.get(k) != extracted.get(k))
    report = [
        "# SPECTER Iraq Al Abbas ICBM Launcher (Iraq_Alhussaien): 30s + fire",
        "",
        "Baseline DATA: PR #590 (Al-Abbas missile-D 30s on PR #589).",
        "Baseline ART: PR #574 ART BIG (unchanged, not rebuilt).",
        "",
        "Screenshot unit is NOT missile-factory Iraq_AlAbbas (CB_MISSILE_D, $2600).",
        "It is War Factory slot 10 Command_ConstructIraq_Alhussaien -> Iraq_Alhussaien",
        "($20000, CSF title 'Al Abbas ICBM Launcher', between SA-6 and BM-21 Grad).",
        "",
        "BuildTime: 1200 -> 30.0 on Object Iraq_Alhussaien only.",
        "Fire: start armed (Rider2), Iraq-only FIRE_WEAPON button without science,",
        "AlAbid science lock stripped (Iraq-only button). Deploy + 500s post-shot",
        "rearm upgrade time preserved. Iskander Command_TacticalStrike unchanged.",
        "PR #590 Iraq_AlAbbas 30.0 / AutoReloadsClip fix preserved.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {data_sha}",
        f"- DATA files: {len(extracted)}",
        f"- ART SHA256 (unchanged): {BASE_ART_SHA}",
        f"- ART size (unchanged): {BASE_ART_SIZE}",
        f"- Changed packed files: {', '.join(changed)}",
        "",
    ]
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        report.append("RUNTIME_TEST=NOT RUN")
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("\n".join(report))
        return 1

    report += [
        "## VALIDATION PASS (static / packed last-wins + independent re-extract)",
        "- Screenshot button Command_ConstructIraq_Alhussaien still Object=Iraq_Alhussaien",
        "- Iraq_Alhussaien BuildTime is exactly 30.0, BuildCost 20000",
        "- Starts GenericFakeRider2 / ArmedCommandSet (WEAPON_RIDER2 ICBM loaded)",
        "- Command_IraqAlAbbasICBMFire = FIRE_WEAPON SECONDARY, no science",
        "- Command_AlAbidMissileStrike science lock removed (Iraq-only)",
        "- Deploy Command_IraqDeployUnitWeapon + Pack/Unpack 6700/6735 preserved",
        "- Post-shot Upgrade_AlhussaienWarheadRearm BuildTime still 500.0",
        "- Iskander Command_TacticalStrike unchanged",
        "- PR #590 Iraq_AlAbbas BuildTime 30.0 preserved; Weapon.ini unchanged this patch",
        "- PR #589 EU5 unlock unchanged; Missile A / 9P117 / factory unchanged",
        "- Independent clean extract repeated the same audit",
        "- ART not rebuilt",
        "",
        "Static validation completed; runtime game test not performed.",
        "",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    (OUT / "HASHES.txt").write_text(
        "DATA_CHANGED=YES\n"
        "ART_CHANGED=NO\n"
        "DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={data_sha}\n"
        f"DATA_FILES={len(extracted)}\n"
        "ART_FILE=PR574 _SPEC_ART_ONE.big (not rebuilt)\n"
        f"ART_SIZE={BASE_ART_SIZE}\n"
        f"ART_SHA256={BASE_ART_SHA}\n"
        "SCREENSHOT_OBJECT=Iraq_Alhussaien\n"
        "PRODUCTION_BUTTON=Command_ConstructIraq_Alhussaien\n"
        "PRODUCTION_COMMANDSET=Iraq_WarFactoryCommandSet_T3\n"
        "PRODUCTION_SLOT=10\n"
        "BUILD_COST=20000\n"
        "BUILD_TIME_BEFORE=1200\n"
        "BUILD_TIME_AFTER=30.0\n"
        "CSF_TITLE=Al Abbas ICBM Launcher\n"
        "FIRE_LOCKS=unarmed Rider1 spawn + NEED_SPECIAL_POWER_SCIENCE on fire buttons\n"
        "FIRE_FIX=start Rider2/armed; Command_IraqAlAbbasICBMFire; strip AlAbid science\n"
        "DEPLOY=Command_IraqDeployUnitWeapon PRESERVED\n"
        "POST_SHOT_REARM=Upgrade_AlhussaienWarheadRearm BuildTime 500.0 UNCHANGED\n"
        f"CHANGED_FILES={', '.join(changed)}\n"
        "BASELINE_DATA=PR #590\n"
        "BASELINE_ART=PR #574\n"
        "PR590_IRAQ_ALABBAS=PRESERVED\n"
        "PR589_EU5=PRESERVED\n"
        "STATIC_VALIDATION=PASS\n"
        "RUNTIME_TEST=NOT RUN\n",
        encoding="utf-8",
    )
    (OUT / "LAST_WINS.txt").write_text(
        "SCREENSHOT=Al Abbas ICBM Launcher / cost 20000 / between SA-6 and BM-21 Grad\n"
        "BUTTON=Command_ConstructIraq_Alhussaien UNIT_BUILD Object=Iraq_Alhussaien\n"
        "OBJECT=Iraq_Alhussaien file=Data\\INI\\Object\\Specter\\Iraq Army\\Wheeled\\AbbasLauncher.ini defs=1\n"
        "NOT_SCREENSHOT=Iraq_AlAbbas CB_MISSILE_D cost 2600 (PR #590, preserved)\n"
        "WF_T3_SLOT10=Command_ConstructIraq_Alhussaien\n"
        "ARMED_SET=Iraq_AlhussaienArmedCommandSet slot1 Command_IraqAlAbbasICBMFire\n"
        "ISKANDER=Command_TacticalStrike UNCHANGED\n",
        encoding="utf-8",
    )
    (OUT / "README.txt").write_text(
        "SPECTER: Iraq Al Abbas ICBM Launcher (War Factory) 30s + fire\n"
        "\n"
        "The production button labeled 'Al Abbas ICBM Launcher' (between\n"
        "2K12 KUB and BM-21 Grad, cost 20000) builds Object Iraq_Alhussaien.\n"
        "BuildTime is now 30 seconds. The launcher starts armed and can fire\n"
        "after its normal deploy sequence, without a science purchase or the\n"
        "500-second first-load rearm. Post-shot rearm time is unchanged.\n"
        "\n"
        "Place this complete replacement DATA BIG in the SPECTER folder:\n"
        "  _SPEC_DATA_ONE.big\n"
        "\n"
        "Keep the existing PR #574/_SPEC_ART_ONE.big (not rebuilt):\n"
        f"  SHA256={BASE_ART_SHA}\n"
        "\n"
        "Static validation completed; runtime game test not performed.\n",
        encoding="utf-8",
    )
    zip_path = ROOT / "patch/Release/SPECTER_IRAQ_ALHUSSAIEN_ICBM_30S_FIRE.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(OUT / "README.txt", "README.txt")
        zf.write(OUT / "HASHES.txt", "HASHES.txt")
        zf.write(OUT / "VALIDATE_REPORT.txt", "VALIDATE_REPORT.txt")
    print("\n".join(report))
    print(f"ZIP {zip_path} size={zip_path.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
