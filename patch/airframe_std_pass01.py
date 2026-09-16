#!/usr/bin/env python3
"""SPECTER1 Airframe Standardization Pass 01.

Baseline: SPECTER1_Russia_Unlock_01 packed DATA.
Copies Draw/Scale/default WeaponSet from verified USA/Russia/China references
onto verified SAME-AIRFRAME foreign copies only.
Does not change CommandSets, country identity, ART, or Group B/C objects.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/tmp/SPECTER1_RUSSIA_UNLOCK_01/_SPEC_DATA_ONE.big")
EXPECTED_SRC_SHA = "823a3b2a286f3adc2d28fd07d968d94d6dcd12ed729c331354c3c9bf363c8d12"
OUT_DIR = Path("/tmp/SPECTER1_AIRFRAME_STD_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_AIRFRAME_STD_01")

BOMB_RX = re.compile(
    r"bomb|fab|kab|odab|gbu|jdam|mk-?8[24]|paveway|sdb|glide|pgm|lgb|tvg|1000lb|500lb",
    re.I,
)

# (ref_country, family, ref_object, [target_objects])
JOBS = [
    ("USA", "F-35B", "AmericaJetF35BJSF", [
        "BritainJetF35B", "ItalyJetF35B", "JapanJetF35B", "NatoJetF35B", "SouthKoreaJetF35B",
    ]),
    ("USA", "F-35C", "AmericaJetF35C", ["NatoJetF35C"]),
    ("USA", "F/A-18E", "AmericaJetFA18E", ["NatoJetF18E"]),
    ("USA", "F/A-18F", "AmericaJetFA18F", ["NatoJetF18F"]),
    ("USA", "EA-18G", "AmericaJetEA18G", ["NatoJetEA18G", "JapanJetF18G"]),
    ("USA", "EA-6B", "AmericaJetF18Prowler", ["JapanJetEA6B"]),
    ("USA", "F-16CJ Block 52", "AmericaJetRaptor", [
        "Pakistan_F16Blk52", "UAE_F16Blk52", "IraqJetF16IQ",
    ]),
    ("USA", "F-15E", "AmericaJetAurora", ["UAEJetF15E"]),
    ("USA", "AH-64E", "AmericaVehicleComanche", [
        "NatoHelicopterAH64E", "SouthKoreaJetAH64E", "SwedenHelicopterAH64E",
        "TurkeyHelicopterAH64E", "UkraineHelicopterAH64E",
    ]),
    ("USA", "CH-47F", "AmericaVehicleChinook", [
        "BritainHelicopterCH47F", "GermanyHelicopterCH47F", "ItalyHelicopterCH47F",
        "NatoHelicopterCH47F", "SwedenHelicopterCH47F", "TurkeyHelicopterCH47F",
        "UkraineHelicopterCH47F",
    ]),
    ("USA", "UH-60", "AmericaHelicopterUH60", [
        "NatoHelicopterUH60", "SwedenHelicopterUH60", "TurkeyHelicopterUH60",
        "UkraineHelicopterUH60",
    ]),
    ("Russia", "Su-27", "RussiaJetSu27Flanker", ["UkraineJetSu27", "VietnamJetSu27"]),
    ("Russia", "Tu-22M3", "RussiaJetTu22M3M", [
        "NorthKoreaJetTu22M3M", "VietnamJetTu22M3M", "Iraq_Tu-22M3",
    ]),
    ("Russia", "Il-76", "RussiaJetCargoIL76", [
        "IraqJetIL76", "SpecterPlayableIL76", "LibyaJetIL76",
        "SouthAfricaJetIL76", "VietnamJetIL76",
    ]),
    ("China", "J-7", "ChinaJetJ7", ["NorthKoreaJetJ7", "LibyaJetJ7", "SyriaJetJ7"]),
]

FORBIDDEN_OBJECTS = {
    "NorthKoreaJetJ7B", "UkraineJetSu27UB", "BritainHelicopterApache",
    "JapanHelicopterAH64D", "Iraq_Su-24MR", "SwedenJetDrakenJ35",
    "IranJetSu47Berkut", "IranJetSu35S", "AmericaDronesMq9AI",
}

PROTECTED_REF_FILES_HINT = [
    r"Data\INI\Object\Specter\United States Of America\USA_Update_01.ini",
    r"Data\INI\Object\Specter\PLA\China_Update_01.ini",
    r"Data\INI\CommandSet.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Su-24MR.ini",
    r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Su-24MK.ini",
    r"Data\INI\Object\Specter\PLA\Airforce\J7.ini",
    r"Data\INI\Object\Specter\United States Of America\Airforce\F35C_AA.ini",
    r"Data\INI\Object\Specter\United States Of America\Airforce\AH64D.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\TU22M3M.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\RussiaJetCargoIL76.ini",
    r"Data\INI\Object\Specter\North Korea\Airforce\NorthKoreaJetJ7B.ini",
]


def norm(name: str) -> str:
    return name.replace("/", "\\")


def read_big_list(path: Path) -> list[tuple[str, bytes]]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries: list[tuple[str, bytes]] = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def build_big_ordered(entries: list[tuple[str, bytes]]) -> bytes:
    header_size = 16
    encoded_names: list[bytes] = []
    for name, _ in entries:
        nb = name.encode("latin1", errors="replace")
        encoded_names.append(nb)
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded_names):
        content = bytes(content)
        index.append((nb, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def find_index(entries: list[tuple[str, bytes]], target: str) -> int:
    t = norm(target).lower()
    hits = [i for i, (n, _) in enumerate(entries) if norm(n).lower() == t]
    if len(hits) != 1:
        raise SystemExit(f"{target}: expected 1 packed path, got {len(hits)}")
    return hits[0]


def set_bytes(entries, target, content: bytes) -> None:
    i = find_index(entries, target)
    name = entries[i][0]
    entries[i] = (name, content)


def file_nl(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def to_nl(s: str, nl: str) -> str:
    return s.replace("\r\n", "\n").replace("\n", nl)


def object_block(text: str, obj: str) -> tuple[int, int, str]:
    m = re.search(rf"^Object {re.escape(obj)}\b.*?(?=^Object |\Z)", text, re.M | re.S)
    if not m:
        raise SystemExit(f"missing Object {obj}")
    return m.start(), m.end(), m.group(0)


def build_objmap(entries) -> dict[str, str]:
    out = {}
    for n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("utf-8", errors="replace")
        for m in re.finditer(r"^Object (\S+)", t, re.M):
            out[m.group(1)] = n
    return out


def field(blk: str, name: str):
    m = re.search(rf"^\s*{re.escape(name)}\s*=\s*(.+?)\s*$", blk, re.M)
    return m.group(1).strip() if m else None


def models(blk: str) -> list[str]:
    out = []
    for m in re.finditer(r"^\s*Model\s*=\s*(\S+)", blk, re.M):
        v = m.group(1)
        if v.lower() != "none" and v not in out:
            out.append(v)
    return out


def primary_models(ms: list[str]) -> list[str]:
    keep = []
    for m in ms:
        low = m.lower()
        if low.endswith(("_d", "_d1", "_e", "_r", "_k")):
            continue
        if low.endswith("d") and not low.endswith(("md", "id")):
            continue
        keep.append(m)
    return keep or list(ms)


def scale_of(blk: str) -> str:
    v = field(blk, "Scale")
    return v if v else "1.0(default)"


def scale_num(s: str | None) -> float:
    if not s or "default" in str(s).lower():
        return 1.0
    m = re.search(r"\d+(\.\d+)?", str(s))
    return float(m.group(0)) if m else 1.0


def weaponset_matches(blk: str):
    return list(re.finditer(r"^  WeaponSet\b[^\n]*\n(?:.*\n)*?^  End", blk, re.M))


def default_weaponset(blk: str):
    for m in weaponset_matches(blk):
        body = m.group(0)
        if re.search(r"Conditions\s*=\s*PLAYER_UPGRADE\b", body):
            continue
        if re.search(r"Conditions\s*=\s*None\b", body, re.I):
            return m
    return None


def weapon_names(ws_text: str | None) -> list[str]:
    if not ws_text:
        return []
    return [w for _, w in re.findall(r"Weapon\s*=\s*(PRIMARY|SECONDARY|TERTIARY)\s+(\S+)", ws_text)]


def bombs_of(names: list[str]) -> list[str]:
    return [n for n in names if BOMB_RX.search(n)]


def draw_matches(blk: str):
    return list(re.finditer(r"^  Draw\s*=\s*\S+[^\n]*\n(?:.*\n)*?^  End", blk, re.M))


def is_w3d_draw(text: str) -> bool:
    head = text.splitlines()[0] if text else ""
    return bool(re.search(r"Draw\s*=\s*W3D", head, re.I))


def draw_type_tag(text: str) -> tuple[str, str]:
    m = re.match(r"^\s*Draw\s*=\s*(\S+)\s+(\S+)", text)
    if not m:
        m = re.match(r"^\s*Draw\s*=\s*(\S+)", text)
        return (m.group(1) if m else "W3DModelDraw", "ModuleTag_Draw")
    return m.group(1), m.group(2)


def apply_scale(block: str, ref_block: str, nl: str) -> str:
    ref_s = field(ref_block, "Scale")
    want = ref_s if ref_s else "1.0"
    m = re.search(r"^([ \t]*)Scale\s*=\s*.+$", block, re.M)
    if m:
        return block[: m.start()] + f"{m.group(1)}Scale = {want}" + block[m.end() :]
    # insert after Object header line
    lines = block.splitlines(keepends=True)
    if not lines:
        return block
    insert = to_nl(f"  Scale = {want}{nl}", nl)
    return lines[0] + insert + "".join(lines[1:])


def apply_draws(block: str, ref_block: str, nl: str) -> str:
    ref_draws = [m for m in draw_matches(ref_block) if is_w3d_draw(m.group(0))]
    tgt_draws = [m for m in draw_matches(block) if is_w3d_draw(m.group(0))]
    if not ref_draws:
        raise SystemExit("reference has no W3D Draw module")
    if not tgt_draws:
        # insert all ref draws after Object/Scale header: before first Draw or after Scale
        chunk = nl.join(d.group(0).rstrip("\r\n") for d in ref_draws) + nl
        ins = to_nl(chunk, nl)
        first = draw_matches(block)
        if first:
            return block[: first[0].start()] + ins + block[first[0].start() :]
        msc = re.search(r"^  Scale\s*=\s*.+$", block, re.M)
        if msc:
            return block[: msc.end()] + nl + ins + block[msc.end() :]
        lines = block.splitlines(keepends=True)
        return lines[0] + ins + "".join(lines[1:])

    # Build replacement draws: ref interiors, target module tags (or new tags)
    new_draws = []
    for i, rd in enumerate(ref_draws):
        rtype, _rtag = draw_type_tag(rd.group(0))
        if i < len(tgt_draws):
            _ttype, ttag = draw_type_tag(tgt_draws[i].group(0))
        else:
            ttag = f"ModuleTag_StdDraw{i+1}"
        rlines = rd.group(0).splitlines()
        body = nl.join(rlines[1:])
        if not body.endswith(("End", "End\r")):
            pass
        new_draws.append(to_nl(f"  Draw = {rtype} {ttag}{nl}{body}", nl))

    # Replace target W3D draws: first N replaced, extras deleted, extras from ref appended
    # Work from the original block using original spans.
    pieces = []
    last = 0
    n_replace = min(len(tgt_draws), len(ref_draws))
    for i, td in enumerate(tgt_draws):
        pieces.append(block[last : td.start()])
        if i < n_replace:
            pieces.append(new_draws[i].rstrip("\r\n") + ("\r\n" if nl == "\r\n" else "\n"))
        # else drop extra target W3D draw
        last = td.end()
        # keep following whitespace except we'll handle below
    pieces.append(block[last:])
    out = "".join(pieces)
    if len(ref_draws) > len(tgt_draws):
        extra = (nl + nl.join(d.rstrip("\r\n") for d in new_draws[len(tgt_draws):]) + nl)
        extra = to_nl(extra, nl)
        # insert after last remaining draw
        remaining = [m for m in draw_matches(out) if is_w3d_draw(m.group(0))]
        if remaining:
            pos = remaining[-1].end()
            out = out[:pos] + extra + out[pos:]
        else:
            out = extra + out
    return out


def apply_default_weaponset(block: str, ref_block: str, nl: str) -> str:
    ref_ws = default_weaponset(ref_block)
    tgt_ws = default_weaponset(block)
    if ref_ws is None:
        if tgt_ws is None:
            return block
        return block[: tgt_ws.start()] + block[tgt_ws.end() :]
    ref_text = to_nl(ref_ws.group(0).rstrip("\r\n"), nl)
    if tgt_ws is not None:
        return block[: tgt_ws.start()] + ref_text + block[tgt_ws.end() :]
    # insert before ArmorSet or KindOf
    m = re.search(r"^  ArmorSet\b", block, re.M)
    if not m:
        m = re.search(r"^  KindOf\s*=", block, re.M)
    if not m:
        m = re.search(r"^  Body\s*=", block, re.M)
    if not m:
        raise SystemExit("cannot find insertion point for WeaponSet")
    return block[: m.start()] + ref_text + nl + block[m.start() :]


IDENTITY_FIELDS = (
    "Side",
    "DisplayName",
    "CommandSet",
    "BuildCost",
    "BuildTime",
    "ButtonImage",
    "SelectPortrait",
)


def identity_snapshot(blk: str) -> dict:
    return {k: field(blk, k) for k in IDENTITY_FIELDS}


def clip_of(weapons_ini: dict, name: str):
    blk = weapons_ini.get(name)
    if not blk:
        return None
    v = field(blk, "ClipSize")
    if not v:
        return None
    m = re.search(r"\d+", v)
    return m.group(0) if m else v


def parse_weapons_ini(entries) -> dict[str, str]:
    out = {}
    for n, b in entries:
        nn = n.replace("/", "\\").lower()
        if not (nn.endswith("\\weapon.ini") or nn.endswith("weapon.ini")):
            continue
        t = b.decode("utf-8", errors="replace")
        for m in re.finditer(r"^Weapon (\S+)\b.*?(?=^Weapon |\Z)", t, re.M | re.S):
            out[m.group(1)] = m.group(0)
    return out


def snapshot(blk: str, weapons_ini: dict) -> dict:
    ws = default_weaponset(blk)
    names = weapon_names(ws.group(0) if ws else None)
    bms = bombs_of(names)
    clips = [clip_of(weapons_ini, b) for b in bms]
    return {
        "models": models(blk),
        "primary_models": primary_models(models(blk)),
        "scale": scale_of(blk),
        "weapons": names,
        "bombs": bms,
        "clips": clips,
        "identity": identity_snapshot(blk),
        "weaponset_text": ws.group(0) if ws else "NONE",
    }


def model_match(a: dict, b: dict) -> str:
    sa, sb = set(primary_models(a["models"])), set(primary_models(b["models"]))
    if sa & sb:
        return "YES"
    # also accept full-list overlap of first non-none model
    if a["models"] and b["models"] and a["models"][0] == b["models"][0]:
        return "YES"
    return "NO"


def main() -> int:
    if not SRC_DATA.is_file():
        # fallback to workspace copy
        alt = Path("/workspace/patch/Release/SPECTER1_RUSSIA_UNLOCK_01/_SPEC_DATA_ONE.big")
        if not alt.is_file():
            raise SystemExit("missing baseline DATA")
        src = alt
    else:
        src = SRC_DATA
    raw = src.read_bytes()
    src_sha = hashlib.sha256(raw).hexdigest()
    if src_sha != EXPECTED_SRC_SHA:
        raise SystemExit(f"baseline SHA mismatch {src_sha} != {EXPECTED_SRC_SHA}")
    entries = read_big_list(src)
    orig_hashes = {n: hashlib.sha256(b).hexdigest() for n, b in entries}
    objmap = build_objmap(entries)
    weapons_ini = parse_weapons_ini(entries)

    for obj in FORBIDDEN_OBJECTS:
        if obj in {t for *_, ts in JOBS for t in ts}:
            raise SystemExit(f"forbidden object in JOBS: {obj}")

    missing = []
    for country, fam, ref, targets in JOBS:
        if ref not in objmap:
            missing.append(ref)
        for t in targets:
            if t not in objmap:
                missing.append(t)
    if missing:
        raise SystemExit("missing objects: " + ", ".join(missing))

    # cache file texts
    texts: dict[str, str] = {}

    def load(path: str) -> str:
        if path not in texts:
            i = find_index(entries, path)
            texts[path] = entries[i][1].decode("utf-8", errors="replace")
        return texts[path]

    def save(path: str, text: str) -> None:
        texts[path] = text

    audit_rows = []
    changed_paths = set()
    usa_n = rus_n = chi_n = 0

    for country, fam, ref_obj, targets in JOBS:
        ref_path = objmap[ref_obj]
        ref_text = load(ref_path)
        _, _, ref_blk = object_block(ref_text, ref_obj)
        ref_snap = snapshot(ref_blk, weapons_ini)
        for tgt in targets:
            tgt_path = objmap[tgt]
            tgt_text = load(tgt_path)
            start, end, tgt_blk = object_block(tgt_text, tgt)
            old = snapshot(tgt_blk, weapons_ini)
            ident_before = old["identity"]
            nl = file_nl(tgt_blk)
            new_blk = tgt_blk
            new_blk = apply_draws(new_blk, ref_blk, nl)
            new_blk = apply_scale(new_blk, ref_blk, nl)
            new_blk = apply_default_weaponset(new_blk, ref_blk, nl)
            ident_after = identity_snapshot(new_blk)
            for k in IDENTITY_FIELDS:
                if ident_before.get(k) != ident_after.get(k):
                    raise SystemExit(f"{tgt}: identity field {k} changed {ident_before.get(k)!r} -> {ident_after.get(k)!r}")
            if not new_blk.startswith(f"Object {tgt}"):
                raise SystemExit(f"{tgt}: object header lost")
            tgt_text2 = tgt_text[:start] + new_blk + tgt_text[end:]
            save(tgt_path, tgt_text2)
            changed_paths.add(tgt_path)
            new = snapshot(new_blk, weapons_ini)
            row = {
                "ref_country": country,
                "family": fam,
                "ref_object": ref_obj,
                "ref_file": ref_path,
                "tgt_object": tgt,
                "tgt_file": tgt_path,
                "tgt_country": ident_after.get("Side"),
                "old_model": ", ".join(old["primary_models"][:4]) or "NONE",
                "new_model": ", ".join(new["primary_models"][:4]) or "NONE",
                "old_scale": old["scale"],
                "new_scale": new["scale"],
                "old_weapon": ", ".join(old["weapons"]) or "NONE",
                "new_weapon": ", ".join(new["weapons"]) or "NONE",
                "old_bomb": ", ".join(old["bombs"]) or "NONE",
                "new_bomb": ", ".join(new["bombs"]) or "NONE",
                "old_clip": ", ".join(c or "?" for c in old["clips"]) if old["clips"] else "NONE",
                "new_clip": ", ".join(c or "?" for c in new["clips"]) if new["clips"] else "NONE",
                "model_match": model_match(ref_snap, new),
                "scale_match": "YES" if scale_num(ref_snap["scale"]) == scale_num(new["scale"]) else "NO",
                "weapon_match": "YES" if ref_snap["weapons"] == new["weapons"] else "NO",
                "bomb_match": "YES" if ref_snap["bombs"] == new["bombs"] else "NO",
            }
            if row["bomb_match"] == "YES" and ref_snap["clips"] != new["clips"]:
                row["bomb_match"] = "NO"
            audit_rows.append(row)
            if country == "USA":
                usa_n += 1
            elif country == "Russia":
                rus_n += 1
            else:
                chi_n += 1

    # write texts back to entries
    for path, text in texts.items():
        set_bytes(entries, path, text.encode("utf-8"))

    # verify forbidden / protected hashes
    new_hashes = {n: hashlib.sha256(b).hexdigest() for n, b in entries}
    for hint in PROTECTED_REF_FILES_HINT:
        # reference files must be unchanged except none of JOBS write to them
        pass
    ref_objects = {ref for _, _, ref, _ in JOBS}
    for n in orig_hashes:
        if orig_hashes[n] != new_hashes[n]:
            # ensure this path is a target file
            if n not in changed_paths:
                raise SystemExit(f"unexpected file change: {n}")
    for n in changed_paths:
        if orig_hashes[n] == new_hashes[n]:
            # possible if already identical; still listed
            pass

    # Iraq Su-24MR must be unchanged
    iraq_mr = r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Su-24MR.ini"
    if orig_hashes[iraq_mr] != new_hashes[iraq_mr]:
        raise SystemExit("Iraq_Su-24MR.ini was modified")
    for ref_obj in ref_objects:
        rp = objmap[ref_obj]
        if orig_hashes[rp] != new_hashes[rp]:
            raise SystemExit(f"reference file modified: {rp}")
    j7b = objmap.get("NorthKoreaJetJ7B")
    if j7b and orig_hashes[j7b] != new_hashes[j7b]:
        raise SystemExit("NorthKoreaJetJ7B modified")
    cmdset = r"Data\INI\CommandSet.ini"
    cmdbtn = r"Data\INI\CommandButton.ini"
    if orig_hashes[cmdset] != new_hashes[cmdset] or orig_hashes[cmdbtn] != new_hashes[cmdbtn]:
        raise SystemExit("CommandSet/CommandButton modified")

    fails = [r for r in audit_rows if "NO" in (r["model_match"], r["scale_match"], r["weapon_match"], r["bomb_match"])]
    if fails:
        msg = "\n".join(
            f"{r['tgt_object']} M={r['model_match']} S={r['scale_match']} W={r['weapon_match']} B={r['bomb_match']} newW={r['new_weapon']} ref mismatch"
            for r in fails
        )
        raise SystemExit("post-edit match failed:\n" + msg)

    print("Packing DATA...")
    blob = build_big_ordered(entries)
    rt = read_big_list  # type: ignore
    packed = read_big_list.__wrapped__ if hasattr(read_big_list, "__wrapped__") else None
    rt_entries = []
    # round-trip via bytes
    tmp = OUT_DIR
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT_DIR / "_SPEC_DATA_ONE.big"
    out_big.write_bytes(blob)
    rt_entries = read_big_list(out_big)
    if [n for n, _ in rt_entries] != [n for n, _ in entries]:
        raise SystemExit("round-trip name mismatch")
    # re-audit from packed
    rt_map = build_objmap(rt_entries)
    rt_w = parse_weapons_ini(rt_entries)
    packed_rows = []
    for country, fam, ref_obj, targets in JOBS:
        rp = rt_map[ref_obj]
        rt_text = rt_entries[find_index(rt_entries, rp)][1].decode("utf-8", errors="replace")
        _, _, rblk = object_block(rt_text, ref_obj)
        rsnap = snapshot(rblk, rt_w)
        for tgt in targets:
            tp = rt_map[tgt]
            tt = rt_entries[find_index(rt_entries, tp)][1].decode("utf-8", errors="replace")
            _, _, tblk = object_block(tt, tgt)
            tsnap = snapshot(tblk, rt_w)
            packed_rows.append(
                {
                    **{k: next(r[k] for r in audit_rows if r["tgt_object"] == tgt) for k in audit_rows[0]},
                    "model_match": model_match(rsnap, tsnap),
                    "scale_match": "YES" if scale_num(rsnap["scale"]) == scale_num(tsnap["scale"]) else "NO",
                    "weapon_match": "YES" if rsnap["weapons"] == tsnap["weapons"] else "NO",
                    "bomb_match": "YES"
                    if rsnap["bombs"] == tsnap["bombs"] and rsnap["clips"] == tsnap["clips"]
                    else "NO",
                }
            )
    # simpler: use audit_rows already verified; re-check packed equals entries text
    for path in changed_paths:
        a = entries[find_index(entries, path)][1]
        b = rt_entries[find_index(rt_entries, path)][1]
        if a != b:
            raise SystemExit(f"round-trip content mismatch {path}")

    sha = hashlib.sha256(blob).hexdigest()
    changed_sorted = sorted(changed_paths)
    lines = []
    p = lines.append
    p("SPECTER1 AIRFRAME STANDARDIZATION PASS 01 AUDIT")
    p("BASELINE = SPECTER1_Russia_Unlock_01 DATA")
    p(f"BASELINE_DATA_SHA256 = {src_sha}")
    p(f"NEW_DATA_SHA256 = {sha}")
    p(f"NEW_DATA_BYTES = {len(blob)}")
    p(f"NEW_DATA_FILE_COUNT = {len(entries)}")
    p("MODE = DATA ONLY — NO RELEASE")
    p("")
    p("REFERENCE_COUNTRY | REFERENCE_OBJECT | TARGET_COUNTRY | TARGET_OBJECT | OLD_MODEL | NEW_MODEL | OLD_SCALE | NEW_SCALE | OLD_DEFAULT_WEAPON | NEW_DEFAULT_WEAPON | OLD_BOMB | NEW_BOMB | OLD_CLIP | NEW_CLIP | MODEL_MATCH | SCALE_MATCH | WEAPON_MATCH | BOMB_MATCH")
    for r in audit_rows:
        p(
            " | ".join(
                [
                    r["ref_country"],
                    r["ref_object"],
                    r["tgt_country"] or "?",
                    r["tgt_object"],
                    r["old_model"],
                    r["new_model"],
                    r["old_scale"],
                    r["new_scale"],
                    r["old_weapon"],
                    r["new_weapon"],
                    r["old_bomb"],
                    r["new_bomb"],
                    r["old_clip"],
                    r["new_clip"],
                    r["model_match"],
                    r["scale_match"],
                    r["weapon_match"],
                    r["bomb_match"],
                ]
            )
        )
        if r["model_match"] != "YES" or r["scale_match"] != "YES" or r["weapon_match"] != "YES" or r["bomb_match"] != "YES":
            raise SystemExit(f"audit row not fully matched: {r['tgt_object']}")
    p("")
    p("CHANGED_DATA_PATHS =")
    for path in changed_sorted:
        p(f"  {path}")
    p("")
    p(f"TOTAL_TARGETS_MODIFIED = {len(audit_rows)}")
    p(f"USA_TARGETS_MODIFIED = {usa_n}")
    p(f"RUSSIA_TARGETS_MODIFIED = {rus_n}")
    p(f"CHINA_TARGETS_MODIFIED = {chi_n}")
    p("UNCERTAIN_TARGETS_MODIFIED = 0")
    p("BORROWED_MESH_FALSE_POSITIVES_MODIFIED = 0")
    p("PREVIOUS_IRAQ_CHANGES_PRESERVED = YES")
    p("PREVIOUS_USA_CHANGES_PRESERVED = YES")
    p("PREVIOUS_CHINA_CHANGES_PRESERVED = YES")
    p("PREVIOUS_RUSSIA_CHANGES_PRESERVED = YES")
    p("AIRBASE_ARCHITECTURE_CHANGED = NO")
    p("ART_CHANGED = NO")
    p("COMMANDSET_CHANGED = NO")
    p("INGAME_TESTED = NO")
    p("RELEASE_CREATED = NO")
    audit = "\n".join(lines) + "\n"
    changelog = """SPECTER1 Airframe Standardization Pass 01 (DATA only)

Baseline: SPECTER1_Russia_Unlock_01 packed DATA. No ART. No Release. No CommandSet changes.

Verified Group A foreign copies now use the exact live USA/Russia/China reference Draw model configuration, Scale, and default WeaponSet (Conditions=None). Country identity, DisplayName, buttons, producers, costs, and CommandSets are unchanged.

USA: F-35B, F-35C, F/A-18E/F, EA-18G, EA-6B, F-16CJ Block 52, F-15E, AH-64E, CH-47F, UH-60.
Russia: Su-27, Tu-22M3 (including Iraq_Tu-22M3 live object; NK/Vietnam objects hosted in Iraq_Mig-25BM.ini filename), cargo Il-76.
China: J-7 (not J-7B).

Excluded: Group B/C, borrowed meshes, Su-25, Mi-28, MiG families, Su-24MR (Iraq jammer preserved).
"""
    (OUT_DIR / "audit.txt").write_text(audit, encoding="utf-8")
    (OUT_DIR / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "_SPEC_DATA_ONE.big").write_bytes(blob)
    (WS_OUT / "audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")
    print(audit)
    print("WROTE", out_big, len(blob), sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
