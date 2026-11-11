"""SAGE INI parser for Object / Weapon / CommandSet / Draw dependency walking.

Nested Draw / Behavior / ConditionState End tokens do not close the parent
Object. OCL = MIDPOINT is not a Weapon. Keys are last-win within a block;
VFS last-win is applied by callers stacking sources in load order.
"""
from __future__ import annotations

import re
from pathlib import Path

DEFINE_KINDS = (
    "Object",
    "Weapon",
    "CommandSet",
    "CommandButton",
    "Armor",
    "Locomotor",
    "ObjectCreationList",
    "FXList",
    "DamageFX",
    "ParticleSystem",
    "SpecialPower",
    "Upgrade",
    "Science",
    "PlayerTemplate",
    "MappedImage",
    "AudioEvent",
    "DialogEvent",
    "EvaEvent",
    "CrateData",
    "CrateTemplate",
    "Rank",
    "AIData",
)
# SAGE uses CrateData; some docs say CrateTemplate. Lookup treats them as one table.
KIND_ALIASES = {
    "CrateData": ("CrateTemplate",),
    "CrateTemplate": ("CrateData",),
}
DEFINE_RE = re.compile(
    r"^(" + "|".join(DEFINE_KINDS) + r")\s+(\S+)",
    re.I,
)

# Block headers with no '='. `Turret = BONE` inside Draw is a key; `Turret` inside AIUpdate is a block.
NEST_NO_EQ = {
    "defaultconditionstate",
    "armorset",
    "weaponset",
    "locomotorset",
    "unitspecificsounds",
    "unitspecificfx",
    "prerequisites",
    "turret",
    "altturret",
    "attackturret",
    "createobject",
    "createdebris",
    "applyrandomforce",
    "applyfcforce",
    "waitforvoice",
}
MODULE_BLOCKS = {"draw", "body", "behavior", "clientupdate"}
NEST_WITH_EQ = {"conditionstate", "transitionstate"}

# Keys whose values are named defs (not art files). MIDPOINT is an OCL token, not a weapon.
NAMED_KEYS = {
    "weapon": "Weapon",
    "primaryweapon": "Weapon",
    "secondaryweapon": "Weapon",
    "tertiaryweapon": "Weapon",
    "weaponslot": "Weapon",
    "weaponoid": "Weapon",
    "weaponoid2": "Weapon",
    "weaponoid3": "Weapon",
    "projectileobject": "Object",
    "projectileobjectname": "Object",
    "projectile": "Object",
    "object": "Object",
    "objectnames": "Object",
    "payload": "Object",
    "payloadtemplate": "Object",
    "transportslot": "Object",
    "rider": "Object",
    "ridertemplate": "Object",
    "contain": "Object",
    "dieobject": "Object",
    "spawnobject": "Object",
    "spawnedobject": "Object",
    "replacementobject": "Object",
    "upgradeobject": "Object",
    "commandset": "CommandSet",
    "commandbutton": "CommandButton",
    "buttonimage": "MappedImage",
    "selectportrait": "MappedImage",
    "buttonborder": "MappedImage",
    "armorset": "Armor",
    "armor": "Armor",
    "damagetype": None,
    "deathtype": None,
    "locomotor": "Locomotor",
    "locomotors": "Locomotor",
    "locomoterset": "Locomotor",
    "ocl": "ObjectCreationList",
    "oclcreate": "ObjectCreationList",
    "createocloverride": "ObjectCreationList",
    "ocloncreate": "ObjectCreationList",
    "fireocl": "ObjectCreationList",
    "veterancyfireocl": "ObjectCreationList",
    "projectiledetonationocl": "ObjectCreationList",
    "fxlist": "FXList",
    "fx": "FXList",
    "firefx": "FXList",
    "veterancyfirefx": "FXList",
    "projectiledetonationfx": "FXList",
    "particlesystem": "ParticleSystem",
    "specialpower": "SpecialPower",
    "specialpowertemplate": "SpecialPower",
    "upgrade": "Upgrade",
    "requiredupgrade": "Upgrade",
    "conflictupgrade": "Upgrade",
    "grantupgrade": "Upgrade",
    "triggeredupgrade": "Upgrade",
    "science": "Science",
    "prerequisitescience": "Science",
    "voiceattack": "AudioEvent",
    "voiceselect": "AudioEvent",
    "voicemove": "AudioEvent",
    "soundambient": "AudioEvent",
    "soundmove": "AudioEvent",
    "soundcreated": "AudioEvent",
    "soundondamage": "AudioEvent",
    "soundonreallydamaged": "AudioEvent",
    "soundenter": "AudioEvent",
    "soundexit": "AudioEvent",
    "soundpromoted": "AudioEvent",
    "firesound": "AudioEvent",
    "firevoice": "AudioEvent",
    "soundimpact": "AudioEvent",
    "voiceguard": "AudioEvent",
    "voiceattackair": "AudioEvent",
    "voicecreate": "AudioEvent",
    "deathfx": "FXList",
    "damagefx": "DamageFX",
    "majorfx": "FXList",
    "minorfx": "FXList",
    "veterancymajorfx": "FXList",
    "veterancyminorfx": "FXList",
    "projectileexhaust": "ParticleSystem",
    "cratedata": "CrateData",
    "crateobject": "Object",
    "firesweapon": "Weapon",
    "weaponstouse": "Weapon",
}
DAMAGEFX_FX_KEYS = {
    "majorfx",
    "minorfx",
    "veterancymajorfx",
    "veterancyminorfx",
}

ART_KEYS = {
    "model",
    "w3dmodelname",
    "w3danimationname",
    "animation",
    "idleanim",
    "texture",
    "altmodel",
    "portraitimage",
    "buttonimage",
    "selectportrait",
    "radariconimage",
    "trackmarks",
}

SKIP_NAMED_VALUES = {
    "",
    "none",
    "null",
    "default",
    "yes",
    "no",
    "true",
    "false",
    "primary",
    "secondary",
    "tertiary",
    "autochoose",
    "hardpoint",
    "turret",
    "midpoint",
    "final",
    "initial",
    "delay",
    "burst",
    "create_located",
    "create_above",
    "self",
    "set_normal",
    "set_normal_upgraded",
    "set_wander",
    "set_panic",
    "set_taxiing",
    "set_super_upgraded",
    "set_free_fall",
    "set_sluggish",
    "heroic",
    "veteran",
    "elite",
    "regular",
    "rookie",
}


def strip_comment(line: str) -> str:
    if ";" in line:
        line = line[: line.index(";")]
    return line.strip()


def parse_ini_text(text: str, source: str) -> dict[str, dict]:
    """Return {kind: {name: {source, body, keys, named_refs, art_refs}}}."""
    kinds: dict[str, dict] = {}
    current_kind = None
    current_name = None
    nest = 0
    buf: list[str] = []
    keys: list[tuple[str, str]] = []

    def flush() -> None:
        nonlocal current_kind, current_name, nest, buf, keys
        if not current_kind or not current_name:
            nest = 0
            buf, keys = [], []
            return
        body = "\n".join(buf)
        named, art = classify_refs(keys, current_kind)
        kinds.setdefault(current_kind, {})[current_name] = {
            "kind": current_kind,
            "name": current_name,
            "source": source,
            "body": body,
            "keys": keys,
            "named_refs": named,
            "art_refs": art,
            "behaviors": behavior_types(keys),
            "damage_types": damage_types_from_keys(keys, current_kind),
        }
        current_kind = None
        current_name = None
        nest = 0
        buf, keys = [], []

    for raw in text.splitlines():
        line = strip_comment(raw)
        if not line:
            if current_name:
                buf.append(raw.rstrip("\n"))
            continue
        token = line.split()[0]
        token_l = token.lower()

        if token_l == "end":
            if current_name:
                buf.append(raw.rstrip("\n"))
                if nest > 0:
                    nest -= 1
                else:
                    flush()
            continue

        m = DEFINE_RE.match(line)
        if m and current_name is None:
            name = m.group(2)
            # `Object = Payload` is a key, not a new Object named "=".
            if name == "=" or line.split(None, 1)[1].startswith("="):
                continue
            current_kind = m.group(1)
            current_name = name
            nest = 0
            buf = [raw.rstrip("\n")]
            keys = []
            continue

        if current_name is None:
            continue

        buf.append(raw.rstrip("\n"))
        opens_block = False
        if "=" not in line and token_l in NEST_NO_EQ:
            opens_block = True
        elif token_l in MODULE_BLOCKS and "=" in line:
            opens_block = True
        elif token_l in NEST_WITH_EQ:
            opens_block = True
        if opens_block:
            nest += 1
        if "=" in line:
            k, v = line.split("=", 1)
            keys.append((k.strip(), v.strip()))
        elif keys and not opens_block:
            # Continuation of previous key (KindOf flags wrapped to next line).
            pk, pv = keys[-1]
            keys[-1] = (pk, pv + " " + line)

    flush()
    return kinds


def classify_refs(
    keys: list[tuple[str, str]], parent_kind: str | None = None
) -> tuple[dict[str, list[str]], list[str]]:
    named: dict[str, list[str]] = {}
    art: list[str] = []
    for k, v in keys:
        kl = re.sub(r"[^a-z0-9]", "", k.lower())
        tokens = [t.strip() for t in re.split(r"[\s,]+", v) if t.strip()]
        # CommandSet slots: 1 = Command_ConstructFoo
        if k.strip().isdigit():
            named.setdefault("CommandButton", []).extend(
                t for t in tokens if t.lower() not in SKIP_NAMED_VALUES
            )
            continue
        for m in re.finditer(r"PSys:(\S+)", v, re.I):
            named.setdefault("ParticleSystem", []).append(m.group(1).rstrip(","))
        for m in re.finditer(r"FXList:(\S+)", v, re.I):
            named.setdefault("FXList", []).append(m.group(1).rstrip(","))
        if kl in ART_KEYS or kl.endswith("model") or kl.endswith("anim") or kl.endswith("animation"):
            for t in tokens:
                if t.lower() not in SKIP_NAMED_VALUES and not t.replace(".", "", 1).isdigit():
                    art.append(t)
        # DamageFX tables: last token is the FXList; earlier tokens are DamageType / veterancy.
        if parent_kind == "DamageFX" and kl in DAMAGEFX_FX_KEYS:
            last = tokens[-1] if tokens else ""
            if last and last.lower() not in SKIP_NAMED_VALUES:
                named.setdefault("FXList", []).append(last)
            continue
        kind = NAMED_KEYS.get(kl)
        if not kind and re.fullmatch(r"rider\d+", kl):
            kind = "Object"
            tokens = tokens[:1]
        if not kind:
            continue
        # Armor tables are `Armor = 50% SMALL_ARMS`, not nested Armor defs.
        if parent_kind == "Armor" and kind == "Armor":
            continue
        for t in tokens:
            tl = t.lower()
            if tl in SKIP_NAMED_VALUES or t.replace(".", "", 1).isdigit() or t.endswith("%"):
                continue
            if kind == "Weapon" and tl in ("midpoint", "create_located", "create_above"):
                continue
            if kind == "Armor" and t.endswith("%"):
                continue
            if tl.startswith("set_"):
                continue
            # CWC often stores an OCL name in an Object= slot.
            if kind == "Object" and t.upper().startswith("OCL_"):
                named.setdefault("ObjectCreationList", []).append(t)
                continue
            named.setdefault(kind, []).append(t)
    for k, vals in named.items():
        seen = set()
        uniq = []
        for v in vals:
            if v.lower() not in seen:
                seen.add(v.lower())
                uniq.append(v)
        named[k] = uniq
    art_u = []
    seen_a = set()
    for a in art:
        al = a.lower()
        if al not in seen_a:
            seen_a.add(al)
            art_u.append(a)
    return named, art_u


def merge_vfs(*layers: dict[str, dict]) -> dict[str, dict]:
    """Later layers win on (kind, name)."""
    out: dict[str, dict] = {}
    for layer in layers:
        for kind, defs in layer.items():
            bucket = out.setdefault(kind, {})
            for name, rec in defs.items():
                bucket[name] = rec
    return out


def behavior_types(keys: list[tuple[str, str]]) -> list[str]:
    out = []
    seen = set()
    for k, v in keys:
        if k.strip().lower() != "behavior":
            continue
        mod = v.split()[0] if v.strip() else ""
        if mod and mod.lower() not in seen:
            seen.add(mod.lower())
            out.append(mod)
    return out


def damage_types_from_keys(keys: list[tuple[str, str]], parent_kind: str | None) -> list[str]:
    out = []
    seen = set()
    for k, v in keys:
        kl = k.strip().lower()
        if parent_kind == "Weapon" and kl == "damagetype":
            tok = v.split()[0] if v.strip() else ""
            if tok and tok.lower() not in seen:
                seen.add(tok.lower())
                out.append(tok)
        if parent_kind == "Armor" and kl == "armor":
            # `INFANTRY_MISSILE   100%` or `100% EXPLOSION`
            for tok in v.replace("%", " ").split():
                if tok.replace(".", "", 1).isdigit():
                    continue
                if tok.lower() not in seen:
                    seen.add(tok.lower())
                    out.append(tok)
    return out


def gameplay_fingerprint(rec: dict) -> str:
    """Effective behavior, not comments or ModuleTag numbers."""
    named = rec.get("named_refs") or {}
    parts = [
        rec.get("kind") or "",
        "kindof:" + " ".join(
            sorted(
                t.upper()
                for k, v in rec.get("keys") or []
                if k.strip().lower() == "kindof"
                for t in v.split()
            )
        ),
        "behaviors:" + ",".join(rec.get("behaviors") or []),
        "damage:" + ",".join(rec.get("damage_types") or []),
        "art:" + ",".join((rec.get("art_refs") or [])[:12]),
    ]
    for kind in sorted(named):
        parts.append(kind + ":" + ",".join(named[kind]))
    anti = []
    for k, v in rec.get("keys") or []:
        kl = k.strip().lower()
        if kl.startswith("anti") and v.strip():
            anti.append(f"{kl}={v.split()[0].lower()}")
    parts.append("anti:" + ",".join(sorted(anti)))
    return "\n".join(parts)


def parse_file(path: Path, source: str | None = None) -> dict[str, dict]:
    text = path.read_text(encoding="latin1", errors="replace")
    return parse_ini_text(text, source or str(path))
