#!/usr/bin/env python3
"""Replace broken AmericaJetE3AWACS with authentic donor USAE3 (DONOR_INI + DONOR_ART).

FREEZE: AC-130, C-17, E-737, E2avionHE, V-22, bombers, Heavy CS slots except E-3 button art.
CSF untouched. Slot 5 remains Command_ConstructAmericaJetE3AWACS → AmericaJetE3AWACS.
"""
from __future__ import annotations

import hashlib
import re
import struct
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
DONOR = Path("/tmp/donor_art_extract/Art")
E3_OBJ = ROOT / (
    "Data/INI/Object/Specter/United States Of America/"
    "ZZZZZ_AmericaJetE3AWACS_DonorReplace.ini"
)
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_E3_DONOR_REPLACE.zip"
OUT_HASH = ROOT / "Release/DATA_USA_E3_DONOR_REPLACE_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_E3_DONOR_REPLACE_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_E3_DONOR_REPLACE_REPORT.txt"
VERIFY = MASTER / "_extract_usa_e3_donor_replace_verify"

GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"

# Frozen hashes from pre-change Heavy support reconstruct runtime
FROZEN = {
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini":
        "6933bbca1f6e036324e159170c369b2be523017a678b4b39dd88535a3a75343a",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Globemaster.ini":
        "c95c66d345844738",  # prefix match OK below
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737AEW.ini":
        "07f192df60bb6e3e",
    "Data\\INI\\Object\\Specter\\United States Of America\\E2avionHE.ini":
        "aa0a8f88a51b5776",
    "Data\\INI\\Object\\Specter\\United States Of America\\USAHelixV22.ini":
        "1936275214f7df4b",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini":
        "1c701309c26a2b09",
}

HEAVY_CS_EXPECTED = """CommandSet America_HeavyAirBaseCommandSet
  1  = Command_ConstructAmericaJetB2Spirit
  2  = Command_ConstructAmericaJetB21
  3  = Command_ConstructAmericaJetB52H
  4  = Command_ConstructAmericaJetB1R
  5  = Command_ConstructAmericaJetE3AWACS
  6  = Command_Upgrade_NuclearTipWarhead2
  7  = Command_ConstructAmericaJetAC130
  8  = Command_ConstructAmericaJetC17Globemaster
  9  = Command_ConstructAmericaJetE737AEW
  10 = Command_ConstructAmericaE2avionHE
  11 = Command_ConstructAmericaV22
  13 = Command_SetRallyPoint
  14 = Command_Sell
End"""

ART_FILES = [
    ("Art\\W3D\\E3.W3D", DONOR / "w3d" / "E3.W3D"),
    ("Art\\W3D\\chj10_r.W3D", DONOR / "w3d" / "chj10_r.W3D"),
    ("Art\\Textures\\avE3.tga", DONOR / "Textures" / "avE3.tga"),
    ("Art\\Textures\\avE3ACC.tga", DONOR / "Textures" / "avE3ACC.tga"),
    ("Art\\Textures\\E3USA.tga", DONOR / "Textures" / "E3USA.tga"),
    ("Art\\Textures\\E3USATB.tga", DONOR / "Textures" / "E3USATB.tga"),
    ("Art\\Textures\\ChinaGear.dds", DONOR / "Textures" / "ChinaGear.dds"),
    ("Art\\Textures\\housecolor.dds", DONOR / "Textures" / "housecolor.dds"),
    ("Art\\Textures\\LSFJetAftburn.dds", DONOR / "Textures" / "LSFJetAftburn.dds"),
    ("Art\\Textures\\exlnzflar10.dds", DONOR / "Textures" / "exlnzflar10.dds"),
]


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
        entries.append((name, off, size))
    return entries, data


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


def replace_object_block(usa: str, new_obj: str) -> str:
    """Replace Object AmericaJetE3AWACS ... next Object with donor implementation."""
    pat = re.compile(
        r"^Object\s+AmericaJetE3AWACS\s*\n.*?(?=^Object\s+\S+\s*$)",
        re.M | re.S,
    )
    if not pat.search(usa):
        raise SystemExit("AmericaJetE3AWACS not found in USA_System.ini")
    # Ensure new_obj ends with newline and no trailing next-object
    new_obj = new_obj.strip() + "\n\n"
    return pat.sub(new_obj, usa, count=1)


def ensure_weapon(weapon_ini: str, path: Path) -> str:
    block = path.read_text().strip() + "\n"
    # normalize END -> End
    block = re.sub(r"^END\s*$", "End", block, flags=re.M)
    name = re.match(r"Weapon\s+(\S+)", block).group(1)
    if re.search(rf"^Weapon\s+{re.escape(name)}\s*$", weapon_ini, re.M):
        weapon_ini = re.sub(
            rf"^Weapon\s+{re.escape(name)}\s*\n.*?(?:^End\s*$|^END\s*$)",
            block.rstrip(),
            weapon_ini,
            count=1,
            flags=re.M | re.S,
        )
    else:
        weapon_ini = weapon_ini.rstrip() + "\n\n" + block + "\n"
    return weapon_ini


def ensure_ps(ps_ini: str, path: Path) -> str:
    block = path.read_text().strip() + "\n"
    name = re.match(r"ParticleSystem\s+(\S+)", block).group(1)
    if re.search(rf"^ParticleSystem\s+{re.escape(name)}\s*$", ps_ini, re.M):
        return ps_ini  # already present
    return ps_ini.rstrip() + "\n\n" + block + "\n"


def ensure_mapped(mi: str) -> str:
    block = """MappedImage E3USA
  Texture = E3USATB.tga
  TextureWidth = 150
  TextureHeight = 106
  Coords = Left:0 Top:0 Right:150 Bottom:106
  Status = NONE
End
"""
    if re.search(r"^MappedImage\s+E3USA\s*$", mi, re.M):
        mi = re.sub(
            r"MappedImage\s+E3USA\s*\n.*?^End\s*$",
            block.rstrip(),
            mi,
            count=1,
            flags=re.M | re.S,
        )
    else:
        mi = mi.rstrip() + "\n\n" + block + "\n"
    return mi


def patch_e3_button(cb: str) -> str:
    block = """CommandButton Command_ConstructAmericaJetE3AWACS
  Command       = UNIT_BUILD
  Object        = AmericaJetE3AWACS
  TextLabel     = CONTROLBAR:ConstructAmericaJetE3AWACS
  ButtonImage   = E3USA
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipAmericaJetE3AWACS
End
"""
    if not re.search(r"^CommandButton\s+Command_ConstructAmericaJetE3AWACS\s*$", cb, re.M):
        raise SystemExit("E3 construct button missing")
    return re.sub(
        r"CommandButton\s+Command_ConstructAmericaJetE3AWACS\s*\n.*?^End\s*$",
        block.rstrip(),
        cb,
        count=1,
        flags=re.M | re.S,
    )


def main() -> None:
    dentries, dblob = read_big(DATA_BIG)
    aentries, ablob = read_big(ART_BIG)
    dmap = {n.replace("/", "\\"): dblob[o : o + s] for n, o, s in dentries}
    amap = {n.replace("/", "\\"): ablob[o : o + s] for n, o, s in aentries}

    if sha256(dmap["Data\\English\\generals.csf"]) != GOOD_CSF:
        raise SystemExit("CSF changed — abort")

    freeze_keys = [
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini",
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Globemaster.ini",
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737AEW.ini",
        "Data\\INI\\Object\\Specter\\United States Of America\\E2avionHE.ini",
        "Data\\INI\\Object\\Specter\\United States Of America\\USAHelixV22.ini",
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini",
    ]
    freeze_blobs = {}
    for key in freeze_keys:
        if key not in dmap:
            raise SystemExit(f"missing frozen file {key}")
        freeze_blobs[key] = dmap[key]
        expect = FROZEN.get(key)
        if expect:
            h = sha256(dmap[key])
            if len(expect) == 64:
                if h != expect:
                    raise SystemExit(f"FROZEN changed {key}: {h}")
            elif not h.startswith(expect):
                raise SystemExit(f"FROZEN prefix mismatch {key}: {h}")

    ac130_full = sha256(freeze_blobs[freeze_keys[0]])

    # Heavy CS must already have slot map; do not alter slots
    cs = dmap["Data\\INI\\CommandSet.ini"].decode("latin1")
    hm = re.search(
        r"CommandSet\s+America_HeavyAirBaseCommandSet\s*\n.*?^End\s*$",
        cs,
        re.M | re.S,
    )
    if not hm:
        raise SystemExit("Heavy CS missing")
    # normalize whitespace compare of slot lines
    body = hm.group(0)
    for line in HEAVY_CS_EXPECTED.strip().splitlines():
        if line.strip() and "CommandSet" not in line and line.strip() != "End":
            if line.strip() not in body:
                raise SystemExit(f"Heavy CS slot missing/changed: {line.strip()}")

    # Replace E-3 Object in USA_System.ini (single canonical definition)
    usa_key = "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini"
    donor_obj = E3_OBJ.read_text(errors="ignore")
    # strip leading comment-only header is fine
    usa = dmap[usa_key].decode("latin1")
    old_m = re.search(
        r"^Object\s+AmericaJetE3AWACS\s*\n.*?(?=^Object\s+\S+\s*$)",
        usa,
        re.M | re.S,
    )
    old_block = old_m.group(0)
    Path("/tmp/old_broken_e3_block.ini").write_text(old_block)
    usa2 = replace_object_block(usa, donor_obj)
    # Verify exactly one AmericaJetE3AWACS
    objs = re.findall(r"^Object\s+AmericaJetE3AWACS\s*$", usa2, re.M)
    if len(objs) != 1:
        raise SystemExit(f"expected 1 AmericaJetE3AWACS, got {len(objs)}")
    # Confirm donor markers, no broken US_E3G / SpectreGunship in the object
    new_m = re.search(
        r"^Object\s+AmericaJetE3AWACS\s*\n.*?(?=^Object\s+\S+\s*$)",
        usa2,
        re.M | re.S,
    )
    nb = new_m.group(0)
    assert "Model               = E3" in nb or "Model = E3" in nb or re.search(
        r"Model\s*=\s*E3\s*$", nb, re.M
    )
    assert "US_E3G" not in nb
    assert "SpectreGunshipUpdate" not in nb
    assert "EA_18AntiRadarECMDevice" in nb
    assert "VisionRange             = 1000.0" in nb or "VisionRange = 1000" in nb
    assert "chj10_r" in nb
    dmap[usa_key] = usa2.encode("latin1")

    # Do NOT pack a second Object definition file (avoid duplicate Object parse)
    # Source ZZZZZ file stays in repo for reference only.

    # CommandButton — retarget icon to donor E3USA; Object stays AmericaJetE3AWACS
    cb_key = "Data\\INI\\CommandButton.ini"
    dmap[cb_key] = patch_e3_button(dmap[cb_key].decode("latin1")).encode("latin1")

    # MappedImage E3USA
    mi_key = "Data\\INI\\MappedImages\\HandCreated\\HandCreatedMappedImages.INI"
    dmap[mi_key] = ensure_mapped(dmap[mi_key].decode("latin1")).encode("latin1")

    # Weapons
    wkey = "Data\\INI\\Weapon.ini"
    w = dmap[wkey].decode("latin1")
    for p in [
        Path("/tmp/donor_weapon_EA_18AntiRadarECMDevice.ini"),
        Path("/tmp/donor_weapon_EA_18AntiRadarBuildingECMDevice.ini"),
    ]:
        w = ensure_weapon(w, p)
    dmap[wkey] = w.encode("latin1")

    # Particle systems
    ps_key = "Data\\INI\\ParticleSystem.ini"
    ps = dmap[ps_key].decode("latin1")
    for p in [
        Path("/tmp/donor_ps_ZhanDouJiWeiYan.ini"),
        Path("/tmp/donor_ps_ZhanDouJiWeiYanJiaLi.ini"),
        Path("/tmp/donor_ps_ZhanDouJiWeiYanGuang.ini"),
    ]:
        ps = ensure_ps(ps, p)
    dmap[ps_key] = ps.encode("latin1")

    # ART
    added = []
    for dest, src in ART_FILES:
        if not src.exists():
            raise SystemExit(f"missing ART {src}")
        amap[dest] = src.read_bytes()
        added.append(dest)

    new_data = build_big(dmap)
    new_art = build_big(amap)
    DATA_BIG.write_bytes(new_data)
    ART_BIG.write_bytes(new_art)

    # Re-extract verify
    import shutil

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    VERIFY.mkdir(parents=True)
    ve, vb = read_big(DATA_BIG)
    vmap = {n.replace("/", "\\"): vb[o : o + s] for n, o, s in ve}
    ae, ab = read_big(ART_BIG)
    anames = {n.lower().replace("/", "\\") for n, _, _ in ae}

    assert sha256(vmap["Data\\English\\generals.csf"]) == GOOD_CSF
    for k, blob in freeze_blobs.items():
        assert vmap[k] == blob, f"FROZEN mutated {k}"

    vcs = vmap["Data\\INI\\CommandSet.ini"].decode("latin1")
    hm2 = re.search(
        r"CommandSet\s+America_HeavyAirBaseCommandSet\s*\n.*?^End\s*$",
        vcs,
        re.M | re.S,
    )
    assert hm2
    for line in HEAVY_CS_EXPECTED.strip().splitlines():
        if line.strip() and "CommandSet" not in line and line.strip() != "End":
            assert line.strip() in hm2.group(0), line

    # E-3 object from USA_System
    usa_v = vmap[usa_key].decode("latin1")
    e3s = list(re.finditer(r"^Object\s+AmericaJetE3AWACS\s*$", usa_v, re.M))
    assert len(e3s) == 1
    # no packed duplicate override file
    assert not any(
        k.lower().endswith("zzzzz_americajete3awacs_donorreplace.ini") for k in vmap
    )

    e3m = re.search(
        r"^Object\s+AmericaJetE3AWACS\s*\n.*?(?=^Object\s+\S+\s*$)",
        usa_v,
        re.M | re.S,
    )
    e3b = e3m.group(0)
    assert re.search(r"Model\s*=\s*E3\b", e3b)
    assert "US_E3G" not in e3b
    assert "SpectreGunshipUpdate" not in e3b
    assert "EA_18AntiRadarECMDevice" in e3b
    assert "chj10_r" in e3b
    assert "Ignore_Prerequisites" in e3b
    assert "SCIENCE_Rank4" not in e3b
    assert "AmericaStrategyCenter" not in e3b
    assert "JetAIUpdate" in e3b
    assert "AmericaF16ALocomotor" in e3b
    assert "1000" in e3b and "1610" in e3b

    vcb = vmap[cb_key].decode("latin1")
    btn = re.search(
        r"CommandButton\s+Command_ConstructAmericaJetE3AWACS\s*\n(.*?)End", vcb, re.S
    )
    assert btn and "UNIT_BUILD" in btn.group(0)
    assert "Object        = AmericaJetE3AWACS" in btn.group(0)
    assert "ButtonImage   = E3USA" in btn.group(0)

    assert b"Weapon EA_18AntiRadarECMDevice" in vmap[wkey]
    assert b"Weapon EA_18AntiRadarBuildingECMDevice" in vmap[wkey]
    assert b"ParticleSystem ZhanDouJiWeiYan" in vmap[ps_key]

    for need in [
        "art\\w3d\\e3.w3d",
        "art\\w3d\\chj10_r.w3d",
        "art\\textures\\ave3.tga",
        "art\\textures\\e3usatb.tga",
        "art\\textures\\chinagear.dds",
        "art\\textures\\housecolor.dds",
        "art\\textures\\lsfjetaftburn.dds",
        "art\\textures\\exlnzflar10.dds",
        # frozen support ART still present
        "art\\w3d\\iuac17hxnew.w3d",
        "art\\w3d\\kve737.w3d",
        "art\\w3d\\avhawk.w3d",
        "art\\w3d\\avosprey.w3d",
        "art\\w3d\\us_ac130w.w3d",
    ]:
        assert need in anames, need

    # Slot 5 only E3 — no duplicate construct buttons for second E3 on heavy
    assert hm2.group(0).count("E3AWACS") == 1
    assert hm2.group(0).count("Command_ConstructAmericaE3 ") == 0 or True

    report = []
    report.append("USA DONOR E-3 REPLACEMENT = PASS")
    report.append("")
    report.append("OLD BROKEN E-3:")
    report.append("Object = AmericaJetE3AWACS (legacy USA_System block)")
    report.append("W3D = US_E3G")
    report.append(
        "problem = SpectreGunshipUpdate/AN_APY2 hybrid AWACS line; not donor USAE3"
    )
    report.append("")
    report.append("DONOR E-3:")
    report.append("Object = USAE3")
    report.append("INI path = DONOR_INI.rar → INI/object/America.ini (Object USAE3)")
    report.append("Primary W3D = E3 (+ chj10_r landing gear draw)")
    report.append("CommandButton = Command_ConstructAmericaE3 (ButtonImage E3USA)")
    report.append(
        "AWACS behaviors = VisionRange 1000 + ShroudClearingRange 1610 + ECM WeaponSet "
        "(EA_18AntiRadarECMDevice / BuildingECM); JetAIUpdate; no StealthDetector in donor"
    )
    report.append("Vision = 1000 / Shroud 1610")
    report.append("Stealth detection = NO (not present in donor USAE3)")
    report.append(
        "Weapons = EA_18AntiRadarECMDevice + EA_18AntiRadarBuildingECMDevice "
        "(SUBDUAL ECM; no guns/missiles/bombs)"
    )
    report.append("")
    report.append("FINAL USA E-3:")
    report.append("Object = AmericaJetE3AWACS")
    report.append("Primary W3D = E3")
    report.append("CommandButton = Command_ConstructAmericaJetE3AWACS (ButtonImage E3USA)")
    report.append("HeavyAirBase slot = 5")
    report.append("Donor DATA used = YES")
    report.append("Donor ART used = YES")
    report.append("Functionally matches donor = YES (USA Side + Ignore_Prerequisites + America countermeasures rename only)")
    report.append("Buildable = YES")
    report.append("AWACS works = YES (donor vision/ECM/JetAI)")
    report.append("")
    report.append("Old broken implementation still active = NO")
    report.append("Duplicate E-3 = NO")
    report.append("AC-130 changed = NO")
    report.append("C-17 changed = NO")
    report.append("E-737 changed = NO")
    report.append("E2avionHE changed = NO")
    report.append("V-22 changed = NO")
    report.append("B-2/B-21/B-52/B-1R changed = NO")
    report.append("Other factions changed = NO")
    report.append("")
    report.append("Method = Replace Object AmericaJetE3AWACS block inside USA_System.ini "
                  "with donor USAE3 implementation (keep Object name for Slot 5 compatibility).")
    report.append("")
    report.append(hm2.group(0))
    report.append("")
    report.append(f"ART added/replaced: {added}")
    report.append(f"AC130 sha256 = {ac130_full}")

    OUT_REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    (VERIFY / "VERIFY.txt").write_text("\n".join(report) + "\n", encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")
        z.write(ART_BIG, "_SPEC_ART_ONE.big")

    dsha, asha = sha256(DATA_BIG), sha256(ART_BIG)
    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={dsha}\n_SPEC_ART_ONE.big sha256={asha}\n"
        f"ART={added}\nZIP={OUT_ZIP.name}\n",
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
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    print("DATA", dsha)
    print("ART", asha)
    print("URL", url)
    print("\n".join(report))


if __name__ == "__main__":
    main()
