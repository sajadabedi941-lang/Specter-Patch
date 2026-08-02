#!/usr/bin/env python3
"""Specter Zero Hour boot-crash audit against an actual _SPEC_DATA_ONE.big."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_specter_aircraft_aab_global_fixed_big import catalog, parse_big

OBJ_RE = re.compile(r"(?m)^Object\s+(\S+)")


def audit(entries):
    cats = catalog(entries)
    hard = []
    preload_prereq = []
    for name, raw in entries:
        path = name.replace("\\", "/")
        if not path.lower().endswith(".ini"):
            continue
        text = raw.decode("latin-1", "replace")
        for match in OBJ_RE.finditer(text):
            obj = match.group(1)
            if obj.startswith("=") or obj == "Reskin":
                continue
            start = match.start()
            nxt = OBJ_RE.search(text, match.end())
            end = nxt.start() if nxt else len(text)
            body = text[start:end]
            line0 = text.count("\n", 0, start) + 1
            preload = bool(re.search(r"(?mi)^\s*KindOf\s*=.*\bPRELOAD\b", body))

            def add(kind, token, ln, sev=0):
                hard.append(
                    {
                        "sev": sev if preload else max(sev, 2),
                        "path": path,
                        "obj": obj,
                        "line": ln,
                        "kind": kind,
                        "missing": token,
                        "preload": preload,
                    }
                )

            for cm in re.finditer(r"(?mi)^\s*CommandSet\s*=\s*(\S+)", body):
                v = cm.group(1).rstrip(";")
                if v in ("None", "NONE", "") or v.startswith(";"):
                    continue
                if v not in cats["CommandSet"]:
                    add("CommandSet", v, line0 + body[: cm.start()].count("\n"))
            for sm in re.finditer(r"(?mi)^\s*Science\s*=\s*(.+)$", body):
                ln = line0 + body[: sm.start()].count("\n")
                for v in sm.group(1).split():
                    if v.startswith(";"):
                        break
                    if v in ("None", "NONE"):
                        continue
                    if v not in cats["Science"]:
                        add("Science", v, ln)
            for sp in re.finditer(r"(?mi)^\s*SpecialPowerTemplate\s*=\s*(\S+)", body):
                v = sp.group(1)
                if v in ("None", "NONE"):
                    continue
                if v not in cats["SpecialPower"]:
                    add("SpecialPower", v, line0 + body[: sp.start()].count("\n"))
            for fm in re.finditer(
                r"(?ms)^\s*Behavior\s*=\s*FireWeaponUpdate\s+\S+.*?^\s*End\s*$", body
            ):
                wm = re.search(r"(?mi)^\s*Weapon\s*=\s*(\S+)", fm.group(0))
                if not wm:
                    continue
                w = wm.group(1)
                if w in ("None", "NONE"):
                    continue
                if w not in cats["Weapon"]:
                    add(
                        "Weapon",
                        w,
                        line0 + body[: fm.start() + wm.start()].count("\n"),
                    )
            for wm in re.finditer(
                r"(?mi)^\s*Weapon\s*=\s*(PRIMARY|SECONDARY|TERTIARY|QUATERNARY|QUINARY|SIXTH|SEVENTH|EIGHTH|NINTH|TENTH|FINAL)\s+(\S+)",
                body,
            ):
                w = wm.group(2)
                if w in ("None", "NONE"):
                    continue
                if w not in cats["Weapon"]:
                    add("Weapon", w, line0 + body[: wm.start()].count("\n"))

            in_prereq = False
            for i, line in enumerate(body.splitlines()):
                code = line.split(";", 1)[0]
                if re.match(r"^\s*Prerequisites\s*$", code):
                    in_prereq = True
                    continue
                if in_prereq and re.match(r"^\s*End\s*$", code):
                    in_prereq = False
                    continue
                if in_prereq:
                    om = re.match(r"^\s*Object\s*=\s*(.+)$", code)
                    if om:
                        for v in om.group(1).split():
                            if v not in cats["Object"] and preload:
                                preload_prereq.append(
                                    {
                                        "path": path,
                                        "obj": obj,
                                        "line": line0 + i,
                                        "missing": v,
                                    }
                                )
    preload_hard = [h for h in hard if h["preload"]]
    return cats, hard, preload_hard, preload_prereq


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--big", required=True)
    ap.add_argument("--json-out")
    args = ap.parse_args()
    big = Path(args.big)
    entries = parse_big(big)
    cats, hard, preload_hard, preload_prereq = audit(entries)
    payload = {
        "sha256": hashlib.sha256(big.read_bytes()).hexdigest(),
        "size": big.stat().st_size,
        "catalog": {k: len(v) for k, v in sorted(cats.items())},
        "preload_hard": preload_hard,
        "hardish": hard,
        "preload_prereq": preload_prereq,
        "gate_pass": not preload_hard and not [h for h in hard if h["sev"] <= 2] and not preload_prereq,
    }
    # gate: no preload hard, no hardish sev<=2 (includes non-preload FireWeaponUpdate), no preload prereq
    payload["gate_pass"] = (
        len(preload_hard) == 0
        and len([h for h in hard if h["sev"] <= 2]) == 0
        and len(preload_prereq) == 0
    )
    print(json.dumps({k: payload[k] for k in ("sha256", "size", "catalog", "gate_pass")}, indent=2))
    print("preload_hard", len(preload_hard))
    print("hardish_sev<=2", len([h for h in hard if h["sev"] <= 2]))
    print("preload_prereq", len(preload_prereq))
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(payload, indent=2))
    return 0 if payload["gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
