"""Build an experimental SPECTER DATA+ART BIG pair for ChinaCSSA1 and ChinaHQ11.

Writes only to an experimental output directory. Original SPECTER FINAL BIGs are
never opened for write. No loose INI is emitted.
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from . import archive, big, data_rebuild, ini
from .art_index import ArtIndex
from .rewrite import independent_name, rewrite_text

SAMPLE_OBJECTS = ("ChinaCSSA1", "ChinaHQ11")

# Extracted from SPECTER Object ChinaWarFactory (Data\INI\Object\Specter\PLA\Buildings\Warfactory.ini):
# CommandSet = PLAWarFactoryCommandSet. Slots 4, 7, 15, 18 are unused in SPECTER FINAL.
SPECTER_CHINA_FACTORY_OBJECT = "ChinaWarFactory"
SPECTER_CHINA_FACTORY_COMMANDSET = "PLAWarFactoryCommandSet"
CSSA1_FACTORY_SLOT = "4"
HQ11_FACTORY_SLOT = "7"

EMIT_KINDS = {
    "Object",
    "Weapon",
    "Armor",
    "Locomotor",
    "FXList",
    "DamageFX",
    "CrateData",
    "CrateTemplate",
    "ObjectCreationList",
    "ParticleSystem",
    "AudioEvent",
    "MappedImage",
}

SKIP_IMPORT_NAMES = {
    "command_constructchinacssa1",
    "command_constructchinahq11",
    "ssattackmove2",
    "sdguard",
    "sdstop",
}

SKIP_ART_STEMS = {
    "ssattackmove2",
    "sdguard",
    "sdstop",
    "ssuserinterface512_001",
    "ssuserinterface512_001.tga",
}

KIND_BUNDLE = {
    "Object": None,  # per-object unique path
    "Weapon": r"Data\INI\Weapon\SilentDeath\SD25_Weapons.ini",
    "Armor": r"Data\INI\Armor_SilentDeath.ini",
    "Locomotor": r"Data\INI\Locomotor_SilentDeath.ini",
    "FXList": r"Data\INI\FXList_SilentDeath.ini",
    "DamageFX": r"Data\INI\DamageFX_SilentDeath.ini",
    "CrateData": r"Data\INI\Crate_SilentDeath.ini",
    "CrateTemplate": r"Data\INI\Crate_SilentDeath.ini",
    "ObjectCreationList": r"Data\INI\ObjectCreationList_SilentDeath.ini",
    "ParticleSystem": r"Data\INI\ParticleSystem_SilentDeath.ini",
    "AudioEvent": r"Data\INI\SoundEffects_SilentDeath.ini",
    "MappedImage": r"Data\INI\MappedImages\SilentDeath\SilentDeathMappedImages.ini",
}

PORTRAIT_IMAGES = {"cssa1tb", "chhq11tb"}

RIDER_CONTAIN_RE = re.compile(
    r"^\s*Behavior\s*=\s*RiderChangeContain\b.*?^\s*End\s*$",
    re.I | re.M | re.S,
)
OCL_POWER_RE = re.compile(
    r"^\s*Behavior\s*=\s*OCLSpecialPower\b.*?^\s*End\s*$",
    re.I | re.M | re.S,
)
AIUPDATE_RE = re.compile(
    r"^\s*Behavior\s*=\s*AIUpdateInterface\b.*?^\s*End\s*$",
    re.I | re.M | re.S,
)
WEAPONSET_BLOCK_RE = re.compile(
    r"^\s*WeaponSet\b.*?^\s*End\s*$",
    re.I | re.M | re.S,
)


def unique_def_name(kind: str, name: str, action: str, planned: str | None) -> str | None:
    if kind not in EMIT_KINDS:
        return None
    if action in ("REUSE_NATIVE", "CYCLE", "BLOCKED"):
        return None
    if action == "MANUAL_REBUILD":
        return None
    if (name or "").lower() in SKIP_IMPORT_NAMES:
        return None
    if kind in ("MappedImage", "CommandSet", "CommandButton"):
        return None
    if action == "INDEPENDENT_ADD" and planned and planned.upper().startswith("SD25_"):
        return planned
    if action == "RENAME_AND_REWRITE" and planned:
        return planned if planned.upper().startswith("SD25_") else independent_name(planned)
    if action in ("IMPORT_UNIQUE", "INDEPENDENT_ADD", "RECOVER_FROM_V25"):
        return independent_name(name)
    return None


def build_rename_map(rows: list[dict]) -> dict[str, str]:
    mp: dict[str, str] = {}
    for row in rows:
        if row.get("action") == "CYCLE":
            continue
        new = unique_def_name(row.get("kind") or "", row.get("name") or "", row.get("action") or "", row.get("planned"))
        old = row.get("name") or ""
        if new and old and new != old:
            mp[old] = new
        if row.get("kind") == "CommandSet" and (row.get("name") or "").startswith("SD25_"):
            mp[row["name"]] = row["name"]
    return mp


def object_ini_path(side: str, name: str) -> str:
    return rf"Data\INI\Object\SilentDeath\{side}\{name}.ini"


def rewrite_header(kind: str, new_name: str, body: str) -> str:
    lines = (body or "").splitlines()
    header = f"{kind} {new_name}"
    if lines:
        first = lines[0].strip()
        if first.lower().startswith(kind.lower()):
            lines[0] = header
        else:
            lines.insert(0, header)
    else:
        lines = [header, "End"]
    return "\n".join(lines) + "\n"


def strip_behavior_blocks(body: str, pattern: re.Pattern) -> str:
    return pattern.sub("", body)


def transform_hq11_body(body: str, deployed_weapon: str) -> str:
    """CWC riders/OCL → stock DeployStyleAIUpdate + DEPLOYED WeaponSet. Preview applied to unique Object."""
    text = body
    text = strip_behavior_blocks(text, RIDER_CONTAIN_RE)
    text = strip_behavior_blocks(text, OCL_POWER_RE)
    deploy_block = (
        "  Behavior = DeployStyleAIUpdate ModuleTag_SD25_Deploy\n"
        "    AutoAcquireEnemiesWhenIdle = Yes Stealthed\n"
        "    MoodAttackCheckRate = 150\n"
        f"    PackTime = {data_rebuild.HQ11_PACK_MS}\n"
        f"    UnpackTime = {data_rebuild.HQ11_PACK_MS}\n"
        "    TurretsFunctionOnlyWhenDeployed = Yes\n"
        "    TurretsMustCenterBeforePacking = Yes\n"
        "    ResetTurretBeforePacking = Yes\n"
        "  End\n"
    )
    if AIUPDATE_RE.search(text):
        text = AIUPDATE_RE.sub(deploy_block, text, count=1)
    else:
        text += "\n" + deploy_block

    weapon_blocks = (
        "  WeaponSet\n"
        "    Conditions = None\n"
        "    Weapon = PRIMARY None\n"
        "  End\n"
        "  WeaponSet\n"
        "    Conditions = DEPLOYED\n"
        f"    Weapon = PRIMARY {deployed_weapon}\n"
        "    AutoChooseSources = PRIMARY FROM_PLAYER FROM_AI FROM_SCRIPT\n"
        "    PreferredAgainst = PRIMARY BALLISTIC_MISSILE AIRCRAFT\n"
        "  End\n"
    )
    if WEAPONSET_BLOCK_RE.search(text):
        first = True

        def _sub(m, _first=[]):
            if not _first:
                _first.append(True)
                return weapon_blocks
            return ""

        text = WEAPONSET_BLOCK_RE.sub(_sub, text)
    else:
        text = weapon_blocks + text

    # Duplicate complete RIDER2 ConditionState groups as DEPLOYED inside the Draw.
    text = map_rider2_draw_to_deployed(text)

    text = re.sub(
        r"^\s*Locomotor\s*=\s*SET_SLUGGISH\s+\S+\s*$",
        "  ; SET_SLUGGISH deployed locomotor not bound: stock DeployStyle cannot switch locomotor sets.",
        text,
        flags=re.I | re.M,
    )
    text = re.sub(
        r"^\s*CommandSet\s*=\s*\S+\s*$",
        "  CommandSet = SD25_ChinaHQ11CommandSet",
        text,
        flags=re.I | re.M,
        count=1,
    )
    return text


def strip_after_object_end(text: str) -> str:
    """Drop tokens that leaked past the Object's column-0 End."""
    lines = text.splitlines()
    last = None
    for i, line in enumerate(lines):
        if re.match(r"^End\s*$", line, re.I):
            last = i
    if last is None:
        return text if text.endswith("\n") else text + "\n"
    return "\n".join(lines[: last + 1]) + "\n"


def map_rider2_draw_to_deployed(text: str) -> str:
    """Copy complete RIDER2 ConditionState groups as DEPLOYED inside the same Draw.

    Never leaves ConditionState/AliasConditionState after the Object End.
    """
    text = strip_after_object_end(text)
    lines = text.splitlines()
    extra: list[str] = []
    last_rider = None
    i = 0
    while i < len(lines):
        if re.match(r"^\s*ConditionState\s*=\s*.*\bRIDER2\b", lines[i], re.I):
            block = [re.sub(r"\bRIDER2\b", "DEPLOYED", lines[i], flags=re.I)]
            i += 1
            while i < len(lines) and not re.match(r"^\s*End\s*$", lines[i], re.I):
                block.append(lines[i])
                i += 1
            if i < len(lines):
                block.append(lines[i])
                i += 1
            while i < len(lines) and re.match(
                r"^\s*AliasConditionState\s*=\s*.*\bRIDER2\b", lines[i], re.I
            ):
                block.append(re.sub(r"\bRIDER2\b", "DEPLOYED", lines[i], flags=re.I))
                i += 1
            extra.extend(block)
            extra.append("")
            last_rider = i - 1
            continue
        if re.search(r"\bRIDER2\b", lines[i], re.I):
            last_rider = i
        i += 1
    inside = "\n".join(lines)
    already = re.search(r"(?im)^\s*ConditionState\s*=\s*DEPLOYED\b", inside)
    if extra and last_rider is not None and not already:
        lines = lines[: last_rider + 1] + extra + lines[last_rider + 1 :]
    return "\n".join(lines) + "\n"


def insert_lines_after_last_rider2(text: str, extra: list[str]) -> str:
    """Keep extra Draw lines inside the same Draw as RIDER2, before Object End."""
    lines = text.splitlines()
    last = None
    for i, line in enumerate(lines):
        if re.search(r"\bRIDER2\b", line, re.I):
            last = i
    if last is None:
        for i in range(len(lines) - 1, -1, -1):
            if re.match(r"^End\s*$", lines[i], re.I):
                last = i - 1
                break
    if last is None:
        last = len(lines) - 1
    return "\n".join(lines[: last + 1] + extra + lines[last + 1 :]) + "\n"


def split_named_blocks(kind: str, text: str) -> list[str]:
    return re.split(rf"(?=^{re.escape(kind)}\s+(?![=])\S+)", text, flags=re.I | re.M)


def repair_armor_file(text: str) -> str:
    return "".join(dedupe_named_blocks("Armor", split_named_blocks("Armor", text)))


STAGE5_FXLIST_PATH = r"Data\INI\FXList_SilentDeath.ini"
STAGE5_HQ11_PATH = r"Data\INI\Object\SilentDeath\China\SD25_ChinaHQ11.ini"
STAGE5_ARMOR_PATH = r"Data\INI\Armor_SilentDeath.ini"


def repair_stage5_payloads(payloads: dict[str, bytes]) -> dict[str, bytes]:
    """Fix the three diagnosed Stage 5 INI payloads. Names and FX effect bodies stay."""
    by_key = {big.nkey(n): (n, blob) for n, blob in payloads.items()}
    out: dict[str, bytes] = {}
    fx_key = big.nkey(STAGE5_FXLIST_PATH)
    hq_key = big.nkey(STAGE5_HQ11_PATH)
    ar_key = big.nkey(STAGE5_ARMOR_PATH)
    if fx_key in by_key:
        name, blob = by_key[fx_key]
        out[name] = close_fxlist_blocks(blob.decode("latin1", errors="replace")).encode("latin1", errors="replace")
    if hq_key in by_key:
        name, blob = by_key[hq_key]
        out[name] = map_rider2_draw_to_deployed(blob.decode("latin1", errors="replace")).encode(
            "latin1", errors="replace"
        )
    if ar_key in by_key:
        name, blob = by_key[ar_key]
        out[name] = repair_armor_file(blob.decode("latin1", errors="replace")).encode("latin1", errors="replace")
    missing = [p for p, k in (
        (STAGE5_FXLIST_PATH, fx_key),
        (STAGE5_HQ11_PATH, hq_key),
        (STAGE5_ARMOR_PATH, ar_key),
    ) if k not in by_key]
    if missing:
        raise ValueError("repair_stage5_payloads missing: " + ", ".join(missing))
    return out


def close_fxlist_blocks(text: str) -> str:
    """SPECTER FXList.ini uses nested End plus a column-0 End per FXList."""
    chunks = re.split(r"(?=^FXList\s+\S+)", text, flags=re.I | re.M)
    out: list[str] = []
    for chunk in chunks:
        if not re.match(r"^FXList\s+\S+", chunk.lstrip(), re.I):
            out.append(chunk)
            continue
        body = chunk.rstrip() + "\n"
        if not re.search(r"(?m)^End\s*$", body):
            body = body.rstrip() + "\nEnd\n"
        out.append(body)
    return "".join(out)


def dedupe_named_blocks(kind: str, chunks: list[str]) -> list[str]:
    """Keep the first Armor/FXList/etc. body per name."""
    seen: set[str] = set()
    out: list[str] = []
    header = re.compile(rf"^{re.escape(kind)}\s+(\S+)", re.I | re.M)
    for chunk in chunks:
        m = header.search(chunk)
        if not m:
            out.append(chunk)
            continue
        key = m.group(1).lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(chunk)
    return out


def factory_overlay_text(specter_cs: dict, cssa1_btn: str, hq11_btn: str) -> str:
    lines = [f"CommandSet {SPECTER_CHINA_FACTORY_COMMANDSET}"]
    slots = {k.strip(): v.strip() for k, v in (specter_cs.get("keys") or []) if k.strip().isdigit()}
    slots[CSSA1_FACTORY_SLOT] = cssa1_btn
    slots[HQ11_FACTORY_SLOT] = hq11_btn
    for num in sorted(slots, key=lambda x: int(x)):
        lines.append(f"  {num} = {slots[num]}")
    lines.append("End")
    lines.append("")
    lines.append("; Overlay of SPECTER PLAWarFactoryCommandSet via unique last-win path.")
    lines.append("; Original Data\\INI\\CommandSet.ini is not modified. Empty slots 4 and 7 filled.")
    return "\n".join(lines) + "\n"


def construct_button(name: str, object_name: str, image: str, label: str) -> str:
    return (
        f"CommandButton {name}\n"
        f"  Command       = UNIT_BUILD\n"
        f"  Object        = {object_name}\n"
        f"  TextLabel     = {label}\n"
        f"  ButtonImage   = {image}\n"
        f"  ButtonBorderType = BUILD\n"
        f"  DescriptLabel = {label}\n"
        f"End\n"
    )


def deploy_button() -> str:
    return (
        "CommandButton SD25_Command_ChinaHQ11Deploy\n"
        "  Command       = DEPLOY\n"
        "  Options       = OK_FOR_MULTI_SELECT\n"
        "  TextLabel     = CONTROLBAR:Deploy\n"
        "  ButtonImage   = CHHQ11TB\n"
        "  ButtonBorderType = ACTION\n"
        "  DescriptLabel = CONTROLBAR:Deploy\n"
        "End\n"
    )


def hq11_unit_commandset() -> str:
    return (
        "CommandSet SD25_ChinaHQ11CommandSet\n"
        "  1 = SD25_Command_ChinaHQ11Deploy\n"
        "  11 = Command_AttackMove\n"
        "  13 = Command_Guard\n"
        "  14 = Command_Stop\n"
        "End\n"
    )


def mapped_image_from_texture(name: str, filename: str, w: int, h: int) -> str:
    return (
        f"MappedImage {name}\n"
        f"  Texture = {filename}\n"
        f"  TextureWidth = {w}\n"
        f"  TextureHeight = {h}\n"
        f"  Coords = Left:0 Top:0 Right:{w} Bottom:{h}\n"
        f"  Status = NONE\n"
        f"End\n"
    )


def tga_or_dds_size(blob: bytes) -> tuple[int, int]:
    if blob[:4] == b"DDS ":
        h = int.from_bytes(blob[12:16], "little")
        w = int.from_bytes(blob[16:20], "little")
        return max(w, 1), max(h, 1)
    if len(blob) >= 18:
        w = int.from_bytes(blob[12:14], "little")
        h = int.from_bytes(blob[14:16], "little")
        if w and h:
            return w, h
    return 128, 128


def art_dest_path(filename: str) -> str:
    low = filename.lower()
    base = Path(filename.replace("\\", "/")).name
    if low.endswith(".w3d"):
        return rf"Art\W3D\{base}"
    if low.endswith(".wav"):
        return rf"Data\Audio\Sounds\{base}"
    return rf"Art\Textures\{base}"


def vfs_dest_from_rec(filename: str, rec: dict | None) -> str:
    inner = ""
    if rec:
        inner = rec.get("inner") or rec.get("path") or ""
    base = inner.replace("/", "\\")
    low = base.lower()
    if "art\\" in low:
        return "Art\\" + base.split("Art\\", 1)[-1] if "Art\\" in base else "Art\\" + base.split("art\\", 1)[-1]
    if "data\\" in low:
        return "Data\\" + base.split("Data\\", 1)[-1] if "Data\\" in base else "Data\\" + base.split("data\\", 1)[-1]
    return art_dest_path(filename)


HEADER_RE = re.compile(
    r"^(Object|Weapon|Armor|Locomotor|FXList|DamageFX|CrateData|CrateTemplate|"
    r"ObjectCreationList|ParticleSystem|AudioEvent|CommandSet|CommandButton|MappedImage)"
    r"\s+(?![=])([A-Za-z_][A-Za-z0-9_]*)",
    re.I | re.M,
)
ALLOWED_NON_SD25 = {
    ("commandset", "plawarfactorycommandset"),
    ("mappedimage", "cssa1tb"),
    ("mappedimage", "chhq11tb"),
}
def skip_ref_set(plans: dict) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for plan in plans.values():
        for kind, name in (plan.get("deploy_proof") or {}).get("skip_refs") or []:
            out.add((str(kind).lower(), str(name).lower()))
    return out


def validate_added_defs(added_data: dict[str, bytes], added_art: dict[str, bytes]) -> dict:
    errors: list[str] = []
    headers: list[dict] = []
    for path, blob in added_data.items():
        n = big.nkey(path)
        if n in {p.replace("/", "\\").lower() for p in data_rebuild.PUBLIC_INI_BLOCKED}:
            errors.append(f"protected public INI path added: {path}")
        text = blob.decode("latin1", errors="replace")
        for m in HEADER_RE.finditer(text):
            kind, name = m.group(1), m.group(2)
            headers.append({"kind": kind, "name": name, "path": path})
            if (kind.lower(), name.lower()) in ALLOWED_NON_SD25:
                continue
            if not name.upper().startswith("SD25_"):
                errors.append(f"{kind} {name} in {path} is not an independent SD25 name")
    overlay = added_data.get(r"Data\INI\CommandSet_ZZZZ_SilentDeath_China.ini", b"").decode("latin1", errors="replace")
    if f"{CSSA1_FACTORY_SLOT} = SD25_Command_ConstructChinaCSSA1" not in overlay:
        errors.append("ChinaCSSA1 factory slot 4 missing from overlay")
    if f"{HQ11_FACTORY_SLOT} = SD25_Command_ConstructChinaHQ11" not in overlay:
        errors.append("ChinaHQ11 factory slot 7 missing from overlay")
    if "CommandSet PLAWarFactoryCommandSet" not in overlay:
        errors.append("factory overlay does not last-win PLAWarFactoryCommandSet")
    hq11_path = object_ini_path("China", "SD25_ChinaHQ11")
    hq11 = added_data.get(hq11_path, b"").decode("latin1", errors="replace")
    if "DeployStyleAIUpdate" not in hq11:
        errors.append("SD25_ChinaHQ11 missing DeployStyleAIUpdate")
    if "Conditions = DEPLOYED" not in hq11:
        errors.append("SD25_ChinaHQ11 missing DEPLOYED WeaponSet")
    if re.search(r"RiderChangeContain|OCLSpecialPower", hq11, re.I):
        errors.append("SD25_ChinaHQ11 still contains CWC rider/OCL modules")
    if "TurretsFunctionOnlyWhenDeployed = Yes" not in hq11:
        errors.append("SD25_ChinaHQ11 missing TurretsFunctionOnlyWhenDeployed")
    cssa = added_data.get(object_ini_path("China", "SD25_ChinaCSSA1"), b"").decode("latin1", errors="replace")
    if "Object SD25_ChinaCSSA1" not in cssa:
        errors.append("SD25_ChinaCSSA1 object missing")
    if cssa and not re.search(r"(?i)Armor\s*=\s*SD25_TankArmor\b", cssa):
        errors.append("SD25_ChinaCSSA1 must keep Armor = SD25_TankArmor")
    if hq11 and not re.search(r"(?i)Armor\s*=\s*SD25_HumveeArmor\b", hq11):
        errors.append("SD25_ChinaHQ11 must keep Armor = SD25_HumveeArmor")
    if hq11:
        last_end = None
        for i, line in enumerate(hq11.splitlines()):
            if re.match(r"^End\s*$", line, re.I):
                last_end = i
        if last_end is not None:
            after = [ln.strip() for ln in hq11.splitlines()[last_end + 1 :] if ln.strip() and not ln.strip().startswith(";")]
            if after:
                errors.append("SD25_ChinaHQ11 has tokens after Object End: " + "; ".join(after[:6]))
        if "ConditionState = DEPLOYED" not in hq11:
            errors.append("SD25_ChinaHQ11 missing DEPLOYED draw ConditionState")
    fx = added_data.get(r"Data\INI\FXList_SilentDeath.ini", b"").decode("latin1", errors="replace")
    if fx.strip():
        n_lists = len(re.findall(r"(?im)^FXList\s+\S+", fx))
        n_end = len(re.findall(r"(?im)^End\s*$", fx))
        if n_lists and n_end < n_lists:
            errors.append(f"FXList_SilentDeath.ini missing column-0 End ({n_end} End for {n_lists} FXList)")
    armor = added_data.get(r"Data\INI\Armor_SilentDeath.ini", b"").decode("latin1", errors="replace")
    armor_names = re.findall(r"(?im)^Armor\s+(?![=])(\S+)", armor)
    seen_a: dict[str, int] = {}
    for n in armor_names:
        seen_a[n.lower()] = seen_a.get(n.lower(), 0) + 1
    dups = [n for n, c in seen_a.items() if c > 1]
    if dups:
        errors.append("duplicate Armor defs: " + ", ".join(dups))
    for path in added_art:
        n = big.nkey(path)
        if n.endswith(".wav"):
            if not n.startswith("data\\audio\\sounds\\"):
                errors.append(f"wav not in DATA audio folder: {path}")
        elif n.endswith(".w3d"):
            if not n.startswith("art\\w3d\\"):
                errors.append(f"W3D not under Art\\W3D: {path}")
        elif n.endswith((".tga", ".dds", ".bmp")):
            if not n.startswith("art\\textures\\"):
                errors.append(f"texture not under Art\\Textures: {path}")
        else:
            errors.append(f"unexpected art path: {path}")
    return {"ok": not errors, "errors": errors, "headers": headers, "header_count": len(headers)}


class SamplePacker:
    def __init__(self, engine, resolver, art: ArtIndex, zip_path: Path, out_dir: Path):
        self.eng = engine
        self.resolver = resolver
        self.art = art
        self.zip_path = zip_path
        self.out_dir = out_dir
        self.protected = json_protected(engine)
        self.ss1 = engine.ss1
        self.warnings: list[str] = []
        self.added_data: dict[str, bytes] = {}
        self.added_art: dict[str, bytes] = {}
        self.emitted: list[dict] = []

    def run(self) -> dict:
        orig_data = self.ss1 / "_SPEC_DATA_ONE.big"
        orig_art = self.ss1 / "_SPEC_ART_TWO.big"
        if not orig_data.is_file() or not orig_art.is_file():
            raise FileNotFoundError("SPECTER FINAL BIGs not found for copy")
        orig_hashes = {
            "_SPEC_DATA_ONE.big": _sha(orig_data),
            "_SPEC_ART_TWO.big": _sha(orig_art),
        }
        factory = self.resolver.lookup_spec("CommandSet", SPECTER_CHINA_FACTORY_COMMANDSET)
        factory_obj = self.resolver.lookup_spec("Object", SPECTER_CHINA_FACTORY_OBJECT)
        if not factory or not factory_obj:
            raise RuntimeError("SPECTER China war factory CommandSet/Object missing")
        used = {k.strip() for k, _ in (factory.get("keys") or []) if k.strip().isdigit()}
        if CSSA1_FACTORY_SLOT in used or HQ11_FACTORY_SLOT in used:
            raise RuntimeError(
                f"SPECTER {SPECTER_CHINA_FACTORY_COMMANDSET} slots "
                f"{CSSA1_FACTORY_SLOT}/{HQ11_FACTORY_SLOT} are not empty: {sorted(used)}"
            )

        plans = {name: self.resolver.plan_object(name) for name in SAMPLE_OBJECTS}
        rename = {}
        for plan in plans.values():
            rename.update(build_rename_map(plan.get("deps") or []))
        rename["ChinaCSSA1"] = "SD25_ChinaCSSA1"
        rename["ChinaHQ11"] = "SD25_ChinaHQ11"

        skip_refs = skip_ref_set(plans)
        bundles: dict[str, list[str]] = defaultdict(list)
        for plan in plans.values():
            self._emit_plan(plan, rename, bundles, skip_refs)

        cssa1 = "SD25_ChinaCSSA1"
        hq11 = "SD25_ChinaHQ11"
        btn_cssa = "SD25_Command_ConstructChinaCSSA1"
        btn_hq = "SD25_Command_ConstructChinaHQ11"
        buttons = (
            construct_button(btn_cssa, cssa1, "CSSA1TB", "CONTROLBAR:SD25_ChinaCSSA1")
            + construct_button(btn_hq, hq11, "CHHQ11TB", "CONTROLBAR:SD25_ChinaHQ11")
            + deploy_button()
        )
        self.added_data[r"Data\INI\CommandButton_SilentDeath.ini"] = buttons.encode("latin1", errors="replace")
        overlay = factory_overlay_text(factory, btn_cssa, btn_hq)
        overlay += "\n" + hq11_unit_commandset()
        self.added_data[r"Data\INI\CommandSet_ZZZZ_SilentDeath_China.ini"] = overlay.encode("latin1", errors="replace")

        for kind, chunks in bundles.items():
            path = KIND_BUNDLE.get(kind)
            if path and chunks:
                if kind == "Armor":
                    chunks = dedupe_named_blocks("Armor", chunks)
                if kind == "FXList":
                    chunks = [close_fxlist_blocks(c) for c in chunks]
                    joined = close_fxlist_blocks("\n".join(chunks))
                else:
                    joined = "\n".join(chunks)
                blob = joined.encode("latin1", errors="replace")
                if path in self.added_data:
                    self.added_data[path] += b"\n" + blob
                else:
                    self.added_data[path] = blob

        existing_art = {big.nkey(n) for n in big.list_names(orig_art)}
        existing_data = {big.nkey(n) for n in big.list_names(orig_data)}
        self._index_optional_audio()
        self._recover_art(plans, existing_art | existing_data)

        data_adds: dict[str, bytes] = dict(self.added_data)
        art_adds: dict[str, bytes] = {}
        for path, blob in self.added_art.items():
            if big.nkey(path).startswith("data\\"):
                data_adds[path] = blob
            else:
                art_adds[path] = blob
        self.added_data = data_adds
        self.added_art = art_adds

        validation = validate_added_defs(self.added_data, self.added_art)
        if not validation["ok"]:
            raise RuntimeError("experimental pack validation failed: " + "; ".join(validation["errors"]))

        exp = self.out_dir
        exp.mkdir(parents=True, exist_ok=True)
        dest_data = exp / "_SPEC_DATA_ONE.big"
        dest_art = exp / "_SPEC_ART_TWO.big"
        data_info = big.copy_big_with_adds(orig_data, dest_data, self.added_data, set(self.protected))
        art_info = big.copy_big_with_adds(orig_art, dest_art, self.added_art, set())

        after_orig = {
            "_SPEC_DATA_ONE.big": _sha(orig_data),
            "_SPEC_ART_TWO.big": _sha(orig_art),
        }
        if after_orig != orig_hashes:
            raise RuntimeError("Original SPECTER FINAL BIG hashes changed during pack")

        packed_data = {big.nkey(n) for n in big.list_names(dest_data)}
        packed_art = {big.nkey(n) for n in big.list_names(dest_art)}
        missing_added = [n for n in self.added_data if big.nkey(n) not in packed_data]
        missing_added += [n for n in self.added_art if big.nkey(n) not in packed_art]
        if missing_added:
            raise RuntimeError("packed BIG missing added members: " + ", ".join(missing_added[:20]))

        report = {
            "stage": 5,
            "applies_to_original_specter": False,
            "generals_exe_run": False,
            "original_hashes_unchanged": True,
            "original_hashes": orig_hashes,
            "experimental_dir": str(exp),
            "experimental_hashes": {
                "_SPEC_DATA_ONE.big": _sha(dest_data),
                "_SPEC_ART_TWO.big": _sha(dest_art),
            },
            "data_big": {k: v for k, v in data_info.items() if k != "source"},
            "art_big": {k: v for k, v in art_info.items() if k != "source"},
            "china_build_location": {
                "object": SPECTER_CHINA_FACTORY_OBJECT,
                "commandset": SPECTER_CHINA_FACTORY_COMMANDSET,
                "source": factory_obj.get("source"),
                "extracted_empty_slots": [CSSA1_FACTORY_SLOT, HQ11_FACTORY_SLOT],
                "ChinaCSSA1_slot": CSSA1_FACTORY_SLOT,
                "ChinaHQ11_slot": HQ11_FACTORY_SLOT,
                "command_type": "UNIT_BUILD",
                "note": (
                    "SPECTER ChinaWarFactory uses PLAWarFactoryCommandSet, not ChinaWarFactoryCommandSet. "
                    "ChinaSupplyCenter only builds the supply truck. Dozer places buildings (HQ-9 site), not this TEL."
                ),
            },
            "rename_map": rename,
            "emitted": self.emitted,
            "warnings": list(dict.fromkeys(self.warnings)),
            "loose_ini_written": False,
            "validation": {
                "ok": validation["ok"],
                "errors": validation["errors"],
                "header_count": validation["header_count"],
                "headers": validation["headers"],
            },
            "capabilities_kept": [
                "ChinaCSSA1 UNIT_BUILD from ChinaWarFactory / PLAWarFactoryCommandSet slot 4",
                "ChinaHQ11 UNIT_BUILD from ChinaWarFactory / PLAWarFactoryCommandSet slot 7",
                "HQ11 pack/unpack via stock DeployStyleAIUpdate",
                "HQ11 fire only when deployed (WeaponSet Conditions = DEPLOYED + TurretsFunctionOnlyWhenDeployed)",
                "Original W3D/texture/animation filenames (not SD25-prefixed)",
                "Unique AudioEvent names; wav stems unchanged",
            ],
            "limitations": [
                "Runtime CommandSet swap (packed vs deployed labels) is not available on stock Generals.exe",
                "SET_SLUGGISH crawl-while-deployed is not bound; unit packs then moves on SET_NORMAL",
                "PackTime/UnpackTime = 2000 copied from V25 SDSR5, not measured CWC rider timing",
                "Shilka CWC voice wavs may be missing if they live only in WYS/Audio.big",
                "Generals.exe was not run",
            ],
        }
        return report

    def _emit_plan(
        self,
        plan: dict,
        rename: dict[str, str],
        bundles: dict[str, list[str]],
        skip_refs: set[tuple[str, str]],
    ) -> None:
        obj_name = plan["object"]
        side = (plan.get("meta") or {}).get("specter_side") or "China"
        seen = set()
        for row in plan.get("deps") or []:
            kind = row.get("kind") or ""
            name = row.get("name") or ""
            action = row.get("action") or ""
            key = (kind.lower(), name.lower())
            if key in seen:
                continue
            seen.add(key)
            if key in skip_refs:
                continue
            new = unique_def_name(kind, name, action, row.get("planned"))
            if not new:
                continue
            rec = self.resolver.lookup_v25(kind, name)
            if rec is None and kind == "CrateData":
                rec = self.resolver.lookup_v25("CrateTemplate", name)
            body = (rec or {}).get("body") or ""
            if not body:
                self.warnings.append(f"no V25 body for {kind}:{name}")
                continue
            kind_out = "CrateData" if kind == "CrateTemplate" else kind
            text = rewrite_header(kind_out, new, rewrite_text(body, rename))
            if obj_name == "ChinaHQ11" and kind == "Object" and name.lower() == "chinahq11":
                deployed = rename.get("HQ11MissileWeapon", "SD25_HQ11MissileWeapon")
                text = transform_hq11_body(text, deployed)
            if kind == "Object":
                path = object_ini_path(side, new)
                self.added_data[path] = text.encode("latin1", errors="replace")
            else:
                bundles[kind_out].append(text)
            self.emitted.append({"kind": kind_out, "from": name, "to": new, "action": action})

    def _recover_art(self, plans: dict, existing: set[str] | None = None) -> None:
        existing = existing or set()
        wanted: dict[str, dict] = {}
        for plan in plans.values():
            for row in plan.get("deps") or []:
                if row.get("kind") != "ArtFile":
                    continue
                if row.get("action") not in ("RECOVER_FROM_V25", "IMPORT_UNIQUE"):
                    continue
                stem = row["name"]
                if _art_stem(stem) in SKIP_ART_STEMS:
                    continue
                wanted[stem] = row
            for row in plan.get("deps") or []:
                if row.get("kind") == "MappedImage" and (row.get("name") or "").lower() in PORTRAIT_IMAGES:
                    wanted[row["name"]] = row
        for name, row in wanted.items():
            blob, filename, rec = self._read_art_blob(name, row)
            if not blob:
                if _is_w3d_subobject(name):
                    continue
                self.warnings.append(f"ART not recovered (exact stem only): {name}")
                continue
            dest = vfs_dest_from_rec(filename, rec)
            if big.nkey(dest) in {big.nkey(n) for n in self.added_art}:
                continue
            if big.nkey(dest) in existing:
                self.emitted.append({"kind": "ArtFile", "from": name, "to": dest, "action": "REUSE_NATIVE"})
                continue
            self.added_art[dest] = blob
            if Path(filename).stem.lower() in PORTRAIT_IMAGES:
                w, h = tga_or_dds_size(blob)
                path = KIND_BUNDLE["MappedImage"]
                mi_name = "CSSA1TB" if Path(filename).stem.lower() == "cssa1tb" else "CHHQ11TB"
                extra = mapped_image_from_texture(mi_name, Path(filename).name, w, h).encode("latin1")
                self.added_data[path] = self.added_data.get(path, b"") + extra
            self.emitted.append({"kind": "ArtFile", "from": name, "to": dest, "action": row.get("action")})

        for rec in self.emitted:
            if rec["kind"] != "AudioEvent":
                continue
            src = self.resolver.lookup_v25("AudioEvent", rec["from"])
            if not src:
                continue
            for k, v in src.get("keys") or []:
                if k.strip().lower() not in ("sounds", "attack", "decay"):
                    continue
                for tok in v.split():
                    if tok.lower() in ("random", "interrupt", "none"):
                        continue
                    wav = tok if "." in tok else f"{tok}.wav"
                    blob, filename, hit = self._read_art_blob(tok, {"name": tok})
                    if not blob:
                        self.warnings.append(f"audio wav not recovered: {tok}")
                        continue
                    dest = vfs_dest_from_rec(filename if filename.lower().endswith(".wav") else wav, hit)
                    if big.nkey(dest) in existing or big.nkey(dest) in {big.nkey(n) for n in self.added_art}:
                        continue
                    self.added_art[dest] = blob
                    self.emitted.append({"kind": "ArtFile", "from": tok, "to": dest, "action": "RECOVER_FROM_V25"})

    def _index_optional_audio(self) -> None:
        if not self.zip_path or not self.art:
            return
        member = "Generals Silent Death V25/WYS/Audio.big"
        found = list(self.art.cache.rglob("Audio.big")) if self.art.cache.is_dir() else []
        if not found:
            archive.extract(self.zip_path, self.art.cache, [member])
            found = list(self.art.cache.rglob("Audio.big"))
        if found:
            self.art._index_big_file(found[0], container=member)
        else:
            self.warnings.append("V25 WYS/Audio.big not present; unique voice wavs may be missing")

    def _read_art_blob(self, name: str, row: dict) -> tuple[bytes | None, str, dict | None]:
        hits = self.art.find(name) if self.art else []
        rec = _pick_hit(hits, name)
        if rec:
            filename = rec.get("filename") or (name if "." in name else f"{name}.dds")
            blob = None
            if rec.get("container") == "zip" and rec.get("path") and self.zip_path:
                blob = self._extract_zip_member(rec["path"])
            elif rec.get("container") == "nested_big":
                blob = self.art._read_nested(rec)
            if blob:
                return blob, filename, rec
        extract = Path("/tmp/v25_extract/Generals Silent Death V25")
        stem = name.split(".")[0]
        for folder, ext in (
            ("Art/W3D", ".W3D"),
            ("Art/Textures", ".tga"),
            ("Art/Textures", ".dds"),
            ("Data/Audio/Sounds", ".wav"),
        ):
            folder_p = extract.joinpath(folder)
            if folder_p.is_dir():
                for cand in folder_p.glob(stem + ".*"):
                    return cand.read_bytes(), cand.name, None
            p = extract / folder / f"{name}{ext}"
            if p.is_file():
                return p.read_bytes(), p.name, None
        return None, name, None

    def _extract_zip_member(self, member: str) -> bytes | None:
        dest = Path("/tmp/v25_sync_cache/stage5_art")
        dest.mkdir(parents=True, exist_ok=True)
        archive.extract(self.zip_path, dest, [member])
        found = list(dest.rglob(Path(member).name))
        if found:
            return found[0].read_bytes()
        return None


def _art_stem(name: str) -> str:
    base = name.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if "." in base:
        return base.rsplit(".", 1)[0]
    return base


def _is_w3d_subobject(name: str) -> bool:
    low = name.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if any(low.endswith(ext) for ext in (".tga", ".dds", ".wav", ".w3d", ".bmp")):
        return False
    return "." in low


def _pick_hit(hits: list[dict], name: str) -> dict | None:
    if not hits:
        return None
    low = name.lower()

    def fname(h: dict) -> str:
        return (h.get("filename") or "").lower()

    if low.endswith(".w3d"):
        prefer = [h for h in hits if fname(h).endswith(".w3d")]
    elif low.endswith(".wav"):
        prefer = [h for h in hits if fname(h).endswith(".wav")]
    elif low.endswith((".tga", ".dds", ".bmp")):
        prefer = [h for h in hits if fname(h).endswith((".tga", ".dds", ".bmp"))]
    else:
        prefer = [h for h in hits if fname(h).endswith(".w3d")]
        if not prefer:
            prefer = [h for h in hits if fname(h).endswith(".wav")]
    return (prefer or hits)[0]


def json_protected(engine) -> list[str]:
    paths = list(engine.protected.get("ini_paths") or [])
    return [p.replace("/", "\\").lower() for p in paths]


def _sha(path: Path) -> str:
    from .engine import sha256_file

    return sha256_file(path)
