"""First real V25 → SS1 transfer of a small READY group.

Writes only to an independent output directory. Original SPECTER FINAL BIGs
are never opened for write. No loose INI. Generals.exe is not run.
"""
from __future__ import annotations

from pathlib import Path

from . import big, catalog, data_rebuild
from .art_prove import prove_object_art, read_art_blob, _stem
from .pack_sample import (
    HEADER_RE,
    construct_button,
    mapped_image_from_texture,
    tga_or_dds_size,
)
from .pack_ready import assemble_ready_payloads
from .preflight import native_def_index, preflight_payloads
from .ss1_layout import emit_path, path_is_protected, path_loadable

PREFERRED = (
    "ChinaS75",
    "ChinaZFB05",
    "SX250Transport",
    "AGS17GrenadeLauncher",
    "Mk19GrenadeLauncher",
    "ChinaVehicleListeningOutpost",
    "ChinaHQ7Radar",
    "ChinaCSSC8",
)
MAX_GROUP = 3

SIDE_FACTORY = {
    "China": ("ChinaWarFactory", "PLAWarFactoryCommandSet", ("4", "7", "15")),
    "America": ("AmericaWarFactory", "AmericaWarFactoryCommandSet", ("18",)),
    "Russia": ("RussiaWarFactory", "RussiaWarFactoryCommandSet", ("13", "15", "16")),
}


def select_ready_rows(cat_rows: list[dict], names: tuple[str, ...] = PREFERRED) -> list[dict]:
    by = {r["object"]: r for r in cat_rows}
    out = []
    for n in names:
        row = by.get(n)
        if row and row.get("ready_for_safe_transfer") and row.get("status") == "unique_import_ready":
            out.append(row)
    return out


def factory_overlay(cs_name: str, specter_cs: dict, fills: dict[str, str]) -> str:
    lines = [f"CommandSet {cs_name}"]
    slots = {k.strip(): v.strip() for k, v in (specter_cs.get("keys") or []) if k.strip().isdigit()}
    for slot, btn in fills.items():
        if slot in slots:
            raise ValueError(f"refusing to overwrite occupied factory slot {slot}")
        slots[slot] = btn
    for num in sorted(slots, key=lambda x: int(x)):
        lines.append(f"  {num} = {slots[num]}")
    lines += [
        "End",
        "",
        f"; Overlay of SPECTER {cs_name} via unique last-win path.",
        "; Original Data\\INI\\CommandSet.ini is not modified.",
        "",
    ]
    return "\n".join(lines)


def portrait_stem(art_refs: list[str]) -> str | None:
    for a in art_refs:
        st = _stem(a)
        if st.endswith("tb"):
            return a
    return None


def art_dest_from_filename(filename: str) -> str:
    from .pack_sample import art_dest_path

    return art_dest_path(filename)


def validate_first_transfer(
    added_data: dict[str, bytes],
    added_art: dict[str, bytes],
    proved: list[dict],
    factory_note: list[dict],
) -> dict:
    errors: list[str] = []
    blocked = {p.replace("/", "\\").lower() for p in data_rebuild.PUBLIC_INI_BLOCKED}
    objects = {p["row"]["object"] for p in proved}
    planned = {p["row"]["object"]: (p.get("planned") or p["row"]["object"]) for p in proved}

    for path in added_data:
        n = big.nkey(path)
        if n in blocked:
            errors.append(f"protected public INI path added: {path}")
        if n.endswith(".ini"):
            load = path_loadable(path)
            if not load.get("loaded") or load.get("confidence") != "proven":
                errors.append(f"unproven dest: {path} {load}")
            if path_is_protected(path):
                errors.append(f"protected dest: {path}")

    found_objects: set[str] = set()
    found_buttons: set[str] = set()
    for path, blob in added_data.items():
        if not big.nkey(path).endswith(".ini"):
            continue
        text = blob.decode("latin1", errors="replace") if isinstance(blob, (bytes, bytearray)) else blob
        for m in HEADER_RE.finditer(text):
            kind, name = m.group(1), m.group(2)
            if kind.lower() == "object":
                found_objects.add(name)
            if kind.lower() == "commandbutton":
                found_buttons.add(name)

    for p in proved:
        want = p.get("planned") or p["row"]["object"]
        if want not in found_objects:
            errors.append(f"missing Object {want} in added DATA")
        btn = f"SD25_Command_Construct{p['row']['object']}"
        if btn not in found_buttons:
            errors.append(f"missing construct button {btn}")

    w3d_names = [n for n in added_art if n.lower().endswith(".w3d")]
    if not w3d_names:
        errors.append("no W3D recovered into experimental ART TWO")
    tex_names = [n for n in added_art if n.lower().endswith((".tga", ".dds"))]
    if not tex_names:
        errors.append("no textures recovered into experimental ART TWO")

    for note in factory_note:
        cs = note.get("commandset")
        overlay_path = emit_path("CommandSet", "x", note.get("side") or "China")
        text = (added_data.get(overlay_path) or b"").decode("latin1", errors="replace")
        if cs and f"CommandSet {cs}" not in text:
            errors.append(f"factory overlay missing CommandSet {cs}")
        for slot, btn in (note.get("fills") or {}).items():
            if f"{slot} = {btn}" not in text:
                errors.append(f"factory slot {slot} missing {btn}")

    return {
        "ok": not errors,
        "errors": errors,
        "objects": sorted(objects),
        "planned": planned,
        "w3d": len(w3d_names),
        "textures": len(tex_names),
        "generals_exe_run": False,
    }


class FirstTransfer:
    def __init__(self, engine, art, zip_path: Path | None, out_dir: Path):
        self.eng = engine
        self.art = art
        self.zip_path = zip_path
        self.out_dir = Path(out_dir)
        self.protected = {p.replace("/", "\\").lower() for p in (engine.protected.get("ini_paths") or [])}

    def run(self, cat_rows: list[dict]) -> dict:
        orig_data = self.eng.ss1 / "_SPEC_DATA_ONE.big"
        orig_art = self.eng.ss1 / "_SPEC_ART_TWO.big"
        if not orig_data.is_file() or not orig_art.is_file():
            raise FileNotFoundError("SPECTER FINAL BIGs not found")
        dest_root = self.out_dir
        dest_root.mkdir(parents=True, exist_ok=True)
        dest_data = dest_root / "_SPEC_DATA_ONE.big"
        dest_art = dest_root / "_SPEC_ART_TWO.big"
        if dest_data.resolve() == orig_data.resolve() or dest_art.resolve() == orig_art.resolve():
            raise ValueError("refusing to write over original SPECTER BIGs")
        if dest_root.resolve() == orig_data.parent.resolve():
            raise ValueError("refusing to write experimental pack into the original SPECTER FINAL folder")

        from .engine import sha256_file

        before = {
            "_SPEC_DATA_ONE.big": sha256_file(orig_data),
            "_SPEC_ART_TWO.big": sha256_file(orig_art),
        }
        v25 = self.eng.inventory_v25()
        spec = self.eng.inventory_specter()
        spec_idx = catalog._index(spec)
        cache: dict = {}
        rows = select_ready_rows(cat_rows)
        ss1_art_names = {big.nkey(n) for n in big.list_names(orig_art)}
        ss1_art_stems = {big.stem_lower(n) for n in big.list_names(orig_art)}
        ss1_data_names = {big.nkey(n) for n in big.list_names(orig_data)}

        proved = []
        skipped = []
        for row in rows:
            name = row["object"]
            rec = catalog._lookup_rec(v25, "Object", name)
            if rec is None or not row.get("ready_for_safe_transfer"):
                skipped.append({"object": name, "reason": "not READY"})
                continue
            art = prove_object_art(
                name, v25, spec_idx, cache, self.art, self.zip_path, ss1_art_stems, ss1_art_names
            )
            if not art.get("ok"):
                skipped.append({"object": name, "reason": "incomplete_art", "missing": art.get("missing")})
                continue
            proved.append({"row": row, "rec": rec, "art": art})
            if len(proved) >= MAX_GROUP:
                break

        install_ready = False
        factory_note: list[dict] = []
        objects_out = []
        added_data: dict[str, bytes] = {}
        added_art: dict[str, bytes] = {}
        emitted: list[dict] = []
        validation = {"ok": False, "errors": ["no complete READY+ART group"]}

        if len(proved) >= 2:
            ready_rows = [p["row"] for p in proved]
            assembled = assemble_ready_payloads(ready_rows, v25, spec, spec_idx, cache)
            payloads = dict(assembled["payloads"])

            buttons: list[str] = []
            mapped: list[str] = []
            by_side: dict[str, list[tuple[str, str]]] = {}
            for i, p in enumerate(proved):
                row, rec, art = p["row"], p["rec"], p["art"]
                planned = assembled["objects"][i]["planned_name"]
                p["planned"] = planned
                btn = f"SD25_Command_Construct{row['object']}"
                side = row.get("side") or "China"
                by_side.setdefault(side, []).append((btn, planned))
                port = portrait_stem(rec.get("art_refs") or []) or "SNComand"
                image = _stem(port).upper() if port else "SNComand"
                buttons.append(construct_button(btn, planned, image, f"CONTROLBAR:SD25_{row['object']}"))
                objects_out.append(
                    {
                        "v25_object": row["object"],
                        "ss1_name": planned,
                        "dest_ini": assembled["objects"][i]["dest_ini"],
                        "side": side,
                        "needs_normalize": bool(row.get("needs_normalize")),
                        "rename": planned != row["object"],
                        "art": art.get("recovered"),
                        "missing_art": art.get("missing"),
                        "data_deps": (
                            catalog.walk_object_chain("Object", row["object"], v25, spec_idx, cache).get("visited") or []
                        )[:80],
                    }
                )

            for side, items in by_side.items():
                fac = SIDE_FACTORY.get(side)
                if not fac:
                    continue
                obj_name, cs_name, slots = fac
                spec_cs = catalog._lookup_rec(spec, "CommandSet", cs_name)
                if spec_cs is None:
                    continue
                fills = {}
                for slot, (btn, _planned) in zip(slots, items):
                    fills[slot] = btn
                cs_path = emit_path("CommandSet", "x", side)
                payloads[cs_path] = (payloads.get(cs_path) or "") + "\n" + factory_overlay(cs_name, spec_cs, fills)
                factory_note.append(
                    {
                        "side": side,
                        "object": obj_name,
                        "commandset": cs_name,
                        "slots": list(fills),
                        "fills": fills,
                    }
                )
            payloads[r"Data\INI\CommandButton_SilentDeath.ini"] = (
                (payloads.get(r"Data\INI\CommandButton_SilentDeath.ini") or "") + "\n" + "\n".join(buttons)
            )

            existing = ss1_art_names | ss1_data_names
            for p in proved:
                for rec in p["art"].get("recovered") or []:
                    if rec.get("action") != "RECOVER_FROM_V25":
                        emitted.append(rec)
                        continue
                    blob, filename, _hit = read_art_blob(self.art, self.zip_path, rec["from"])
                    if not blob:
                        continue
                    dest = rec.get("to") or art_dest_from_filename(filename)
                    already = big.nkey(dest) in existing or big.nkey(dest) in {
                        big.nkey(n) for n in added_art
                    } | {big.nkey(n) for n in added_data}
                    if already:
                        emitted.append({**rec, "action": "REUSE_NATIVE"})
                        continue
                    if dest.replace("/", "\\").lower().startswith("data\\"):
                        added_data[dest] = blob
                    else:
                        added_art[dest] = blob
                    emitted.append({**rec, "to": dest, "bytes": len(blob)})
                    st = Path(filename).stem.lower()
                    if st.endswith("tb") and filename.lower().endswith((".tga", ".dds")):
                        w, h = tga_or_dds_size(blob)
                        mapped.append(mapped_image_from_texture(Path(filename).stem, Path(filename).name, w, h))

            if mapped:
                mi_path = emit_path("MappedImage", "x")
                payloads[mi_path] = (payloads.get(mi_path) or "") + "\n" + "\n".join(mapped)

            for path, text in payloads.items():
                if path_is_protected(path):
                    raise ValueError(f"protected dest: {path}")
                load = path_loadable(path)
                if not load.get("loaded") or load.get("confidence") != "proven":
                    raise ValueError(f"unproven dest: {path} {load}")
                added_data[path] = text.encode("latin1", errors="replace")

            native = native_def_index(spec)
            pf = preflight_payloads(
                {
                    k: v.decode("latin1", errors="replace") if isinstance(v, (bytes, bytearray)) else v
                    for k, v in added_data.items()
                    if k.lower().endswith(".ini")
                },
                native_defs=native,
            )
            validation = validate_first_transfer(added_data, added_art, proved, factory_note)
            if not pf.get("ok"):
                validation = {"ok": False, "errors": (pf.get("errors") or [])[:12], "preflight": pf}
            install_ready = bool(validation.get("ok") and added_art and added_data and len(proved) >= 2)

            if validation.get("ok"):
                data_info = big.copy_big_with_adds(orig_data, dest_data, added_data, self.protected)
                art_info = big.copy_big_with_adds(orig_art, dest_art, added_art, set())
            else:
                data_info = {}
                art_info = {}
        else:
            assembled = {"objects": [], "payloads": {}}
            data_info = {}
            art_info = {}
            skipped.append(
                {
                    "object": "*",
                    "reason": "fewer_than_two_complete_units",
                    "proved": [p["row"]["object"] for p in proved],
                }
            )

        after = {
            "_SPEC_DATA_ONE.big": sha256_file(orig_data),
            "_SPEC_ART_TWO.big": sha256_file(orig_art),
        }
        if after != before:
            raise RuntimeError("Original SPECTER FINAL hashes changed")

        exp_hashes = {}
        if dest_data.is_file():
            exp_hashes["_SPEC_DATA_ONE.big"] = sha256_file(dest_data)
        if dest_art.is_file():
            exp_hashes["_SPEC_ART_TWO.big"] = sha256_file(dest_art)

        report = {
            "mode": "first-transfer",
            "applies_to_original_specter": False,
            "game_bigs_modified": False,
            "original_hashes_unchanged": after == before,
            "original_hashes": after,
            "experimental_hashes": exp_hashes,
            "generals_exe_run": False,
            "loose_ini_written": False,
            "equipment_imported": False,
            "install_ready": install_ready,
            "objects": objects_out,
            "skipped": skipped,
            "added_data_names": sorted(added_data),
            "added_art_names": sorted(added_art),
            "emitted": emitted[:80],
            "validation": {
                "ok": validation.get("ok"),
                "errors": validation.get("errors") or [],
            },
            "factories": factory_note if len(proved) >= 2 else [],
            "data_big": data_info,
            "art_big": art_info,
            "experimental_dest": str(dest_root),
            "note": (
                "Independent DATA+ART copy of a small Ready-Gate group with proven W3D/textures. "
                "Original SS1 BIGs untouched. Generals.exe was not run."
            ),
        }
        self._write_install_docs(dest_root, report)
        return report

    def _write_install_docs(self, dest: Path, report: dict) -> None:
        orig = report.get("original_hashes") or {}
        exp = report.get("experimental_hashes") or {}
        ready = report.get("install_ready")
        lines = [
            "SPECTER FINAL — Silent Death V25 first transfer (independent copy).",
            "Original SPECTER FINAL is not modified by this packer.",
            "",
            "Generals.exe was NOT run. This is not an in-game test report.",
            f"Install-ready (DATA preflight + ART bytes recovered): {ready}",
            "",
        ]
        if ready:
            lines += [
                "Install (replace the two BIGs in the SPECTER FINAL folder):",
                "  1. Quit the game.",
                "  2. Backup the originals:",
                "       copy _SPEC_DATA_ONE.big _SPEC_DATA_ONE.big.bak",
                "       copy _SPEC_ART_TWO.big _SPEC_ART_TWO.big.bak",
                "  3. Copy these files from this ZIP over the SPECTER FINAL folder:",
                "       _SPEC_DATA_ONE.big",
                "       _SPEC_ART_TWO.big",
                "  4. Do not add loose Data\\INI files. This pack is BIG-only.",
                "",
                "Factory overlays (empty slots only, unique last-win CommandSet):",
            ]
            for fac in report.get("factories") or []:
                lines.append(
                    f"  - {fac.get('side')} {fac.get('commandset')} slots {fac.get('slots')}"
                )
            for obj in report.get("objects") or []:
                lines.append(f"  - {obj.get('v25_object')} → {obj.get('ss1_name')} ({obj.get('side')})")
            lines += [
                "",
                "Expected original SHA256 (before replace):",
                f"  _SPEC_DATA_ONE.big  {orig.get('_SPEC_DATA_ONE.big')}",
                f"  _SPEC_ART_TWO.big   {orig.get('_SPEC_ART_TWO.big')}",
                "",
                "This pack SHA256:",
                f"  _SPEC_DATA_ONE.big  {exp.get('_SPEC_DATA_ONE.big')}",
                f"  _SPEC_ART_TWO.big   {exp.get('_SPEC_ART_TWO.big')}",
                "",
            ]
        else:
            lines += [
                "This pack is NOT presented as install-ready: ART or DATA was incomplete.",
                "Do not copy these files over SPECTER FINAL.",
                "",
            ]
        (dest / "INSTALL.txt").write_text("\n".join(lines), encoding="utf-8")
        (dest / "REVERT.txt").write_text(
            "\n".join(
                [
                    "Revert first-transfer pack — restore SPECTER FINAL originals.",
                    "",
                    "  1. Quit the game.",
                    "  2. Restore backups:",
                    "       copy /Y _SPEC_DATA_ONE.big.bak _SPEC_DATA_ONE.big",
                    "       copy /Y _SPEC_ART_TWO.big.bak  _SPEC_ART_TWO.big",
                    f"  3. Original hashes: DATA {orig.get('_SPEC_DATA_ONE.big')} ART TWO {orig.get('_SPEC_ART_TWO.big')}",
                    "  4. There are no loose INI to remove.",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        from .engine import sha256_file

        sums = []
        for name in ("_SPEC_DATA_ONE.big", "_SPEC_ART_TWO.big", "INSTALL.txt", "REVERT.txt"):
            p = dest / name
            if p.is_file():
                sums.append(f"{sha256_file(p)}  {name}")
        (dest / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")
