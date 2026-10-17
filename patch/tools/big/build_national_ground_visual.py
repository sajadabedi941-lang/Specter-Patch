#!/usr/bin/env python3
"""ART-only National Ground Forces visual upgrade.

Does not change weapons, armor, locomotor, cost, time, prerequisites,
CommandButtons, CommandSets, or CSF strings.
"""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_national_ground_forces import (
    DONOR_BIGS,
    DonorLib,
    _tex_walk,
    basename,
    build_big_ordered,
    last_named,
    norm,
    parse_big,
)
from national_ground_roster import LOCKED_BIG_PATHS, all_units
from national_ground_visual_map import PROTECTED_ART_STEMS, PROTECTED_SIDES, VISUAL_UPGRADES

SRC_DATA = Path("/tmp/national_ground_forces/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/national_ground_forces/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/national_ground_visual")


def replace_models(blk: str, new_model: str) -> str:
    old_models = set(re.findall(r"(?m)^\s*Model\s+=\s+(\S+)", blk))
    old_models.discard("None")
    old_models.discard("NONE")
    old_models.discard("none")
    for om in old_models:
        blk = re.sub(rf"(?m)^(\s*Model\s+=\s+){re.escape(om)}\s*$", rf"\1{new_model}", blk)
        blk = re.sub(rf"(?m)^(\s*Animation\s+=\s+){re.escape(om)}\.\S+", rf"\1{new_model}.{new_model}", blk)
    return blk


def current_model(blk: str) -> str | None:
    m = re.search(r"(?m)^\s*Model\s+=\s+(\S+)", blk)
    return m.group(1) if m else None


def side_of(blk: str) -> str:
    m = re.search(r"(?m)^\s*Side\s+=\s+(\S+)", blk)
    return m.group(1) if m else ""


def main() -> int:
    if not SRC_DATA.is_file() or not SRC_ART.is_file():
        print("missing source BIG", file=sys.stderr)
        return 1

    data_entries = parse_big(SRC_DATA)
    art_entries = parse_big(SRC_ART)
    data_index = {norm(n): i for i, (n, _) in enumerate(data_entries)}
    art_index = {norm(n): (n, b) for n, b in art_entries}
    src_data_names = [n for n, _ in data_entries]
    src_art_names = [n for n, _ in art_entries]
    packed_bases = {basename(n): n for n, _ in art_entries}

    donor = DonorLib([p for p in DONOR_BIGS if p.is_file()])
    inject_art = []
    seen_inject = set()

    def packed_stem(stem: str):
        key = stem.lower() + ".w3d"
        if key in packed_bases:
            return Path(packed_bases[key].replace("\\", "/")).stem
        return None

    def ensure_model(stem: str) -> str:
        hit_packed = packed_stem(stem)
        if hit_packed:
            return hit_packed
        for n, _b in inject_art:
            if basename(n) == stem.lower() + ".w3d":
                return Path(n.replace("\\", "/")).stem
        hit = donor.get(stem + ".w3d") or donor.get(stem)
        if not hit:
            raise SystemExit(f"missing visual donor mesh {stem}")
        name, blob = hit
        out_name = rf"Art\W3D\{Path(name.replace(chr(92), '/')).name}"
        if any(x in basename(out_name) for x in PROTECTED_ART_STEMS) and norm(out_name) in art_index:
            raise SystemExit(f"refusing overwrite packed {out_name}")
        if norm(out_name) not in art_index and norm(out_name) not in seen_inject:
            inject_art.append((out_name, blob))
            seen_inject.add(norm(out_name))
            print("inject W3D", out_name, "bytes", len(blob))
            for tex in _tex_walk(blob, 0, len(blob)):
                tb = basename(tex)
                if tb in packed_bases or any(basename(n) == tb for n, _ in inject_art):
                    continue
                th = donor.get(tex) or donor.get(Path(tex).name)
                if not th:
                    continue
                tname, tblob = th
                tout = rf"Art\Textures\{Path(tname.replace(chr(92), '/')).name}"
                if norm(tout) in art_index or norm(tout) in seen_inject:
                    continue
                if any(x in basename(tout) for x in PROTECTED_ART_STEMS) and norm(tout) in art_index:
                    continue
                inject_art.append((tout, tblob))
                seen_inject.add(norm(tout))
                print("  inject tex", tout)
        return Path(out_name.replace("\\", "/")).stem

    # locate last-wins object file
    obj_files: dict[str, tuple[int, str]] = {}
    for i, (n, blob) in enumerate(data_entries):
        if not n.lower().endswith(".ini"):
            continue
        t = blob.decode("latin1")
        for name in re.findall(r"(?m)^Object\s+(\S+)\s*$", t):
            obj_files[name] = (i, n)

    changed = []
    skipped = []
    wanted = {u.obj: (c.key, u) for c, u in all_units()}

    for obj, (stem, reason) in VISUAL_UPGRADES.items():
        if obj not in obj_files:
            raise SystemExit(f"object missing {obj}")
        i, fname = obj_files[obj]
        text = data_entries[i][1].decode("latin1")
        m = last_named(text, "Object", obj)
        if not m:
            raise SystemExit(f"no block {obj} in {fname}")
        blk = m.group(0)
        if side_of(blk) in PROTECTED_SIDES:
            raise SystemExit(f"refusing protected side object {obj}")
        old = current_model(blk)
        if old and old.lower() == stem.lower():
            skipped.append((obj, old, "already using target mesh"))
            print("skip already", obj, old)
            continue
        new_stem = ensure_model(stem)
        new_blk = replace_models(blk, new_stem)
        if new_blk == blk:
            skipped.append((obj, old, "no Model= lines changed"))
            continue
        # refuse weapon / cost / commandset edits
        for field in ("BuildCost", "BuildTime", "Weapon =", "Locomotor", "CommandSet"):
            if field.startswith("Weapon"):
                old_w = re.findall(r"(?m)^\s*Weapon\s+=\s+.+$", blk)
                new_w = re.findall(r"(?m)^\s*Weapon\s+=\s+.+$", new_blk)
                if old_w != new_w:
                    raise SystemExit(f"weapon changed on {obj}")
            elif field == "Locomotor":
                if re.findall(r"(?m)^\s*Locomotor\s+=\s+.+$", blk) != re.findall(r"(?m)^\s*Locomotor\s+=\s+.+$", new_blk):
                    raise SystemExit(f"locomotor changed on {obj}")
            else:
                if re.findall(rf"(?m)^\s*{field}\s+=\s+(\S+)", blk) != re.findall(rf"(?m)^\s*{field}\s+=\s+(\S+)", new_blk):
                    raise SystemExit(f"{field} changed on {obj}")
        text = text[: m.start()] + new_blk + text[m.end() :]
        data_entries[i] = (data_entries[i][0], text.encode("latin1"))
        changed.append((obj, old, new_stem, fname, reason))
        print("visual", obj, old, "->", new_stem, "in", fname)

    locked = {norm(p) for p in LOCKED_BIG_PATHS}
    for path in LOCKED_BIG_PATHS:
        key = norm(path)
        if key in data_index:
            # compare later in audit; do not rewrite
            pass
        if key in locked and key in data_index:
            pass

    for n, blob in inject_art:
        if norm(n) in art_index:
            print("skip existing ART", n)
            continue
        art_entries.append((n, blob))
        art_index[norm(n)] = (n, blob)
        packed_bases[basename(n)] = n

    if [n for n, _ in data_entries][: len(src_data_names)] != src_data_names:
        raise SystemExit("DATA entry-order prefix changed")
    if [n for n, _ in art_entries][: len(src_art_names)] != src_art_names:
        raise SystemExit("ART entry-order prefix changed")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(data_entries)
    art_big = build_big_ordered(art_entries)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(art_big)
    (OUT_DIR / "visual_changes.txt").write_text(
        "\n".join(f"{o}\t{old}\t{new}\t{fn}\t{why}" for o, old, new, fn, why in changed) + "\n"
    )
    print("CHANGED", len(changed), "SKIPPED", len(skipped))
    print("DATA_SHA256", hashlib.sha256(data_big).hexdigest())
    print("ART_SHA256", hashlib.sha256(art_big).hexdigest())
    print("DATA_BYTES", len(data_big), "FILES", len(data_entries))
    print("ART_BYTES", len(art_big), "FILES", len(art_entries))
    print("wanted_units", len(wanted))
    return 0


if __name__ == "__main__":
    sys.exit(main())
