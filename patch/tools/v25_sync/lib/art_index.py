"""Recursive ART index: zip members plus files inside nested SAGE BIGs.

Never returns a different stem as a stand-in for a missing file.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import archive, big, w3d

ART_SUFFIX = (".w3d", ".tga", ".dds", ".bmp", ".png", ".wav")
NESTED_BIG_PATTERNS = (
    "WYS/Textures.big",
    "WYS/W3D.big",
    "WYS/Window.big",
    "TexturesZH.big",
    "W3DZH.big",
    "W3DEnglishZH.big",
    "WindowZH.big",
    "TerrainZH.big",
    "WYS/Terrain.big",
)


def _stem(name: str) -> str:
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    if "." in base:
        return base.rsplit(".", 1)[0].lower()
    return base.lower()


class ArtIndex:
    def __init__(self, zip_path: Path | None, cache: Path, extract_root: Path | None = None):
        self.zip_path = zip_path
        self.cache = cache / "nested_bigs"
        self.cache.mkdir(parents=True, exist_ok=True)
        self.extract_root = extract_root
        self.stems: dict[str, list[dict]] = {}
        self.nested_bigs_indexed: list[str] = []
        self._indexed_paths: set[str] = set()
        self._tex_cache: dict[str, list[str]] = {}
        self._anim_cache: dict[str, list[str]] = {}
        self._w3d_cache: dict[str, bytes | None] = {}
        if zip_path:
            self._index_zip_members()
            self._extract_and_index_nested_bigs()
        if extract_root:
            self._index_extracted_bigs(extract_root)
        (cache / "art_index_meta.json").write_text(
            json.dumps({"stems": len(self.stems), "nested_bigs": self.nested_bigs_indexed}) + "\n"
        )

    def index_big(self, path: Path, container: str) -> None:
        """Index one nested BIG. Public so tests can skip the V25 zip."""
        self._index_big_file(path, container)

    def _add(self, stem: str, rec: dict) -> None:
        bucket = self.stems.setdefault(stem.lower(), [])
        key = (rec.get("container"), rec.get("inner") or rec.get("path"), rec.get("local_path"))
        if any((x.get("container"), x.get("inner") or x.get("path"), x.get("local_path")) == key for x in bucket):
            return
        bucket.append(rec)

    def _index_zip_members(self) -> None:
        listing = archive.list_archive(self.zip_path)
        for line in listing.splitlines():
            if "Generals Silent Death V25/" not in line:
                continue
            path = line[line.index("Generals Silent Death V25/") :]
            if path.endswith("/") or path.endswith("\\"):
                continue
            low = path.lower()
            if not any(low.endswith(s) for s in ART_SUFFIX + (".big",)):
                continue
            self._add(
                _stem(path),
                {
                    "container": "zip",
                    "path": path,
                    "inner": None,
                    "filename": path.replace("\\", "/").rsplit("/", 1)[-1],
                    "source_big": None,
                    "local_path": None,
                },
            )

    def _extract_and_index_nested_bigs(self) -> None:
        if not self.zip_path:
            return
        missing = []
        for rel in NESTED_BIG_PATTERNS:
            dest = self.cache / rel.replace("/", "_")
            if not dest.is_file():
                missing.append(f"Generals Silent Death V25/{rel}")
        if missing:
            archive.extract(self.zip_path, self.cache, missing)
        for rel in NESTED_BIG_PATTERNS:
            member = f"Generals Silent Death V25/{rel}"
            dest = self.cache / rel.replace("/", "_")
            found = dest if dest.is_file() else None
            if found is None:
                matches = [p for p in self.cache.rglob(Path(rel).name) if p.is_file()]
                if matches:
                    found = matches[0]
            if found is not None:
                self._index_big_file(found, container=member)

    def _index_extracted_bigs(self, root: Path) -> None:
        for bp in root.rglob("*.big"):
            rel = str(bp.relative_to(root)).replace("\\", "/")
            if any(rel.endswith(p.split("/")[-1]) for p in NESTED_BIG_PATTERNS) or "WYS" in rel:
                self._index_big_file(bp, container=rel)

    def _index_big_file(self, path: Path, container: str) -> None:
        key = str(path.resolve()) if path.exists() else str(path)
        if key in self._indexed_paths:
            return
        self._indexed_paths.add(key)
        self.nested_bigs_indexed.append(container)
        for name, blob in big.iter_big(path, lambda n: big.nkey(n).endswith(".big")):
            if blob:
                nested_path = self.cache / (container.replace("/", "_") + "_" + big.basename(name))
                if not nested_path.is_file():
                    nested_path.write_bytes(blob)
                self._index_big_file(nested_path, container=f"{container}::{name}")
        for name, _blob in big.iter_big(path, lambda n: False):
            low = big.nkey(name)
            if not any(low.endswith(s) for s in ART_SUFFIX):
                continue
            self._add(
                big.stem_lower(name),
                {
                    "container": "nested_big",
                    "path": container,
                    "inner": name,
                    "filename": big.basename(name),
                    "source_big": container,
                    "local_path": str(path),
                },
            )

    def find(self, name: str) -> list[dict]:
        """Exact stem match only. Never substitutes a similarly named file."""
        if not name:
            return []
        return list(self.stems.get(_stem(name), []))

    def read_w3d(self, name: str) -> bytes | None:
        stem = _stem(name)
        if stem in self._w3d_cache:
            return self._w3d_cache[stem]
        blob = self._read_w3d_uncached(name)
        self._w3d_cache[stem] = blob
        return blob

    def _read_w3d_uncached(self, name: str) -> bytes | None:
        hits = [h for h in self.find(name) if str(h.get("inner") or h.get("path") or "").lower().endswith(".w3d")]
        if not hits:
            hits = [h for h in self.find(name) if name.lower().endswith(".w3d")]
        for rec in hits:
            if rec.get("container") == "zip" and rec.get("path") and str(rec["path"]).lower().endswith(".w3d"):
                dest = self.cache / Path(rec["path"]).name
                if not dest.is_file() and self.zip_path:
                    archive.extract(self.zip_path, self.cache, [rec["path"]])
                    found = list(self.cache.rglob(Path(rec["path"]).name))
                    if found:
                        return found[0].read_bytes()
                elif dest.is_file():
                    return dest.read_bytes()
            if rec.get("container") == "nested_big":
                blob = self._read_nested(rec)
                if blob:
                    return blob
        return None

    def _read_nested(self, rec: dict) -> bytes | None:
        inner = rec.get("inner")
        if not inner:
            return None
        big_path = Path(rec["local_path"]) if rec.get("local_path") else None
        if big_path is None or not big_path.is_file():
            container = rec.get("path") or rec.get("source_big") or ""
            cand = self.cache / str(container).replace("/", "_")
            if cand.is_file():
                big_path = cand
        if big_path is None or not big_path.is_file():
            return None
        want = inner.replace("/", "\\").lower()

        def match(n: str, _want=want) -> bool:
            return big.nkey(n) == _want or big.nkey(n).endswith(_want)

        for _name, blob in big.iter_big(big_path, match):
            if blob:
                return blob
        return None

    def textures_in_w3d(self, model_name: str) -> list[str]:
        stem = _stem(model_name)
        if stem in self._tex_cache:
            return self._tex_cache[stem]
        blob = self.read_w3d(model_name)
        found = w3d.texture_names(blob) if blob else []
        self._tex_cache[stem] = found
        return found

    def animations_in_w3d(self, model_name: str) -> list[str]:
        stem = _stem(model_name)
        if stem in self._anim_cache:
            return self._anim_cache[stem]
        blob = self.read_w3d(model_name)
        found = w3d.animation_names(blob) if blob else []
        self._anim_cache[stem] = found
        return found
