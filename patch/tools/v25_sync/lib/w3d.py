"""Read texture and animation names from a SAGE W3D blob. No substitution."""
from __future__ import annotations

import re

TEX_RE = re.compile(rb"[A-Za-z0-9_\-]{3,64}\.(?:tga|dds|TGA|DDS)")
ANIM_RE = re.compile(rb"[A-Za-z][A-Za-z0-9_\-]{2,47}\.[A-Za-z][A-Za-z0-9_\-]{2,47}")


def texture_names(blob: bytes) -> list[str]:
    found = []
    seen = set()
    for m in TEX_RE.finditer(blob):
        name = m.group(0).decode("latin1")
        key = name.lower()
        if key not in seen:
            seen.add(key)
            found.append(name)
    return found


def animation_names(blob: bytes) -> list[str]:
    """W3D animation refs look like ModelName.AnimName (dot, no extension)."""
    found = []
    seen = set()
    for m in ANIM_RE.finditer(blob):
        name = m.group(0).decode("latin1")
        if name.lower().endswith((".tga", ".dds", ".w3d", ".ini")):
            continue
        if name.lower() not in seen:
            seen.add(name.lower())
            found.append(name)
    return found[:40]
