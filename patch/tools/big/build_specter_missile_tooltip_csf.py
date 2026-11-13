#!/usr/bin/env python3
"""Patch factory missile production-button tooltips into generals.csf.

Adds Re-fire: 300 sec to all 250 A-J production tooltips (DelayBetweenShots
from PR #684). Adds Blast radius from last-wins PrimaryDamageRadius for the
16 factory missiles whose warhead mass exceeds 4000 kg.

Does not change Weapon.ini gameplay. Rebuilds 0_SPECTER_MissileCooldown.big
with the existing weapon overlay files plus Data\\English\\generals.csf.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
FACTORY_WEAPON_LIST = SCRIPT_DIR / "factory_aj_launch_weapons.json"
HEAVY_MASS_KG = 4000.0
REFIRE_LINE = "Re-fire: 300 sec"

COUNTRY_TIP = re.compile(
    r"^CONTROLBAR:ToolTip(America|Britain|China|France|Germany|India|Iran|"
    r"Israel|Italy|Japan|Libya|NorthKorea|Pakistan|Russia|SaudiArabia|"
    r"SouthAfrica|SouthKorea|Spain|Sweden|Syria|Turkey|UAE|Ukraine|Vietnam)"
    r"Missile[A-J]$"
)
IRAQ_TIP = re.compile(r"^CONTROLBAR:ToolTipSpecterMissile[A-J]$")


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off = struct.unpack(">I", data[pos : pos + 4])[0]
        size = struct.unpack(">I", data[pos + 4 : pos + 8])[0]
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, off, size))
    return entries, data


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1
    index = []
    blobs = []
    offset = header_size
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def norm_key(name: str) -> str:
    return name.replace("/", "\\").lower()


def parse_blocks(text: str, kind: str) -> dict[str, str]:
    pat = re.compile(rf"(?mi)^{kind}\s+(\S+)")
    matches = list(pat.finditer(text))
    out = {}
    for i, m in enumerate(matches):
        name = m.group(1).strip("\r")
        if name == "=":
            continue
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[name] = text[start:end]
    return out


def field(block: str, name: str) -> str | None:
    m = re.search(rf"(?mi)^\s*{re.escape(name)}\s*=\s*(.+?)\s*$", block)
    if not m:
        return None
    return m.group(1).split(";", 1)[0].strip()


def last_wins_weapons(file_map: dict[str, bytes]) -> dict[str, str]:
    items = [(norm_key(n), blob) for n, blob in file_map.items()]
    ini = [blob for k, blob in items if k == "data\\ini\\weapon.ini"]
    frags = sorted(
        [(k, blob) for k, blob in items if k.startswith("data\\ini\\weapon\\")],
        key=lambda t: t[0],
    )
    blocks: dict[str, str] = {}
    for blob in ini:
        blocks.update(parse_blocks(blob.decode("latin1"), "Weapon"))
    for _, blob in frags:
        blocks.update(parse_blocks(blob.decode("latin1"), "Weapon"))
    return blocks


def parse_csf(blob: bytes) -> tuple[bytes, list[tuple[str, str]]]:
    nlabels = struct.unpack_from("<I", blob, 8)[0]
    pos = 24
    recs = []
    for _ in range(nlabels):
        pos += 4  # LBL
        nstr, llen = struct.unpack_from("<II", blob, pos)
        pos += 8
        label = blob[pos : pos + llen].decode("ascii", errors="replace")
        pos += llen
        text = ""
        for _s in range(nstr):
            pos += 4  # STR
            slen = struct.unpack_from("<I", blob, pos)[0]
            pos += 4
            raw = blob[pos : pos + slen * 2]
            pos += slen * 2
            text = bytes(b ^ 0xFF for b in raw).decode("utf-16-le", errors="replace")
        recs.append((label, text))
    return blob[:24], recs


def write_csf(header: bytes, recs: list[tuple[str, str]]) -> bytes:
    out = bytearray()
    out += header[:4]
    out += struct.pack("<IIIII", 3, len(recs), len(recs), 0, 0)
    for label, text in recs:
        raw = bytes(b ^ 0xFF for b in text.encode("utf-16-le"))
        chars = len(raw) // 2
        out += b" LBL"
        out += struct.pack("<II", 1, len(label))
        out += label.encode("ascii")
        out += b" RTS"
        out += struct.pack("<I", chars)
        out += raw
    return bytes(out)


def fmt_radius(value: float) -> str:
    rounded = round(value)
    if abs(value - rounded) < 0.05:
        return str(int(rounded))
    return f"{value:.1f}"


def insert_after_line(text: str, pattern: str, line: str) -> str | None:
    m = re.search(pattern, text)
    if not m:
        return None
    return text[: m.end()] + line + "\n" + text[m.end() :]


def add_refire(text: str) -> str:
    if re.search(r"(?im)^Re-fire:", text):
        return text
    updated = insert_after_line(
        text,
        r"(?im)^Radar (?:Stealth|evasion):[^\n]*\n",
        REFIRE_LINE,
    )
    if updated is not None:
        return updated
    updated = insert_after_line(text, r"(?im)^Warhead:[^\n]*\n", REFIRE_LINE)
    if updated is not None:
        return updated
    return text.rstrip("\n") + "\n" + REFIRE_LINE + "\n"


def add_blast(text: str, radius: str) -> str:
    if re.search(r"(?im)^Blast radius:", text):
        return re.sub(
            r"(?im)^Blast radius:[^\n]*$",
            f"Blast radius: {radius}",
            text,
            count=1,
        )
    line = f"Blast radius: {radius}"
    updated = insert_after_line(text, r"(?im)^Warhead:[^\n]*\n", line)
    if updated is not None:
        return updated
    return text.rstrip("\n") + "\n" + line + "\n"


def fix_iraq_units(label: str, text: str) -> str:
    """Fix obvious unit typos on Iraq production tooltips we already rewrite."""
    if label == "CONTROLBAR:ToolTipSpecterMissileG":
        text = re.sub(r"(?m)^Warhead:\s*400k\s*$", "Warhead: 400 kg", text)
        text = re.sub(r"(?m)^Range:\s*1000k\s*$", "Range: 1000 km", text)
    return text


def collect_files(entries, raw, pred) -> dict[str, bytes]:
    out = {}
    for name, off, size in entries:
        if pred(norm_key(name)):
            out[name.replace("/", "\\")] = raw[off : off + size]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--data-big",
        type=Path,
        default=Path("/tmp/sp_work/SPECTER FINAL (GeneralsMode.com)/_SPEC_DATA_ONE.big"),
    )
    ap.add_argument(
        "--overlay-big",
        type=Path,
        default=Path("/workspace/patch/tools/installer/0_SPECTER_MissileCooldown.big"),
    )
    ap.add_argument(
        "--manifest",
        type=Path,
        default=Path("/workspace/patch/tools/installer/MISSILE_TOOLTIP_MANIFEST.json"),
    )
    args = ap.parse_args()

    factory = json.loads(FACTORY_WEAPON_LIST.read_text())
    factory_set = set(factory)

    data_entries, data_raw = read_big(args.data_big)
    ov_entries, ov_raw = read_big(args.overlay_big)

    data_files = collect_files(data_entries, data_raw, lambda k: True)
    ov_files = collect_files(ov_entries, ov_raw, lambda k: True)
    merged = dict(data_files)
    merged.update(ov_files)
    weapons = last_wins_weapons(merged)

    csf_name = "Data\\English\\generals.csf"
    if csf_name not in data_files:
        raise SystemExit("generals.csf missing from DATA BIG")
    header, recs = parse_csf(data_files[csf_name])
    table = {k: v for k, v in recs}

    cb_blocks: dict[str, str] = {}
    cb_blocks.update(
        parse_blocks(data_files["Data\\INI\\CommandButton.ini"].decode("latin1", "replace"), "CommandButton")
    )
    for name in sorted(data_files):
        key = norm_key(name)
        if key.endswith(".ini") and "commandbutton" in key and key != "data\\ini\\commandbutton.ini":
            cb_blocks.update(
                parse_blocks(data_files[name].decode("latin1", "replace"), "CommandButton")
            )

    tip_to_weapon: dict[str, str] = {}
    for _btn, blk in cb_blocks.items():
        desc = field(blk, "DescriptLabel") or ""
        if not (COUNTRY_TIP.match(desc) or IRAQ_TIP.match(desc)):
            continue
        obj_name = field(blk, "Object") or ""
        obj_blk = None
        # Object last-wins alphabetical Object INI
        for oname in sorted(
            (n for n in data_files if norm_key(n).startswith("data\\ini\\object") and n.lower().endswith(".ini")),
            key=lambda s: norm_key(s),
        ):
            if obj_name.encode("ascii", "ignore") not in data_files[oname]:
                continue
            parsed = parse_blocks(data_files[oname].decode("latin1", "replace"), "Object")
            if obj_name in parsed:
                obj_blk = parsed[obj_name]
        if not obj_blk:
            raise SystemExit(f"object {obj_name} for {desc} not found")
        m = re.search(r"(?mi)^\s*Weapon\s*=\s*PRIMARY\s+(\S+)", obj_blk)
        if not m:
            raise SystemExit(f"no PRIMARY on {obj_name} ({desc})")
        tip_to_weapon[desc] = m.group(1)

    if len(tip_to_weapon) != 250:
        raise SystemExit(f"expected 250 production tooltips, found {len(tip_to_weapon)}")
    missing_wpn = [w for w in tip_to_weapon.values() if w not in weapons]
    if missing_wpn:
        raise SystemExit(f"PRIMARY missing from last-wins weapons: {missing_wpn[:6]}")
    extra_factory = factory_set - set(tip_to_weapon.values())
    extra_tips = set(tip_to_weapon.values()) - factory_set
    if extra_factory or extra_tips:
        raise SystemExit(f"button/weapon set mismatch factory_only={sorted(extra_factory)[:6]} tip_only={sorted(extra_tips)[:6]}")

    heavy_pdr: dict[str, str] = {}
    for tip, wpn in tip_to_weapon.items():
        pd = float(field(weapons[wpn], "PrimaryDamage") or "0")
        mass = pd / 5.0
        if mass > HEAVY_MASS_KG:
            pdr = float(field(weapons[wpn], "PrimaryDamageRadius") or "0")
            heavy_pdr[tip] = fmt_radius(pdr)

    if len(heavy_pdr) != 16:
        raise SystemExit(f"expected 16 heavy tooltips, found {len(heavy_pdr)}")

    changed = []
    new_recs = []
    for label, text in recs:
        original = text
        if label in tip_to_weapon:
            text = fix_iraq_units(label, text)
            if label in heavy_pdr:
                text = add_blast(text, heavy_pdr[label])
            text = add_refire(text)
            if not re.search(r"(?im)^Re-fire:\s*300 sec\s*$", text):
                raise SystemExit(f"{label} missing Re-fire line")
            if label in heavy_pdr and f"Blast radius: {heavy_pdr[label]}" not in text:
                raise SystemExit(f"{label} missing Blast radius")
            if "EndWeapon" in text:
                raise SystemExit(f"{label} corrupted")
        if text != original:
            changed.append(
                {
                    "label": label,
                    "weapon": tip_to_weapon.get(label),
                    "heavy": label in heavy_pdr,
                    "blast_radius": heavy_pdr.get(label),
                    "new": text,
                }
            )
        new_recs.append((label, text))

    if len(changed) != 250:
        raise SystemExit(f"expected 250 tooltip edits, got {len(changed)}")

    # Unchanged CSF keys: sample controls
    for ctrl in (
        "CONTROLBAR:ToolTipAmericaMissileFactory",
        "CONTROLBAR:ToolTipIraqMissileRebuild",
        "CONTROLBAR:ToolTipSpecterMissileK",
        "CONTROLBAR:ToolTipSpecterMissileL",
    ):
        old = table.get(ctrl)
        new = dict(new_recs).get(ctrl)
        if old is not None and old != new:
            raise SystemExit(f"unrelated CSF key changed: {ctrl}")

    new_csf = write_csf(header, new_recs)
    # round-trip
    _, check = parse_csf(new_csf)
    if [k for k, _ in check] != [k for k, _ in recs]:
        raise SystemExit("CSF label order changed")
    if len(check) != 10977:
        raise SystemExit(f"CSF label count {len(check)}")

    out_files = dict(ov_files)
    out_files[csf_name] = new_csf
    packed = build_big(out_files)
    args.overlay_big.write_bytes(packed)

    manifest = {
        "overlay": str(args.overlay_big.name),
        "sha256": hashlib.sha256(packed).hexdigest(),
        "bytes": len(packed),
        "csf_bytes": len(new_csf),
        "tooltips_updated": len(changed),
        "heavy_blast_tooltips": [
            {"label": c["label"], "weapon": c["weapon"], "blast_radius": c["blast_radius"]}
            for c in sorted((x for x in changed if x["heavy"]), key=lambda x: x["label"])
        ],
        "notes": [
            "Re-fire: 300 sec is the production-button display of DelayBetweenShots = 300000.",
            "Blast radius is last-wins PrimaryDamageRadius for warheads above 4000 kg.",
            "Warhead kg / Range km / Accuracy / Radar Stealth lines were already correct and were kept.",
            "Iraq K/L extra missiles and the pay-to-rebuild string were not changed.",
        ],
    }
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"tooltips updated: {len(changed)}")
    print(f"heavy blast lines: {len(heavy_pdr)}")
    print(f"wrote {args.overlay_big} ({len(packed)} bytes)")
    print(f"sha256 {manifest['sha256']}")
    for c in sorted(changed, key=lambda x: x["label"]):
        if c["heavy"]:
            print(f"  {c['label']} {c['weapon']} blast {c['blast_radius']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
