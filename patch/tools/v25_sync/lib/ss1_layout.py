"""Discover SPECTER FINAL (SS1) INI load topology from the live DATA BIG.

SS1 is the reference. Emit paths must match how Generals actually loads INI
from `_SPEC_DATA_ONE.big`, not V25 loose-folder conventions.

This module never opens SS1 BIGs for write.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from . import big

# Prefixes that already appear as extra root INI files in SPECTER FINAL.
# These are loaded because GameEngine loadDirectory("Data\\INI", subdirs=False)
# parses every root *.ini by first-token block type.
PROVEN_ROOT_PREFIXES = (
    "CommandButton_",
    "CommandSet_",
    "Weapon_",
    "Object_",
    "ObjectCreationList_",
    "Science_",
    "SpecialPower_",
    "Upgrade_",
    "PlayerTemplate_",
    "ControlBarScheme_",
)

# MappedImages is not a generic Data\\INI recursive walk. SPECTER only ships
# these two subfolders, which match the stock ZH MappedImageCollection loads.
MAPPEDIMAGE_LOADED_SUBDIRS = ("HandCreated", "TextureSize_512")

PROTECTED_BASENAMES = {
    "commandset.ini",
    "commandbutton.ini",
    "weapon.ini",
    "armor.ini",
    "locomotor.ini",
    "playertemplate.ini",
    "objectcreationlist.ini",
    "fxlist.ini",
    "damagefx.ini",
    "crate.ini",
    "specialpower.ini",
    "science.ini",
    "upgrade.ini",
    "particlesystem.ini",
    "soundeffects.ini",
    "voice.ini",
    "eva.ini",
    "gamedata.ini",
    "aidata.ini",
}

# Stock tables that live as Data\\INI\\<Name>.ini in SPECTER FINAL (from live BIG).
STOCK_ROOT_KIND_FILES = {
    "Armor": "Armor.ini",
    "Locomotor": "Locomotor.ini",
    "FXList": "FXList.ini",
    "DamageFX": "DamageFX.ini",
    "CrateData": "Crate.ini",
    "CrateTemplate": "Crate.ini",
    "ParticleSystem": "ParticleSystem.ini",
    "AudioEvent": "SoundEffects.ini",
    "Weapon": "Weapon.ini",
    "CommandSet": "CommandSet.ini",
    "CommandButton": "CommandButton.ini",
    "ObjectCreationList": "ObjectCreationList.ini",
    "SpecialPower": "SpecialPower.ini",
    "Upgrade": "Upgrade.ini",
    "Science": "Science.ini",
}

PREFIX_TO_KIND = {
    "Armor_": "Armor",
    "Locomotor_": "Locomotor",
    "FXList_": "FXList",
    "DamageFX_": "DamageFX",
    "Crate_": "CrateData",
    "ParticleSystem_": "ParticleSystem",
    "SoundEffects_": "AudioEvent",
    "Weapon_": "Weapon",
    "CommandSet_": "CommandSet",
    "CommandButton_": "CommandButton",
    "ObjectCreationList_": "ObjectCreationList",
    "Object_": "Object",
    "SpecialPower_": "SpecialPower",
    "Upgrade_": "Upgrade",
    "Science_": "Science",
}

KIND_ROOT_FILE = {
    "Weapon": r"Data\INI\Weapon_SilentDeath.ini",
    "Armor": r"Data\INI\Armor_SilentDeath.ini",
    "Locomotor": r"Data\INI\Locomotor_SilentDeath.ini",
    "FXList": r"Data\INI\FXList_SilentDeath.ini",
    "DamageFX": r"Data\INI\DamageFX_SilentDeath.ini",
    "CrateData": r"Data\INI\Crate_SilentDeath.ini",
    "CrateTemplate": r"Data\INI\Crate_SilentDeath.ini",
    "ObjectCreationList": r"Data\INI\ObjectCreationList_SilentDeath.ini",
    "ParticleSystem": r"Data\INI\ParticleSystem_SilentDeath.ini",
    "AudioEvent": r"Data\INI\SoundEffects_SilentDeath.ini",
    "CommandButton": r"Data\INI\CommandButton_SilentDeath.ini",
    "CommandSet": r"Data\INI\CommandSet_ZZZZ_SilentDeath_{Side}.ini",
    "MappedImage": r"Data\INI\MappedImages\HandCreated\SilentDeathMappedImages.ini",
}


def nkey(name: str) -> str:
    return name.replace("/", "\\").lower()


def extra_root_count(layout: dict | None) -> str:
    if layout and layout.get("extra_root_ini_count") is not None:
        return str(layout["extra_root_ini_count"])
    return "N"


def discover(data_big: Path) -> dict:
    """Read-only scan of SS1 DATA member names. No payloads required."""
    names = big.list_names(data_big)
    root_ini: list[str] = []
    dirs: dict[str, list[str]] = defaultdict(list)
    for name in names:
        k = name.replace("/", "\\")
        if not nkey(k).startswith("data\\ini\\"):
            continue
        rest = k[9:]
        if "\\" not in rest:
            root_ini.append(k)
        else:
            dirs[rest.split("\\")[0]].append(k)

    weapon_files = dirs.get("Weapon", [])
    weapon_nested = [p for p in weapon_files if p.replace("/", "\\").count("\\") > 3]
    object_files = dirs.get("Object", [])
    object_depths = Counter()
    for p in object_files:
        object_depths[p.replace("/", "\\").count("\\")] += 1
    mapped = dirs.get("MappedImages", [])
    mapped_sub = Counter()
    for p in mapped:
        parts = p.replace("/", "\\").split("\\")
        if len(parts) >= 4:
            mapped_sub[parts[3]] += 1

    prefixes = Counter()
    stock_basenames = set()
    extra_root = 0
    for p in root_ini:
        base = p.rsplit("\\", 1)[-1]
        if "_" in base:
            prefixes[base.split("_", 1)[0] + "_"] += 1
            extra_root += 1
        else:
            stock_basenames.add(base.lower())

    proven_root_kinds = []
    proven_evidence = {}
    for kind, stock in STOCK_ROOT_KIND_FILES.items():
        if stock.lower() in stock_basenames and extra_root:
            proven_root_kinds.append(kind)
            proven_evidence[kind] = (
                f"stock `{stock}` is at Data\\INI root with {extra_root} extra root INI "
                f"(including Weapon_/CommandSet_ extras). Same loadDirectory; kind is first-token."
            )

    unproven = [
        p
        for p, kind in PREFIX_TO_KIND.items()
        if kind not in proven_root_kinds and p not in PROVEN_ROOT_PREFIXES
    ]

    return {
        "source": str(data_big),
        "total_members": len(names),
        "root_ini_count": len(root_ini),
        "root_ini": sorted(root_ini, key=str.lower),
        "root_extra_prefixes": dict(prefixes),
        "first_level_dirs": {d: len(v) for d, v in sorted(dirs.items(), key=lambda kv: kv[0].lower())},
        "object": {
            "count": len(object_files),
            "recursive": True,
            "reason": "SS1 ships Object\\Specter\\<faction>\\... nested INI that must load.",
            "depth_histogram": {str(k): v for k, v in sorted(object_depths.items())},
        },
        "weapon_dir": {
            "count": len(weapon_files),
            "recursive": False,
            "nested_files": len(weapon_nested),
            "reason": (
                "SS1 Data\\INI\\Weapon\\ holds only flat Weapon_*.ini. Extra weapons also "
                "live at Data\\INI\\Weapon_*.ini. No Weapon\\<subdir>\\ members exist."
            ),
            "files": sorted(weapon_files, key=str.lower),
        },
        "mappedimages": {
            "subdirs": dict(mapped_sub),
            "loaded_subdirs": list(MAPPEDIMAGE_LOADED_SUBDIRS),
            "reason": "SS1 only contains HandCreated and TextureSize_512 under MappedImages.",
        },
        "proven_root_prefixes": [p for p in PROVEN_ROOT_PREFIXES if prefixes.get(p)],
        "proven_root_kinds": proven_root_kinds,
        "proven_root_kind_evidence": proven_evidence,
        "extra_root_ini_count": extra_root,
        "unproven_root_kinds": unproven,
        "emit": dict(KIND_ROOT_FILE),
        "object_emit": r"Data\INI\Object\SilentDeath\{Side}\{Name}.ini",
        "audio_emit": r"Data\Audio\Sounds\{stem}.wav",
    }


def path_is_protected(path: str, protected_basenames: set[str] | None = None) -> bool:
    base = nkey(path).rsplit("\\", 1)[-1]
    blocked = protected_basenames or PROTECTED_BASENAMES
    if base in blocked:
        return True
    if nkey(path) == nkey(r"Data\INI\MappedImages\HandCreated\HandCreatedMappedImages.ini"):
        return True
    return False


def path_loadable(path: str, layout: dict | None = None) -> dict:
    """Whether SS1's VFS load pattern will parse this member as INI.

    Confidence:
      proven — SS1 already has the same class of path, or stock root table + extra root loader
      unlikely — contradicts SS1 topology (never treat likely as loadable)
    """
    k = nkey(path)
    if k.endswith(".wav"):
        ok = k.startswith("data\\audio\\sounds\\")
        return {
            "path": path,
            "loaded": ok,
            "confidence": "proven" if ok else "unlikely",
            "reason": "wav under Data\\Audio\\Sounds" if ok else "wav not in Data\\Audio\\Sounds",
        }
    if not k.startswith("data\\ini\\"):
        return {"path": path, "loaded": False, "confidence": "unlikely", "reason": "not under Data\\INI"}
    rest = path.replace("/", "\\")[9:]
    parts = rest.split("\\")
    if len(parts) == 1:
        base = parts[0]
        if path_is_protected(path):
            return {
                "path": path,
                "loaded": True,
                "confidence": "proven",
                "reason": "stock public INI (blocked for write, loaded by name)",
                "protected": True,
            }
        prefix = base.split("_", 1)[0] + "_" if "_" in base else ""
        if prefix in PROVEN_ROOT_PREFIXES:
            return {
                "path": path,
                "loaded": True,
                "confidence": "proven",
                "reason": f"SS1 already loads extra {prefix}*.ini at Data\\INI root",
            }
        kind = PREFIX_TO_KIND.get(prefix)
        proven_kinds = (layout or {}).get("proven_root_kinds")
        if proven_kinds is None:
            # No live layout: stock table at root + extra root loader (Weapon_/CommandSet_).
            proven_kinds = list(STOCK_ROOT_KIND_FILES)
        if kind and kind in proven_kinds:
            return {
                "path": path,
                "loaded": True,
                "confidence": "proven",
                "reason": (
                    f"SS1 stock `{STOCK_ROOT_KIND_FILES.get(kind)}` is a root INI; "
                    f"{extra_root_count(layout)} extra root INI prove the folder loader. "
                    f"Unique `{prefix}*.ini` is the same class as Weapon_*.ini."
                ),
            }
        return {
            "path": path,
            "loaded": False,
            "confidence": "unlikely",
            "reason": (
                "no SS1 extra of this prefix and no stock root table of this kind; "
                "do not emit"
            ),
        }
    top = parts[0]
    if top.lower() == "object":
        return {
            "path": path,
            "loaded": True,
            "confidence": "proven",
            "reason": "Object directory is recursive in SS1 (Object\\Specter\\...)",
        }
    if top.lower() == "weapon":
        # Data\INI\Weapon\Weapon_China_Missiles.ini → 2 components under Weapon
        if len(parts) == 2:
            return {
                "path": path,
                "loaded": True,
                "confidence": "proven",
                "reason": "SS1 Weapon\\ is flat Weapon_*.ini only",
            }
        return {
            "path": path,
            "loaded": False,
            "confidence": "unlikely",
            "reason": "SS1 has zero nested Data\\INI\\Weapon\\<subdir>\\ members; do not emit here",
        }
    if top.lower() == "mappedimages":
        if len(parts) >= 3 and parts[1] in MAPPEDIMAGE_LOADED_SUBDIRS:
            prot = path_is_protected(path)
            return {
                "path": path,
                "loaded": True,
                "confidence": "proven",
                "reason": f"SS1 MappedImages\\{parts[1]} is a live folder",
                "protected": prot,
            }
        return {
            "path": path,
            "loaded": False,
            "confidence": "unlikely",
            "reason": "SS1 MappedImages only loads HandCreated and TextureSize_512",
        }
    if top.lower() == "default":
        return {
            "path": path,
            "loaded": True,
            "confidence": "proven",
            "reason": "SS1 Data\\INI\\Default exists",
        }
    return {
        "path": path,
        "loaded": False,
        "confidence": "unlikely",
        "reason": f"no SS1 precedent for Data\\INI\\{top}\\...",
    }


def emit_path(kind: str, name: str, side: str = "China") -> str:
    if kind == "Object":
        return rf"Data\INI\Object\SilentDeath\{side}\{name}.ini"
    tmpl = KIND_ROOT_FILE.get(kind)
    if not tmpl:
        return rf"Data\INI\{kind}_SilentDeath.ini"
    return tmpl.replace("{Side}", side).replace("{Name}", name)


def layout_markdown(layout: dict) -> str:
    lines = [
        "# SS1 INI load topology (from live `_SPEC_DATA_ONE.big`)",
        "",
        f"- Source: `{layout.get('source')}`",
        f"- DATA members: **{layout.get('total_members')}**",
        f"- Data\\INI root files: **{layout.get('root_ini_count')}**",
        "",
        "## First-level Data\\INI directories",
        "",
    ]
    for d, c in (layout.get("first_level_dirs") or {}).items():
        lines.append(f"- `{d}/` {c}")
    w = layout.get("weapon_dir") or {}
    o = layout.get("object") or {}
    m = layout.get("mappedimages") or {}
    lines += [
        "",
        "## Object",
        "",
        f"- Recursive: **{o.get('recursive')}** ({o.get('reason')})",
        f"- Files: {o.get('count')}",
        "",
        "## Weapon directory",
        "",
        f"- Recursive: **{w.get('recursive')}**",
        f"- Nested subdir files: **{w.get('nested_files')}**",
        f"- {w.get('reason')}",
        "",
        "## MappedImages",
        "",
        f"- Subdirs: `{m.get('subdirs')}`",
        f"- Loaded: {m.get('loaded_subdirs')}",
        f"- {m.get('reason')}",
        "",
        "## Proven extra root prefixes",
        "",
    ]
    for p in layout.get("proven_root_prefixes") or []:
        lines.append(f"- `{p}*`")
    lines += [
        "",
        "## Proven root kinds (stock table + extra root loader)",
        "",
        f"- Extra root INI: **{layout.get('extra_root_ini_count')}**",
    ]
    for kind in layout.get("proven_root_kinds") or []:
        ev = (layout.get("proven_root_kind_evidence") or {}).get(kind, "")
        lines.append(f"- `{kind}`: {ev}")
    lines += [
        "",
        "## Emit paths (SS1-safe)",
        "",
        f"- Object: `{layout.get('object_emit')}`",
    ]
    for kind, path in (layout.get("emit") or {}).items():
        lines.append(f"- {kind}: `{path}`")
    lines += [
        "",
        "Weapons go to **root** `Weapon_SilentDeath.ini`, not `Weapon\\SilentDeath\\`.",
        "MappedImages go to **HandCreated**, not a new SilentDeath folder.",
        "",
    ]
    return "\n".join(lines) + "\n"
