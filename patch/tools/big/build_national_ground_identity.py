#!/usr/bin/env python3
"""ART national-identity pass for the 17-nation ground roster.

Does not change weapons, armor, locomotor, cost, time, CommandSets,
CommandButtons, or CSF. Shared US/NATO/Iraqi/Russian meshes are cloned
per nation so markings never leak onto protected factions. Unique meshes
keep the same Model= and only remap hull textures.
"""

from __future__ import annotations

import hashlib
import io
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_national_ground_forces import build_big_ordered, last_named, norm, parse_big
from national_ground_identity import (
    IDENTITY,
    PROTECTED_ART_STEMS,
    PROTECTED_SIDES,
    muted_flag,
    skip_texture,
)
from national_ground_roster import LOCKED_BIG_PATHS, COUNTRIES, all_units

SRC_DATA = Path("/tmp/national_ground_names/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/national_ground_names/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/national_ground_identity")
PREVIEW = Path("/opt/cursor/artifacts/national_ground_identity_preview.png")


def basename(name: str) -> str:
    return name.replace("\\", "/").split("/")[-1].lower()


def texture_refs(blob: bytes):
    refs = []

    def walk(start, end):
        pos = start
        while pos + 8 <= end:
            ct, cs = struct.unpack_from("<II", blob, pos)
            ch = cs & 0x80000000
            csz = cs & 0x7FFFFFFF
            pl = pos + 8
            nxt = pl + csz
            if nxt > end:
                break
            if ct == 0x32:
                z = blob.find(b"\x00", pl)
                if z > pl:
                    refs.append((pl, blob[pl:z].decode("ascii", "replace")))
            if ch:
                walk(pl, nxt)
            pos = nxt

    walk(0, len(blob))
    return refs


def write_tga(img: Image.Image) -> bytes:
    has_a = img.mode in ("RGBA", "LA")
    img = img.convert("RGBA" if has_a else "RGB")
    w, h = img.size
    px = img.load()
    buf = bytearray()
    buf += bytes([0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    buf += struct.pack("<HH", w, h)
    buf += bytes([32 if has_a else 24, 0])
    for y in range(h):
        for x in range(w):
            p = px[x, h - 1 - y]
            if has_a:
                r, g, b, a = p
                buf += bytes([b, g, r, a])
            else:
                r, g, b = p
                buf += bytes([b, g, r])
    return bytes(buf)


def same_len_name(old: str, code: str, used: set[str]) -> str:
    stem, dot, ext = old.rpartition(".")
    if not dot:
        stem, ext = old, ""
        ext_full = ""
    else:
        ext_full = "." + ext
    n = len(stem)
    if n < 2:
        new_stem = (code + stem)[:n].ljust(n, "x")
    else:
        new_stem = (code + stem[2:])[:n].ljust(n, "x")
    # prefer .tga of the same total length
    if ext_full:
        new_ext = ".tga" if len(ext_full) == 4 else ext_full
        if len(new_ext) != len(ext_full):
            new_ext = ext_full
        cand = new_stem + new_ext
    else:
        cand = new_stem
    if len(cand) != len(old):
        cand = (code + old)[: len(old)].ljust(len(old), "x")
    base = cand
    i = 0
    while cand.lower() in used:
        raw = list(base)
        raw[-1] = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[i % 36]
        cand = "".join(raw)
        i += 1
        if i > 36:
            raise SystemExit(f"name collision {old}")
    if len(cand) != len(old):
        raise SystemExit(f"len mismatch {old!r} -> {cand!r}")
    used.add(cand.lower())
    return cand


def apply_tone(img: Image.Image, tone) -> Image.Image:
    src = img.convert("RGBA")
    r_m, g_m, b_m = tone
    r, g, b, a = src.split()
    r = r.point(lambda i, m=r_m: max(0, min(255, int(i * m))))
    g = g.point(lambda i, m=g_m: max(0, min(255, int(i * m))))
    b = b.point(lambda i, m=b_m: max(0, min(255, int(i * m))))
    return Image.merge("RGBA", (r, g, b, a))


def find_decal_box(img: Image.Image, fw: int, fh: int):
    im = img.convert("L")
    w, h = im.size
    if w < fw + 8 or h < fh + 8:
        return (max(0, w - fw - 4), max(0, h - fh - 4))
    pix = im.load()
    best = None
    step = max(4, min(w, h) // 32)
    for y in range(4, h - fh - 4, step):
        for x in range(4, w - fw - 4, step):
            s = 0
            s2 = 0
            n = 0
            for yy in range(0, fh, 2):
                for xx in range(0, fw, 2):
                    v = pix[x + xx, y + yy]
                    s += v
                    s2 += v * v
                    n += 1
            mean = s / n
            var = s2 / n - mean * mean
            if 50 <= mean <= 190:
                score = (1.0 / (1.0 + var / 80.0)) * (1.0 - abs(mean - 120) / 120.0)
                if best is None or score > best[0]:
                    best = (score, x, y)
    if best is None:
        return (w - fw - 8, h - fh - 8)
    return (best[1], best[2])


def stamp_marking(img: Image.Image, style: str, tone) -> Image.Image:
    out = apply_tone(img, tone)
    w, h = out.size
    fw = max(24, min(w, h) // 9)
    fh = max(12, fw // 2)
    flag = muted_flag(style, (fw, fh)).convert("RGBA")
    # slight dirt so it reads as paint, not a sticker
    region_xy = find_decal_box(out, fw, fh)
    crop = out.crop((region_xy[0], region_xy[1], region_xy[0] + fw, region_xy[1] + fh))
    dirt = ImageEnhance.Contrast(crop.convert("L")).enhance(0.55).convert("RGBA")
    mixed = Image.blend(flag, dirt, 0.28)
    # thin dark edge
    edge = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    ImageDraw.Draw(edge).rectangle((0, 0, fw - 1, fh - 1), outline=(20, 20, 16, 160))
    mixed.alpha_composite(edge)
    out.alpha_composite(mixed, region_xy)
    if img.mode != "RGBA":
        return out.convert(img.mode if img.mode in ("RGB", "RGBA") else "RGB")
    return out


def load_tex(blob: bytes) -> Image.Image:
    return Image.open(io.BytesIO(blob))


def find_tex_blob(art_bases: dict, name: str):
    stem = Path(name.replace("\\", "/")).stem.lower()
    for ext in (".tga", ".dds"):
        hit = art_bases.get(stem + ext)
        if hit:
            return hit
    cands = [
        (k, v)
        for k, v in art_bases.items()
        if k.startswith(stem) and k.endswith((".tga", ".dds"))
    ]
    if not cands:
        return None
    cands.sort(key=lambda kv: len(kv[0]))
    return cands[0][1]


def retarget_models(blk: str, mapping: dict[str, str]) -> str:
    def repl_model(m):
        old = m.group(2)
        return m.group(1) + mapping.get(old, old)

    def repl_anim(m):
        val = m.group(2)
        for old, new in mapping.items():
            if val.startswith(old + "."):
                return m.group(1) + new + val[len(old) :]
            if val == old:
                return m.group(1) + new
        return m.group(0)

    blk = re.sub(r"(?m)^(\s*Model\s+=\s+)(\S+)", repl_model, blk)
    blk = re.sub(r"(?m)^(\s*Animation\s+=\s+)(\S+)", repl_anim, blk)
    return blk


def main() -> int:
    if not SRC_DATA.is_file() or not SRC_ART.is_file():
        print("missing names-pack BIG", file=sys.stderr)
        return 1

    data_entries = parse_big(SRC_DATA)
    art_entries = parse_big(SRC_ART)
    src_data_names = [n for n, _ in data_entries]
    src_art_names = [n for n, _ in art_entries]
    art_index = {norm(n): i for i, (n, _) in enumerate(art_entries)}
    art_bases = {basename(n): (n, b) for n, b in art_entries}
    used_tex_names = set(art_bases)

    # last-wins object index
    obj_loc = {}
    texts = {}
    obj_meta = {}
    for i, (n, blob) in enumerate(data_entries):
        if not n.lower().endswith(".ini"):
            continue
        text = blob.decode("latin1")
        texts[i] = text
        for m in re.finditer(r"(?m)^Object\s+(\S+)\s*$", text):
            obj_loc[m.group(1)] = (i, n)
    for obj, (i, _fn) in obj_loc.items():
        m = last_named(texts[i], "Object", obj)
        if not m:
            continue
        blk = m.group(0)
        side = re.search(r"(?m)^\s*Side\s+=\s+(\S+)", blk)
        models = re.findall(r"(?m)^\s*Model\s+=\s+(\S+)", blk)
        obj_meta[obj] = (side.group(1) if side else "?", models, i)

    by_model = defaultdict(list)
    for obj, (side, models, _i) in obj_meta.items():
        for md in models:
            if md.lower() not in {"none", "none"}:
                by_model[md.lower()].append((obj, side))

    nation_sides = {c.side for c in COUNTRIES}
    protected_tex = set()
    for obj, (side, models, _i) in obj_meta.items():
        if side not in PROTECTED_SIDES:
            continue
        for md in models:
            wkey = md.lower() + ".w3d"
            if wkey not in art_bases:
                continue
            for _off, tname in texture_refs(art_bases[wkey][1]):
                protected_tex.add(Path(tname).stem.lower())

    # work list: (country, primary_model) -> objects
    jobs = defaultdict(list)
    for country, unit in all_units():
        if unit.obj not in obj_meta:
            raise SystemExit(f"missing object {unit.obj}")
        side, models, _i = obj_meta[unit.obj]
        if side in PROTECTED_SIDES:
            raise SystemExit(f"refusing protected object {unit.obj}")
        primary = models[0] if models else None
        if not primary:
            raise SystemExit(f"no Model on {unit.obj}")
        jobs[(country.key, primary)].append(unit.obj)

    marked_files = []
    cloned_w3ds = []
    painted_w3ds = []
    model_map_by_obj = {}
    w3d_cache = {}  # (code, old_stem) -> new_stem

    def mark_w3d(old_stem: str, country_key: str, replace_existing: bool) -> str:
        key = (country_key, old_stem)
        if key in w3d_cache:
            return w3d_cache[key]
        code, style, tone = IDENTITY[country_key]
        wkey = old_stem.lower() + ".w3d"
        if wkey not in art_bases:
            raise SystemExit(f"missing W3D {old_stem}")
        old_path, src = art_bases[wkey]
        refs = texture_refs(src)
        names = []
        seen = set()
        for _off, tname in refs:
            if tname.lower() not in seen:
                seen.add(tname.lower())
                names.append(tname)
        paintable = []
        for tname in names:
            if skip_texture(tname):
                continue
            hit = find_tex_blob(art_bases, tname)
            if not hit:
                continue
            try:
                im = load_tex(hit[1])
            except Exception:
                continue
            if im.size[0] * im.size[1] < 64 * 64:
                continue
            paintable.append((tname, hit, im.size[0] * im.size[1]))
        paintable.sort(key=lambda x: -x[2])
        chosen = paintable[:2]
        if not chosen and names:
            # last resort: largest available tex
            fallback = []
            for tname in names:
                hit = find_tex_blob(art_bases, tname)
                if not hit:
                    continue
                try:
                    im = load_tex(hit[1])
                except Exception:
                    continue
                fallback.append((tname, hit, im.size[0] * im.size[1]))
            fallback.sort(key=lambda x: -x[2])
            chosen = fallback[:1]
        if not chosen:
            # Missing packed texture (W3D name exists, file does not).
            # Build a muted camo hull so the mesh can carry a national mark.
            tname = names[0] if names else f"{code}HULL.tga"
            camo = Image.new("RGB", (512, 512), (110, 108, 88))
            d = ImageDraw.Draw(camo)
            for i in range(0, 512, 32):
                col = (int(96 + (i * 0.08)), int(98 + (i * 0.04)), int(72 + (i * 0.03)))
                d.rectangle((0, i, 512, i + 16), fill=col)
            marked = stamp_marking(camo, style, tone)
            new_name = same_len_name(tname, code, used_tex_names)
            blob = write_tga(marked.convert("RGB"))
            out_tex = rf"Art\Textures\{Path(new_name.replace(chr(92), '/')).name}"
            art_entries.append((out_tex, blob))
            art_index[norm(out_tex)] = len(art_entries) - 1
            art_bases[basename(out_tex)] = (out_tex, blob)
            rename = {tname: new_name}
            marked_files.append((country_key, old_stem, tname, new_name))
            print("  synth tex", country_key, old_stem, tname, "->", new_name)
            out = bytearray(src)
            for off, ref_name in refs:
                if ref_name in rename:
                    new = rename[ref_name].encode("ascii")
                    old = ref_name.encode("ascii")
                    out[off : off + len(new)] = new
            new_blob = bytes(out)
            if replace_existing:
                i = art_index[norm(old_path)]
                art_entries[i] = (art_entries[i][0], new_blob)
                art_bases[wkey] = (old_path, new_blob)
                painted_w3ds.append((country_key, old_stem))
                w3d_cache[key] = old_stem
                print("paint-synth", country_key, old_stem)
                return old_stem
            new_stem = f"{code}_{old_stem}"
            out_w3d = rf"Art\W3D\{new_stem}.w3d"
            art_entries.append((out_w3d, new_blob))
            art_index[norm(out_w3d)] = len(art_entries) - 1
            art_bases[basename(out_w3d)] = (out_w3d, new_blob)
            cloned_w3ds.append((country_key, old_stem, new_stem))
            w3d_cache[key] = new_stem
            print("clone-synth", country_key, old_stem, "->", new_stem)
            return new_stem

        rename = {}
        for tname, hit, _area in chosen:
            new_name = same_len_name(tname, code, used_tex_names)
            try:
                im = load_tex(hit[1])
            except Exception as exc:
                print("WARN decode", tname, exc)
                continue
            marked = stamp_marking(im, style, tone)
            blob = write_tga(marked.convert("RGBA" if marked.mode == "RGBA" else "RGB"))
            out_tex = rf"Art\Textures\{Path(new_name.replace(chr(92), '/')).name}"
            if norm(out_tex) in art_index:
                raise SystemExit(f"refusing overwrite packed tex {out_tex}")
            art_entries.append((out_tex, blob))
            art_index[norm(out_tex)] = len(art_entries) - 1
            art_bases[basename(out_tex)] = (out_tex, blob)
            rename[tname] = new_name
            marked_files.append((country_key, old_stem, tname, new_name))
            print("  tex", country_key, tname, "->", new_name, marked.size)

        out = bytearray(src)
        for off, tname in refs:
            if tname in rename:
                new = rename[tname].encode("ascii")
                old = tname.encode("ascii")
                if len(old) != len(new):
                    raise SystemExit(f"tex len {old!r} {new!r}")
                if out[off : off + len(old)] != old:
                    raise SystemExit(f"tex mismatch {old!r}")
                out[off : off + len(new)] = new
        new_blob = bytes(out)

        if replace_existing:
            # unique-to-nation mesh: rewrite this W3D in place
            if old_stem.lower() in PROTECTED_ART_STEMS:
                raise SystemExit(f"refusing overwrite protected W3D {old_stem}")
            i = art_index[norm(old_path)]
            art_entries[i] = (art_entries[i][0], new_blob)
            art_bases[wkey] = (old_path, new_blob)
            painted_w3ds.append((country_key, old_stem))
            w3d_cache[key] = old_stem
            print("paint", country_key, old_stem)
            return old_stem

        new_stem = f"{code}_{old_stem}"
        out_w3d = rf"Art\W3D\{new_stem}.w3d"
        if norm(out_w3d) in art_index:
            raise SystemExit(f"W3D exists {out_w3d}")
        if new_stem.lower() in PROTECTED_ART_STEMS:
            raise SystemExit(f"refusing protected clone name {new_stem}")
        art_entries.append((out_w3d, new_blob))
        art_index[norm(out_w3d)] = len(art_entries) - 1
        art_bases[basename(out_w3d)] = (out_w3d, new_blob)
        cloned_w3ds.append((country_key, old_stem, new_stem))
        w3d_cache[key] = new_stem
        print("clone", country_key, old_stem, "->", new_stem)
        return new_stem

    for (country_key, primary), objs in sorted(jobs.items()):
        users = by_model.get(primary.lower(), [])
        prot = [s for _o, s in users if s in PROTECTED_SIDES]
        other_nations = {s for _o, s in users if s in nation_sides}
        my_side = next(c.side for c in COUNTRIES if c.key == country_key)
        exclusive = (not prot) and other_nations <= {my_side}
        mapping = {}
        # clone/paint every Model= referenced by these objects that equals primary or primaryD
        stems = set()
        for obj in objs:
            _side, models, _i = obj_meta[obj]
            for md in models:
                stems.add(md)
        for md in stems:
            related = md == primary or md.lower() == primary.lower() + "d" or md.lower().startswith(primary.lower())
            if not related:
                # still mark extra models used only by this object set if exclusive to us
                extra_users = {s for _o, s in by_model.get(md.lower(), [])}
                extra_prot = extra_users & PROTECTED_SIDES
                extra_nat = extra_users & nation_sides
                if extra_prot or extra_nat - {my_side}:
                    continue
            new = mark_w3d(md, country_key, replace_existing=exclusive and md == primary)
            if new != md:
                mapping[md] = new
        for obj in objs:
            model_map_by_obj[obj] = mapping

    # patch DATA Model=/Animation= only
    locked = {norm(p) for p in LOCKED_BIG_PATHS}
    patched_objs = 0
    for obj, mapping in model_map_by_obj.items():
        if not mapping:
            continue
        i, fname = obj_loc[obj]
        if norm(fname) in locked:
            raise SystemExit(f"locked object file {fname}")
        text = texts[i]
        m = last_named(text, "Object", obj)
        if not m:
            raise SystemExit(f"no block {obj}")
        blk = m.group(0)
        side = re.search(r"(?m)^\s*Side\s+=\s+(\S+)", blk)
        if side and side.group(1) in PROTECTED_SIDES:
            raise SystemExit(f"refusing patch protected {obj}")
        new_blk = retarget_models(blk, mapping)
        if new_blk == blk:
            continue
        # refuse anything except Model/Animation
        strip = lambda s: re.sub(r"(?m)^\s*(Model|Animation)\s+=\s+\S+", "", s)
        if strip(blk) != strip(new_blk):
            raise SystemExit(f"non-model change on {obj}")
        for field in ("BuildCost", "BuildTime"):
            if re.findall(rf"(?m)^\s*{field}\s+=\s+(\S+)", blk) != re.findall(rf"(?m)^\s*{field}\s+=\s+(\S+)", new_blk):
                raise SystemExit(f"{field} changed {obj}")
        if re.findall(r"(?m)^\s*Weapon\s+=\s+.+$", blk) != re.findall(r"(?m)^\s*Weapon\s+=\s+.+$", new_blk):
            raise SystemExit(f"weapon changed {obj}")
        texts[i] = text[: m.start()] + new_blk + text[m.end() :]
        data_entries[i] = (data_entries[i][0], texts[i].encode("latin1"))
        patched_objs += 1
        print("model", obj, mapping)

    # locked + CSF + command files must stay identical unless we only touched object INIs
    src_map = {norm(n): b for n, b in parse_big(SRC_DATA)}
    for n, b in data_entries:
        key = norm(n)
        if key in locked and src_map.get(key) != b:
            raise SystemExit(f"locked changed {n}")
        if n.lower().endswith("generals.csf") and src_map.get(key) != b:
            raise SystemExit("CSF changed")
        if "commandset" in n.lower() and n.lower().endswith(".ini") and src_map.get(key) != b:
            raise SystemExit(f"CommandSet file changed {n}")
        if n.lower().endswith("commandbutton.ini") and src_map.get(key) != b:
            raise SystemExit("CommandButton.ini changed")

    if [n for n, _ in data_entries] != src_data_names:
        raise SystemExit("DATA entry names/order changed")
    if [n for n, _ in art_entries][: len(src_art_names)] != src_art_names:
        raise SystemExit("ART entry-order prefix changed")

    # preview
    labels = [
        ("japan", "Japan"),
        ("korea", "South Korea"),
        ("germany", "Germany"),
        ("france", "France"),
        ("britain", "Britain"),
        ("italy", "Italy"),
        ("turkey", "Turkey"),
        ("ukraine", "Ukraine"),
        ("sweden", "Sweden"),
        ("india", "India"),
        ("pakistan", "Pakistan"),
        ("saudi", "Saudi"),
        ("uae", "UAE"),
        ("vietnam", "Vietnam"),
        ("syria", "Syria"),
        ("libya", "Libya"),
        ("southafrica", "S. Africa"),
    ]
    cell_w, cell_h = 150, 86
    cols = 6
    rows = 3
    sheet = Image.new("RGB", (cols * cell_w, 28 + rows * cell_h), (32, 34, 30))
    d = ImageDraw.Draw(sheet)
    d.text((8, 6), "National ground markings (muted flags, original camo kept)", fill=(210, 210, 200))
    for i, (style, label) in enumerate(labels):
        r, c = divmod(i, cols)
        x, y = c * cell_w + 8, 28 + r * cell_h + 4
        sheet.paste(muted_flag(style, (128, 64)).resize((128, 64)), (x, y + 14))
        d.text((x, y), label, fill=(200, 200, 190))
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(PREVIEW)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(data_entries)
    art_big = build_big_ordered(art_entries)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(art_big)
    print("PAINTED_W3D", len(painted_w3ds), "CLONED_W3D", len(cloned_w3ds), "MARKED_TEX", len(marked_files), "MODEL_PATCH", patched_objs)
    print("DATA_SHA256", hashlib.sha256(data_big).hexdigest())
    print("ART_SHA256", hashlib.sha256(art_big).hexdigest())
    print("DATA_BYTES", len(data_big), "FILES", len(data_entries))
    print("ART_BYTES", len(art_big), "FILES", len(art_entries))
    print("preview", PREVIEW)
    return 0


if __name__ == "__main__":
    sys.exit(main())
