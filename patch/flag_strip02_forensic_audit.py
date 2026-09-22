#!/usr/bin/env python3
"""Forensic init-crash audit: STRIP_02 vs last-known-launch CAMP_CLONE.

No rebuild. No DATA/ART edits. STRIP_02 still crashed in-game, so unused
clone W3D preload is ruled out.
"""
from __future__ import annotations

import re
import struct
from collections import Counter, defaultdict
from pathlib import Path

import japan_france_roster_01 as jf

STRIP_DATA = Path("/workspace/patch/Release/SPECTER1_FLAG_ART_CLONE_STRIP_02/_SPEC_DATA_ONE.big")
STRIP_ART = Path("/workspace/patch/Release/SPECTER1_FLAG_ART_CLONE_STRIP_02/_SPEC_ART_ONE.big")
GOOD_DATA = Path("/tmp/flag_audit/campclone/_SPEC_DATA_ONE.big")
GOOD_ART = Path("/tmp/flag_audit/campclone/_SPEC_ART_ONE.big")

STRIP_DATA_SHA = "3e42c369fb30e229062fcbf29feafb15c9e59472dc16757d8e5f0c0092813221"
STRIP_ART_SHA = "c16055702267e59770a7f657f843ea49840889b453a5c0611e8971045afe05b7"
GOOD_DATA_SHA = "e04a7b08a2fc6ae5648611d68b3b026e5cb004a103e92b2926d246a9ad1c6dfd"
GOOD_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"

OUT = Path("/workspace/patch/Release/SPECTER1_FLAG_STRIP02_FORENSIC_01")

PT_KEYS = ("FlagWaterMark", "EnabledImage", "SideIconImage", "GeneralImage")
NEW_MI_HINT = ("specter_remainingflags", "specter_campflags", "turkey_factionimages")


def stem_of(path: str) -> str:
    return Path(jf.norm(path).replace("\\", "/")).stem


def tga_info(blob: bytes) -> dict:
    if len(blob) < 18:
        return {"error": f"too small {len(blob)}"}
    idlen, cmap, img = blob[0], blob[1], blob[2]
    cmap_len = struct.unpack_from("<H", blob, 5)[0]
    w, h = struct.unpack_from("<HH", blob, 12)
    bpp, desc = blob[16], blob[17]
    expected = 18 + idlen + cmap_len * max(blob[7] // 8, 0) + w * h * (bpp // 8)
    return {
        "idlen": idlen,
        "cmap": cmap,
        "type": img,
        "w": w,
        "h": h,
        "bpp": bpp,
        "desc": desc,
        "origin": "top-down" if (desc & 0x20) else "bottom-up",
        "size": len(blob),
        "expected": expected,
        "size_ok": len(blob) == expected,
    }


def parse_mappedimages(text: str) -> list[dict]:
    out = []
    for m in re.finditer(r"(?im)^MappedImage\s+(\S+)\s*$", text):
        rest = text[m.end():]
        m2 = re.search(r"(?im)^(?:MappedImage|End)\s", rest)
        # take until End of this block
        endm = re.search(r"(?im)^End\s*$", rest)
        blk = rest[: endm.end()] if endm else rest[:200]
        tex = re.search(r"(?im)^\s*Texture\s*=\s*(\S+)", blk)
        tw = re.search(r"(?im)^\s*TextureWidth\s*=\s*(\d+)", blk)
        th = re.search(r"(?im)^\s*TextureHeight\s*=\s*(\d+)", blk)
        coords = re.search(
            r"(?im)^\s*Coords\s*=\s*Left:(\d+)\s+Top:(\d+)\s+Right:(\d+)\s+Bottom:(\d+)",
            blk,
        )
        out.append({
            "name": m.group(1),
            "texture": tex.group(1) if tex else "",
            "tw": int(tw.group(1)) if tw else None,
            "th": int(th.group(1)) if th else None,
            "box": tuple(int(x) for x in coords.groups()) if coords else None,
        })
    return out


def split_pt(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?im)^PlayerTemplate\s+(\S+)\s*$", text))
    out = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[m.group(1)] = text[m.start():end]
    return out


def pt_field(block: str, key: str) -> str | None:
    m = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(\S+)", block)
    return m.group(1) if m else None


def main() -> int:
    if jf.sha256_file(STRIP_DATA) != STRIP_DATA_SHA:
        raise SystemExit("STRIP DATA SHA mismatch")
    if jf.sha256_file(STRIP_ART) != STRIP_ART_SHA:
        raise SystemExit("STRIP ART SHA mismatch")
    if jf.sha256_file(GOOD_DATA) != GOOD_DATA_SHA:
        raise SystemExit("camp-clone DATA SHA mismatch")
    if jf.sha256_file(GOOD_ART) != GOOD_ART_SHA:
        raise SystemExit("camp-clone ART SHA mismatch")

    strip_d = jf.read_big_list(STRIP_DATA)
    strip_a = jf.read_big_list(STRIP_ART)
    good_d = jf.read_big_list(GOOD_DATA)
    good_a = jf.read_big_list(GOOD_ART)

    sd = {jf.norm(n).lower(): (n, bytes(b)) for n, b in strip_d}
    sa = {jf.norm(n).lower(): (n, bytes(b)) for n, b in strip_a}
    gd = {jf.norm(n).lower(): (n, bytes(b)) for n, b in good_d}
    ga = {jf.norm(n).lower(): (n, bytes(b)) for n, b in good_a}

    added_d = sorted(set(sd) - set(gd))
    removed_d = sorted(set(gd) - set(sd))
    changed_d = sorted(k for k in sd.keys() & gd.keys() if sd[k][1] != gd[k][1])
    added_a = sorted(set(sa) - set(ga))
    removed_a = sorted(set(ga) - set(sa))
    changed_a = sorted(k for k in sa.keys() & ga.keys() if sa[k][1] != ga[k][1])

    dup_d = sorted(n for n, c in Counter(jf.norm(n).lower() for n, _ in strip_d).items() if c > 1)
    dup_a = sorted(n for n, c in Counter(jf.norm(n).lower() for n, _ in strip_a).items() if c > 1)

    # ART remaining vs camp-clone: should be TGA only
    w3d_added = [k for k in added_a if k.endswith(".w3d")]
    w3d_changed = [k for k in changed_a if k.endswith(".w3d")]
    tex_added = [k for k in added_a if k.startswith("art\\textures\\")]
    tex_changed = [k for k in changed_a if k.startswith("art\\textures\\")]
    other_added = [k for k in added_a if k not in tex_added and k not in w3d_added]
    other_changed = [k for k in changed_a if k not in tex_changed and k not in w3d_changed]

    # TGA headers: new/changed vs a known-good flag if present
    ref_keys = [k for k in ga if "dprk_flag" in k or k.endswith("iraqiflag.tga")]
    refs = []
    for k in ref_keys[:3]:
        refs.append((ga[k][0], tga_info(ga[k][1])))

    tga_rows = []
    for k in tex_added + tex_changed:
        name, blob = sa[k]
        info = tga_info(blob)
        old = tga_info(ga[k][1]) if k in ga else None
        tga_rows.append((jf.norm(name), info, old))

    # MappedImages across all DATA
    all_mi: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    new_mi_blocks: list[tuple[str, dict]] = []
    for n, b in strip_d:
        if not str(n).lower().endswith(".ini"):
            continue
        t = b.decode("latin-1", errors="replace")
        if "mappedimage" not in t.lower() and "MappedImage" not in t:
            # still try parse
            pass
        mis = parse_mappedimages(t)
        for mi in mis:
            all_mi[mi["name"].lower()].append((jf.norm(n), mi))
            if any(h in jf.norm(n).lower() for h in NEW_MI_HINT):
                new_mi_blocks.append((jf.norm(n), mi))

    mi_dups = {k: v for k, v in all_mi.items() if len(v) > 1}
    # collisions where a NEW definition overwrites an old name
    new_names = {mi["name"].lower() for _, mi in new_mi_blocks}
    collisions = []
    for name in sorted(new_names):
        defs = all_mi[name]
        files = sorted({p for p, _ in defs})
        if len(files) > 1:
            collisions.append((name, files))

    art_tex_stems = {
        stem_of(n).lower()
        for n, _ in strip_a
        if jf.norm(n).lower().startswith("art\\textures\\")
    }
    missing_tex = []
    coord_oob = []
    long_tex = []
    for path, mi in new_mi_blocks:
        stem = mi["texture"].split(".")[0].lower()
        if stem and stem not in art_tex_stems:
            missing_tex.append(f"{path} MappedImage={mi['name']} Texture={mi['texture']}")
        if len(mi["texture"]) > 13:
            long_tex.append(f"{path} Texture={mi['texture']} len={len(mi['texture'])}")
        if mi["box"] and mi["tw"] and mi["th"]:
            l, t, r, btm = mi["box"]
            if r > mi["tw"] or btm > mi["th"] or l >= r or t >= btm:
                coord_oob.append(
                    f"{path} {mi['name']} Coords={mi['box']} tex={mi['tw']}x{mi['th']}"
                )
        # compare coords vs actual TGA
        tga = None
        for key, (an, blob) in sa.items():
            if key.startswith("art\\textures\\") and stem_of(key).lower() == stem:
                tga = tga_info(blob)
                break
        if tga and "error" not in tga and mi["box"]:
            l, top, r, btm = mi["box"]
            if r > tga["w"] or btm > tga["h"]:
                coord_oob.append(
                    f"{path} {mi['name']} Coords={mi['box']} TGA={tga['w']}x{tga['h']}"
                )
        if tga and mi["tw"] and mi["th"] and (mi["tw"] != tga["w"] or mi["th"] != tga["h"]):
            coord_oob.append(
                f"{path} {mi['name']} declared {mi['tw']}x{mi['th']} TGA {tga.get('w')}x{tga.get('h')}"
            )

    # PlayerTemplate remaps vs camp-clone
    strip_pt = split_pt(jf.text_of(strip_d, r"Data\INI\PlayerTemplate.ini"))
    good_pt = split_pt(jf.text_of(good_d, r"Data\INI\PlayerTemplate.ini"))
    pt_repoints = []
    pt_missing = []
    for name in sorted(set(strip_pt) | set(good_pt)):
        if name not in strip_pt or name not in good_pt:
            continue
        for key in PT_KEYS:
            g = pt_field(good_pt[name], key)
            s = pt_field(strip_pt[name], key)
            if g != s:
                exists = s.lower() in all_mi if s else False
                pt_repoints.append(f"{name} {key} {g} -> {s} MappedImage={'YES' if exists else 'NO'}")
                if s and not exists:
                    pt_missing.append(f"{name} {key}={s}")

    # CommandButton CampFlag
    strip_btn = jf.text_of(strip_d, r"Data\INI\CommandButton.ini")
    good_btn = jf.text_of(good_d, r"Data\INI\CommandButton.ini")
    btn_repoints = []
    btn_missing = []
    for m in re.finditer(r"(?im)^CommandButton\s+(\S+)\s*$", strip_btn):
        rest = strip_btn[m.end():]
        m2 = re.search(r"(?im)^CommandButton\s+\S+", rest)
        blk = rest[: m2.start()] if m2 else rest
        img = re.search(r"(?im)^\s*ButtonImage\s*=\s*(\S+)", blk)
        if img and re.search(r"(?i)CampFlag", img.group(1)):
            exists = img.group(1).lower() in all_mi
            btn_repoints.append(f"{m.group(1)} -> {img.group(1)} MappedImage={'YES' if exists else 'NO'}")
            if not exists:
                btn_missing.append(f"{m.group(1)} {img.group(1)}")

    # DATA clone Model/Anim leftover
    clone_hits = []
    extra_draws = []
    for n, b in strip_d:
        if not str(n).lower().endswith(".ini"):
            continue
        t = b.decode("latin-1", errors="replace")
        if "ModuleTag_SpecterNatFlag" in t or "ModuleTag_SpecterCampFlag" in t:
            extra_draws.append(jf.norm(n))
        for mdl in re.findall(r"(?im)^\s*Model\s*=\s*(\S+)", t):
            if re.search(r"(?i)(IqPwr_|NkPwr_|IqWF_|NkWF_|irq_camp_[A-Za-z]|(DE|FR|IN|IT|JP|LY|PK|SA|SE|SK|SY|TR|UA|UAE|UK|VN|ZA)_Flag_Hs)", mdl):
                clone_hits.append(f"{n} Model={mdl}")
        for anim in re.findall(r"(?im)^\s*Animation\s*=\s*(\S+)", t):
            if re.search(r"(?i)(IqPwr_|NkPwr_|IqWF_|NkWF_|(DE|FR|IN|IT|JP|LY|PK|SA|SE|SK|SY|TR|UA|UAE|UK|VN|ZA)_Flag_Hs)", anim):
                clone_hits.append(f"{n} Animation={anim}")

    banned_w3d = [
        jf.norm(n) for n, _ in strip_a
        if n.lower().endswith(".w3d") and re.search(
            r"(?i)(IqPwr_|NkPwr_|IqWF_|NkWF_|irq_camp_|(DE|FR|IN|IT|JP|LY|PK|SA|SE|SK|SY|TR|UA|UAE|UK|VN|ZA)_Flag_Hs)",
            stem_of(n),
        )
    ]

    # dump new MI files raw-ish (first 40 lines each)
    mi_previews = []
    for k in added_d:
        name, blob = sd[k]
        text = blob.decode("latin-1", errors="replace")
        mi_previews.append((jf.norm(name), text[:1200], len(text), text.count("MappedImage")))

    OUT.mkdir(parents=True, exist_ok=True)
    lines = [
        "SPECTER1 STRIP_02 FORENSIC INIT-CRASH AUDIT",
        "FIX_APPLIED = NO",
        "INGAME_TESTED = YES (user: STRIP_02 still crashes at initialization)",
        "CLONE_W3D_PRELOAD_RULED_OUT = YES",
        f"STRIP_DATA_SHA256 = {STRIP_DATA_SHA}",
        f"STRIP_ART_SHA256 = {STRIP_ART_SHA}",
        f"CAMP_CLONE_DATA_SHA256 = {GOOD_DATA_SHA}",
        f"CAMP_CLONE_ART_SHA256 = {GOOD_ART_SHA}",
        f"PACKED_STRIP_DATA = {len(strip_d)}  CAMP_CLONE_DATA = {len(good_d)}",
        f"PACKED_STRIP_ART = {len(strip_a)}  CAMP_CLONE_ART = {len(good_a)}",
        f"DUPLICATE_DATA = {len(dup_d)}",
        f"DUPLICATE_ART = {len(dup_a)}",
        "",
        "===== REMAINING DIFF vs LAST KNOWN LAUNCH =====",
        f"ADDED_DATA = {len(added_d)}",
        *[f"  + {sd[k][0] if False else k}" for k in added_d],
        f"REMOVED_DATA = {len(removed_d)}",
        *[f"  - {k}" for k in removed_d],
        f"CHANGED_DATA = {len(changed_d)}",
        *[f"  ~ {k}" for k in changed_d],
        f"ADDED_ART = {len(added_a)}",
        *[f"  + {k}" for k in added_a],
        f"REMOVED_ART = {len(removed_a)}",
        *[f"  - {k}" for k in removed_a],
        f"CHANGED_ART = {len(changed_a)}",
        *[f"  ~ {k}" for k in changed_a],
        f"ADDED_W3D = {len(w3d_added)}",
        f"CHANGED_W3D = {len(w3d_changed)}",
        f"OTHER_ART_ADDED = {len(other_added)} {other_added}",
        f"OTHER_ART_CHANGED = {len(other_changed)} {other_changed}",
        f"BANNED_W3D_STILL_PACKED = {len(banned_w3d)}",
        f"DATA_CLONE_MODEL_ANIM = {len(clone_hits)}",
        f"EXTRA_FLAG_DRAWS = {len(extra_draws)}",
        "",
        "===== TGA HEADERS (STRIP_02 new/changed) =====",
    ]
    for name, info, old in tga_rows:
        old_s = ""
        if old:
            old_s = f"  WAS {old.get('w')}x{old.get('h')} bpp={old.get('bpp')} type={old.get('type')} desc={old.get('desc')} origin={old.get('origin')} size={old.get('size')}"
        lines.append(
            f"  {name} {info.get('w')}x{info.get('h')} bpp={info.get('bpp')} type={info.get('type')} "
            f"desc=0x{info.get('desc',0):02x} origin={info.get('origin')} size={info.get('size')} "
            f"expected={info.get('expected')} size_ok={info.get('size_ok')} cmap={info.get('cmap')}{old_s}"
        )
    lines.append("KNOWN_GOOD_TGA_REFS")
    for name, info in refs:
        lines.append(
            f"  {name} {info.get('w')}x{info.get('h')} bpp={info.get('bpp')} type={info.get('type')} "
            f"desc=0x{info.get('desc',0):02x} origin={info.get('origin')} size={info.get('size')} size_ok={info.get('size_ok')}"
        )

    lines += [
        "",
        "===== NEW MAPPEDIMAGE FILES =====",
    ]
    for name, preview, nlen, count in mi_previews:
        lines.append(f"FILE {name} bytes={nlen} MappedImage_count={count}")
        lines.append(preview.replace("\r\n", "\n"))
        lines.append("---")

    lines += [
        f"NEW_MAPPEDIMAGE_BLOCKS = {len(new_mi_blocks)}",
        f"MISSING_TEXTURE_FOR_NEW_MI = {len(missing_tex)}",
        *[f"  {x}" for x in missing_tex],
        f"COORDS_OR_SIZE_MISMATCH = {len(coord_oob)}",
        *[f"  {x}" for x in coord_oob],
        f"TEXTURE_NAME_LEN_GT_13 = {len(long_tex)}",
        *[f"  {x}" for x in long_tex],
        f"MAPPEDIMAGE_NAME_DEFINED_IN_MULTIPLE_FILES = {len(collisions)}",
        *[f"  {n} files={files}" for n, files in collisions],
        "",
        "===== PLAYERTEMPLATE HUD REPOINTS =====",
        f"PT_REPOINTS = {len(pt_repoints)}",
        *[f"  {x}" for x in pt_repoints],
        f"PT_MISSING_MAPPEDIMAGE = {len(pt_missing)}",
        *[f"  {x}" for x in pt_missing],
        "",
        "===== COMMANDBUTTON CAMPFLAG =====",
        f"BTN_REPOINTS = {len(btn_repoints)}",
        *[f"  {x}" for x in btn_repoints],
        f"BTN_MISSING_MAPPEDIMAGE = {len(btn_missing)}",
        *[f"  {x}" for x in btn_missing],
        "",
    ]

    # hypotheses
    turkey_resized = [
        name for name, info, old in tga_rows
        if old and (info.get("w") != old.get("w") or info.get("h") != old.get("h"))
    ]
    new_tga_bad = [
        name for name, info, _ in tga_rows
        if (not info.get("size_ok")) or info.get("type") not in (2, 10) or info.get("bpp") not in (16, 24, 32)
    ]

    lines += [
        "===== CRASH HYPOTHESIS RANKING =====",
        "Ruled out: unused #516-518 clone W3D preload (STRIP_02 removed them; still crashes).",
        "Ruled out: extra Flag_Hs Draws / clone Model= (OBJECT_BOOT DATA has none).",
        "Ruled out: packed-path duplicates.",
        "",
        "H1  NEW MAPPEDIMAGE INIs loaded at init (3 files, not in last known launch)",
        f"    {', '.join(added_d) or 'none'}",
        "    SAGE parses every INI in the DATA BIG at startup. A bad MappedImage",
        "    definition can throw Uncaught Exception during initialization with no stack.",
        f"    New blocks={len(new_mi_blocks)} missing_tex={len(missing_tex)} coord_mismatch={len(coord_oob)}",
        f"    name_collisions_across_files={len(collisions)}",
        "",
        "H2  PLAYERTEMPLATE HUD remaps to those new MappedImages",
        f"    {len(pt_repoints)} fields retargeted vs camp-clone; missing MI={len(pt_missing)}",
        "    Init builds every faction template. A missing or colliding image name crashes here.",
        "",
        "H3  OVERWRITTEN TURKEY HUD TGAs (dimension/format change vs last launch)",
        f"    resized_vs_camp_clone={turkey_resized}",
        "    If MappedImages still declare old TextureWidth/Height/Coords against a new",
        "    128x64 flag TGA, init can fault while building the image atlas.",
        "",
        "H4  NEW COUNTRY FLAG TGAs (format) used by new MappedImages",
        f"    added={len(tex_added)} bad_header={new_tga_bad}",
        "    Lower probability if headers match working DPRK_Flag (128x64 32-bit desc 0x08).",
        "",
        "H5  COMMANDBUTTON CampFlag ButtonImage remaps",
        f"    {len(btn_repoints)} buttons; missing MI={len(btn_missing)}",
        "    CommandButton.ini is parsed at init. Usually image-not-found is nonfatal,",
        "    but a bad MappedImage name shared with H1 can still fault.",
        "",
        "H6  OTHER (not remaining vs camp-clone)",
        f"    added_w3d={len(w3d_added)} changed_w3d={len(w3d_changed)} other_art={other_added or other_changed}",
        "    If this is empty, remaining crash surface is DATA Group A + TGA overlays only.",
        "",
        "===== NEXT ISOLATED REPAIR (do not run in this audit) =====",
        "Do not touch building Object INIs. Do not restore cloth/Draws/clones.",
        "Next pair must keep STRIP_02 ART OR camp-clone ART, and isolate DATA Group A:",
        "  Step A1: restore PlayerTemplate.ini + the 3 new MappedImage INIs + CommandButton.ini",
        "           from CAMP_CLONE. Keep STRIP_02 ART (or revert ART Turkey TGAs too).",
        "           That is: DATA == camp-clone, ART == STRIP_02 or camp-clone.",
        "  If that boots, crash source is Group A (PT/MI/CommandButton/TGA), not buildings.",
        "  Then reintroduce: (1) TGA+MI only, PT/CommandButton still original;",
        "                    (2) PT remaps; (3) CommandButton CampFlag last.",
        "Safest immediate boot pair remains SPECTER1_FLAG_BOOT_SAFE_01 / CAMP_CLONE",
        "(byte-identical last known launch).",
        "",
        "No BIG rebuild in this audit.",
    ]
    report = "\n".join(lines) + "\n"
    (OUT / "audit.txt").write_text(report, encoding="utf-8")
    print(report)
    print("WROTE", OUT / "audit.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
