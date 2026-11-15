#!/usr/bin/env python3
"""Extract V25 W3D/textures required by the Russia CC + independent War Factory pack."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

TOOL = Path(__file__).resolve().parent
ART = TOOL / "art"
W3D_DIR = ART / "W3D"
TEX_DIR = ART / "Textures"
ZIP_PATH = Path("/tmp/v25_src/ V25.zip")

W3DS = [
    "RUS350.W3D",
    "RUS350RD.W3D",
    "INTGSK.W3D",
    "INTGSKw.W3D",
    "UR9S32.W3D",
    "UR9S32w.W3D",
    "URS300V.W3D",
    "URS300Vw.W3D",
    "UR9S18M1.W3D",
    "UR9S18M1w.W3D",
    "RUS400.W3D",
    "SD40V6MD.W3D",
    "RUBALE.W3D",
    "RU9K33.W3D",
    "30N6EFL.W3D",
    "UR9K31.W3D",
    "NKZSU23.W3D",
    "NKZSU23w.W3D",
    "RU9A52.W3D",
    "BUKMM3.W3D",
    "BUKMM3w.W3D",
    "RUS500.W3D",
    "RUMTLB.W3D",
    "RUMTLBw.W3D",
    "RUK300.W3D",
    "StructureHamVhe.W3D",
    "CWCruTSS.W3D",
    "CWCruTSS_d.W3D",
    "CWCruTSS_k.W3D",
]

CAMEOS = [
    "RUS350TB.tga",
    "50N6ATB.tga",
    "URTGSKTB.tga",
    "9S32TB.tga",
    "RUS300VMTB.tga",
    "RU9S18M1TB.tga",
    "RUS400TB.tga",
    "40V6MDTB.tga",
    "BALETB.tga",
    "9K33TB.tga",
    "30N6EFLTB.tga",
    "RY9K31TB.tga",
    "RUZSU4TB.tga",
    "9A52TB.tga",
    "Bukmm3TB.tga",
    "RUS500TB.tga",
    "RUMTLBTB2.tga",
    "RUK300TB.tga",
    "RUWARFCIII.tga",
    "RUchechangTB.tga",
]


def extract(names: list[str], dest: Path) -> list[str]:
    dest.mkdir(parents=True, exist_ok=True)
    missing = []
    for name in names:
        dst = dest / name
        if dst.is_file() and dst.stat().st_size > 0:
            continue
        rc = subprocess.run(
            ["7z", "e", "-y", f"-o{dest}", str(ZIP_PATH), f"*{name}", "-r"],
            check=False,
            capture_output=True,
            text=True,
        )
        found = list(dest.glob(name)) + list(dest.glob(name.replace(".W3D", ".w3d")))
        if not found:
            # 7z may write mixed-case
            for p in dest.iterdir():
                if p.name.lower() == name.lower():
                    p.rename(dest / name)
                    found = [dest / name]
                    break
        if not found:
            missing.append(name)
            print(rc.stdout[-400:] if rc.stdout else rc.stderr[-400:])
    return missing


def textures_from_w3d(path: Path) -> set[str]:
    data = path.read_bytes()
    names = set()
    for m in re.finditer(rb"[\w\-\.]{3,64}\.(dds|tga|DDS|TGA)", data):
        names.add(m.group(0).decode("latin1"))
    return names


def main() -> int:
    if not ZIP_PATH.is_file():
        raise SystemExit(f"missing {ZIP_PATH}")
    miss_w3d = extract(W3DS, W3D_DIR)
    miss_cam = extract(CAMEOS, TEX_DIR)
    tex_names: set[str] = set()
    for w3d in sorted(W3D_DIR.glob("*.W3D")):
        tex_names |= textures_from_w3d(w3d)
    skip = {"EXTireTrack.tga", "EXTnkTrack.tga", "EXTireTrack2.tga"}
    wanted = [n for n in sorted(tex_names) if n not in skip and not n.lower().startswith("tex_")]
    miss_tex = extract(wanted, TEX_DIR)
    print("W3D present:")
    for p in sorted(W3D_DIR.glob("*.W3D")):
        print(f"  {p.name} {p.stat().st_size}")
    print("missing W3D", miss_w3d)
    print("missing cameos", miss_cam)
    print("missing textures", miss_tex)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
