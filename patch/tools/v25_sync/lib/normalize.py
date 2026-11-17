"""Output-only SS1 syntax normalize. Never writes V25 or SPECTER source files."""
from __future__ import annotations

import re

from .pack_sample import close_fxlist_blocks
from .preflight import check_object_orphan_after_end

LOCO_TAIL = re.compile(
    r"^(\s*GroupMovementPriority\s*=\s*\S+)(\s+)(?!;|\s*$)(.*)$",
    re.I,
)


def fix_locomotor_text(text: str) -> str:
    """SS1 uses `GroupMovementPriority = MOVES_BACK; comment`."""
    lines = []
    for line in text.splitlines():
        m = LOCO_TAIL.match(line)
        if m:
            comment = (m.group(3) or "").strip()
            line = f"{m.group(1)}; {comment}".rstrip()
        lines.append(line)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def object_missing_end(text: str, path: str = "") -> bool:
    return any(e.get("code") == "object_missing_end" for e in check_object_orphan_after_end(text, path))


def normalize_payloads(payloads: dict[str, str]) -> dict[str, str]:
    """Return a new dict. Input is unchanged. Not written to disk here."""
    out: dict[str, str] = {}
    for path, text in payloads.items():
        npath = path.replace("/", "\\").lower()
        t = text
        if "fxlist" in npath or re.search(r"(?im)^FXList\s+\S+", t):
            t = close_fxlist_blocks(t)
        if "locomotor" in npath or re.search(r"(?im)^Locomotor\s+\S+", t):
            t = fix_locomotor_text(t)
        out[path] = t
    return out
