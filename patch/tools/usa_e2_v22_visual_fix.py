#!/usr/bin/env python3
"""Fix E-2 Scale (match E-737) + V-22 complete Osprey Draw (DATA only).

Does not modify C-17 / E-737 / E-3 / AC-130 / bombers.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
OBJ_DIR = ROOT / "Data/INI/Object/Specter/United States Of America"
STAGE = MASTER / "_stage_usa_e2_v22_visual_fix"
VERIFY = MASTER / "_extract_usa_e2_v22_visual_fix_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_E2_V22_VISUAL_FIX.zip"
OUT_HASH = ROOT / "Release/DATA_USA_E2_V22_VISUAL_FIX_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_E2_V22_VISUAL_FIX_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_E2_V22_VISUAL_FIX_REPORT.txt"

GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"
AC130_SHA = "6933bbca1f6e036324e159170c369b2be523017a678b4b39dd88535a3a75343a"

UPDATE = {
    "AmericaJetE2Visual.ini": "AmericaJetE2Visual",
    "AmericaJetV22Visual.ini": "AmericaJetV22Visual",
}
FREEZE_FILES = [
    "AmericaJetE3Visual.ini",
    "AmericaJetE737Visual.ini",
    "AmericaJetC17Visual.ini",
    "AmericaJetAC130.ini",
    "AmericaJetB21Clean.ini",
]
OSPREY_W3D = [
    "AVOsprey",
    "AVOsprey_D",
    "AVOsprey_A1",
    "AVOsprey_A2",
    "AVOsprey_A3",
    "AVOsprey_A4",
    "AVOsprey_DA1",
    "AVOsprey_DA2",
    "AVOsprey_DA3",
    "AVOsprey_DA4",
]
OSPREY_TEX = ["AVOsprey.dds", "AVOsprey_D.dds", "AVOsprey_H.dds", "AVOsprey_P.dds"]


def sha256(b: bytes | Path) -> str:
    data = b if isinstance(b, bytes) else Path(b).read_bytes()
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    assert data[:4] == b"BIGF"
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    out: dict[str, bytes] = {}
    for _ in range(n):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        out[name.replace("/", "\\")] = data[off : off + size]
    return out


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16 + sum(8 + len(n.encode("latin1")) + 1 for n, _ in items)
    offset = header_size
    index, blobs = [], []
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">III", offset, len(items), header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for b in blobs:
        out += b
    return bytes(out)


def write_tree(file_map: dict[str, bytes], root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    for name, content in file_map.items():
        path = root / name.replace("\\", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def read_tree(root: Path) -> dict[str, bytes]:
    out = {}
    for p in root.rglob("*"):
        if p.is_file():
            out[str(p.relative_to(root)).replace("/", "\\")] = p.read_bytes()
    return out


def structure_ok(blob: bytes, obj: str) -> None:
    assert all(c < 128 for c in blob), f"{obj} non-ASCII"
    assert b"\x00" not in blob
    assert not blob.startswith(b"\xef\xbb\xbf")
    text = blob.decode("ascii")
    assert len(re.findall(r"(?m)^Object\s+\S+", text)) == 1
    assert re.search(rf"(?m)^Object\s+{re.escape(obj)}\s*$", text)
    assert not re.search(r"(?m)^\s*WeaponSet\b", text)
    assert "TransportContain" not in text
    assert "ChinookAIUpdate" not in text
    stack: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith(";"):
            continue
        if s.startswith("Object "):
            stack = ["Object"]
        elif re.match(
            r"^(Draw|Behavior|ArmorSet|WeaponSet|Body|UnitSpecificSounds|"
            r"Prerequisites|DefaultConditionState|ConditionState|TransitionState)\b",
            s,
        ):
            stack.append(s.split()[0])
        elif s == "End":
            assert stack, f"{obj} extra End"
            stack.pop()
    assert stack == [], f"{obj} unclosed {stack}"


def get_scale(text: str) -> str:
    m = re.search(r"(?m)^\s*Scale\s*=\s*(\S+)\s*$", text)
    return m.group(1) if m else "(none / default 1.0)"


def main() -> None:
    dmap = read_big(DATA_BIG)
    amap = read_big(ART_BIG)
    assert sha256(dmap["Data\\English\\generals.csf"]) == GOOD_CSF
    art_sha = sha256(ART_BIG)

    freeze = {}
    for fn in FREEZE_FILES:
        k = f"Data\\INI\\Object\\Specter\\United States Of America\\{fn}"
        freeze[k] = dmap[k]
    freeze_ac = (
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini"
    )
    assert sha256(freeze[freeze_ac]) == AC130_SHA
    usa_key = "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini"
    freeze[usa_key] = dmap[usa_key]
    cs_key = "Data\\INI\\CommandSet.ini"
    freeze[cs_key] = dmap[cs_key]

    e737_key = (
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737Visual.ini"
    )
    e737_text = dmap[e737_key].decode("latin1")
    e737_scale = get_scale(e737_text)
    assert e737_scale == "0.8"

    e2_old_key = (
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE2Visual.ini"
    )
    e2_old_scale = get_scale(dmap[e2_old_key].decode("latin1"))

    v22_old = dmap[
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetV22Visual.ini"
    ].decode("latin1")
    # old incomplete: single Draw animating body with A1
    old_primary = "AVOsprey (single Draw; A1 animation wrongly on body)"

    for w3d in OSPREY_W3D:
        key = f"Art\\W3D\\{w3d}.W3D"
        assert key in amap, f"missing {key}"
    for tex in OSPREY_TEX:
        key = f"Art\\Textures\\{tex}"
        assert key in amap, f"missing {key}"

    for fn, obj in UPDATE.items():
        blob = (OBJ_DIR / fn).read_bytes()
        text = blob.decode("utf-8")
        assert all(ord(c) < 128 for c in text)
        blob = text.replace("\r\n", "\n").encode("ascii")
        structure_ok(blob, obj)
        key = f"Data\\INI\\Object\\Specter\\United States Of America\\{fn}"
        dmap[key] = blob

    e2_new = dmap[e2_old_key].decode("ascii")
    e2_new_scale = get_scale(e2_new)
    assert e2_new_scale == "0.8"
    assert "Model = AVHawk" in e2_new

    v22_new = dmap[
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetV22Visual.ini"
    ].decode("ascii")
    assert "ModuleTag_Engines01" in v22_new
    assert "AVOsprey_A4" in v22_new and "AVOsprey_A1" in v22_new
    assert "AVOsprey_DA4" in v22_new
    # body must NOT use A1 animation on fuselage alone
    body_draw = re.search(
        r"Draw = W3DModelDraw ModuleTag_01\n(.*?)End\n\n  Draw = W3DModelDraw ModuleTag_Engines01",
        v22_new,
        re.S,
    )
    assert body_draw
    assert "AVOsprey_A1" not in body_draw.group(1)
    assert "Model = AVOsprey" in body_draw.group(1)

    # slots unchanged
    cs = dmap[cs_key].decode("latin1")
    for slot, btn in [
        (5, "E3Visual"),
        (8, "C17Visual"),
        (9, "E737Visual"),
        (10, "E2Visual"),
        (11, "V22Visual"),
    ]:
        assert re.search(
            rf"(?m)^\s*{slot}\s*=\s*Command_ConstructAmericaJet{btn}\s*$", cs
        )

    if STAGE.exists():
        shutil.rmtree(STAGE)
    write_tree(dmap, STAGE / "in")
    staged = read_tree(STAGE / "in")
    new_data = build_big(staged)
    DATA_BIG.write_bytes(new_data)

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    vmap = read_big(DATA_BIG)
    write_tree(vmap, VERIFY / "out")

    for k, blob in freeze.items():
        assert vmap[k] == blob, k
    assert sha256(ART_BIG) == art_sha
    assert sha256(vmap["Data\\English\\generals.csf"]) == GOOD_CSF

    for fn, obj in UPDATE.items():
        key = f"Data\\INI\\Object\\Specter\\United States Of America\\{fn}"
        structure_ok(vmap[key], obj)

    # ensure other visual aircraft unchanged
    for fn in ["AmericaJetE3Visual.ini", "AmericaJetE737Visual.ini", "AmericaJetC17Visual.ini"]:
        k = f"Data\\INI\\Object\\Specter\\United States Of America\\{fn}"
        assert vmap[k] == freeze[k]

    report = []
    report.append("E2 + V22 VISUAL FIX = PASS")
    report.append("")
    report.append("E-2:")
    report.append("Object = AmericaJetE2Visual")
    report.append("W3D = AVHawk")
    report.append(f"E-737 scale = {e737_scale}")
    report.append(f"E-2 old scale = {e2_old_scale}")
    report.append(f"E-2 new scale = {e2_new_scale}")
    report.append("Matches E-737 scale method = YES")
    report.append("")
    report.append("V-22:")
    report.append("Object = AmericaJetV22Visual")
    report.append(f"Old primary visual = {old_primary}")
    report.append(
        "Correct donor primary visual = AVOsprey body Draw + AVOsprey_A*/_DA* engines/rotors Draw"
    )
    report.append("Complete AVOsprey family found = YES")
    report.append("")
    report.append("Required W3Ds =")
    for w in OSPREY_W3D:
        report.append(f"  Art\\W3D\\{w}.W3D")
    report.append("Required textures =")
    for t in OSPREY_TEX:
        report.append(f"  Art\\Textures\\{t}")
    report.append("Required animations =")
    for w in [
        "AVOsprey_A1",
        "AVOsprey_A2",
        "AVOsprey_A3",
        "AVOsprey_A4",
        "AVOsprey_DA1",
        "AVOsprey_DA2",
        "AVOsprey_DA3",
        "AVOsprey_DA4",
    ]:
        report.append(f"  {w}.W3D / {w}.{w}")
    report.append("")
    report.append("Both rotors included = YES (ModuleTag_Engines01 AVOsprey_A* family)")
    report.append("Both nacelles included = YES (same engines Draw)")
    report.append("Complete fuselage = YES (ModuleTag_01 AVOsprey)")
    report.append("Donor DATA imported = NO")
    report.append("")
    report.append("C-17 changed = NO")
    report.append("E-737 changed = NO")
    report.append("E-3 changed = NO")
    report.append("AC-130 changed = NO")
    report.append("Bombers changed = NO")
    report.append("Other factions changed = NO")
    report.append("ART rebuilt = NO")
    report.append(f"DATA sha256 = {sha256(DATA_BIG)}")

    text = "\n".join(report) + "\n"
    OUT_REPORT.write_text(text, encoding="utf-8")
    (VERIFY / "VERIFY.txt").write_text(text, encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")
    with zipfile.ZipFile(OUT_ZIP) as z:
        assert z.namelist() == ["_SPEC_DATA_ONE.big"]

    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={sha256(DATA_BIG)}\n"
        f"_SPEC_ART_ONE.big sha256={art_sha} (unchanged)\n"
        f"ZIP={OUT_ZIP.name}\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            "curl",
            "-sF",
            "reqtype=fileupload",
            "-F",
            "time=72h",
            "-F",
            f"fileToUpload=@{OUT_ZIP}",
            "https://litterbox.catbox.moe/resources/internals/api.php",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    url = (proc.stdout or "").strip()
    if not url.startswith("http"):
        raise SystemExit(f"upload failed: {url!r} {proc.stderr!r}")
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    print(text)
    print("Download =", url)


if __name__ == "__main__":
    main()
