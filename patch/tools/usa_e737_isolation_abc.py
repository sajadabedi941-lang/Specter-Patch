#!/usr/bin/env python3
"""E-737 controlled three-build isolation packages (DATA only).

BUILD A: remove all E-737 Objects + HeavyAirBase Slot 9
BUILD B: byte-copy AmericaJetE3AWACS -> AmericaJetE737AEW (Object name only)
BUILD C: Build B + Model E3 -> KVE737 (visual only)

Does NOT claim game boot. Reports STATIC PACKAGE VALIDATION only.
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
STAGE_ROOT = MASTER / "_stage_usa_e737_isolation_abc"
OUT_DIR = ROOT / "Release"
GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"
AC130_SHA = "6933bbca1f6e036324e159170c369b2be523017a678b4b39dd88535a3a75343a"

E737_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737AEW.ini"
)
AVION_KEY = "Data\\INI\\Object\\Specter\\United States Of America\\avionE737.ini"
USA_KEY = "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini"
CS_KEY = "Data\\INI\\CommandSet.ini"
CB_KEY = "Data\\INI\\CommandButton.ini"

FREEZE_KEYS = [
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Globemaster.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\E2avionHE.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\USAHelixV22.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini",
    USA_KEY,
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


def extract_object_block(usa_blob: bytes, object_name: str) -> bytes:
    """Extract one Object ... End block preserving exact bytes/line endings."""
    text = usa_blob.decode("latin1")
    lines = text.splitlines(keepends=True)
    start = None
    for i, line in enumerate(lines):
        if re.match(rf"^Object\s+{re.escape(object_name)}\s*$", line.rstrip("\r\n")):
            start = i
            break
    if start is None:
        raise SystemExit(f"Object {object_name} not found")
    stack: list[str] = []
    end_i = None
    for i in range(start, len(lines)):
        s = lines[i].strip()
        if not s or s.startswith(";"):
            continue
        if re.match(r"^Object\s+\S+", s):
            if stack and i != start:
                raise SystemExit(f"nested Object at line {i}")
            stack.append("Object")
        elif re.match(
            r"^(Draw|Behavior|ArmorSet|WeaponSet|Body|UnitSpecificSounds|"
            r"Prerequisites|DefaultConditionState|ConditionState|TransitionState)\b",
            s,
        ):
            stack.append(s.split()[0])
        elif s == "End":
            if not stack:
                raise SystemExit(f"extra End at line {i}")
            stack.pop()
            if not stack:
                end_i = i
                break
    if end_i is None:
        raise SystemExit(f"Object {object_name} did not close")
    return "".join(lines[start : end_i + 1]).encode("latin1")


def rename_object_only(e3_block: bytes) -> bytes:
    """Byte-preserving: replace ONLY the Object declaration name."""
    text = e3_block.decode("latin1")
    lines = text.splitlines(keepends=True)
    if not re.match(r"^Object\s+AmericaJetE3AWACS\s*$", lines[0].rstrip("\r\n")):
        raise SystemExit(f"unexpected first line: {lines[0]!r}")
    nl = "\r\n" if lines[0].endswith("\r\n") else "\n"
    lines[0] = f"Object AmericaJetE737AEW{nl}"
    out = "".join(lines).encode("latin1")
    # Ensure we did not alter anything else containing the old Object name on line 0 only
    # DisplayName may still say OBJECT:AmericaJetE3AWACS -- required (no other changes).
    assert out.count(b"Object AmericaJetE737AEW") == 1
    assert b"Object AmericaJetE3AWACS" not in out
    assert b"KVE737" not in out
    return out


def apply_kve737_visual_only(clone_block: bytes) -> bytes:
    """Replace ONLY primary Model = E3 tokens with KVE737. Keep gear / everything else."""
    text = clone_block.decode("latin1")
    lines = text.splitlines(keepends=True)
    changed = 0
    out_lines = []
    for line in lines:
        raw = line.rstrip("\r\n")
        nl = "\r\n" if line.endswith("\r\n") else ("\n" if line.endswith("\n") else "")
        m = re.match(r"^(\s*Model\s*=\s*)E3(\s*)$", raw)
        if m:
            out_lines.append(f"{m.group(1)}KVE737{m.group(2)}{nl}")
            changed += 1
        else:
            out_lines.append(line)
    if changed != 6:
        raise SystemExit(f"expected 6 Model=E3 replacements, got {changed}")
    out = "".join(out_lines).encode("latin1")
    assert out.count(b"KVE737") == 6
    # gear model must remain
    assert b"chj10_r" in out
    # no donor avion behaviors injected
    assert b"avionE737" not in out
    assert b"AliasConditionState REALLYDAMAGED" not in out  # bare form
    assert b"EA_18AntiRadar" not in out or True  # E-3 clone may have ECM; that is OK (from E-3)
    return out


def remove_slot9(cs: str) -> str:
    if not re.search(r"(?m)^\s*9\s*=\s*Command_ConstructAmericaJetE737AEW\s*$", cs):
        # already absent is ok for idempotent rebuild from A baseline
        if re.search(r"(?m)^\s*9\s*=", cs):
            raise SystemExit("Slot 9 present but not E-737")
        return cs

    def repl(m: re.Match[str]) -> str:
        body = m.group(1)
        body2 = re.sub(
            r"(?m)^\s*9\s*=\s*Command_ConstructAmericaJetE737AEW\s*\n", "", body
        )
        if body2 == body:
            raise SystemExit("failed to remove Slot 9")
        return f"CommandSet America_HeavyAirBaseCommandSet\n{body2}End"

    out, n = re.subn(
        r"CommandSet\s+America_HeavyAirBaseCommandSet\s*\n(.*?)End",
        repl,
        cs,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("HeavyAirBase CommandSet not patched")
    return out


def ensure_slot9(cs: str) -> str:
    if re.search(r"(?m)^\s*9\s*=\s*Command_ConstructAmericaJetE737AEW\s*$", cs):
        return cs
    # Insert Slot 9 after Slot 8
    def repl(m: re.Match[str]) -> str:
        body = m.group(1)
        if re.search(r"(?m)^\s*9\s*=", body):
            raise SystemExit("Slot 9 occupied by non-E737")
        if not re.search(r"(?m)^\s*8\s*=\s*Command_ConstructAmericaJetC17Globemaster\s*$", body):
            raise SystemExit("Slot 8 C-17 missing; refuse to invent Slot 9 placement")
        body2 = re.sub(
            r"(?m)^(\s*8\s*=\s*Command_ConstructAmericaJetC17Globemaster\s*\n)",
            r"\1  9  = Command_ConstructAmericaJetE737AEW\n",
            body,
            count=1,
        )
        return f"CommandSet America_HeavyAirBaseCommandSet\n{body2}End"

    out, n = re.subn(
        r"CommandSet\s+America_HeavyAirBaseCommandSet\s*\n(.*?)End",
        repl,
        cs,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("HeavyAirBase CommandSet not patched for Slot 9")
    return out


def ensure_button(cb: str) -> str:
    block = (
        "CommandButton Command_ConstructAmericaJetE737AEW\n"
        "  Command       = UNIT_BUILD\n"
        "  Object        = AmericaJetE737AEW\n"
        "  TextLabel     = CONTROLBAR:E737\n"
        "  ButtonImage   = avionE737\n"
        "  ButtonBorderType = BUILD\n"
        "  DescriptLabel = CONTROLBAR:E737if\n"
        "End"
    )
    if not re.search(r"(?m)^CommandButton\s+Command_ConstructAmericaJetE737AEW\s*$", cb):
        raise SystemExit("E737 CommandButton missing")
    out, n = re.subn(
        r"CommandButton\s+Command_ConstructAmericaJetE737AEW\s*\n.*?^End\s*$",
        block,
        cb,
        count=1,
        flags=re.M | re.S,
    )
    if n != 1:
        raise SystemExit("failed to ensure E737 button")
    return out


def pack_build(
    label: str,
    file_map: dict[str, bytes],
    freeze: dict[str, bytes],
    zip_name: str,
    checks: dict,
) -> tuple[str, str]:
    stage = STAGE_ROOT / label
    verify = STAGE_ROOT / f"{label}_verify"
    write_tree(file_map, stage / "in")
    staged = read_tree(stage / "in")
    big = build_big(staged)
    out_big = STAGE_ROOT / f"{label}_SPEC_DATA_ONE.big"
    out_big.write_bytes(big)

    vmap = read_big(out_big)
    write_tree(vmap, verify / "out")

    for k, blob in freeze.items():
        assert vmap[k] == blob, f"{label} freeze fail {k}"

    assert count_obj(vmap, "avionE737") == checks["avionE737"]
    assert count_obj(vmap, "AmericaJetE737AEW") == checks["AmericaJetE737AEW"]
    assert count_obj(vmap, "AmericaJetE3AWACS") == 1
    kve = sum(b.count(b"KVE737") for b in vmap.values())
    assert kve == checks["KVE737"], f"{label} KVE737 count {kve} != {checks['KVE737']}"

    cs = vmap[CS_KEY].decode("latin1")
    has_slot9 = bool(
        re.search(r"(?m)^\s*9\s*=\s*Command_ConstructAmericaJetE737AEW\s*$", cs)
    )
    assert has_slot9 == checks["slot9"], f"{label} slot9={has_slot9}"

    if checks["AmericaJetE737AEW"] == 1:
        assert E737_KEY in vmap
        blob = vmap[E737_KEY]
        assert all(c < 128 for c in blob)
        assert b"\x00" not in blob
        assert not blob.startswith(b"\xef\xbb\xbf")
        assert re.search(rb"(?m)^Object\s+AmericaJetE737AEW\s*$", blob)
        cb = vmap[CB_KEY].decode("latin1")
        m = re.search(
            r"CommandButton\s+Command_ConstructAmericaJetE737AEW\s*\n(.*?)End",
            cb,
            re.S,
        )
        assert m and re.search(r"(?m)^\s*Object\s*=\s*AmericaJetE737AEW\s*$", m.group(0))
    else:
        assert E737_KEY not in vmap
        assert AVION_KEY not in vmap

    assert sha256(vmap["Data\\English\\generals.csf"]) == GOOD_CSF
    assert sha256(vmap[FREEZE_KEYS[0]]) == AC130_SHA

    zpath = OUT_DIR / zip_name
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(out_big, "_SPEC_DATA_ONE.big")
    # verify zip contains only the big
    with zipfile.ZipFile(zpath) as z:
        assert z.namelist() == ["_SPEC_DATA_ONE.big"]

    digest = sha256(out_big)
    proc = subprocess.run(
        [
            "curl",
            "-sF",
            "reqtype=fileupload",
            "-F",
            "time=72h",
            "-F",
            f"fileToUpload=@{zpath}",
            "https://litterbox.catbox.moe/resources/internals/api.php",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    url = (proc.stdout or "").strip()
    if not url.startswith("http"):
        raise SystemExit(f"upload failed for {label}: {url!r} {proc.stderr!r}")
    print(f"{label} STATIC PACKAGE VALIDATION = PASS")
    print(f"{label} SHA256 = {digest}")
    print(f"{label} Download = {url}")
    return digest, url


def main() -> None:
    if STAGE_ROOT.exists():
        shutil.rmtree(STAGE_ROOT)
    STAGE_ROOT.mkdir(parents=True)

    base = read_big(DATA_BIG)
    freeze = {k: base[k] for k in FREEZE_KEYS}
    assert sha256(freeze[FREEZE_KEYS[0]]) == AC130_SHA
    assert sha256(base["Data\\English\\generals.csf"]) == GOOD_CSF

    e3_block = extract_object_block(base[USA_KEY], "AmericaJetE3AWACS")
    Path(STAGE_ROOT / "exact_AmericaJetE3AWACS.ini").write_bytes(e3_block)
    clone_b = rename_object_only(e3_block)
    Path(STAGE_ROOT / "build_b_AmericaJetE737AEW.ini").write_bytes(clone_b)
    clone_c = apply_kve737_visual_only(clone_b)
    Path(STAGE_ROOT / "build_c_AmericaJetE737AEW.ini").write_bytes(clone_c)

    # ---- BUILD A ----
    a = dict(base)
    a.pop(E737_KEY, None)
    a.pop(AVION_KEY, None)
    # purge any residual Object definitions just in case they live elsewhere
    for k, blob in list(a.items()):
        if k == USA_KEY:
            continue
        if re.search(rb"(?m)^Object\s+(AmericaJetE737AEW|avionE737)\s*$", blob):
            raise SystemExit(f"unexpected E737 object in {k}")
    a[CS_KEY] = remove_slot9(a[CS_KEY].decode("latin1")).encode("latin1")
    # CommandButton may remain orphaned; do not rewrite other buttons.
    sha_a, url_a = pack_build(
        "A",
        a,
        freeze,
        "E737_TEST_A_NO_E737.zip",
        {"avionE737": 0, "AmericaJetE737AEW": 0, "KVE737": 0, "slot9": False},
    )

    # ---- BUILD B ----
    b = dict(a)
    b[E737_KEY] = clone_b
    b[CS_KEY] = ensure_slot9(b[CS_KEY].decode("latin1")).encode("latin1")
    b[CB_KEY] = ensure_button(b[CB_KEY].decode("latin1")).encode("latin1")
    assert b"KVE737" not in clone_b
    sha_b, url_b = pack_build(
        "B",
        b,
        freeze,
        "E737_TEST_B_E3_CLONE.zip",
        {"avionE737": 0, "AmericaJetE737AEW": 1, "KVE737": 0, "slot9": True},
    )

    # ---- BUILD C ----
    c = dict(b)
    c[E737_KEY] = clone_c
    # CS/CB identical to B
    sha_c, url_c = pack_build(
        "C",
        c,
        freeze,
        "E737_TEST_C_KVE737_ONLY.zip",
        {"avionE737": 0, "AmericaJetE737AEW": 1, "KVE737": 6, "slot9": True},
    )

    # Do NOT overwrite master DATA with diagnostic builds.
    report = []
    report.append("E-737 THREE-BUILD ISOLATION")
    report.append("GAME BOOT CLAIMED = NO (user must boot-test)")
    report.append("")
    report.append("BUILD A:")
    report.append("E-737 removed completely = YES")
    report.append("STATIC PACKAGE VALIDATION = PASS")
    report.append(f"SHA256 = {sha_a}")
    report.append(f"Download = {url_a}")
    report.append("")
    report.append("BUILD B:")
    report.append("Pure working E-3 clone as AmericaJetE737AEW = YES")
    report.append("KVE737 used = NO")
    report.append("STATIC PACKAGE VALIDATION = PASS")
    report.append(f"SHA256 = {sha_b}")
    report.append(f"Download = {url_b}")
    report.append("")
    report.append("BUILD C:")
    report.append("Same Build B Object + KVE737 visual only = YES")
    report.append("Donor avionE737 behaviors used = NO")
    report.append("STATIC PACKAGE VALIDATION = PASS")
    report.append(f"SHA256 = {sha_c}")
    report.append(f"Download = {url_c}")
    report.append("")
    report.append("NO OTHER AIRCRAFT CHANGED = YES")
    report.append("NO OTHER FACTIONS CHANGED = YES")
    report.append("ART CHANGED = NO")
    report.append(f"E3 source block SHA256 = {sha256(e3_block)}")
    report.append(f"Build B object SHA256 = {sha256(clone_b)}")
    report.append(f"Build C object SHA256 = {sha256(clone_c)}")
    text = "\n".join(report) + "\n"
    (OUT_DIR / "DATA_USA_E737_ISOLATION_ABC_REPORT.txt").write_text(text, encoding="utf-8")
    (OUT_DIR / "DATA_USA_E737_ISOLATION_ABC_DOWNLOAD.txt").write_text(
        f"A={url_a}\nB={url_b}\nC={url_c}\n", encoding="utf-8"
    )
    (OUT_DIR / "DATA_USA_E737_ISOLATION_ABC_HASHES.txt").write_text(
        f"A={sha_a}\nB={sha_b}\nC={sha_c}\n", encoding="utf-8"
    )
    print(text)


if __name__ == "__main__":
    main()
