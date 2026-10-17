#!/usr/bin/env python3
"""National ground runtime repair.

Fixes in-game War Factory / 14-slot failures found after packed audits:
- leftover StrategyCenter / Rank / Science gates on four existing objects
- missing W3D textures that make units invisible
- inherited USA bone names that do not exist on national meshes
- overlay CommandSet aliases that last-wins-overwrite the 14-slot WF bar

Does not rewrite protected factions, aircraft rosters, PlayerTemplate,
Science, SpecialPower, or JP/SK/VN CommandCenter / VT72B files.
Does not put CommandSet/CommandButton under Data\\INI\\Object\\.
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_national_ground_forces import (
    DONOR_BIGS,
    DonorLib,
    build_big_ordered,
    last_named,
    norm,
    parse_big,
    w3d_textures,
)
from national_ground_roster import (
    ALIAS_COMMANDSETS,
    COUNTRIES,
    LOCKED_BIG_PATHS,
    all_units,
)

SRC_DATA = Path("/tmp/national_ground_commandbar/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/national_ground_commandbar/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/national_ground_runtime")
BASE_ART_SHA = "e72e6334ab7b9691e3327a0d0a76d4fe771b4cb607e656fa97106e4d69b90c12"

W3D_PIVOTS = 0x00000102
SLOT_TOKENS = {"PRIMARY", "SECONDARY", "TERTIARY"}
WEAPON_BONE_KEYS = (
    "WeaponFireFXBone",
    "WeaponRecoilBone",
    "WeaponLaunchBone",
    "WeaponMuzzleFlash",
)
TURRET_BONE_KEYS = ("Turret", "TurretPitch", "AltTurret")
MISSILE_ROLES = {"sam", "ballistic", "mlrs"}

# Overlay files load after CommandSet.ini and last-wins the underscore aliases.
OVERLAY_CS = {
    r"Data\INI\CommandSet_Germany.ini": "Germany_WarFactoryCommandSet",
    r"Data\INI\CommandSet_France.ini": "France_WarFactoryCommandSet",
    r"Data\INI\CommandSet_Britain.ini": "Britain_WarFactoryCommandSet",
    r"Data\INI\CommandSet_Italy.ini": "Italy_WarFactoryCommandSet",
}

PREREQ_FIX = {
    "GermanyVehicleIRIST": "GermanyWarFactory",
    "FranceVehicleVBCI": "FranceWarFactory",
    "FranceVehicleCaesar": "FranceWarFactory",
    "SwedenVehicleIRIST": "SwedenWarFactory",
}


def basename(name: str) -> str:
    return name.replace("\\", "/").split("/")[-1].lower()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def field_line(blk: str, name: str):
    m = re.search(rf"(?m)^\s*{re.escape(name)}\s*=\s*(.+?)\s*$", blk)
    return m.group(1).strip() if m else None


def default_model(blk: str) -> str | None:
    m = re.search(
        r"(?ms)^\s*DefaultConditionState[^\r\n]*\r?\n(.*?)(?=^\s*(?:End|ModelConditionState|DefaultConditionState)\b)",
        blk,
    )
    if m:
        mm = re.search(r"(?m)^\s*Model\s*=\s*(\S+)", m.group(1))
        if mm:
            return mm.group(1)
    mm = re.search(r"(?m)^\s*Model\s*=\s*(\S+)", blk)
    return mm.group(1) if mm else None


def w3d_bones(blob: bytes) -> list[str]:
    names: list[str] = []

    def walk(start: int, end: int) -> None:
        pos = start
        while pos + 8 <= end:
            ct, cs = struct.unpack_from("<II", blob, pos)
            ch = cs & 0x80000000
            csz = cs & 0x7FFFFFFF
            pl = pos + 8
            nxt = pl + csz
            if nxt > end:
                break
            if ct == W3D_PIVOTS:
                rec = 60
                nrec = csz // rec
                for i in range(nrec):
                    raw = blob[pl + i * rec : pl + i * rec + 16]
                    nm = raw.split(b"\x00", 1)[0].decode("ascii", "replace")
                    if nm:
                        names.append(nm)
            if ch:
                walk(pl, nxt)
            pos = nxt

    walk(0, len(blob))
    return names


def art_index(art_entries):
    by_stem = {}
    by_tex = {}
    for n, b in art_entries:
        bn = basename(n)
        if bn.endswith(".w3d"):
            by_stem[bn[:-4]] = (n, b)
        by_tex[Path(bn).stem] = n
        by_tex[bn] = n
    return by_stem, by_tex


def classify_bones(bones: list[str]) -> dict[str, str | None]:
    low = [(b, b.lower()) for b in bones]

    def first(*preds):
        for b, l in low:
            if all(p(l) for p in preds):
                return b
        return None

    turret = first(
        lambda l: "turret" in l,
        lambda l: "el" not in l,
        lambda l: "pitch" not in l,
        lambda l: "ms" not in l or l.endswith("01") or l == "turret01" or l == "turret",
    )
    if turret is None:
        turret = first(lambda l: l in {"turret", "turret01"} or l.startswith("turret"))
        turret = first(lambda l: "turret" in l and "el" not in l) if turret is None else turret
    pitch = first(lambda l: "turretel" in l or l in {"turretele", "turretle"} or "pitch" in l)
    barrel = first(lambda l: "barrel" in l)
    muzzle = first(lambda l: "muzzle" in l)
    fire = first(lambda l: "firepoint" in l or l.startswith("firefx"))
    launch = first(
        lambda l: "launch" in l or "missile" in l or l in {"agm", "weapona01", "weapon01"}
    )
    weapon = first(lambda l: l.startswith("weapon") or "weapon" in l)
    return {
        "turret": turret,
        "pitch": pitch,
        "barrel": barrel,
        "muzzle": muzzle,
        "fire": fire,
        "launch": launch,
        "weapon": weapon,
    }


def fallback_bone(bones: list[str], classed: dict[str, str | None]) -> str | None:
    for k in ("muzzle", "fire", "barrel", "turret", "launch", "weapon", "pitch"):
        if classed.get(k):
            return classed[k]
    for b in bones:
        if b.upper() != "ROOTTRANSFORM":
            return b
    return bones[0] if bones else None


def map_bone(req: str, bones: list[str], classed: dict[str, str | None], role: str) -> str:
    if not req:
        return req
    cmap = {b.lower(): b for b in bones}
    if req.lower() in cmap:
        return cmap[req.lower()]
    r = req.lower()
    if r[:1].isdigit() or r in {"yes", "no", "true", "false"}:
        return req
    last = fallback_bone(bones, classed)

    def pick(*keys):
        for k in keys:
            v = classed.get(k)
            if v:
                return v
        return last

    missile = role in MISSILE_ROLES
    if r in {"turret", "turret01", "turret02"} or r.startswith("turretms"):
        return pick("turret", "barrel", "muzzle", "fire")
    if r in {"turretle", "turretel", "turretele", "turretpitch"} or "pitch" in r:
        return pick("pitch", "turret", "muzzle")
    if r.startswith("barrel"):
        return pick("barrel", "muzzle", "fire", "turret")
    if "muzzle" in r:
        return pick("muzzle", "fire", "barrel", "weapon", "turret")
    if r in {"weapona", "weaponb", "weapon", "weapon01", "weapona01", "weaponb01"} or r.startswith(
        "weapon"
    ):
        if missile:
            return pick("launch", "weapon", "fire", "muzzle", "turret")
        return pick("weapon", "muzzle", "fire", "barrel", "launch", "turret")
    if r in {"missile", "missile01"} or "missile" in r:
        return pick("launch", "weapon", "fire", "muzzle", "turret")
    if missile:
        return pick("launch", "weapon", "fire", "muzzle", "turret")
    return pick("muzzle", "fire", "barrel", "weapon", "turret") or req


def remap_bones(blk: str, bones: list[str], role: str) -> tuple[str, int]:
    if not bones:
        return blk, 0
    classed = classify_bones(bones)
    cmap = {b.lower(): b for b in bones}
    changed = 0

    def repl_weapon(m: re.Match) -> str:
        nonlocal changed
        key, slot, bone = m.group("key"), m.group("slot"), m.group("bone")
        rest = m.group("rest") or ""
        if bone is None:
            if slot.upper() in SLOT_TOKENS:
                return m.group(0)
            old = slot
            new = map_bone(old, bones, classed, role)
            if new != old:
                changed += 1
            return f"{m.group('indent')}{key} = {new}{rest}"
        new = map_bone(bone, bones, classed, role)
        if new != bone:
            changed += 1
        return f"{m.group('indent')}{key} = {slot} {new}{rest}"

    blk = re.sub(
        r"(?m)^(?P<indent>\s*)(?P<key>WeaponFireFXBone|WeaponRecoilBone|WeaponLaunchBone|WeaponMuzzleFlash)\s*=\s*(?P<slot>\S+)(?:\s+(?P<bone>\S+))?(?P<rest>.*)$",
        repl_weapon,
        blk,
    )

    def repl_turret(m: re.Match) -> str:
        nonlocal changed
        key, bone, rest = m.group("key"), m.group("bone"), m.group("rest") or ""
        if re.match(r"^-?\d", bone):
            return m.group(0)
        new = map_bone(bone, bones, classed, role)
        if new != bone:
            changed += 1
        return f"{m.group('indent')}{key} = {new}{rest}"

    blk = re.sub(
        r"(?m)^(?P<indent>\s*)(?P<key>Turret|TurretPitch|AltTurret)\s*=\s*(?P<bone>\S+)(?P<rest>.*)$",
        repl_turret,
        blk,
    )

    def repl_extra(m: re.Match) -> str:
        nonlocal changed
        bone = m.group("bone")
        if bone.lower() in cmap:
            return m.group(0)
        new = map_bone(bone, bones, classed, role)
        if new != bone:
            changed += 1
        return f"{m.group('indent')}ExtraPublicBone = {new}{m.group('rest')}"

    blk = re.sub(
        r"(?m)^(?P<indent>\s*)ExtraPublicBone\s*=\s*(?P<bone>\S+)(?P<rest>.*)$",
        repl_extra,
        blk,
    )
    return blk, changed


def strip_unit_gates(blk: str, wf: str) -> str:
    nl = "\r\n" if "\r\n" in blk else "\n"
    new_pre = f"  Prerequisites{nl}    Object = {wf}{nl}  End"
    pr = re.search(r"(?ms)^(\s*)Prerequisites\s*\r?\n.*?\r?\n\1End[^\S\r\n]*", blk)
    if pr:
        blk = blk[: pr.start()] + new_pre + blk[pr.end() :]
    else:
        side_m = re.search(r"(?m)^(\s*Side\s*=\s*\S+[^\r\n]*)$", blk)
        if side_m:
            blk = blk[: side_m.end()] + nl + new_pre + blk[side_m.end() :]
    blk = re.sub(r"(?m)^\s*Science\s*=\s*\S+[^\r\n]*\r?\n", "", blk)
    blk = re.sub(r"(?m)^\s*NeededUpgrade\s*=\s*\S+[^\r\n]*\r?\n", "", blk)
    return blk


def ensure_can_attack(blk: str) -> str:
    weapons = re.findall(r"(?m)^\s*Weapon\s*=\s*\S+\s+\S+", blk)
    if not weapons:
        return blk
    m = re.search(r"(?m)^(\s*KindOf\s*=\s*)(.+)$", blk)
    if not m:
        return blk
    kinds = m.group(2)
    if "CAN_ATTACK" in kinds:
        return blk
    return blk[: m.start(2)] + "CAN_ATTACK " + kinds + blk[m.end(2) :]


def replace_named_block(text: str, kind: str, name: str, new_blk: str) -> str:
    m = last_named(text, kind, name)
    if not m:
        raise SystemExit(f"missing {kind} {name}")
    return text[: m.start()] + new_blk + text[m.end() :]


def cs_slots(blk: str) -> list[tuple[int, str]]:
    return [(int(a), b) for a, b in re.findall(r"(?m)^\s*(\d+)\s*=\s*(\S+)", blk)]


def write_cs_block(name: str, slots: list[tuple[int, str]], newline: str) -> str:
    lines = [f"CommandSet {name}{newline}"]
    for i, btn in slots:
        lines.append(f"  {i} = {btn}{newline}")
    lines.append(f"End{newline}")
    return "".join(lines)


def packed_tex_stems(art_entries) -> set[str]:
    out = set()
    for n, _b in art_entries:
        bn = basename(n)
        if bn.endswith((".tga", ".dds", ".jpg", ".jpeg")):
            out.add(Path(bn).stem)
    return out


def unique_missing_stems(texs: list[str], packed: set[str]) -> list[str]:
    miss = []
    seen = set()
    for t in texs:
        st = Path(basename(t)).stem
        if st in seen:
            continue
        seen.add(st)
        if st not in packed:
            miss.append(t)
    return miss


def inject_named(art_entries, out_name: str, blob: bytes, seen: set[str]) -> bool:
    key = norm(out_name)
    if key in seen:
        return False
    art_entries.append((out_name, blob))
    seen.add(key)
    print("inject ART", out_name, "bytes", len(blob))
    return True


def donor_get_any(donor: DonorLib, names: list[str]):
    for nm in names:
        hit = donor.get(nm)
        if hit:
            return hit
    return None


def main() -> int:
    if not SRC_DATA.is_file() or not SRC_ART.is_file():
        raise SystemExit(f"missing baseline BIG {SRC_DATA} / {SRC_ART}")
    if sha256(SRC_ART) != BASE_ART_SHA:
        raise SystemExit("ART baseline SHA mismatch")

    data_entries = parse_big(SRC_DATA)
    art_entries = parse_big(SRC_ART)
    locked = {norm(p) for p in LOCKED_BIG_PATHS}
    by_name = {norm(n): i for i, (n, _b) in enumerate(data_entries)}

    donor = DonorLib([p for p in DONOR_BIGS if p.is_file()])
    # Extra donor BIGs that hold remaining textures.
    extra = Path("/tmp/new_donor_extract/New folder")
    extra_bigs = [
        extra / "00PMBeta993.big",
        extra / "00PMBeta999.big",
        extra / "TexturesZH.big",
        extra / "W3DZH.big",
    ]
    donor2 = DonorLib([p for p in extra_bigs if p.is_file()])

    w3d_by_stem, _tex_by = art_index(art_entries)
    packed_stems = packed_tex_stems(art_entries)
    art_seen = {norm(n) for n, _b in art_entries}

    # --- inject missing textures (exact W3D names / stems) ---
    packed_blobs = {basename(n): b for n, b in art_entries}

    def take(src_names, dest_names):
        blob = None
        src = None
        for nm in src_names:
            hit = donor.get(nm) or donor2.get(nm)
            if hit:
                src, blob = hit
                break
            bn = basename(nm)
            if bn in packed_blobs:
                src, blob = nm, packed_blobs[bn]
                break
        if blob is None:
            print("WARN missing donor/packed source", src_names)
            return 0
        n = 0
        for dest in dest_names:
            if inject_named(art_entries, dest, blob, art_seen):
                packed_stems.add(Path(basename(dest)).stem)
                packed_blobs[basename(dest)] = blob
                n += 1
        return n

    injected = 0
    injected += take(["JapTY81M1.dds", "JapTY81M1.tga"], [r"Art\Textures\JapTY81M1.dds"])
    injected += take(["JapTY81M2.dds", "JapTY81M2.tga"], [r"Art\Textures\JapTY81M2.dds"])
    injected += take(["IN02.TGA", "IN02.tga", "IN02.dds", "JP99tb.tga"], [r"Art\Textures\IN02.TGA"])
    injected += take(["JP99tb.tga"], [r"Art\Textures\JPTANK.tga", r"Art\Textures\90_T.tga", r"Art\Textures\JPTank_Headlights.TGA"])
    injected += take(["Treads.dds", "Treads.tga"], [r"Art\Textures\Treads.dds"])
    injected += take(["ABNPatriot02.dds", "ABNPatriot02.tga"], [r"Art\Textures\ABNPatriot02.dds"])
    injected += take(["pac_3_gdghtr.tga", "pac_3_gdghtrsud.tga"], [r"Art\Textures\pac_3_gdghtrsud.tga"])
    injected += take(
        ["ubbarracks.dds", "USBarracksDesert.tga", "USBarracksDesert.dds"],
        [r"Art\Textures\USBarracksDesert.dds"],
    )
    injected += take(
        ["us_humvee-woodland.dds", "CWCusHumvee.dds", "cvhumvee_d1.dds"],
        [r"Art\Textures\CWCusHumvee.dds"],
    )
    injected += take(["avtreads.dds", "avtreads.tga"], [r"Art\Textures\avtreads.dds"])
    # Caesar wheel/cab texture: prefer a real Ural, else the packed Caesar hull.
    injected += take(
        ["CWCruUral.tga", "CWCruUral.dds", "CWCruUralRadar.dds", "LSFKAISA.dds"],
        [r"Art\Textures\CWCruUral.dds"],
    )
    print("texture injects", injected)

    # Rebuild W3D index after appends (W3Ds unchanged; stems unchanged).
    w3d_by_stem, _ = art_index(art_entries)
    packed_stems = packed_tex_stems(art_entries)

    # --- live WF CommandSets from CommandSet.ini ---
    cs_i = by_name[norm(r"Data\INI\CommandSet.ini")]
    cs_text = data_entries[cs_i][1].decode("latin1")
    live_slots = {}
    for country in COUNTRIES:
        m = last_named(cs_text, "CommandSet", country.cs)
        if not m:
            raise SystemExit(f"missing live CS {country.cs}")
        live_slots[country.key] = cs_slots(m.group(0))
        if len(live_slots[country.key]) != 14:
            raise SystemExit(f"{country.cs} slot count {len(live_slots[country.key])}")

    # --- overlay alias CommandSets: copy the live 14-slot bar ---
    overlay_fixed = []
    for ovpath, alias in OVERLAY_CS.items():
        i = by_name.get(norm(ovpath))
        if i is None:
            print("WARN overlay missing", ovpath)
            continue
        country_key = ALIAS_COMMANDSETS[alias]
        text = data_entries[i][1].decode("latin1")
        nl = "\r\n" if text.count("\r\n") >= text.count("\n") / 2 else "\n"
        new_blk = write_cs_block(alias, live_slots[country_key], nl)
        data_entries[i] = (data_entries[i][0], replace_named_block(text, "CommandSet", alias, new_blk).encode("latin1"))
        overlay_fixed.append(alias)
        print("overlay WF CS", alias, "slots", len(live_slots[country_key]))

    # --- object last-wins index ---
    obj_last: dict[str, int] = {}
    for i, (n, blob) in enumerate(data_entries):
        if not n.lower().endswith(".ini"):
            continue
        t = blob.decode("latin1")
        for m in re.finditer(r"(?m)^Object\s+(\S+)", t):
            obj_last[m.group(1)] = i

    wanted = {u.obj: (c, u) for c, u in all_units()}
    bone_fixed = []
    prereq_fixed = []
    kindof_fixed = []
    files_to_write: dict[int, str] = {}

    for obj, (country, unit) in wanted.items():
        i = obj_last.get(obj)
        if i is None:
            raise SystemExit(f"missing object {obj}")
        fname = data_entries[i][0]
        if norm(fname) in locked:
            raise SystemExit(f"refusing locked object file {fname} for {obj}")
        text = files_to_write.get(i)
        if text is None:
            text = data_entries[i][1].decode("latin1")
        m = last_named(text, "Object", obj)
        if not m:
            raise SystemExit(f"no block {obj} in {fname}")
        blk = m.group(0)
        orig = blk
        if obj in PREREQ_FIX:
            blk = strip_unit_gates(blk, PREREQ_FIX[obj])
            prereq_fixed.append(obj)
        blk = ensure_can_attack(blk)
        if blk != orig and "CAN_ATTACK" in blk and "CAN_ATTACK" not in orig:
            kindof_fixed.append(obj)
        model = default_model(blk)
        if not model or model.upper() == "NONE":
            raise SystemExit(f"no DEFAULT model {obj}")
        hit = w3d_by_stem.get(model.lower())
        if not hit:
            raise SystemExit(f"DEFAULT W3D missing {obj} {model}")
        bones = w3d_bones(hit[1])
        blk, nbone = remap_bones(blk, bones, unit.role)
        if nbone:
            bone_fixed.append((obj, nbone, model))
        if blk != orig:
            text = text[: m.start()] + blk + text[m.end() :]
            files_to_write[i] = text

    for i, text in files_to_write.items():
        data_entries[i] = (data_entries[i][0], text.encode("latin1"))
        print("patched", data_entries[i][0])

    # locked files must be byte-identical
    src_locked = {norm(n): b for n, b in parse_big(SRC_DATA) if norm(n) in locked}
    for n, b in data_entries:
        if norm(n) in locked and src_locked[norm(n)] != b:
            raise SystemExit(f"locked file changed {n}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_out = OUT_DIR / "_SPEC_DATA_ONE.big"
    art_out = OUT_DIR / "_SPEC_ART_ONE.big"
    data_out.write_bytes(build_big_ordered(data_entries))
    art_changed = injected > 0
    if art_changed:
        art_out.write_bytes(build_big_ordered(art_entries))
    else:
        art_out.write_bytes(SRC_ART.read_bytes())

    report = OUT_DIR / "runtime_build_log.txt"
    lines = [
        "NATIONAL GROUND RUNTIME BUILD",
        f"DATA_SHA {sha256(data_out)}",
        f"ART_SHA {sha256(art_out)}",
        f"ART_CHANGED {art_changed}",
        f"TEXTURE_INJECTS {injected}",
        f"OVERLAY_CS {overlay_fixed}",
        f"PREREQ_FIXED {prereq_fixed}",
        f"KINDOF_FIXED {kindof_fixed}",
        f"BONE_FIXED {len(bone_fixed)}",
    ]
    for obj, n, model in bone_fixed:
        lines.append(f"  {obj} bones={n} model={model}")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", data_out, "sha", sha256(data_out))
    print("wrote", art_out, "sha", sha256(art_out))
    print("prereq", prereq_fixed)
    print("kindof", kindof_fixed)
    print("bone units", len(bone_fixed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
