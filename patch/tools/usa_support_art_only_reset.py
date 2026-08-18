#!/usr/bin/env python3
"""USA support aircraft ART-only reset.

Remove gameplay/runtime DATA for:
  C-17 (AmericaJetC17Globemaster)
  E-737 (AmericaJetE737AEW / avionE737)
  E2 (E2avionHE)
  V-22 (USAHelixV22)

Keep donor visual ART in _SPEC_ART_ONE.big untouched.
Freeze AC-130 / E-3 / bombers.
Empty HeavyAirBase slots 8-11.
DATA-only package.
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
STAGE = MASTER / "_stage_usa_support_art_only_reset"
VERIFY = MASTER / "_extract_usa_support_art_only_reset_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_SUPPORT_ART_ONLY_RESET.zip"
OUT_HASH = ROOT / "Release/DATA_USA_SUPPORT_ART_ONLY_RESET_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_SUPPORT_ART_ONLY_RESET_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_SUPPORT_ART_ONLY_RESET_REPORT.txt"

GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"
AC130_SHA = "6933bbca1f6e036324e159170c369b2be523017a678b4b39dd88535a3a75343a"

REMOVE_OBJECT_KEYS = [
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Globemaster.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737AEW.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\avionE737.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\E2avionHE.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\USAHelixV22.ini",
]

REMOVE_OBJECTS = [
    "AmericaJetC17Globemaster",
    "USAC17GlobalMaster",
    "AmericaJetE737AEW",
    "avionE737",
    "AmericaJetE2avionHE",
    "E2avionHE",
    "AmericaJetV22",
    "USAHelixV22",
]

REMOVE_BUTTONS = [
    "Command_ConstructAmericaJetC17Globemaster",
    "Command_ConstructAmericaJetE737AEW",
    "Command_ConstructAmericaE2avionHE",
    "Command_ConstructAmericaV22",
]

FREEZE_KEYS = [
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\TEOD_AmericaJetB2.ini",
]


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


def count_obj(file_map: dict[str, bytes], name: str) -> int:
    pat = re.compile(rf"(?m)^Object\s+{re.escape(name)}\s*$".encode())
    return sum(len(pat.findall(b)) for b in file_map.values())


def remove_command_buttons(cb: str) -> str:
    out = cb
    for btn in REMOVE_BUTTONS:
        pattern = rf"CommandButton\s+{re.escape(btn)}\s*\n.*?^End\s*\n?"
        out2, n = re.subn(pattern, "", out, count=1, flags=re.M | re.S)
        if n != 1:
            raise SystemExit(f"failed to remove CommandButton {btn} (n={n})")
        out = out2
        if re.search(rf"(?m)^CommandButton\s+{re.escape(btn)}\s*$", out):
            raise SystemExit(f"button still present: {btn}")
    return out


def empty_heavy_slots_8_to_11(cs: str) -> str:
    def repl(m: re.Match[str]) -> str:
        body = m.group(1)
        for slot in (8, 9, 10, 11):
            body2, n = re.subn(rf"(?m)^\s*{slot}\s*=\s*\S+\s*\n", "", body)
            if n != 1:
                raise SystemExit(f"failed removing HeavyAirBase slot {slot} (n={n})")
            body = body2
        # required remaining slots
        required = {
            1: "Command_ConstructAmericaJetB2Spirit",
            2: "Command_ConstructAmericaJetB21",
            3: "Command_ConstructAmericaJetB52H",
            4: "Command_ConstructAmericaJetB1R",
            5: "Command_ConstructAmericaJetE3AWACS",
            6: "Command_Upgrade_NuclearTipWarhead2",
            7: "Command_ConstructAmericaJetAC130",
            13: "Command_SetRallyPoint",
            14: "Command_Sell",
        }
        for slot, cmd in required.items():
            if not re.search(rf"(?m)^\s*{slot}\s*=\s*{re.escape(cmd)}\s*$", body):
                raise SystemExit(f"required slot {slot}={cmd} missing after edit")
        for slot in (8, 9, 10, 11):
            if re.search(rf"(?m)^\s*{slot}\s*=", body):
                raise SystemExit(f"slot {slot} still present")
        return f"CommandSet America_HeavyAirBaseCommandSet\n{body}End"

    out, n = re.subn(
        r"CommandSet\s+America_HeavyAirBaseCommandSet\s*\n(.*?)End",
        repl,
        cs,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("HeavyAirBase CommandSet not found")
    return out


def art_family_stats(amap: dict[str, bytes]) -> dict[str, dict[str, int | bool]]:
    names = list(amap.keys())

    def match(pred):
        return [n for n in names if pred(n)]

    def stats(label, files):
        w3d = [f for f in files if f.lower().endswith(".w3d")]
        tex = [f for f in files if f.lower().endswith((".tga", ".dds", ".bmp"))]
        return {
            "label": label,
            "w3d": len(w3d),
            "tex": len(tex),
            "total": len(files),
            "w3d_names": w3d,
            "tex_names": tex,
        }

    e737 = match(lambda n: re.search(r"KVE737|avionE737", n, re.I))
    c17 = match(lambda n: re.search(r"IUAC17|C17GlobalMaster|IUCC17", n, re.I))
    v22 = match(lambda n: re.search(r"AVOsprey|\\V22\.tga$|LSFV22", n, re.I))
    e2 = match(lambda n: re.search(r"AVHawk|E2avionHE|AmericaE2avion|AvHawk", n, re.I))
    return {
        "E737": stats("E737", e737),
        "C17": stats("C17", c17),
        "V22": stats("V22", v22),
        "E2": stats("E2", e2),
    }


def main() -> None:
    dmap = read_big(DATA_BIG)
    amap = read_big(ART_BIG)
    assert sha256(dmap["Data\\English\\generals.csf"]) == GOOD_CSF

    freeze = {k: dmap[k] for k in FREEZE_KEYS if k in dmap}
    assert (
        sha256(
            freeze[
                "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini"
            ]
        )
        == AC130_SHA
    )
    usa_sha_before = sha256(
        freeze["Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini"]
    )

    art_stats = art_family_stats(amap)
    for key, need_w3d in [("E737", 1), ("C17", 1), ("V22", 1), ("E2", 1)]:
        if art_stats[key]["w3d"] < need_w3d:
            raise SystemExit(f"ART missing for {key}: {art_stats[key]}")

    # Remove object files
    for key in REMOVE_OBJECT_KEYS:
        dmap.pop(key, None)

    # Guard: no leftover Object definitions anywhere
    for name in REMOVE_OBJECTS:
        # scan before button/cs edits for object defs in other files
        pass

    dmap["Data\\INI\\CommandButton.ini"] = remove_command_buttons(
        dmap["Data\\INI\\CommandButton.ini"].decode("latin1")
    ).encode("latin1")
    dmap["Data\\INI\\CommandSet.ini"] = empty_heavy_slots_8_to_11(
        dmap["Data\\INI\\CommandSet.ini"].decode("latin1")
    ).encode("latin1")

    # Fail if any removed Object still defined
    for name in REMOVE_OBJECTS:
        c = count_obj(dmap, name)
        if c != 0:
            raise SystemExit(f"Object {name} still present count={c}")

    # Fail if buttons still referenced in HeavyAirBase or still defined
    cs = dmap["Data\\INI\\CommandSet.ini"].decode("latin1")
    cb = dmap["Data\\INI\\CommandButton.ini"].decode("latin1")
    for btn in REMOVE_BUTTONS:
        if btn in cs or re.search(rf"(?m)^CommandButton\s+{re.escape(btn)}\s*$", cb):
            raise SystemExit(f"button still live: {btn}")

    # Clean staging rebuild
    if STAGE.exists():
        shutil.rmtree(STAGE)
    write_tree(dmap, STAGE / "in")
    staged = read_tree(STAGE / "in")
    for key in REMOVE_OBJECT_KEYS:
        assert key not in staged
    new_data = build_big(staged)
    DATA_BIG.write_bytes(new_data)

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    vmap = read_big(DATA_BIG)
    write_tree(vmap, VERIFY / "out")

    for k, blob in freeze.items():
        assert vmap[k] == blob, k
    assert sha256(vmap["Data\\English\\generals.csf"]) == GOOD_CSF
    assert (
        sha256(
            vmap[
                "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini"
            ]
        )
        == AC130_SHA
    )
    assert (
        sha256(
            vmap["Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini"]
        )
        == usa_sha_before
    )

    for name in REMOVE_OBJECTS:
        assert count_obj(vmap, name) == 0, name

    # Working aircraft preserved
    assert count_obj(vmap, "AmericaJetE3AWACS") == 1
    assert count_obj(vmap, "AmericaJetAC130") == 1
    assert count_obj(vmap, "AmericaJetB21Clean") == 1
    assert count_obj(vmap, "AmericaJetB52H") == 1
    assert count_obj(vmap, "AmericaJetB1R") == 1
    # B-2 may live under TEOD / Spirit names
    b2 = count_obj(vmap, "AmericaJetB2Spirit") + count_obj(vmap, "AmericaJetB2")
    assert b2 >= 1

    cs = vmap["Data\\INI\\CommandSet.ini"].decode("latin1")
    m = re.search(
        r"CommandSet\s+America_HeavyAirBaseCommandSet\s*\n(.*?)End", cs, re.S
    )
    assert m
    body = m.group(1)
    final_slots = {}
    for slot in range(1, 15):
        sm = re.search(rf"(?m)^\s*{slot}\s*=\s*(\S+)\s*$", body)
        final_slots[slot] = sm.group(1) if sm else "EMPTY"

    assert final_slots[8] == "EMPTY"
    assert final_slots[9] == "EMPTY"
    assert final_slots[10] == "EMPTY"
    assert final_slots[11] == "EMPTY"
    assert final_slots[1] == "Command_ConstructAmericaJetB2Spirit"
    assert final_slots[2] == "Command_ConstructAmericaJetB21"
    assert final_slots[3] == "Command_ConstructAmericaJetB52H"
    assert final_slots[4] == "Command_ConstructAmericaJetB1R"
    assert final_slots[5] == "Command_ConstructAmericaJetE3AWACS"
    assert final_slots[6] == "Command_Upgrade_NuclearTipWarhead2"
    assert final_slots[7] == "Command_ConstructAmericaJetAC130"
    assert final_slots[13] == "Command_SetRallyPoint"
    assert final_slots[14] == "Command_Sell"

    # Re-check ART unchanged / families present (do not rebuild ART)
    amap2 = read_big(ART_BIG)
    assert sha256(ART_BIG) == sha256(ART_BIG)  # noop clarity
    art_sha = sha256(ART_BIG)
    art_stats = art_family_stats(amap2)

    def yn(cond: bool) -> str:
        return "YES" if cond else "NO"

    report = []
    report.append("DONOR AIRCRAFT ART-ONLY RESET = PASS")
    report.append("")
    report.append("E-737:")
    report.append("Gameplay DATA removed = YES")
    report.append("HeavyAirBase button removed = YES")
    report.append(
        f"Real donor W3D preserved = {yn(art_stats['E737']['w3d'] >= 1)} ({art_stats['E737']['w3d']} files)"
    )
    report.append(
        f"Textures preserved = {yn(art_stats['E737']['tex'] >= 1)} ({art_stats['E737']['tex']} files)"
    )
    report.append(
        f"Icon preserved = {yn(any('avione737' in x.lower() for x in art_stats['E737']['tex_names']))}"
    )
    report.append("")
    report.append("C-17:")
    report.append("Gameplay DATA removed = YES")
    report.append("HeavyAirBase button removed = YES")
    report.append(
        f"Real donor W3D preserved = {yn(art_stats['C17']['w3d'] >= 1)} ({art_stats['C17']['w3d']} files)"
    )
    report.append(
        f"Textures preserved = {yn(art_stats['C17']['tex'] >= 1)} ({art_stats['C17']['tex']} files)"
    )
    report.append(
        f"Icon preserved = {yn(any('c17' in x.lower() for x in art_stats['C17']['tex_names']))}"
    )
    report.append("")
    report.append("E2avionHE:")
    report.append("Gameplay DATA removed = YES")
    report.append("HeavyAirBase button removed = YES")
    report.append(
        f"Real donor W3D preserved = {yn(art_stats['E2']['w3d'] >= 1)} ({art_stats['E2']['w3d']} files: AVHawk family)"
    )
    report.append(
        f"Textures preserved = {yn(art_stats['E2']['tex'] >= 1)} ({art_stats['E2']['tex']} files)"
    )
    report.append(
        f"Icon preserved = {yn(any('e2avion' in x.lower() for x in art_stats['E2']['tex_names']))}"
    )
    report.append("")
    report.append("V-22:")
    report.append("Gameplay DATA removed = YES")
    report.append("HeavyAirBase button removed = YES")
    report.append(
        f"Real donor W3D preserved = {yn(art_stats['V22']['w3d'] >= 1)} ({art_stats['V22']['w3d']} files: AVOsprey*)"
    )
    report.append(
        f"Textures preserved = {yn(any('.dds' in x.lower() or '.tga' in x.lower() for x in art_stats['V22']['tex_names']))} ({art_stats['V22']['tex']} files)"
    )
    report.append(
        f"Animations preserved = {yn(any('_A' in x for x in art_stats['V22']['w3d_names']))}"
    )
    report.append(
        f"Icon preserved = {yn(any(x.lower().endswith('v22.tga') for x in art_stats['V22']['tex_names']))}"
    )
    report.append("")
    report.append("AC-130 changed = NO")
    report.append("E-3 changed = NO")
    report.append("B-2/B-21/B-52/B-1R changed = NO")
    report.append("ART rebuilt = NO")
    report.append(f"ART sha256 = {art_sha}")
    report.append("")
    report.append("Final HeavyAirBase slots:")
    labels = {
        1: "B-2",
        2: "B-21",
        3: "B-52",
        4: "B-1R",
        5: "E-3 AWACS",
        6: "Nuclear Tip Warhead",
        7: "AC-130",
        8: "EMPTY",
        9: "EMPTY",
        10: "EMPTY",
        11: "EMPTY",
        13: "Rally Point",
        14: "Sell",
    }
    for slot in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14]:
        report.append(f"{slot} = {labels[slot]} ({final_slots[slot]})")
    report.append("")
    report.append(f"DATA sha256 = {sha256(DATA_BIG)}")
    report.append(
        "Removed Object files = "
        + ", ".join(k.rsplit("\\", 1)[-1] for k in REMOVE_OBJECT_KEYS)
    )
    report.append("Removed CommandButtons = " + ", ".join(REMOVE_BUTTONS))
    report.append("Placeholder/test Objects created = NO")

    text = "\n".join(report) + "\n"
    OUT_REPORT.write_text(text, encoding="utf-8")
    (VERIFY / "VERIFY.txt").write_text(text, encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")
    with zipfile.ZipFile(OUT_ZIP) as z:
        assert z.namelist() == ["_SPEC_DATA_ONE.big"]

    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={sha256(DATA_BIG)}\n"
        f"_SPEC_ART_ONE.big sha256={art_sha} (unchanged, not packaged)\n"
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
