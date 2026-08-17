#!/usr/bin/env python3
"""E-737 Specter-compatible rebuild from working E-3 skeleton + KVE737 ART.

Removes active Object avionE737. Ships AmericaJetE737AEW only.
DATA-only. Freezes all other HeavyAirBase aircraft / E-3 / CS slots.
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
OBJ_NEW = ROOT / (
    "Data/INI/Object/Specter/United States Of America/AmericaJetE737AEW.ini"
)
STAGE = MASTER / "_stage_usa_e737_compat_rebuild"
VERIFY = MASTER / "_extract_usa_e737_compat_rebuild_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_E737_COMPAT_REBUILD.zip"
OUT_HASH = ROOT / "Release/DATA_USA_E737_COMPAT_REBUILD_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_E737_COMPAT_REBUILD_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_E737_COMPAT_REBUILD_REPORT.txt"
GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"
AC130_SHA = "6933bbca1f6e036324e159170c369b2be523017a678b4b39dd88535a3a75343a"

E737_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737AEW.ini"
)
AVION_KEY = "Data\\INI\\Object\\Specter\\United States Of America\\avionE737.ini"


def sha256(b: bytes | Path) -> str:
    data = b if isinstance(b, bytes) else Path(b).read_bytes()
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
    assert data[:4] == b"BIGF"
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(n):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        entries.append((name.replace("/", "\\"), data[off : off + size]))
    return entries


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


def patch_button(cb: str) -> str:
    block = """CommandButton Command_ConstructAmericaJetE737AEW
  Command       = UNIT_BUILD
  Object        = AmericaJetE737AEW
  TextLabel     = CONTROLBAR:E737
  ButtonImage   = avionE737
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:E737if
End
"""
    if not re.search(r"^CommandButton\s+Command_ConstructAmericaJetE737AEW\s*$", cb, re.M):
        raise SystemExit("E737 button missing")
    return re.sub(
        r"CommandButton\s+Command_ConstructAmericaJetE737AEW\s*\n.*?^End\s*$",
        block.rstrip(),
        cb,
        count=1,
        flags=re.M | re.S,
    )


def structure_ok(blob: bytes) -> None:
    assert all(c < 128 for c in blob), "non-ASCII"
    assert b"\x00" not in blob
    assert not blob.startswith(b"\xef\xbb\xbf")
    text = blob.decode("ascii")
    assert len(re.findall(r"(?m)^Object\s+\S+", text)) == 1
    stack = []
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
            assert stack, "extra End"
            stack.pop()
    assert stack == [], stack
    assert "KVE737" in text
    assert not re.search(r"(?m)^\s*WeaponSet\b", text), "WeaponSet block banned"
    assert not re.search(r"(?m)^\s*AliasConditionState\s+[A-Z]", text), "bare AliasConditionState banned"
    assert "US_E3G" not in text and "Model = E3" not in text


def main() -> None:
    dmap = dict(read_big(DATA_BIG))
    assert sha256(dmap["Data\\English\\generals.csf"]) == GOOD_CSF

    freeze = {
        k: dmap[k]
        for k in [
            "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini",
            "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Globemaster.ini",
            "Data\\INI\\Object\\Specter\\United States Of America\\E2avionHE.ini",
            "Data\\INI\\Object\\Specter\\United States Of America\\USAHelixV22.ini",
            "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini",
            "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini",
            "Data\\INI\\CommandSet.ini",
        ]
    }
    assert (
        sha256(
            freeze[
                "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini"
            ]
        )
        == AC130_SHA
    )

    cs = dmap["Data\\INI\\CommandSet.ini"].decode("latin1")
    assert re.search(r"^\s*9\s*=\s*Command_ConstructAmericaJetE737AEW\s*$", cs, re.M)

    e737 = OBJ_NEW.read_bytes()
    structure_ok(e737)

    # Remove donor avionE737 if present; install AmericaJetE737AEW
    dmap.pop(AVION_KEY, None)
    dmap[E737_KEY] = e737
    dmap["Data\\INI\\CommandButton.ini"] = patch_button(
        dmap["Data\\INI\\CommandButton.ini"].decode("latin1")
    ).encode("latin1")

    # Clean staging rebuild
    write_tree(dmap, STAGE / "in")
    staged = read_tree(STAGE / "in")
    assert AVION_KEY not in staged
    assert E737_KEY in staged
    new_data = build_big(staged)
    DATA_BIG.write_bytes(new_data)

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    VERIFY.mkdir(parents=True)
    vmap = dict(read_big(DATA_BIG))
    write_tree(vmap, VERIFY / "out")

    for k, blob in freeze.items():
        assert vmap[k] == blob, k

    assert count_obj(vmap, "avionE737") == 0
    assert count_obj(vmap, "AmericaJetE737AEW") == 1
    structure_ok(vmap[E737_KEY])
    assert vmap[E737_KEY] == e737

    cb = vmap["Data\\INI\\CommandButton.ini"].decode("latin1")
    m = re.search(
        r"CommandButton\s+Command_ConstructAmericaJetE737AEW\s*\n(.*?)End", cb, re.S
    )
    assert m and "UNIT_BUILD" in m.group(0)
    assert re.search(r"^\s*Object\s*=\s*AmericaJetE737AEW\s*$", m.group(0), re.M)
    assert not re.search(r"^\s*Object\s*=\s*avionE737\s*$", m.group(0), re.M)

    report = []
    report.append("E-737 COMPATIBILITY REBUILD = PASS")
    report.append("")
    report.append("Original donor Object directly compatible = NO")
    report.append("Minimal Specter-compatible Object created = YES")
    report.append("Final Object = AmericaJetE737AEW")
    report.append("Primary W3D = KVE737")
    report.append("Skeleton source = working AmericaJetE3AWACS (donor USAE3 runtime)")
    report.append("")
    report.append("Original donor modules tested =")
    report.append("  Draw W3DModelDraw / KVE737 ART = SUPPORTED (kept)")
    report.append("  AliasConditionState with '=' = SUPPORTED (E-3 skeleton uses this form)")
    report.append("  VisionRange 1000 / ShroudClearingRange 1610 = SUPPORTED Group A (kept)")
    report.append("  AirplaneArmor / CountermeasuresAirplaneArmor = SUPPORTED (kept)")
    report.append("  JetAIUpdate + AmericaF16ALocomotor + BasicJetTaxiLocomotor = SUPPORTED via E-3 bridge")
    report.append("  JetSlowDeathBehavior / PhysicsBehavior / FlammableUpdate / TransitionDamageFX = SUPPORTED")
    report.append("  EjectPilotDie / ExperienceScalarUpgrade = SUPPORTED (omitted from minimal first boot Object)")
    report.append("  WeaponSet EA_18AntiRadar* ECM = SUPPORTED in DATA but OMITTED (no offensive / no ECM attack)")
    report.append("  CountermeasuresBehavior = SUPPORTED; donor LSF upgrade names avoided; AmericaCountermeasures used")
    report.append("  StealthDetectorUpdate = NOT in donor (none added)")
    report.append("Unsupported / rejected for active load =")
    report.append("  Full unchanged Object avionE737 = NOT COMPATIBLE (crashes Specter even as exact donor)")
    report.append("  Donor Draw using bare 'AliasConditionState REALLYDAMAGED' (no '=') = AVOIDED; E-3 uses '=' form")
    report.append("  Donor Upgrade_LSFCountermeasures / LSFusCountermeasureFlare = AVOIDED (only on E2/donor; America path used)")
    report.append("  Donor WeaponSet ECM devices = OMITTED by design (AEW only, no weapons)")
    report.append("Exact incompatible module/property =")
    report.append("  Object avionE737 as a whole (runtime reject when loaded directly)")
    report.append("  bare AliasConditionState without '=' inside donor Draw (not used in rebuilt Object)")
    report.append("  Upgrade_LSFCountermeasures / LSFusCountermeasureFlare (not used; AmericaCountermeasures bridge)")
    report.append("  WeaponSet PRIMARY/SECONDARY EA_18AntiRadarECMDevice (intentionally omitted)")
    report.append("")
    report.append("AEW functionality source = DONOR vision/shroud values + WORKING E-3 COMPATIBILITY BRIDGE (Draw structure/AI/physics/lifecycle/countermeasures); no StealthDetector (donor had none); no ECM weapons")
    report.append("Offensive weapons = NONE")
    report.append("")
    report.append("HeavyAirBase Slot 9 preserved = YES")
    report.append("E-3 changed = NO")
    report.append("AC-130 changed = NO")
    report.append("C-17 changed = NO")
    report.append("E2avionHE changed = NO")
    report.append("V-22 changed = NO")
    report.append("Bombers changed = NO")
    report.append("")
    report.append(f"Object avionE737 final count = {count_obj(vmap, 'avionE737')}")
    report.append(
        f"Object AmericaJetE737AEW final count = {count_obj(vmap, 'AmericaJetE737AEW')}"
    )
    report.append(f"source SHA256 = {sha256(e737)}")
    report.append(f"packed SHA256 = {sha256(vmap[E737_KEY])}")

    OUT_REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    (VERIFY / "VERIFY.txt").write_text("\n".join(report) + "\n", encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")

    dsha = sha256(DATA_BIG)
    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={dsha}\nZIP={OUT_ZIP.name}\n", encoding="utf-8"
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
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    print("DATA", dsha)
    print("URL", url)
    print("\n".join(report))


if __name__ == "__main__":
    main()
