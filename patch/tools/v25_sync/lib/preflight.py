"""Static preflight for unique-path INI that will be added to an SS1 DATA copy.

Catches the Stage 5 boot-crash classes: unloadable paths, missing parse-time
templates, FXList/Object End errors, duplicate Armor, Locomotor comment syntax.

This is not a Generals.exe run.
"""
from __future__ import annotations

import re
from collections import defaultdict

from . import ini
from .ss1_layout import path_is_protected, path_loadable

PARSE_FATAL_KINDS = {
    "Weapon",
    "Armor",
    "Locomotor",
    "Object",
    "FXList",
    "ObjectCreationList",
    "DamageFX",
    "CommandSet",
    "CommandButton",
    "SpecialPower",
    "Upgrade",
}
RUNTIME_SOFT_KINDS = {"AudioEvent", "ParticleSystem", "MappedImage", "DialogEvent"}

FXLIST_NEST = {
    "particlesystem",
    "sound",
    "viewshake",
    "lightpulse",
    "terrainscorch",
    "tracer",
}
DEFINE_RE = re.compile(
    r"^(Object|Weapon|CommandSet|CommandButton|Armor|Locomotor|ObjectCreationList|"
    r"FXList|DamageFX|ParticleSystem|MappedImage|AudioEvent|CrateData|CrateTemplate)\s+(?![=])(\S+)",
    re.I,
)
LOCO_PRIORITY_RE = re.compile(
    r"^(\s*GroupMovementPriority\s*=\s*\S+)(\s+)(?!;|\s*$)",
    re.I,
)


def _defs_in_payloads(payloads: dict[str, str]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    for path, text in payloads.items():
        parsed = ini.parse_ini_text(text, path)
        for kind, table in parsed.items():
            for name in table:
                out[kind.lower()].add(name.lower())
                if kind.lower() in ("cratedata", "cratetemplate"):
                    out["cratedata"].add(name.lower())
                    out["cratetemplate"].add(name.lower())
    return out


def check_fxlist_ends(text: str, path: str) -> list[dict]:
    errors = []
    n_lists = len(re.findall(r"(?im)^FXList\s+\S+", text))
    n_end = len(re.findall(r"(?im)^End\s*$", text))
    if n_lists and n_end < n_lists:
        errors.append(
            {
                "path": path,
                "severity": "fatal",
                "code": "fxlist_missing_column0_end",
                "detail": f"{n_end} column-0 End for {n_lists} FXList (SS1 FXList.ini uses nested End + column-0 End)",
            }
        )
    return errors


def check_object_orphan_after_end(text: str, path: str) -> list[dict]:
    if not re.search(r"(?im)^Object\s+\S+", text):
        return []
    last = None
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^End\s*$", line, re.I):
            last = i
    if last is None:
        return [{"path": path, "severity": "fatal", "code": "object_missing_end", "detail": "no column-0 End"}]
    after = [
        ln.strip()
        for ln in lines[last + 1 :]
        if ln.strip() and not ln.strip().startswith(";")
    ]
    if after:
        return [
            {
                "path": path,
                "severity": "fatal",
                "code": "tokens_after_object_end",
                "detail": after[:8],
                "line": last + 2,
            }
        ]
    return []


def check_duplicate_named_blocks(text: str, path: str) -> list[dict]:
    errors = []
    for kind in ("Armor", "Weapon", "FXList", "Locomotor", "Object", "ParticleSystem", "AudioEvent"):
        names = re.findall(rf"(?im)^{kind}\s+(?![=])(\S+)", text)
        seen: dict[str, int] = {}
        for n in names:
            seen[n.lower()] = seen.get(n.lower(), 0) + 1
        dups = [n for n, c in seen.items() if c > 1]
        if dups:
            errors.append(
                {
                    "path": path,
                    "severity": "fatal",
                    "code": "duplicate_named_block",
                    "detail": f"{kind}: {', '.join(dups)}",
                }
            )
    return errors


def check_locomotor_comments(text: str, path: str) -> list[dict]:
    errors = []
    if not re.search(r"(?im)^Locomotor\s+\S+", text):
        return errors
    for i, line in enumerate(text.splitlines(), 1):
        if LOCO_PRIORITY_RE.search(line.split(";", 1)[0]):
            errors.append(
                {
                    "path": path,
                    "line": i,
                    "severity": "fatal",
                    "code": "locomotor_uncommented_tail",
                    "detail": line.strip(),
                    "hint": "SS1 uses GroupMovementPriority = MOVES_BACK; comment",
                }
            )
    return errors


def check_parse_fatal_refs(
    payloads: dict[str, str],
    native: dict[str, set[str]] | None = None,
) -> list[dict]:
    """Refs that SS1 resolves while parsing the INI (missing template = Serious Error)."""
    native = native or {}
    local = _defs_in_payloads(payloads)
    errors = []
    for path, text in payloads.items():
        parsed = ini.parse_ini_text(text, path)
        for kind, table in parsed.items():
            for name, rec in table.items():
                refs = rec.get("named_refs") or {}
                for rkind, rnames in refs.items():
                    if rkind not in PARSE_FATAL_KINDS:
                        continue
                    for rn in rnames:
                        rl = rn.lower()
                        if rl in local.get(rkind.lower(), set()):
                            continue
                        if rl in native.get(rkind.lower(), set()):
                            continue
                        if rkind.lower() in ("cratedata", "cratetemplate"):
                            if rl in local.get("cratedata", set()) or rl in native.get("cratedata", set()):
                                continue
                        errors.append(
                            {
                                "path": path,
                                "def": f"{kind} {name}",
                                "severity": "fatal",
                                "code": "missing_parse_ref",
                                "ref": f"{rkind}:{rn}",
                            }
                        )
    return errors


def preflight_payloads(
    payloads: dict[str, bytes] | dict[str, str],
    *,
    native_defs: dict[str, set[str]] | None = None,
    layout: dict | None = None,
) -> dict:
    texts: dict[str, str] = {}
    for path, blob in payloads.items():
        texts[path] = blob.decode("latin1", errors="replace") if isinstance(blob, (bytes, bytearray)) else blob

    errors: list[dict] = []
    warnings: list[dict] = []
    for path, text in texts.items():
        load = path_loadable(path, layout)
        if load.get("protected"):
            errors.append({"path": path, "severity": "fatal", "code": "protected_path", "detail": load})
        elif not load.get("loaded"):
            errors.append({"path": path, "severity": "fatal", "code": "unloadable_path", "detail": load})
        elif load.get("confidence") == "likely":
            warnings.append({"path": path, "severity": "warn", "code": "unproven_root_kind", "detail": load})
        errors.extend(check_fxlist_ends(text, path))
        errors.extend(check_object_orphan_after_end(text, path))
        errors.extend(check_duplicate_named_blocks(text, path))
        errors.extend(check_locomotor_comments(text, path))
    errors.extend(check_parse_fatal_refs(texts, native_defs))

    fatal = [e for e in errors if e.get("severity") == "fatal"]
    return {
        "ok": not fatal,
        "error_count": len(fatal),
        "warning_count": len(warnings),
        "errors": fatal,
        "warnings": warnings,
        "generals_exe_run": False,
        "file_count": len(texts),
    }


def native_def_index(spec_inventory: dict) -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    for kind, table in spec_inventory.items():
        if not isinstance(table, dict):
            continue
        for name in table:
            out[kind.lower()].add(name.lower())
    return out
