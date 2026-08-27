#!/usr/bin/env python3
"""Overlay Draw/Model swaps for final aircraft completion. Gameplay unchanged."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_final_global_completion as g

ROOT = Path("/workspace/patch/Data")


def apply_state_models(text: str, old: set[str], model: str, model_d: str, model_k: str, strip_anim: bool = False) -> str:
    out = []
    state = "default"
    for line in text.splitlines(True):
        s = line.strip()
        if s.startswith("DefaultConditionState"):
            state = "default"
        elif s.startswith("ConditionState") and "RUBBLE" in s:
            state = "rubble"
        elif s.startswith("ConditionState") and "REALLYDAMAGED" in s:
            state = "damaged"
        elif s.startswith("ConditionState"):
            state = "other"
        if strip_anim and re.match(r"\s*Animation(Mode)?\s*=", line):
            continue
        m = re.match(r"(\s*Model\s+=\s+)(\S+)(\s*)$", line)
        if m and m.group(2) in old:
            tgt = model if state in ("default", "other") else (model_k if state == "rubble" else model_d)
            nl = "\n" if line.endswith("\n") else ""
            line = m.group(1) + tgt + nl
        out.append(line)
    return "".join(out)


OVERLAY = [
    {
        "rel": "INI/Object/Specter/PLA/Airforce/ChinaJetJ20C.ini",
        "note": "PLA J-20C. New folder TEOD NVJ-20. Gameplay unchanged.",
        "old": {"LSFJ20"},
        "models": ("NVJ-20", "NVJ-20D", "NVJ-20D1"),
    },
    {
        "rel": "INI/Object/Specter/Italian Armed Forces/Airforce/ItalyJetF35A.ini",
        "note": "Italy F-35A. New folder TEOD AVF-35. Gameplay unchanged. Old US_F35A kept packed.",
        "old": {"US_F35A"},
        "models": ("AVF-35", "AVF-35_D", "AVF-35_E"),
    },
]


def main() -> None:
    for spec in OVERLAY:
        path = ROOT / spec["rel"]
        text = path.read_text(encoding="ascii")
        lines = text.splitlines()
        if lines and lines[0].startswith(";"):
            lines[0] = f"; SPECTER - {spec['note']}"
        text = "\n".join(lines) + "\n"
        m, md, mk = spec["models"]
        text = apply_state_models(text, spec["old"], m, md, mk)
        g.w(path, text)
        print("patched overlay", spec["rel"])


if __name__ == "__main__":
    main()
