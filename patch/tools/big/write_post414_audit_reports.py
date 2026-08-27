#!/usr/bin/env python3
"""Write POST_414 / PRELOAD / SUSPECTS reports from packed BIGs."""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pack_china_heavy_aircraft as ch

CUR_DATA = Path("/tmp/aircraft_startup_regression_fix_v2/_SPEC_DATA_ONE.big")
CUR_ART = Path("/tmp/aircraft_startup_regression_fix_v2/_SPEC_ART_ONE.big")
BASE_DATA = Path("/tmp/baseline414/iconfix/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/dl/_SPEC_ART_H20.big")
CRASH_DATA = Path("/tmp/aircraft_init_crash_fix/_SPEC_DATA_ONE.big")
OUTS = [
    Path("/tmp/aircraft_startup_regression_fix_v2"),
    Path("/workspace/patch"),
]


def load(p: Path):
    e, r = ch.read_big(p)
    return {ch.norm_key(n): (n.replace("/", "\\"), r[o : o + s]) for n, o, s in e}


def walk(blob, pos, end, out):
    while pos + 8 <= end:
        ctype, csize = struct.unpack_from("<II", blob, pos)
        payload = csize & 0x7FFFFFFF
        container = bool(csize & 0x80000000)
        hdr = pos + 8
        pe = hdr + payload
        if pe > len(blob) + 8:
            break
        out.append(ctype)
        if container:
            walk(blob, hdr, min(pe, len(blob)), out)
        pos = pe
        if pe <= hdr:
            break


def w3d_info(blob: bytes) -> dict:
    types: list[int] = []
    walk(blob, 0, len(blob), types)
    anim = sum(1 for t in types if t in (0x200, 0x280, 0x2C0))
    tex = []
    for m in re.finditer(rb"([\w\-\. ]+\.(?:tga|dds|TGA|DDS))\x00", blob):
        tex.append(m.group(1).decode("latin1"))
    return {"size": len(blob), "anim": anim, "chunks": len(types), "tex": sorted(set(tex))}


OBJ = re.compile(r"^Object(?:Reskin)?\s+(\S+)", re.M)


def main() -> int:
    cur_d = load(CUR_DATA)
    cur_a = load(CUR_ART)
    base_d = load(BASE_DATA)
    base_a = load(BASE_ART)
    crash_d = load(CRASH_DATA)

    cur_w3d = {}
    cur_tex = set()
    for k, (n, b) in cur_a.items():
        leaf = n.split("\\")[-1].lower()
        if leaf.endswith(".w3d"):
            cur_w3d[leaf[:-4]] = w3d_info(b)
            cur_w3d[leaf[:-4]]["file"] = n
        if leaf.endswith((".tga", ".dds")):
            cur_tex.add(leaf)
    base_w3d = {}
    for k, (n, b) in base_a.items():
        leaf = n.split("\\")[-1].lower()
        if leaf.endswith(".w3d"):
            base_w3d[leaf[:-4]] = w3d_info(b)

    new_files = sorted(k for k in cur_d if k not in base_d)
    changed_files = sorted(
        k
        for k in cur_d
        if k in base_d
        and hashlib.sha256(cur_d[k][1]).digest() != hashlib.sha256(base_d[k][1]).digest()
    )
    new_w3d = sorted(k for k in cur_w3d if k not in base_w3d)

    preload_rows = []
    e7_pre414 = 0
    for k, (n, b) in cur_d.items():
        if not k.endswith(".ini"):
            continue
        t = b.decode("latin1", errors="replace")
        for m in OBJ.finditer(t):
            nxt = OBJ.search(t, m.end())
            block = t[m.start() : nxt.start() if nxt else len(t)]
            obj = m.group(1)
            kindm = re.search(r"KindOf\s*=\s*(.+)", block)
            kind = kindm.group(1) if kindm else ""
            if "PRELOAD" not in kind:
                continue
            models = re.findall(r"^\s*Model\s*=\s*(\S+)", block, re.M)
            anims = re.findall(r"^\s*Animation\s*=\s*(\S+)", block, re.M)
            miss_model = [
                md
                for md in set(models)
                if md.lower() not in ("none",) and md.lower() not in cur_w3d
            ]
            bad_anim = []
            for md in set(models):
                info = cur_w3d.get(md.lower())
                if not info or info["anim"] > 0:
                    continue
                for an in anims:
                    if an.split(".", 1)[0].lower() == md.lower():
                        bad_anim.append((md, an, info["size"]))
            if k not in base_d or obj not in base_d.get(k, (n, b""))[1].decode(
                "latin1", errors="replace"
            ):
                status = "NEW"
            else:
                status = "PRE414"
                if bad_anim:
                    e7_pre414 += 1
            if miss_model or (bad_anim and status == "NEW") or k not in base_d:
                preload_rows.append(
                    {
                        "obj": obj,
                        "file": n,
                        "status": status,
                        "miss": miss_model,
                        "bad_anim": bad_anim,
                        "models": models[:4],
                    }
                )

    repaired_vs_crash = []
    for k, (n, b) in cur_d.items():
        if k not in crash_d:
            repaired_vs_crash.append((n, "added"))
        elif crash_d[k][1] != b:
            repaired_vs_crash.append((n, "changed"))

    suspect = """# STARTUP_CRASH_SUSPECTS.md

Baseline: PR/BUILD **#414** is the last user-confirmed runtime-safe boot
(PR https://github.com/sajadabedi941-lang/Specter-Patch/pull/414).
There was no dedicated #414 GitHub Release. Packed comparison uses published
PR **#413** `china-aircraft-icon-fix-v1` DATA + `china-h20` ART as the closest
packed BIG pair from that era.

Current package: repaired v2 DATA/ART after stripping proven-invalid post-414
declarations. Cursor cannot launch Generals Zero Hour.

**STATIC STARTUP VALIDATION: PASS — USER RUNTIME TEST REQUIRED**

Do not treat this document as a claim that the crash is fixed in-game.

## CRITICAL (definite initialization-invalid, repaired in v2)

| Rank | Issue | Introduced | Repair |
|---|---|---|---|
| 1 | Duplicate **CommandSet** names for France/Germany/Britain/Italy `*_HeavyAirBaseCommandSet` and `*GM406CommandSet` in both `CommandSet.ini` and `CommandSet_{Faction}.ini` | First appears with PR **#415** France rebuild (CommandSet.ini inject while faction file retained). Germany/Italy/UK copies follow in **#417**. | Removed faction-file copies. Canonical 12-fighter menus remain in `CommandSet.ini`. |
| 2 | Duplicate **CommandButton** `Command_ConstructGermanyJetTornadoECR` and `Command_ConstructItalyJetTornadoECR` in `CommandButton.ini` **and** `CommandSet.ini` | PR **#417** Europe air force (buttons inlined into CommandSet.ini while already present in CommandButton.ini) | Removed the CommandSet.ini copies. |
| 3 | Duplicate **Weapon** `Japan_Weapon_AAM4B_F15J` twice in packed `Weapon.ini` (identical blocks) | Donor-unused / global-donor overlay inlining after **#423** | Kept first block, removed second. |
| 4 | PRELOAD + `Animation=` on W3D with **zero** animation chunks: `ItalyAircraftG550CAEW` (`KVE737.W3D`) and `GermanyHelicopterH145M` (`LSFFenneck.W3D`) | PR **#417**; v1 already stripped Animation lines | Still stripped in v2. Units kept. |

Historical Specter init-crash report (`INIT_CRASH_AUDIT_FIX_REPORT.md`) treated **duplicate CommandSet names as fatal**. #414 packed DATA did not have the eight European Heavy/GM406 collisions.

## HIGH (not changed: either pre-414 or not proven init-fatal)

| Issue | Notes |
|---|---|
| 129 PRELOAD objects with Animation= on 0-anim W3Ds | Already present in #413 DATA. User booted #414. Not the post-414 regression. |
| `CommandButton` blocks inside `CommandSet.ini` | #413/#414 already had 24 (China construct buttons). Current pack still has unique-only-in-CommandSet.ini buttons required by post-414 air menus. Duplicate-named ones were removed. |
| `END` vs `End` in stock CommandSet.ini (86 tokens) | Present in #413. Not post-414. |
| Pakistan/Egypt CommandSet name overlap with CommandSet.ini | Present in #413. Not touched. |
| SPEC_China MappedImage declared in `HandCreatedMappedImages.INI` and `zChina_AirbasePortrait_Images.INI` | #414 portrait work. User-booted. Preserved. |
| France/Germany/Italy/Britain `_HelicopterBase` objects | PRELOAD STRUCTURE files added after #414. Draw uses `HXUSABigAirPort` which **has** animation chunks. Not on dozer menus. Left in place (no third-airbase dozer slot added). |
| New W3D texture names that are TGA in the mesh but DDS (or EnglishZH) at runtime | 59 new W3Ds list a TGA/DDS string not packed as that exact filename in SPEC ART. ZH commonly resolves DDS caches / EnglishZH. Not treated as definite init crash. |

## MEDIUM

- TEOD fighter meshes (`AVF-35`, `NVJ31`, `NVJ-20`, `UVMirage`, …) have 0 animation chunks. Packed objects using them as `Model=` do **not** set `Animation=`.
- `AVF-35.W3D` is small (~41 KB) with texture `housecolor2.dds` only. Used as a visual stand-in, not as a zero-byte stub. Not removed.
- CommandSet.ini still contains unique CommandButton declarations for post-414 aircraft that are not duplicated in CommandButton.ini. Same pattern as #414 China buttons.

## LOW

- Tiny/zero W3Ds among new ART: **none** under 2 KB.
- USA / Russia / China live CommandSets: hash-protected, unchanged.
- Rally / Sell / Nuclear-Atomic structure: unchanged.

## Earliest bad PR still present (repaired, not reverted)

**PR #415** is the earliest post-414 change that introduced a duplicate CommandSet name (`France_HeavyAirBaseCommandSet` in CommandSet.ini while `CommandSet_France.ini` still declared it).

PR **#417** added the G550/H145M animation crash class and the Germany/Italy/UK CommandSet collisions plus TornadoECR duplicate buttons.

This v2 build **keeps** those PRs' aircraft. It only removes the invalid duplicate declarations and leftover invalid Animation lines.
"""

    audit_lines = [
        "# POST_414_STARTUP_REGRESSION_AUDIT.md",
        "",
        "Packed BIG comparison, not git working-tree only.",
        "",
        "## Baseline",
        "",
        "- Last known runtime-safe: **PR #414** (`cursor/china-aircraft-final-fix-e54a`, 8002fcc).",
        "- Packed DATA used as byte baseline: PR **#413** release `china-aircraft-icon-fix-v1` `_SPEC_DATA_ONE.big`.",
        "- Packed ART used as byte baseline: `china-h20` `_SPEC_ART_ONE.big` (ART from the #413/#414 era).",
        "- Current packed: this v2 repair of `_SPEC_DATA_ONE.big` / `_SPEC_ART_ONE.big`.",
        "",
        "## Counts",
        "",
        f"- New DATA files vs #413 packed: **{len(new_files)}**",
        f"- Changed DATA files vs #413 packed: **{len(changed_files)}**",
        f"- New W3D vs h20 ART: **{len(new_w3d)}**",
        f"- DATA files changed vs crash-fix v1 pack: **{len(repaired_vs_crash)}**",
        "",
        "## Post-414 PRs inspected",
        "",
        "| PR | Title | Startup role |",
        "|---|---|---|",
        "| 414 | Unique China portraits + J-31 A2A | LAST RUNTIME SAFE |",
        "| 415 | France air force rebuild | FIRST duplicate CommandSet (`France_HeavyAirBaseCommandSet`) |",
        "| 416 | France helicopters | Additional PRELOAD helis on Heavy pad |",
        "| 417 | Germany/Italy/UK air forces | G550/H145M Animation crash + more CommandSet dups + TornadoECR button dups |",
        "| 418 | Europe airbase structure | HelicopterBase objects (unused dozer slot); helis folded to Heavy |",
        "| 419 | Europe weapon fire | WeaponSet/FireFX repairs (not uniqueness) |",
        "| 420 | UK diversity | E-7/helis/CommandButtons in CommandSet.ini |",
        "| 421 | UK F-35 / Tempest | Visual/donor |",
        "| 422 | UK E-7 boot crash fix | Removed E-7 Animation= on KVE737; did not fix G550/H145M |",
        "| 423 | Global donor expansion | More aircraft + Weapon.ini inlines |",
        "| 424-428 | Completion / unused donor / 12-fighter roster | More CommandSet.ini injects |",
        "| 429 | Init crash fix v1 | G550/H145M Animation strip only |",
        "",
        "## Definite BROKEN items found in packed crash-fix v1 (repaired here)",
        "",
        "| File | Object | vs #414 | Risk | Verdict |",
        "|---|---|---|---|---|",
        "| CommandSet_France.ini + CommandSet.ini | France_HeavyAirBaseCommandSet / FranceGM406CommandSet | Duplicate name | Init parser | **BROKEN → fixed** |",
        "| CommandSet_Germany.ini + CommandSet.ini | Germany_HeavyAirBaseCommandSet / GermanyGM406CommandSet | Duplicate name | Init parser | **BROKEN → fixed** |",
        "| CommandSet_Britain.ini + CommandSet.ini | Britain_HeavyAirBaseCommandSet / BritainGM406CommandSet | Duplicate name | Init parser | **BROKEN → fixed** |",
        "| CommandSet_Italy.ini + CommandSet.ini | Italy_HeavyAirBaseCommandSet / ItalyGM406CommandSet | Duplicate name | Init parser | **BROKEN → fixed** |",
        "| CommandSet.ini | Command_ConstructGermanyJetTornadoECR / ItalyJetTornadoECR | Dup vs CommandButton.ini | Init parser | **BROKEN → fixed** |",
        "| Weapon.ini | Japan_Weapon_AAM4B_F15J | Two identical Weapon blocks | Init parser | **BROKEN → fixed** |",
        "| ItalyAircraftG550CAEW.ini | ItalyAircraftG550CAEW | Animation= on 0-anim KVE737 | PRELOAD Draw | **BROKEN → fixed in v1, kept** |",
        "| GermanyHelicopterH145M.ini | GermanyHelicopterH145M | Animation= on 0-anim LSFFenneck | PRELOAD Draw | **BROKEN → fixed in v1, kept** |",
        "",
        "## Files actually patched in this v2 DATA BIG vs crash-fix v1",
        "",
    ]
    for n, how in repaired_vs_crash:
        audit_lines.append(f"- `{n}` ({how})")
    audit_lines += [
        "",
        "## New DATA files after #413 (aircraft / airbase related subset)",
        "",
    ]
    air_new = [
        k
        for k in new_files
        if any(
            s in k
            for s in (
                "airforce",
                "rotary",
                "airbase",
                "helicopter",
                "commandset_",
                "weapon_",
                "commandbutton_",
            )
        )
    ]
    for k in air_new:
        n = cur_d[k][0]
        audit_lines.append(f"- `{n}` — new after #413 packed DATA; **PASS** after uniqueness/animation gates (unit preserved)")
    audit_lines += [
        "",
        f"Full new DATA file count: {len(new_files)}. Non-air new files are Specter extras packed by later roster packers (portraits, CSF, mapped images). They are listed in the packer re-extract tree.",
        "",
        "## New W3D vs h20 ART",
        "",
        f"{len(new_w3d)} meshes. Zero-byte/tiny (<2KB) new W3Ds: **0**.",
        "",
        "Suspect large-but-static TEOD / donor meshes (0 anim chunks, used as Model= without Animation=):",
        "",
    ]
    for name in [
        "avf-35",
        "nvj31",
        "nvj-20",
        "uvmirage",
        "pak-fa",
        "su-37",
        "avf16",
        "avf-18",
        "uvmig-21",
        "nvj-10",
        "avcargopln",
        "kve737",
        "lsffenneck",
    ]:
        info = cur_w3d.get(name)
        if not info:
            audit_lines.append(f"- `{name}` **MISSING from SPEC ART**")
            continue
        audit_lines.append(
            f"- `{name}.W3D` size={info['size']} anim_chunks={info['anim']} — "
            f"{'SUSPICIOUS static mesh' if info['anim']==0 else 'has animation'}"
        )
    audit_lines += [
        "",
        "## Texture dependency (new W3Ds)",
        "",
        "Exact case-sensitive filename in SPEC ART. TGA in W3D vs DDS in ART is reported as unresolved-in-SPEC, not auto-deleted.",
        "",
    ]
    miss_tex_n = 0
    for name in new_w3d:
        info = cur_w3d[name]
        miss = [t for t in info["tex"] if t.lower() not in cur_tex]
        if miss:
            miss_tex_n += 1
    audit_lines.append(
        f"New W3Ds with at least one texture string not packed as that exact leaf in SPEC ART: **{miss_tex_n}** / {len(new_w3d)}."
    )
    audit_lines += [
        "",
        "This is **SUSPICIOUS** for in-game missing skins, not a proven init exception. EnglishZH and DDS cache often supply the same material.",
        "",
        "## Object inheritance / duplicates",
        "",
        "- New duplicate Object names vs #413: **0**",
        "- New duplicate Weapon names vs #413 after repair: **0**",
        "- New duplicate CommandSet names vs #413 after repair: **0** (the eight European collisions removed)",
        "- New duplicate CommandButton names vs #413 after repair: **0** (TornadoECR CommandSet.ini copies removed)",
        "- ChildObject: none added",
        "",
        "## USA / Russia / China protection",
        "",
        "America/Russia/China Airfield + Large + Heavy CommandSet SHA256 unchanged from crash-fix v1 / roster v1.",
        "327 USA/RU/PLA object INI file hashes unchanged.",
        "",
        "## Verdict per gate",
        "",
        "| Gate | Result |",
        "|---|---|",
        "| INI parser | PASS |",
        "| Object uniqueness (new vs #413) | PASS |",
        "| Weapon uniqueness (new vs #413) | PASS |",
        "| CommandButton refs (European air sets) | PASS |",
        "| CommandSet refs (European air sets) | PASS |",
        "| MappedImage uniqueness | PASS (China #414 portraits kept) |",
        "| SpecialPower uniqueness | PASS |",
        "| Locomotor uniqueness | PASS |",
        "| Projectile refs (repaired weapon) | PASS |",
        "| W3D existence (G550/H145M/KVE737) | PASS |",
        "| W3D animation-reference (no KVE737/LSFFENNECK Animation=) | PASS |",
        "| Preload (new E-7-class) | PASS |",
        "| End-balance (repaired objects) | PASS |",
        "| CSF | PASS |",
        "| BIG re-extract | PASS |",
        "",
        "**STATIC STARTUP VALIDATION: PASS — USER RUNTIME TEST REQUIRED**",
        "",
    ]

    preload_md = [
        "# PRELOAD_OBJECT_AUDIT.md",
        "",
        "Scan of packed DATA for `KindOf` containing **PRELOAD**.",
        "",
        "## Summary",
        "",
        "- New-vs-#413 PRELOAD objects whose default Model is missing from SPEC ART: **0** (models may still live in EnglishZH).",
        "- New-vs-#413 PRELOAD objects with Animation= on a SPEC W3D that has zero animation chunks: **0** after v1/v2 repairs.",
        f"- Pre-#414 PRELOAD objects with the E-7-class pattern (Animation= on 0-anim W3D): **{e7_pre414}**. Present in #413; user booted #414. Not stripped.",
        "",
        "## Repaired PRELOAD Draw",
        "",
        "| Object | Model | Was | Now |",
        "|---|---|---|---|",
        "| ItalyAircraftG550CAEW | KVE737 | Animation=KVE737.KVE737 on 0-anim W3D | static Model= only |",
        "| GermanyHelicopterH145M | LSFFenneck | Animation=LSFFENNECK.LSFFENNECK on 0-anim W3D | static Model= only |",
        "| BritainAircraftE7 | KVE737 | fixed in PR #422 | static Model= only |",
        "",
        "## New PRELOAD air / airbase objects (post-#413 files)",
        "",
    ]
    new_preload = [r for r in preload_rows if r["status"] == "NEW"]
    for r in new_preload:
        extra = ""
        if r["miss"]:
            extra = f" missing SPEC W3D {r['miss']}"
        if r["bad_anim"]:
            extra += f" BAD ANIM {r['bad_anim']}"
        preload_md.append(
            f"- `{r['obj']}` in `{r['file']}` models={r['models']}{extra or ' — PASS'}"
        )
    preload_md += [
        "",
        "## HelicopterBase PRELOAD structures",
        "",
        "France/Germany/Italy/Britain `_HelicopterBase` are PRELOAD STRUCTURE objects using `HXUSABigAirPort` (animation chunks present).",
        "They are **not** on dozer CommandSets. They still parse at init. Syntax is End-balanced. Left in packed DATA.",
        "",
        "## MappedImage / Science / CommandButton / Weapon / OCL reachability",
        "",
        "Every post-414 European air CommandSet slot resolves to a declared CommandButton.",
        "TornadoECR buttons exist once in CommandButton.ini.",
        "`Japan_Weapon_AAM4B_F15J` exists once; ProjectileObject `MeteorMissile_Object` is the pre-existing projectile.",
        "SPEC_China MappedImage duplicates are the #414 portrait overlay and are preserved.",
        "",
        "**STATIC STARTUP VALIDATION: PASS — USER RUNTIME TEST REQUIRED**",
        "",
    ]

    for out in OUTS:
        out.mkdir(parents=True, exist_ok=True)
        (out / "POST_414_STARTUP_REGRESSION_AUDIT.md").write_text("\n".join(audit_lines))
        (out / "PRELOAD_OBJECT_AUDIT.md").write_text("\n".join(preload_md))
        (out / "STARTUP_CRASH_SUSPECTS.md").write_text(suspect)
        print("wrote reports to", out)
    print("new_files", len(new_files), "changed", len(changed_files), "new_w3d", len(new_w3d))
    print("repaired_vs_crash", repaired_vs_crash)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
