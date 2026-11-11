"""Reference rewrite planner. Does not write game INI; returns rewritten text."""
from __future__ import annotations

import re

PREFIX = "SD25_"


def independent_name(name: str) -> str:
    if not name:
        return name
    if name.upper().startswith(PREFIX):
        return name
    return f"{PREFIX}{name}"


def token_pattern(name: str) -> re.Pattern:
    return re.compile(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])")


def rewrite_text(text: str, mapping: dict[str, str]) -> str:
    """Replace identifier tokens. Longer names first so Foo is not eaten by FooBar's inverse."""
    out = text
    for old in sorted(mapping, key=len, reverse=True):
        new = mapping[old]
        if old == new:
            continue
        out = token_pattern(old).sub(new, out)
    return out


def rewrite_keys(keys: list[tuple[str, str]], mapping: dict[str, str]) -> list[tuple[str, str]]:
    return [(k, rewrite_text(v, mapping)) for k, v in keys]


def collect_rewrite_map(actions: list[dict]) -> dict[str, str]:
    """Build old->new from resolver actions with RENAME_AND_REWRITE."""
    mp: dict[str, str] = {}
    for row in actions:
        if row.get("action") == "RENAME_AND_REWRITE":
            old = row.get("name")
            new = row.get("planned") or independent_name(old)
            if old and new and old != new:
                mp[old] = new
    return mp
