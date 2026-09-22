#!/usr/bin/env python3
"""Read-only audit of the current Specter flag-crash BIG pair.

Does not modify DATA/ART. Maps Object -> Draw -> Model -> Animation -> W3D
and reports broken chains, leftovers from PR #516/#517/#518, and duplicates.

Current pair = SPECTER1_FLAG_OBJECT_BOOT_01 (PR #520, latest release).
Baseline   = SPECTER1_CAMP_CLONE_IRAQ_VIETNAM (last known launch).
"""
from __future__ import annotations

import re
import struct
from collections import Counter, defaultdict
from pathlib import Path

import japan_france_roster_01 as jf

CUR_DATA = Path("/tmp/flag_audit/current/_SPEC_DATA_ONE.big")
CUR_ART = Path("/tmp/flag_audit/current/_SPEC_ART_ONE.big")
GOOD_DATA = Path("/tmp/flag_audit/campclone/_SPEC_DATA_ONE.big")
GOOD_ART = Path("/tmp/flag_audit/campclone/_SPEC_ART_ONE.big")

CUR_DATA_SHA = "3e42c369fb30e229062fcbf29feafb15c9e59472dc16757d8e5f0c0092813221"
CUR_ART_SHA = "2b84d7836b6560d22f32ce2c6687a167a52515ea2f70aeecbc934968fccb9af1"
GOOD_DATA_SHA = "e04a7b08a2fc6ae5648611d68b3b026e5cb004a103e92b2926d246a9ad1c6dfd"
GOOD_ART_SHA = "15ca142798e737cb7fd7434c02976d55c40948a42b4ee121143253911aad740a"

OUT = Path("/workspace/patch/Release/SPECTER1_FLAG_REMAIN_AUDIT_01")

FLAG_NEEDLE = re.compile(
    r"(?i)(Flag_Hs|IqPwr_|NkPwr_|IqWF_|NkWF_|irq_camp_|NK_camp_"
    r"|Iraq_Powerplant_|NKor_Powerplant_|NKr_Powerplant_"
    r"|Irq_WarFactory_|NKr_WarFactory_|Iraq_Supply_|NKor_Supply_|NKr_Command_"
    r"|CampFlag|SpecterNatFlag|SpecterCampFlag|Specter_RemainingFlags|Specter_CampFlags"
    r"|UK_Flag_Hs|Irq__IqFlag_Hs|NKr__NKFlag_Hs)"
)
CLONE_MODEL_RE = re.compile(
    r"(?i)(IqPwr_|NkPwr_|IqWF_|NkWF_|irq_camp_[A-Za-z]"
    r"|Iraq_Powerplant_|NKor_Powerplant_|NKr_Powerplant_"
    r"|Irq_WarFactory_|NKr_WarFactory_|Iraq_Supply_|NKor_Supply_|NKr_Command_"
    r"|(DE|FR|IN|IT|JP|LY|PK|SA|SE|SK|SY|TR|UA|UAE|UK|VN|ZA)_Flag_Hs)"
)
WATCH = (
    "Iraq_Powerplant", "NKor_Powerplant", "NKr_Powerplant",
    "Irq_WarFactory", "NKr_WarFactory", "Flag_Hs",
    "UK_Flag_Hs", "NKr__NKFlag_Hs", "Irq__IqFlag_Hs",
    "IqPwr_", "NkPwr_", "IqWF_", "NkWF_", "irq_camp_", "NK_camp_",
    "CampFlag", "ModuleTag_SpecterNatFlag", "ModuleTag_SpecterCampFlag",
)

W3D_MESH_HEADER3 = 0x0000001F
W3D_HIERARCHY_HEADER = 0x00000101
W3D_ANIMATION_HEADER = 0x00000201
W3D_COMPRESSED_ANIMATION_HEADER = 0x00000281


def cstr16(buf: bytes, off: int = 0) -> str:
    raw = buf[off:off + 16]
    if not raw:
        return ""
    return raw.split(b"\x00", 1)[0].decode("latin-1", errors="replace")


def w3d_names(blob: bytes) -> dict[str, set[str]]:
    meshes: set[str] = set()
    anims: set[str] = set()
    hier: set[str] = set()
    pos = 0
    n = len(blob)
    while pos + 8 <= n:
        ctype, csize = struct.unpack_from("<II", blob, pos)
        size = csize & 0x7FFFFFFF
        payload = pos + 8
        end = payload + size
        if end > n or size < 0:
            pos += 1
            continue
        if ctype == W3D_MESH_HEADER3 and size >= 36:
            meshes.add(cstr16(blob, payload + 4))
            hier.add(cstr16(blob, payload + 20))
        elif ctype == W3D_HIERARCHY_HEADER and size >= 20:
            hier.add(cstr16(blob, payload + 4))
        elif ctype in (W3D_ANIMATION_HEADER, W3D_COMPRESSED_ANIMATION_HEADER) and size >= 36:
            anims.add(cstr16(blob, payload + 4))
            hier.add(cstr16(blob, payload + 20))
        pos = payload if (csize & 0x80000000) else end
        if pos <= payload - 8:
            pos = end
    return {"mesh": {x for x in meshes if x}, "anim": {x for x in anims if x}, "hier": {x for x in hier if x}}


def parse_objects(text: str, path: str) -> list[dict]:
    matches = list(re.finditer(r"(?im)^Object\s+(\S+)\s*$", text))
    objs = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[m.start():end]
        draws = []
        draw_iter = list(re.finditer(r"(?im)^[ \t]*Draw\s*=\s*(\S+)(?:\s+(\S+))?", block))
        for j, d in enumerate(draw_iter):
            dend = draw_iter[j + 1].start() if j + 1 < len(draw_iter) else len(block)
            dblk = block[d.start():dend]
            models = re.findall(r"(?im)^\s*Model\s*=\s*(\S+)", dblk)
            anims = re.findall(r"(?im)^\s*Animation\s*=\s*(\S+)", dblk)
            draws.append({
                "kind": d.group(1),
                "tag": d.group(2) or "",
                "models": models,
                "anims": anims,
                "raw_head": d.group(0).strip(),
            })
        objs.append({
            "name": m.group(1),
            "path": path,
            "draws": draws,
            "flaggy": bool(FLAG_NEEDLE.search(block)),
        })
    return objs


def main() -> int:
    if jf.sha256_file(CUR_DATA) != CUR_DATA_SHA:
        raise SystemExit("current DATA SHA mismatch")
    if jf.sha256_file(CUR_ART) != CUR_ART_SHA:
        raise SystemExit("current ART SHA mismatch")
    if jf.sha256_file(GOOD_DATA) != GOOD_DATA_SHA:
        raise SystemExit("camp-clone DATA SHA mismatch")
    if jf.sha256_file(GOOD_ART) != GOOD_ART_SHA:
        raise SystemExit("camp-clone ART SHA mismatch")

    data = jf.read_big_list(CUR_DATA)
    art = jf.read_big_list(CUR_ART)
    good_d = jf.read_big_list(GOOD_DATA)
    good_a = jf.read_big_list(GOOD_ART)

    dnames = [jf.norm(n).lower() for n, _ in data]
    anames = [jf.norm(n).lower() for n, _ in art]
    dup_data = sorted({k for k, c in Counter(dnames).items() if c > 1})
    dup_art = sorted({k for k, c in Counter(anames).items() if c > 1})

    art_map = {jf.norm(n).lower(): (n, bytes(b)) for n, b in art}
    good_amap = {jf.norm(n).lower(): bytes(b) for n, b in good_a}
    good_dmap = {jf.norm(n).lower(): bytes(b) for n, b in good_d}
    cur_dmap = {jf.norm(n).lower(): bytes(b) for n, b in data}

    added_data = sorted(set(cur_dmap) - set(good_dmap))
    added_art = sorted(set(art_map) - set(good_amap))
    removed_data = sorted(set(good_dmap) - set(cur_dmap))
    removed_art = sorted(set(good_amap) - set(art_map))
    changed_data = sorted(k for k in cur_dmap.keys() & good_dmap.keys() if cur_dmap[k] != good_dmap[k])
    changed_art = sorted(k for k in art_map.keys() & good_amap.keys() if art_map[k][1] != good_amap[k])

    w3d_index: dict[str, dict] = {}
    for key, (name, blob) in art_map.items():
        if not key.endswith(".w3d"):
            continue
        stem = Path(key.replace("\\", "/")).stem
        info = w3d_names(blob)
        w3d_index[stem] = {
            "path": jf.norm(name),
            "stem": stem,
            "len": len(stem),
            "meshes": sorted(info["mesh"]),
            "anims": sorted(info["anim"]),
            "hier": sorted(info["hier"]),
            "new_vs_clone": key not in good_amap,
        }

    objects: list[dict] = []
    for n, b in data:
        if not str(n).lower().endswith(".ini"):
            continue
        text = b.decode("latin-1", errors="replace")
        objects.extend(parse_objects(text, jf.norm(n)))

    chains = []
    broken = []
    long_models = []
    leftover_clones = []
    extra_draws = []
    remaining_flag_hs = []
    for obj in objects:
        for dr in obj["draws"]:
            if re.search(r"(?i)Specter(?:Nat|Camp)Flag", dr["tag"]):
                extra_draws.append(f"{obj['name']} {dr['tag']} {obj['path']}")
            last_model = None
            for mdl in dr["models"]:
                last_model = mdl
                if len(mdl) > 15:
                    long_models.append(f"{obj['name']} Model={mdl} len={len(mdl)} {obj['path']}")
                if CLONE_MODEL_RE.search(mdl):
                    leftover_clones.append(f"{obj['name']} Model={mdl} {obj['path']}")
                if re.search(r"(?i)Flag_Hs", mdl):
                    remaining_flag_hs.append(f"{obj['name']} Model={mdl} tag={dr['tag']} {obj['path']}")
                art_key = f"art\\w3d\\{mdl}.w3d".lower()
                w3d = w3d_index.get(mdl.lower())
                status = []
                if mdl.lower() in ("none", "null"):
                    status.append("NONE")
                elif w3d is None:
                    status.append("MISSING_W3D")
                else:
                    if w3d["meshes"] and mdl not in w3d["meshes"] and mdl.lower() not in {x.lower() for x in w3d["meshes"]}:
                        status.append(f"MESH_NAME_MISMATCH meshes={w3d['meshes']}")
                    if len(mdl) > 15:
                        status.append("MODEL_LEN_GT_15")
                rec = {
                    "object": obj["name"],
                    "path": obj["path"],
                    "draw": dr["tag"] or dr["kind"],
                    "model": mdl,
                    "anims": [],
                    "w3d": w3d["path"] if w3d else "",
                    "w3d_meshes": w3d["meshes"] if w3d else [],
                    "w3d_anims": w3d["anims"] if w3d else [],
                    "status": status,
                }
                chains.append(rec)
                if any(s != "NONE" for s in status):
                    broken.append(rec)
            for anim in dr["anims"]:
                container, _, inner = anim.partition(".")
                w3d = w3d_index.get(container.lower())
                status = []
                if last_model and container.lower() != last_model.lower():
                    status.append(f"ANIM_CONTAINER_NE_MODEL model={last_model}")
                if w3d is None:
                    status.append("MISSING_ANIM_W3D")
                elif inner and w3d["anims"] and inner not in w3d["anims"] and inner.lower() not in {x.lower() for x in w3d["anims"]}:
                    status.append(f"ANIM_NAME_MISSING_IN_W3D have={w3d['anims']}")
                rec = {
                    "object": obj["name"],
                    "path": obj["path"],
                    "draw": dr["tag"] or dr["kind"],
                    "model": last_model or "",
                    "anims": [anim],
                    "w3d": w3d["path"] if w3d else "",
                    "w3d_meshes": w3d["meshes"] if w3d else [],
                    "w3d_anims": w3d["anims"] if w3d else [],
                    "status": status,
                }
                chains.append(rec)
                if status:
                    broken.append(rec)
                if CLONE_MODEL_RE.search(anim):
                    leftover_clones.append(f"{obj['name']} Animation={anim} {obj['path']}")

    # leftover #516-518 names still referenced
    removed_name_refs = []
    old_stems = {
        Path(k.replace("\\", "/")).stem.lower()
        for k in added_art if k.endswith(".w3d")
    }
    for rec in chains:
        mdl = rec["model"]
        if mdl and mdl.lower() in old_stems:
            removed_name_refs.append(f"{rec['object']} still Model={mdl} (new ART clone)")
        for anim in rec["anims"]:
            cont = anim.split(".", 1)[0]
            if cont.lower() in old_stems:
                removed_name_refs.append(f"{rec['object']} still Animation={anim}")

    # W3D clones whose filename != internal mesh (crash class if referenced)
    filename_mesh_mismatch = []
    for stem, info in sorted(w3d_index.items()):
        if not info["new_vs_clone"]:
            continue
        meshes = info["meshes"]
        if meshes and stem not in {m.lower() for m in meshes} and info["stem"] not in meshes:
            filename_mesh_mismatch.append(
                f"{info['path']} stem={info['stem']} meshes={meshes}"
            )

    # unused new ART still packed
    referenced_models = {rec["model"].lower() for rec in chains if rec["model"]}
    unused_new_w3d = [
        w3d_index[s]["path"] for s in sorted(w3d_index)
        if w3d_index[s]["new_vs_clone"] and s not in referenced_models
    ]
    used_new_w3d = [
        w3d_index[s]["path"] for s in sorted(w3d_index)
        if w3d_index[s]["new_vs_clone"] and s in referenced_models
    ]

    watch_hits = defaultdict(list)
    for n, b in data:
        if not str(n).lower().endswith(".ini"):
            continue
        t = b.decode("latin-1", errors="replace")
        for w in WATCH:
            if w.lower() in t.lower():
                watch_hits[w].append(jf.norm(n))

    flag_objects = [o for o in objects if o["flaggy"]]
    boot_safe = (
        not dup_data and not dup_art
        and not extra_draws and not leftover_clones
        and not long_models and not used_new_w3d
        and not any("MISSING" in " ".join(r["status"]) for r in broken)
        and not any("ANIM_CONTAINER" in " ".join(r["status"]) for r in broken)
    )

    lines = [
        "SPECTER1 FLAG REMAINING-INIT AUDIT (NO FIX)",
        "CURRENT_RELEASE = SPECTER1_FLAG_OBJECT_BOOT_01 (PR #520)",
        f"CURRENT_DATA_SHA256 = {CUR_DATA_SHA}",
        f"CURRENT_ART_SHA256 = {CUR_ART_SHA}",
        "LAST_KNOWN_LAUNCH = SPECTER1_CAMP_CLONE_IRAQ_VIETNAM",
        f"CAMP_CLONE_DATA_SHA256 = {GOOD_DATA_SHA}",
        f"CAMP_CLONE_ART_SHA256 = {GOOD_ART_SHA}",
        f"PACKED_DATA_FILES = {len(data)}",
        f"PACKED_ART_FILES = {len(art)}",
        f"DUPLICATE_DATA_PATHS = {len(dup_data)}",
        *[f"  {x}" for x in dup_data],
        f"DUPLICATE_ART_PATHS = {len(dup_art)}",
        *[f"  {x}" for x in dup_art],
        f"BIG_INTEGRITY = YES",
        f"BOOT_SAFE_LOGICAL = {'YES' if boot_safe else 'NO'}",
        "INGAME_TESTED = NO",
        "FIX_APPLIED = NO",
        "",
        "===== VS CAMP-CLONE =====",
        f"ADDED_DATA = {len(added_data)}",
        *[f"  + {n}" for n in added_data],
        f"REMOVED_DATA = {len(removed_data)}",
        *[f"  - {n}" for n in removed_data],
        f"CHANGED_DATA = {len(changed_data)}",
        *[f"  ~ {n}" for n in changed_data],
        f"ADDED_ART = {len(added_art)}",
        *[f"  + {n}" for n in added_art],
        f"REMOVED_ART = {len(removed_art)}",
        *[f"  - {n}" for n in removed_art[:20]],
        f"CHANGED_ART = {len(changed_art)}",
        *[f"  ~ {n}" for n in changed_art],
        "",
        "===== BROKEN CHAINS (Object -> Draw -> Model -> Animation -> W3D) =====",
        f"BROKEN_COUNT = {len(broken)}",
    ]
    for rec in broken:
        lines.append(
            f"  OBJ={rec['object']} DRAW={rec['draw']} MODEL={rec['model']} "
            f"ANIM={','.join(rec['anims']) or '-'} W3D={rec['w3d'] or 'MISSING'} "
            f"STATUS={';'.join(rec['status'])} FILE={rec['path']}"
        )

    lines += [
        "",
        "===== EXTRA FLAG DRAWS (should be 0 after #520) =====",
        f"EXTRA_DRAWS = {len(extra_draws)}",
        *[f"  {x}" for x in extra_draws],
        "",
        "===== LEFTOVER CLONE MODEL/ANIM REFS =====",
        f"LEFTOVER_CLONES = {len(leftover_clones)}",
        *[f"  {x}" for x in leftover_clones],
        "",
        "===== MODEL NAMES > 15 =====",
        f"LONG_MODELS = {len(long_models)}",
        *[f"  {x}" for x in long_models],
        "",
        "===== NEW W3D FILENAME vs INTERNAL MESH =====",
        f"FILENAME_MESH_MISMATCH_CLONES = {len(filename_mesh_mismatch)}",
        *[f"  {x}" for x in filename_mesh_mismatch],
        f"USED_NEW_W3D_BY_OBJECT = {len(used_new_w3d)}",
        *[f"  {x}" for x in used_new_w3d],
        f"UNUSED_NEW_W3D_STILL_PACKED = {len(unused_new_w3d)}",
        *[f"  {x}" for x in unused_new_w3d],
        "",
        "===== REMAINING OBJECT FLAG_HS (camp-clone originals if any) =====",
        f"REMAINING_FLAG_HS = {len(remaining_flag_hs)}",
        *[f"  {x}" for x in remaining_flag_hs],
        "",
        "===== REFS TO NEW CLONE STEMS =====",
        f"REMOVED_NAME_STILL_REFERENCED = {len(removed_name_refs)}",
        *[f"  {x}" for x in removed_name_refs],
        "",
        "===== WATCH =====",
        *[f"  {w}: {len(watch_hits[w])} files" for w in WATCH],
        "",
        "===== FLAG-TOUCHED OBJECTS =====",
        f"FLAGGY_OBJECTS = {len(flag_objects)}",
        *[f"  {o['name']} draws={len(o['draws'])} {o['path']}" for o in flag_objects],
        "",
        "===== DEPENDENCY MAP (flag-related Object/Draw/Model/Anim only) =====",
    ]
    for obj in flag_objects:
        lines.append(f"Object {obj['name']}")
        lines.append(f"  FILE {obj['path']}")
        for dr in obj["draws"]:
            if not (dr["models"] or dr["anims"] or re.search(r"(?i)flag|specter", dr["tag"])):
                # still show draws that carry models matching flag needles
                if not any(FLAG_NEEDLE.search(x) for x in dr["models"] + dr["anims"]):
                    continue
            lines.append(f"  Draw {dr['kind']} {dr['tag']}")
            for mdl in dr["models"]:
                w3d = w3d_index.get(mdl.lower())
                lines.append(
                    f"    Model={mdl} len={len(mdl)} w3d={'YES' if w3d else 'NO'} "
                    f"meshes={w3d['meshes'] if w3d else []} anims={w3d['anims'] if w3d else []}"
                )
            for anim in dr["anims"]:
                lines.append(f"    Animation={anim}")
        lines.append("")

    OUT.mkdir(parents=True, exist_ok=True)
    report = "\n".join(lines) + "\n"
    (OUT / "audit.txt").write_text(report, encoding="utf-8")
    print(report)
    print("WROTE", OUT / "audit.txt")
    print("BROKEN", len(broken), "EXTRA_DRAWS", len(extra_draws), "LEFTOVER", len(leftover_clones))
    print("FILENAME_MESH_MISMATCH", len(filename_mesh_mismatch))
    print("USED_NEW_W3D", len(used_new_w3d), "UNUSED_NEW_W3D", len(unused_new_w3d))
    print("BOOT_SAFE_LOGICAL", "YES" if boot_safe else "NO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
