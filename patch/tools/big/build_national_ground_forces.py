#!/usr/bin/env python3
"""National Ground Forces expansion - DATA first, ART only if a donor mesh is used.

Does not modify protected factions, PlayerTemplate, Science, CommandCenter,
VT72B, or airfields. Does not copy donor DATA logic.
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from national_ground_roster import (
    COUNTRIES,
    DO_NOT_PACK_OVERLAY,
    LOCKED_BIG_PATHS,
    PROTECTED_COMMANDSETS,
    TEMPLATES,
    all_units,
)

SRC_DATA = Path("/tmp/wf_national_markings/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/wf_national_markings/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/national_ground_forces")
DONOR_DIR = Path("/tmp/new_donor_extract/New folder")
DONOR_BIGS = (
    DONOR_DIR / "00PMBeta999.big",
    DONOR_DIR / "00PMBeta993.big",
    DONOR_DIR / "00PMBeta995.big",
    DONOR_DIR / "W3DZH.big",
    DONOR_DIR / "TexturesZH.big",
)


def parse_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    nfiles = struct.unpack(">I", data[8:12])[0]
    off = 16
    entries = []
    for _ in range(nfiles):
        eoff, esz = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries.append((name, data[eoff : eoff + esz]))
    return entries


def index_big_on_disk(path: Path):
    data = path.read_bytes()
    nfiles = struct.unpack(">I", data[8:12])[0]
    off = 16
    idx = {}
    for _ in range(nfiles):
        eoff, esz = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        idx[name.replace("/", "\\").lower()] = (eoff, esz, name)
    return data, idx


def build_big_ordered(entries):
    header_size = 16
    encoded = [(n.encode("latin1"), b) for n, b in entries]
    for nb, _blob in encoded:
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for nb, blob in encoded:
        index.append((nb, offset, len(blob)))
        blobs.append(blob)
        offset += len(blob)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(encoded))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def norm(name: str) -> str:
    return name.replace("/", "\\").lower()


def basename(name: str) -> str:
    return name.replace("\\", "/").split("/")[-1].lower()


def last_named(text: str, kind: str, name: str):
    hits = list(re.finditer(rf"(?ms)^{kind}\s+{re.escape(name)}\s*\r?\n.*?(?=^{kind}\s|\Z)", text))
    return hits[-1] if hits else None


def last_object(text: str, obj: str):
    return last_named(text, "Object", obj)


def xor_csf_utf16(s: str) -> bytes:
    return bytes(b ^ 0xFF for b in s.encode("utf-16-le"))


def append_csf_labels(blob: bytes, labels: dict[str, str]) -> bytes:
    if blob[:4] != b" FSC":
        raise SystemExit("generals.csf is not CSF")
    _version, nlabels, nstrings = struct.unpack_from("<III", blob, 4)
    extra = bytearray()
    add_labels = 0
    add_strings = 0
    existing = blob.upper()
    for name, value in labels.items():
        key = name.encode("latin1")
        if key.upper() in existing:
            continue
        extra += b" LBL"
        extra += struct.pack("<II", 1, len(key))
        extra += key
        extra += b" RTS"
        extra += struct.pack("<I", len(value))
        extra += xor_csf_utf16(value)
        add_labels += 1
        add_strings += 1
    if add_labels == 0:
        return blob
    out = bytearray(blob)
    struct.pack_into("<I", out, 8, nlabels + add_labels)
    struct.pack_into("<I", out, 12, nstrings + add_strings)
    out += extra
    return bytes(out)


def w3d_textures(blob: bytes) -> list[str]:
    names = []
    pos = 0
    end = len(blob)
    while pos + 8 <= end:
        ctype, csize = struct.unpack_from("<II", blob, pos)
        has = csize & 0x80000000
        size = csize & 0x7FFFFFFF
        pl = pos + 8
        nxt = pl + size
        if nxt > end:
            break
        if ctype == 0x32:
            z = blob.find(b"\x00", pl)
            if z > pl:
                names.append(blob[pl:z].decode("ascii", "replace"))
        if has:
            names.extend(w3d_textures(blob[pl:nxt]) if False else [])
            # recurse into children
            cpos = pl
            while cpos + 8 <= nxt:
                ct, cs = struct.unpack_from("<II", blob, cpos)
                ch = cs & 0x80000000
                csz = cs & 0x7FFFFFFF
                cpl = cpos + 8
                cnxt = cpl + csz
                if cnxt > nxt:
                    break
                if ct == 0x32:
                    z = blob.find(b"\x00", cpl)
                    if z > cpl:
                        names.append(blob[cpl:z].decode("ascii", "replace"))
                if ch:
                    names.extend(_tex_walk(blob, cpl, cnxt))
                cpos = cnxt
        pos = nxt
    return names


def _tex_walk(blob, start, end):
    names = []
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
                names.append(blob[pl:z].decode("ascii", "replace"))
        if ch:
            names.extend(_tex_walk(blob, pl, nxt))
        pos = nxt
    return names


def find_art_stem(art_index, stem: str):
    key = norm(rf"Art\W3D\{stem}.W3D")
    if key in art_index:
        return stem
    want = stem.lower() + ".w3d"
    for n in art_index:
        if basename(n) == want:
            raw = art_index[n][0]
            return Path(raw.replace("\\", "/")).stem
    return None


class DonorLib:
    def __init__(self, paths):
        self.readers = []
        self.by_base = {}
        for path in paths:
            if not path.is_file():
                print("missing donor", path)
                continue
            data, idx = index_big_on_disk(path)
            self.readers.append((path, data, idx))
            for key, (_off, _sz, name) in idx.items():
                self.by_base.setdefault(basename(name), (path, data, idx, key))
            print("indexed donor", path.name, "files", len(idx))

    def get(self, stem_or_file: str):
        base = basename(stem_or_file)
        if not base.endswith(".w3d") and not base.endswith(".tga") and not base.endswith(".dds"):
            for ext in (".w3d", ".tga", ".dds"):
                hit = self.by_base.get(base + ext)
                if hit:
                    path, data, idx, key = hit
                    off, sz, name = idx[key]
                    return name, data[off : off + sz]
            return None
        hit = self.by_base.get(base)
        if not hit:
            return None
        path, data, idx, key = hit
        off, sz, name = idx[key]
        return name, data[off : off + sz]


def clone_object(blk: str, new_obj: str, side: str, display_key: str, model: str, cost: int, time: int, prereq: str, image: str) -> str:
    m = re.match(r"(?m)^Object\s+(\S+)", blk)
    if not m:
        raise SystemExit("template missing Object name")
    old = m.group(1)
    blk = re.sub(rf"(?m)^Object\s+{re.escape(old)}\s*$", f"Object {new_obj}", blk, count=1)
    blk = re.sub(r"(?m)^(\s*DisplayName\s+=\s+)\S+", rf"\1{display_key}", blk, count=1)
    blk = re.sub(r"(?m)^(\s*Side\s+=\s+)\S+", rf"\1{side}", blk, count=1)
    blk = re.sub(r"(?m)^(\s*BuildCost\s+=\s+)\S+", r"\g<1>" + str(cost), blk, count=1)
    blk = re.sub(r"(?m)^(\s*BuildTime\s+=\s+)\S+", r"\g<1>" + ("%.1f" % time), blk, count=1)
    blk = re.sub(r"(?m)^(\s*SelectPortrait\s+=\s+)\S+", rf"\1{image}", blk, count=1)
    blk = re.sub(r"(?m)^(\s*ButtonImage\s+=\s+)\S+", rf"\1{image}", blk, count=1)
    old_models = set(re.findall(r"(?m)^\s*Model\s+=\s+(\S+)", blk))
    for om in old_models:
        blk = re.sub(rf"(?m)^(\s*Model\s+=\s+){re.escape(om)}\s*$", rf"\1{model}", blk)
        blk = re.sub(rf"(?m)^(\s*Animation\s+=\s+){re.escape(om)}\.\S+", rf"\1{model}.{model}", blk)
    nl = "\r\n" if "\r\n" in blk else "\n"
    new_pre = f"  Prerequisites{nl}    Object = {prereq}{nl}  End"
    prereq_blk = re.search(r"(?ms)^(\s*)Prerequisites\s*\r?\n.*?\n\1End\s*$", blk)
    if prereq_blk:
        blk = blk[: prereq_blk.start()] + new_pre + blk[prereq_blk.end() :]
    else:
        # Insert after Side so every cloned unit is gated to its national War Factory.
        side_m = re.search(r"(?m)^(\s*Side\s+=\s+\S+\s*)$", blk)
        if side_m:
            blk = blk[: side_m.end()] + nl + new_pre + blk[side_m.end() :]
        else:
            blk = blk.rstrip() + nl + new_pre + nl
    return blk


def commandset_block(name: str, buttons: list[str]) -> str:
    lines = [f"CommandSet {name}\r\n"]
    for i, btn in enumerate(buttons, 1):
        lines.append(f"  {i:2d} = {btn}\r\n")
    lines.append("End\r\n")
    return "".join(lines)


def construct_button(btn: str, obj: str, text: str, tip: str, image: str) -> str:
    return (
        f"CommandButton {btn}\r\n"
        f"  Command       = UNIT_BUILD\r\n"
        f"  Object        = {obj}\r\n"
        f"  TextLabel     = {text}\r\n"
        f"  ButtonImage   = {image}\r\n"
        f"  ButtonBorderType        = BUILD\r\n"
        f"  DescriptLabel           = {tip}\r\n"
        f"End\r\n"
    )


def find_template(data_entries, obj: str) -> str:
    for _n, blob in data_entries:
        if not _n.lower().endswith(".ini"):
            continue
        t = blob.decode("latin1")
        m = last_object(t, obj)
        if m:
            return m.group(0)
    raise SystemExit(f"missing template object {obj}")


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

    templates = {}
    for role, (tobj, _c, _t, _img) in TEMPLATES.items():
        templates[role] = find_template(data_entries, tobj)
        print("template", role, tobj, "lines", templates[role].count("\n"))

    existing_objects = set()
    existing_buttons = set()
    for n, blob in data_entries:
        if not n.lower().endswith(".ini"):
            continue
        t = blob.decode("latin1")
        if "nationalground" not in n.lower():
            existing_objects.update(re.findall(r"(?m)^Object\s+(\S+)\s*$", t))
        existing_buttons.update(re.findall(r"(?m)^CommandButton\s+(\S+)", t))

    resolved = {}
    inject_art = []
    seen_inject = set()

    def packed_stem(stem: str):
        key = stem.lower() + ".w3d"
        if key in packed_bases:
            return Path(packed_bases[key].replace("\\", "/")).stem
        return None

    def ensure_model(stem: str, fallback: str) -> str:
        hit_packed = packed_stem(stem)
        if hit_packed:
            return hit_packed
        for n, _b in inject_art:
            if basename(n) == stem.lower() + ".w3d":
                return Path(n.replace("\\", "/")).stem
        hit = donor.get(stem + ".w3d") or donor.get(stem)
        if hit:
            name, blob = hit
            out_name = rf"Art\W3D\{Path(name.replace(chr(92), '/')).name}"
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
                    inject_art.append((tout, tblob))
                    seen_inject.add(norm(tout))
                    print("  inject tex", tout)
            return Path(out_name.replace("\\", "/")).stem
        fb = packed_stem(fallback)
        if fb:
            print("fallback", stem, "->", fb)
            return fb
        raise SystemExit(f"no model for {stem} / {fallback}")

    for country, unit in all_units():
        if unit.obj in existing_objects:
            resolved[(country.key, unit.obj)] = "(existing)"
            continue
        model = ensure_model(unit.model_pref, unit.model_fallback)
        resolved[(country.key, unit.obj)] = model

    # build object INI and buttons / CSF
    object_ini = ["; National Ground Forces - generated, DATA clone of proven Specter templates\r\n"]
    buttons = []
    csf = {}

    country_buttons = {c.key: [] for c in COUNTRIES}
    for country, unit in all_units():
        role_tmpl, cost, time, default_img = TEMPLATES[unit.role]
        image = unit.image or default_img
        obj_key = f"OBJECT:{unit.obj}"
        text = f"CONTROLBAR:Construct{unit.obj}"
        tip = f"CONTROLBAR:ToolTip{unit.obj}"
        btn = f"Command_Construct{unit.obj}"
        if unit.obj in existing_objects:
            print("reuse existing object", country.key, unit.role, unit.obj)
        else:
            model = resolved[(country.key, unit.obj)]
            blk = clone_object(templates[unit.role], unit.obj, country.side, obj_key, model, cost, time, country.wf, image)
            object_ini.append(blk.rstrip() + "\r\n\r\n")
            print("unit", country.key, unit.role, unit.obj, "model", model)
        if btn not in existing_buttons:
            buttons.append(construct_button(btn, unit.obj, text, tip, image))
            existing_buttons.add(btn)
        country_buttons[country.key].append(btn)
        csf[obj_key] = unit.display
        csf[text] = unit.display
        csf[tip] = unit.tooltip

    new_obj_path = r"Data\INI\Object\Specter\NationalGround\NationalGroundForces.ini"
    if norm(new_obj_path) in data_index:
        i = data_index[norm(new_obj_path)]
        data_entries[i] = (data_entries[i][0], "".join(object_ini).encode("latin1"))
    else:
        data_entries.append((new_obj_path, "".join(object_ini).encode("latin1")))
        data_index[norm(new_obj_path)] = len(data_entries) - 1
        print("added", new_obj_path)

    def mut(path, fn):
        key = norm(path)
        if key in {norm(p) for p in LOCKED_BIG_PATHS}:
            raise SystemExit(f"locked {path}")
        i = data_index[key]
        name, blob = data_entries[i]
        old = blob.decode("latin1")
        new = fn(old)
        if new != old:
            data_entries[i] = (name, new.encode("latin1"))
            print("patched", path, "delta", len(new) - len(old))

    def patch_commandset(text: str) -> str:
        hits = []
        for country in COUNTRIES:
            names = (country.cs, country.cs + "1", country.cs + "2", country.cs + "3")
            for csname in names:
                if csname in PROTECTED_COMMANDSETS:
                    raise SystemExit(f"refusing protected CS {csname}")
                m = last_named(text, "CommandSet", csname)
                if m:
                    hits.append((m.start(), m.end(), country, csname))
        hits.sort(key=lambda x: x[0], reverse=True)
        for start, end, country, csname in hits:
            new_blk = commandset_block(csname, country_buttons[country.key])
            text = text[:start] + new_blk + text[end:]
            print("rewrote", csname, "slots", len(country_buttons[country.key]))
        return text

    def patch_buttons(text: str) -> str:
        if not buttons:
            return text
        if not text.endswith("\n"):
            text += "\r\n"
        return text + "\r\n" + "\r\n".join(buttons)

    locked = {norm(p) for p in LOCKED_BIG_PATHS}
    skip_overlay = {norm(p) for p in DO_NOT_PACK_OVERLAY}
    for n, _blob in list(data_entries):
        key = norm(n)
        if key in locked or key in skip_overlay:
            continue
        if n.lower().endswith(".ini") and "commandset" in n.lower():
            mut(n, patch_commandset)
    mut(r"Data\INI\CommandButton.ini", patch_buttons)

    csf_key = None
    for n, _b in data_entries:
        if n.lower().endswith("generals.csf"):
            csf_key = n
            break
    if not csf_key:
        raise SystemExit("generals.csf missing")
    i = data_index[norm(csf_key)]
    data_entries[i] = (data_entries[i][0], append_csf_labels(data_entries[i][1], csf))
    print("csf labels requested", len(csf))

    for n, blob in inject_art:
        if any(x in n.lower() for x in ("us_m1a2sep2", "rus_t90a", "chi_", "irn_", "irq_t72m1")) and norm(n) in art_index:
            raise SystemExit(f"refusing overwrite packed {n}")
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
    return _finish(data_entries, art_entries, resolved)


def _finish(data_entries, art_entries, resolved):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(data_entries)
    art_big = build_big_ordered(art_entries)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(art_big)
    print("DATA_SHA256", hashlib.sha256(data_big).hexdigest())
    print("ART_SHA256", hashlib.sha256(art_big).hexdigest())
    print("DATA_BYTES", len(data_big), "FILES", len(data_entries))
    print("ART_BYTES", len(art_big), "FILES", len(art_entries))
    print("UNITS", len(resolved))
    return 0


if __name__ == "__main__":
    sys.exit(main())
