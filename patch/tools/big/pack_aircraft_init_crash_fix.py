#!/usr/bin/env python3
"""Pack initialization-crash fix BIGs from the current roster baseline.

Does not add aircraft. Does not change USA/Russia/China live files.
Fixes proven PRELOAD+missing-animation Draw blocks and strips duplicate
overlay INIs that were inlined into Weapon.ini / CommandSet.ini /
HandCreatedMappedImages.ini after PR #414.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pack_china_heavy_aircraft as ch
import pack_france_airforce as fr
import pack_uk_e7_boot_crash_fix as e7

ROOT = Path("/workspace")
PATCH = ROOT / "patch/Data"
BASE_DATA = Path("/tmp/final_global_roster/_SPEC_DATA_ONE.big")
BASE_ART = Path("/tmp/final_global_roster/_SPEC_ART_ONE.big")

G550_SRC = (
    PATCH
    / "INI/Object/Specter/Italian Armed Forces/Airforce/ItalyAircraftG550CAEW.ini"
)
H145_SRC = (
    PATCH
    / "INI/Object/Specter/German Armed Forces/Rotary/GermanyHelicopterH145M.ini"
)
G550_KEY = r"data\ini\object\specter\italian armed forces\airforce\italyaircraftg550caew.ini"
G550_NAME = r"Data\INI\Object\Specter\Italian Armed Forces\Airforce\ItalyAircraftG550CAEW.ini"
H145_KEY = r"data\ini\object\specter\german armed forces\rotary\germanyhelicopterh145m.ini"
H145_NAME = r"Data\INI\Object\Specter\German Armed Forces\Rotary\GermanyHelicopterH145M.ini"

PROTECT_SETS = [
    "AmericaAirfieldCommandSet",
    "America_LargeAirBaseCommandSet",
    "America_HeavyAirBaseCommandSet",
    "RussiaAirfieldCommandSet",
    "Russia_LargeAirBaseCommandSet",
    "Russia_HeavyAirBaseCommandSet",
    "PLAAirfieldCommandSet",
    "China_LargeAirBaseCommandSet",
    "China_HeavyAirBaseCommandSet",
]

# Overlay files whose definitions were also inlined into the canonical INI.
# ZH does not safely override all of these; E-7 packer already stripped
# SpecialPower_BritainAirforce.ini for the same reason.
STRIP_DUP_OVERLAYS = {
    r"data\ini\weapon_franceairforce.ini",
    r"data\ini\weapon_europeairforce.ini",
    r"data\ini\weapon_donorunusedaircraft.ini",
    r"data\ini\weapon_finalglobalairforceroster.ini",
    r"data\ini\commandbutton_donorunusedaircraft.ini",
    r"data\ini\commandbutton_finalglobalairforceroster.ini",
    r"data\ini\mappedimages\handcreated\zfrance_airbaseportrait_images.ini",
    r"data\ini\mappedimages\handcreated\zeurope_airbaseportrait_images.ini",
    r"data\ini\mappedimages\handcreated\zglobaldonor_airbaseportrait_images.ini",
    r"data\ini\mappedimages\handcreated\zfinalglobalcompletion_portrait_images.ini",
    r"data\ini\mappedimages\handcreated\znewfoldersourcefix_portrait_images.ini",
    r"data\ini\mappedimages\handcreated\zdonorunused_airbaseportrait_images.ini",
    r"data\ini\mappedimages\handcreated\zfinalglobal_airbaseportrait_images.ini",
}


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def validate_g550(text: str) -> list[str]:
    errors = []
    if text.count("Object ItalyAircraftG550CAEW") != 1:
        errors.append("G550 object count")
    if "\r" in text:
        errors.append("G550 CRLF")
    if text.startswith("\ufeff"):
        errors.append("G550 BOM")
    errors.extend(e7.balanced_end(text, "ItalyAircraftG550CAEW"))
    if re.search(r"Animation\s*=", text):
        errors.append("G550 still has Animation=")
    if "Model = KVE737" not in text:
        errors.append("G550 lost KVE737")
    if re.search(r"KindOf\s*=.*\bRADAR\b", text):
        errors.append("G550 KindOf RADAR")
    if "PRELOAD" not in text:
        errors.append("G550 lost PRELOAD")
    tags = re.findall(r"ModuleTag_\S+", text)
    if len(tags) != len(set(tags)):
        errors.append(f"G550 duplicate module tags {tags}")
    return errors


def validate_h145(text: str) -> list[str]:
    errors = []
    if text.count("Object GermanyHelicopterH145M") != 1:
        errors.append("H145 object count")
    if "\r" in text:
        errors.append("H145 CRLF")
    if text.startswith("\ufeff"):
        errors.append("H145 BOM")
    errors.extend(e7.balanced_end(text, "GermanyHelicopterH145M"))
    if re.search(r"Animation\s*=", text):
        errors.append("H145 still has Animation=")
    if "Model = LSFFenneck" not in text:
        errors.append("H145 lost LSFFenneck")
    if "ChinookAIUpdate" not in text:
        errors.append("H145 lost ChinookAIUpdate")
    if "PRELOAD" not in text:
        errors.append("H145 lost PRELOAD")
    tags = re.findall(r"ModuleTag_\S+", text)
    if len(tags) != len(set(tags)):
        errors.append(f"H145 duplicate module tags {tags}")
    return errors


def write_install(out: Path) -> None:
    (out / "INSTALL.txt").write_text(
        """SPECTER AIRCRAFT INITIALIZATION CRASH FIX

Copy both BIG files into the game folder, replacing previous Specter BIGs:

  _SPEC_DATA_ONE.big
  _SPEC_ART_ONE.big

This build keeps the post-#414 aircraft roster. It repairs the
initialization crash introduced after PR #414.

See INITIALIZATION_CRASH_FINAL_REPORT.md.

LAST KNOWN RUNTIME SAFE: #414
This package is a STATIC initialization repair. Please runtime-test in ZH.
"""
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("/tmp/aircraft_init_crash_fix"))
    args = ap.parse_args()
    out = args.out_dir
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    g550 = ch.lf(G550_SRC.read_bytes()).decode("ascii")
    h145 = ch.lf(H145_SRC.read_bytes()).decode("ascii")
    errs = validate_g550(g550) + validate_h145(h145)
    if errs:
        raise SystemExit("SOURCE FAIL\n" + "\n".join(errs))
    fr.parse_check({G550_NAME: g550.encode("ascii"), H145_NAME: h145.encode("ascii")})
    print("source parser PASS")

    data_entries, data_raw = ch.read_big(BASE_DATA)
    art_entries, art_raw = ch.read_big(BASE_ART)
    data_map: dict[str, tuple[str, bytes]] = {}
    data_keys = []
    for name, off, size in data_entries:
        key = ch.norm_key(name)
        if key not in data_map:
            data_keys.append(key)
        data_map[key] = (name.replace("/", "\\"), data_raw[off : off + size])
    art_map: dict[str, tuple[str, bytes]] = {}
    art_keys = []
    for name, off, size in art_entries:
        key = ch.norm_key(name)
        if key not in art_map:
            art_keys.append(key)
        art_map[key] = (name.replace("/", "\\"), art_raw[off : off + size])

    protect_hash = {}
    cs_probe = data_map["data\\ini\\commandset.ini"][1].decode("latin1")
    for n in PROTECT_SETS:
        protect_hash[n] = hashlib.sha256(ch.grab_block(cs_probe, n).encode("latin1")).hexdigest()
        print("protect", n, protect_hash[n][:16])

    usa_ru_cn_file_hash = {}
    for key, (name, blob) in data_map.items():
        if not key.endswith(".ini"):
            continue
        if any(
            s in key
            for s in (
                "united states of america",
                "armed forces of russian federation",
                "\\pla\\",
                "\\specter\\pla\\",
            )
        ):
            usa_ru_cn_file_hash[key] = hashlib.sha256(blob).hexdigest()
    print("protected INI files", len(usa_ru_cn_file_hash))

    if G550_KEY not in data_map:
        raise SystemExit("packed DATA missing Italy G550")
    if H145_KEY not in data_map:
        raise SystemExit("packed DATA missing Germany H145M")
    data_map[G550_KEY] = (G550_NAME, ch.lf(g550.encode("ascii")))
    data_map[H145_KEY] = (H145_NAME, ch.lf(h145.encode("ascii")))
    print("patched ItalyAircraftG550CAEW and GermanyHelicopterH145M")

    stripped = []
    for key in list(data_keys):
        if key in STRIP_DUP_OVERLAYS:
            data_keys.remove(key)
            data_map.pop(key, None)
            stripped.append(key)
            print("STRIP duplicate overlay", key)
        elif not (key.startswith("data\\") or key.startswith("art\\")):
            data_keys.remove(key)
            data_map.pop(key, None)
            stripped.append(key)
            print("STRIP orphan path", key)

    data_files = {data_map[k][0]: data_map[k][1] for k in data_keys}
    art_files = {art_map[k][0]: art_map[k][1] for k in art_keys}
    out_data = out / "_SPEC_DATA_ONE.big"
    out_art = out / "_SPEC_ART_ONE.big"
    out_data.write_bytes(ch.build_big(data_files))
    out_art.write_bytes(ch.build_big(art_files))
    dh = sha256(out_data)
    ah = sha256(out_art)
    print("DATA sha256", dh)
    print("ART sha256", ah)

    # re-extract
    extract = out / "reextract"
    extract.mkdir()
    data_x = extract / "data"
    art_x = extract / "art"
    data_x.mkdir()
    art_x.mkdir()
    n1 = 0
    v_entries, v_raw = ch.read_big(out_data)
    v_map = {}
    for name, off, size in v_entries:
        key = ch.norm_key(name)
        v_map[key] = (name, v_raw[off : off + size])
        rel = name.replace("\\", "/").lstrip("/")
        dest = data_x / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(v_raw[off : off + size])
        n1 += 1
    n2 = 0
    va_entries, va_raw = ch.read_big(out_art)
    va_w3d = set()
    for name, off, size in va_entries:
        rel = name.replace("\\", "/").lstrip("/")
        dest = art_x / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(va_raw[off : off + size])
        n2 += 1
        leaf = name.split("\\")[-1].lower()
        if leaf.endswith(".w3d"):
            va_w3d.add(leaf.replace(".w3d", ""))
    print("RE-EXTRACT DATA files", n1)
    print("RE-EXTRACT ART files", n2)

    vcs = v_map["data\\ini\\commandset.ini"][1].decode("latin1")
    for n, h in protect_hash.items():
        got = hashlib.sha256(ch.grab_block(vcs, n).encode("latin1")).hexdigest()
        if got != h:
            raise SystemExit(f"PROTECTED CommandSet changed {n}")
    print("USA/RU/CN CommandSet hash PASS")
    for key, h in usa_ru_cn_file_hash.items():
        if hashlib.sha256(v_map[key][1]).hexdigest() != h:
            raise SystemExit(f"PROTECTED file changed {key}")
    print("USA/RU/CN object INI hash PASS")

    g550_p = v_map[G550_KEY][1].decode("ascii")
    h145_p = v_map[H145_KEY][1].decode("ascii")
    errs = validate_g550(g550_p) + validate_h145(h145_p)
    if errs:
        raise SystemExit("RE-EXTRACT OBJECT FAIL\n" + "\n".join(errs))
    print("re-extract object PASS")

    # no remaining E-7-class KVE737 / Fenneck animations
    kve_anim = []
    fen_anim = []
    for key, (name, blob) in v_map.items():
        if not key.endswith(".ini"):
            continue
        t = blob.decode("latin1")
        if re.search(r"Animation\s*=\s*KVE737", t, re.I):
            kve_anim.append(name)
        if re.search(r"Animation\s*=\s*LSFFENNECK", t, re.I):
            fen_anim.append(name)
    if kve_anim:
        raise SystemExit("KVE737 Animation still present: " + ", ".join(kve_anim))
    if fen_anim:
        raise SystemExit("LSFFENNECK Animation still present: " + ", ".join(fen_anim))
    print("no KVE737/LSFFENNECK Animation leftover PASS")

    for key in STRIP_DUP_OVERLAYS:
        if key in v_map:
            raise SystemExit(f"duplicate overlay still packed {key}")
    print("duplicate overlay strip PASS")
    for key in v_map:
        if not (key.startswith("data\\") or key.startswith("art\\")):
            raise SystemExit(f"orphan path still packed {key}")
    print("orphan path strip PASS")

    if "kve737" not in va_w3d:
        raise SystemExit("ART lost KVE737")
    if "lsffenneck" not in va_w3d:
        raise SystemExit("ART lost LSFFenneck")
    print("ART models present PASS")

    write_install(out)
    # hashes
    (out / "HASHES.txt").write_text(
        f"DATA sha256 {dh}\nART sha256 {ah}\nREEXTRACT_DATA {n1}\nREEXTRACT_ART {n2}\n"
        f"STRIPPED {len(stripped)}\n"
    )
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
