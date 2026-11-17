"""Locate, verify, and extract Generals Silent Death V25 split ZIPs."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

VOL_RE = re.compile(r"^V25(?:\.zip|\.z(\d+))$", re.I)


def _norm_name(path: Path) -> str:
    return path.name.strip()


def find_volumes(search_dirs: list[Path]) -> dict[int, Path]:
    """Return {0: V25.zip, 1: V25.z01, ...} from dirs. Leading spaces in names are ignored."""
    found: dict[int, Path] = {}
    for d in search_dirs:
        if not d or not d.is_dir():
            continue
        for p in d.iterdir():
            if not p.is_file():
                continue
            m = VOL_RE.match(_norm_name(p))
            if not m:
                continue
            idx = 0 if _norm_name(p).lower() == "v25.zip" else int(m.group(1))
            # Prefer the larger/newer copy if duplicates exist.
            prev = found.get(idx)
            if prev is None or p.stat().st_size >= prev.stat().st_size:
                found[idx] = p
    return found


def volume_health(vols: dict[int, Path]) -> dict:
    idxs = sorted(vols)
    missing = [i for i in range(0, (max(idxs) if idxs else -1) + 1) if i not in vols]
    # Official Silent Death V25 zip is zip + z01..z157 = 158 volumes.
    expected = list(range(0, 158))
    missing_expected = [i for i in expected if i not in vols]
    extra = [i for i in idxs if i not in expected]
    return {
        "count": len(vols),
        "min": idxs[0] if idxs else None,
        "max": idxs[-1] if idxs else None,
        "expected_volumes": 158,
        "missing_expected": missing_expected,
        "extra_volumes": extra,
        "complete_for_7z": missing_expected == [],
        "names": {str(i): str(vols[i]) for i in idxs},
        "bytes": sum(p.stat().st_size for p in vols.values()),
    }


def stage_volumes(vols: dict[int, Path], dest: Path) -> Path:
    """Copy/symlink volumes into dest with canonical names (no leading space)."""
    dest.mkdir(parents=True, exist_ok=True)
    zip_path = dest / "V25.zip"
    for idx, src in vols.items():
        name = "V25.zip" if idx == 0 else f"V25.z{idx:02d}" if idx < 100 else f"V25.z{idx}"
        # Keep 7z naming: V25.z01 not V25.z1
        if idx == 0:
            name = "V25.zip"
        elif idx < 10:
            name = f"V25.z0{idx}"
        else:
            name = f"V25.z{idx}"
        target = dest / name
        if target.exists() and target.stat().st_size == src.stat().st_size:
            continue
        if target.exists() or target.is_symlink():
            target.unlink()
        try:
            target.symlink_to(src.resolve())
        except OSError:
            shutil.copy2(src, target)
    return zip_path if zip_path.exists() else dest / "V25.zip"


def sevenz() -> str:
    for cand in ("7z", "7za", "7zr"):
        if shutil.which(cand):
            return cand
    raise FileNotFoundError("7z is required to read V25 volumes")


def test_archive(zip_path: Path) -> dict:
    cmd = [sevenz(), "t", str(zip_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    ok = proc.returncode == 0 and "Everything is Ok" in out
    return {"ok": ok, "returncode": proc.returncode, "tail": "\n".join(out.splitlines()[-30:])}


def list_archive(zip_path: Path) -> str:
    proc = subprocess.run([sevenz(), "l", str(zip_path)], capture_output=True, text=True)
    return (proc.stdout or "") + (proc.stderr or "")


def extract(zip_path: Path, dest: Path, patterns: list[str] | None = None) -> dict:
    dest.mkdir(parents=True, exist_ok=True)
    cmd = [sevenz(), "x", "-y", f"-o{dest}", str(zip_path)]
    if patterns:
        cmd.extend(patterns)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    return {
        "ok": proc.returncode == 0 and "Everything is Ok" in out,
        "returncode": proc.returncode,
        "tail": "\n".join(out.splitlines()[-40:]),
    }
