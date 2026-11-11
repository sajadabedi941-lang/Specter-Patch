"""Prove W3D + texture bytes for a READY object chain. No SS1 writes."""
from __future__ import annotations

from pathlib import Path

from . import archive, catalog, w3d
from .pack_sample import _is_w3d_subobject, _pick_hit, art_dest_path, vfs_dest_from_rec
from .ss1_layout import path_loadable

SKIP_ART_STEMS = {
    "ssattackmove2",
    "sdguard",
    "sdstop",
    "aliasconditionstate",
    "reallydamaged",
    "sncomand",
}

# CommandButton/MappedImage/AudioEvent are UI/audio, not W3D install art.
MODEL_ART_KINDS = {
    "Object",
    "Weapon",
    "Projectile",
    "Upgrade",
    "ObjectCreationList",
    "ParticleSystem",
    "Draw",
}


def _stem(name: str) -> str:
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    if "." in base:
        ext = base.rsplit(".", 1)[-1].lower()
        if ext in {"tga", "dds", "w3d", "wav", "bmp"}:
            return base.rsplit(".", 1)[0].lower()
        # Model.Anim lives inside the W3D; prove the model stem only.
        return base.split(".", 1)[0].lower()
    return base.lower()


def collect_chain_art(name: str, v25: dict, spec_idx: dict, cache: dict) -> list[str]:
    chain = catalog.walk_object_chain("Object", name, v25, spec_idx, cache)
    stems: list[str] = []
    seen: set[str] = set()
    for item in chain.get("visited") or []:
        if ":" not in item:
            continue
        kind, dep = item.split(":", 1)
        rec = catalog._lookup_rec(v25, kind, dep)
        if rec is None:
            continue
        if kind not in MODEL_ART_KINDS:
            continue
        for a in rec.get("art_refs") or []:
            if _is_w3d_subobject(a):
                continue
            st = _stem(a)
            if st in SKIP_ART_STEMS or st in seen:
                continue
            seen.add(st)
            stems.append(a)
    return stems


def read_art_blob(art, zip_path: Path | None, name: str) -> tuple[bytes | None, str, dict | None]:
    hits = art.find(name) if art else []
    rec = _pick_hit(hits, name)
    if rec:
        filename = rec.get("filename") or (name if "." in name else f"{name}.w3d")
        blob = None
        if rec.get("container") == "zip" and rec.get("path") and zip_path:
            dest = Path("/tmp/v25_sync_cache/first_transfer_art")
            dest.mkdir(parents=True, exist_ok=True)
            archive.extract(zip_path, dest, [rec["path"]])
            found = list(dest.rglob(Path(rec["path"]).name))
            if found:
                blob = found[0].read_bytes()
        elif rec.get("container") == "nested_big":
            blob = art._read_nested(rec)
        if blob:
            return blob, filename, rec
    extract = Path("/tmp/v25_extract/Generals Silent Death V25")
    stem = name.split(".")[0]
    for folder, ext in (
        ("Art/W3D", ".W3D"),
        ("Art/Textures", ".tga"),
        ("Art/Textures", ".dds"),
        ("Data/Audio/Sounds", ".wav"),
    ):
        folder_p = extract.joinpath(folder)
        if folder_p.is_dir():
            for cand in folder_p.glob(stem + ".*"):
                return cand.read_bytes(), cand.name, None
        p = extract / folder / f"{stem}{ext}"
        if p.is_file():
            return p.read_bytes(), p.name, None
    return None, name, None


def prove_object_art(
    name: str,
    v25: dict,
    spec_idx: dict,
    cache: dict,
    art,
    zip_path: Path | None,
    ss1_art_stems: set[str],
    ss1_art_names: set[str],
) -> dict:
    """Exact-stem ART proof. Missing W3D or texture is not READY for install."""
    wanted = collect_chain_art(name, v25, spec_idx, cache)
    recovered: list[dict] = []
    missing: list[str] = []
    reused: list[str] = []
    textures_needed: list[str] = []
    seen_tex: set[str] = set()

    def handle(stem_name: str, kind_hint: str) -> None:
        st = _stem(stem_name)
        if st in SKIP_ART_STEMS:
            return
        blob, filename, rec = read_art_blob(art, zip_path, stem_name)
        dest = vfs_dest_from_rec(filename, rec) if rec else art_dest_path(filename)
        load = path_loadable(dest) if dest.lower().endswith(".wav") else {
            "loaded": dest.replace("/", "\\").lower().startswith(("art\\w3d\\", "art\\textures\\")),
            "confidence": "proven" if dest.replace("/", "\\").lower().startswith(("art\\w3d\\", "art\\textures\\")) else "unlikely",
        }
        if st in ss1_art_stems and not blob:
            reused.append(stem_name)
            recovered.append(
                {
                    "from": stem_name,
                    "to": dest,
                    "action": "REUSE_NATIVE",
                    "bytes": 0,
                    "kind": kind_hint,
                }
            )
            return
        if not blob:
            missing.append(stem_name)
            return
        recovered.append(
            {
                "from": stem_name,
                "to": dest,
                "action": "RECOVER_FROM_V25",
                "bytes": len(blob),
                "kind": kind_hint,
                "filename": filename,
                "loadable": bool(load.get("loaded")),
            }
        )
        if filename.lower().endswith(".w3d"):
            for tex in w3d.texture_names(blob):
                tstem = _stem(tex)
                if tstem in seen_tex:
                    continue
                seen_tex.add(tstem)
                textures_needed.append(tex)

    for a in wanted:
        handle(a, "model_or_texture")
    for tex in list(textures_needed):
        handle(tex, "w3d_texture")

    ok = not missing
    return {
        "object": name,
        "ok": ok,
        "wanted": wanted,
        "recovered": recovered,
        "reused_ss1": reused,
        "missing": missing,
        "textures_from_w3d": textures_needed,
        "generals_exe_run": False,
        "ss1_art_name_hits": [n for n in wanted if _stem(n) in {s.lower() for s in ss1_art_names}],
    }
