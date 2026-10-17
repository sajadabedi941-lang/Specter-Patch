#!/usr/bin/env python3
"""Add passive Specter AWACS functionality to E-2 / E-3 / E-737 Visual aircraft.

Reference: NatoJetE3AAWACS (proven Specter AEW — Vision 900 / Shroud 700 /
StealthDetector 1000 / Cost 4200 / Health 1000 / CMF56 Speed 128).

Preserves donor visuals, scales, buttons, HeavyAirBase slots, and runway
JetAIUpdate + BasicJetTaxiLocomotor. Adds StealthDetectorUpdate + REVEALS_ENEMY_PATHS.
Creates F100-family locomotor variants with role-scaled Speed/Accel/Turn.
Weapons = NONE. No SpecialPower / SpectreGunship.
"""
from __future__ import annotations

import hashlib
import math
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
STAGE = MASTER / "_stage_usa_e2_e3_e737_awacs"
VERIFY = MASTER / "_extract_usa_e2_e3_e737_awacs_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_E2_E3_E737_AWACS.zip"
OUT_HASH = ROOT / "Release/DATA_USA_E2_E3_E737_AWACS_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_E2_E3_E737_AWACS_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_E2_E3_E737_AWACS_REPORT.txt"
SRC_DIR = ROOT / "Data/INI/Object/Specter/United States Of America"

# CSF may already be modified by B2A; accept current packed CSF as freeze baseline
CSF_KEY = "Data\\English\\generals.csf"
LOCO_KEY = "Data\\INI\\Locomotor.ini"
CS_KEY = "Data\\INI\\CommandSet.ini"
CB_KEY = "Data\\INI\\CommandButton.ini"
HEAVY_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\"
    "America_HeavyAirBase.ini"
)

E2_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE2Visual.ini"
)
E3_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE3Visual.ini"
)
E737_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737Visual.ini"
)

# Reference NatoJetE3AAWACS / CMF56_2_Turbofan_engine
REF = {
    "vision": 900.0,
    "shroud": 700.0,  # radar / surveillance radius
    "stealth": 1000.0,
    "cost": 4200,
    "build": 70.0,
    "health": 1000.0,
    "speed": 128.0,
    "accel": 73.0,
    "turn": 37.0,
    "speed_dmg": 100.0,
    "accel_dmg": 43.0,
    "turn_dmg": 22.0,
}

# Role multipliers
ROLES = {
    "E3": {
        "key": E3_KEY,
        "loco": "F100_PW_229_E3AWACS",
        "radar_m": 1.25,
        "vision_m": 1.20,
        "stealth_m": 1.15,
        "cost_m": 1.25,
        "build_m": 1.15,
        "health_m": 1.15,
        "speed_m": 0.90,
        "accel_m": 0.90,
        "turn_m": 0.90,
        "role": "STRATEGIC AWACS",
        "freeze_scale": None,  # no Scale line currently / leave as-is
    },
    "E737": {
        "key": E737_KEY,
        "loco": "F100_PW_229_E737AEW",
        "radar_m": 1.05,
        "vision_m": 1.05,
        "stealth_m": 1.00,
        "cost_m": 1.05,
        "build_m": 1.00,
        "health_m": 1.00,
        "speed_m": 1.10,
        "accel_m": 1.10,
        "turn_m": 1.10,
        "role": "BALANCED AEW&C",
        "freeze_scale": 0.8,
    },
    "E2": {
        "key": E2_KEY,
        "loco": "F100_PW_229_E2AEW",
        "radar_m": 0.75,
        "vision_m": 0.80,
        "stealth_m": 0.85,
        "cost_m": 0.75,
        "build_m": 0.75,
        "health_m": 0.85,
        "speed_m": 1.15,
        "accel_m": 1.20,
        "turn_m": 1.20,
        "role": "TACTICAL AEW",
        "freeze_scale": 1.5,
    },
}

FREEZE_OBJECTS = [
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB2A.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetV22Visual.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini",
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


def rnd(x: float) -> int:
    return int(round(x))


def rnd1(x: float) -> float:
    return round(x, 1)


def compute(role: dict) -> dict:
    return {
        "shroud": rnd(REF["shroud"] * role["radar_m"]),
        "vision": rnd1(REF["vision"] * role["vision_m"]),
        "stealth": rnd(REF["stealth"] * role["stealth_m"]),
        "cost": rnd(REF["cost"] * role["cost_m"]),
        "build": rnd1(REF["build"] * role["build_m"]),
        "health": rnd1(REF["health"] * role["health_m"]),
        "speed": rnd(REF["speed"] * role["speed_m"]),
        "accel": rnd(REF["accel"] * role["accel_m"]),
        "turn": rnd(REF["turn"] * role["turn_m"]),
        "speed_dmg": rnd(REF["speed_dmg"] * role["speed_m"]),
        "accel_dmg": rnd(REF["accel_dmg"] * role["accel_m"]),
        "turn_dmg": rnd(REF["turn_dmg"] * role["turn_m"]),
        "loco": role["loco"],
        "role": role["role"],
    }


# Exact NatoJetE3AAWACS StealthDetectorUpdate syntax (ModuleTag_16f6), range scaled.
STEALTH_BLOCK = """
  Behavior = StealthDetectorUpdate ModuleTag_AWACS_StealthDetect
    DetectionRate   = 1800   ; how often to rescan for stealthed things in my sight (msec)
    DetectionRange = {stealth}
    CanDetectWhileGarrisoned  = No ;Garrisoned means being in a structure that you units can shoot out of.
    CanDetectWhileContained   = No ;Contained means being in a transport or tunnel network.
    ExtraForbiddenKindOf = UNATTACKABLE
  End
"""


def patch_object(text: str, stats: dict, freeze_scale: float | None) -> str:
    # Vision / shroud
    text = re.sub(
        r"(?m)^(\s*VisionRange\s*=\s*).*$",
        rf"\g<1>{stats['vision']}",
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(\s*ShroudClearingRange\s*=\s*).*$",
        rf"\g<1>{stats['shroud']}",
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(\s*BuildCost\s*=\s*).*$",
        rf"\g<1>{stats['cost']}",
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(\s*BuildTime\s*=\s*).*$",
        rf"\g<1>{stats['build']}",
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(\s*MaxHealth\s*=\s*).*$",
        rf"\g<1>{stats['health']}",
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(\s*InitialHealth\s*=\s*).*$",
        rf"\g<1>{stats['health']}",
        text,
        count=1,
    )
    # KindOf — add REVEALS_ENEMY_PATHS, keep no CAN_ATTACK
    def kindof_repl(m: re.Match[str]) -> str:
        indent, vals = m.group(1), m.group(2)
        parts = vals.split()
        if "REVEALS_ENEMY_PATHS" not in parts:
            parts.append("REVEALS_ENEMY_PATHS")
        # strip CAN_ATTACK if present (unarmed AEW)
        parts = [p for p in parts if p != "CAN_ATTACK"]
        return f"{indent}KindOf = " + " ".join(parts)

    text = re.sub(r"(?m)^(\s*)KindOf\s*=\s*(.*)$", kindof_repl, text, count=1)

    # Locomotor normal set (lines are indented in Specter Object INIs)
    text = re.sub(
        r"(?m)^(\s*Locomotor\s*=\s*SET_NORMAL\s+)\S+\s*$",
        rf"\g<1>{stats['loco']}",
        text,
        count=1,
    )

    # Remove any WeaponSet blocks (must stay NONE)
    text = re.sub(r"(?ms)^\s*WeaponSet\b.*?\n\s*End\s*\n", "", text)

    # Insert StealthDetector if missing (before Geometry)
    if "StealthDetectorUpdate" not in text:
        block = STEALTH_BLOCK.format(stealth=stats["stealth"]).rstrip() + "\n"
        text = re.sub(
            r"(?m)^(\s*Geometry\s*=)",
            block + r"\n\1",
            text,
            count=1,
        )
    else:
        text = re.sub(
            r"(?m)^(\s*DetectionRange\s*=\s*).*$",
            rf"\g<1>{stats['stealth']}",
            text,
            count=1,
        )

    # Freeze scale
    if freeze_scale is not None:
        m = re.search(r"(?m)^(\s*Scale\s*=\s*)([0-9.]+)\s*$", text)
        assert m, "Scale missing"
        assert abs(float(m.group(2)) - freeze_scale) < 0.001

    # Preserve model / button markers
    assert "JetAIUpdate" in text
    assert "BasicJetTaxiLocomotor" in text
    assert "WeaponSet" not in text
    assert "SpectreGunship" not in text
    assert "SpecialAbility" not in text
    return text


def make_loco(template: str, name: str, stats: dict) -> str:
    body = template
    body = re.sub(
        r"(?m)^Locomotor\s+F100_PW_229\s*$",
        f"Locomotor {name}",
        body,
        count=1,
    )
    reps = {
        "Speed": stats["speed"],
        "SpeedDamaged": stats["speed_dmg"],
        "TurnRate": stats["turn"],
        "TurnRateDamaged": stats["turn_dmg"],
        "Acceleration": stats["accel"],
        "AccelerationDamaged": stats["accel_dmg"],
        "MinTurnSpeed": max(40, rnd(stats["speed"] * 0.75)),
    }
    for key, val in reps.items():
        body = re.sub(
            rf"(?m)^(\s*{key}\s*=\s*)\S+",
            rf"\g<1>{val}",
            body,
            count=1,
        )
    return body.rstrip() + "\n"


def upsert_locomotors(loco_ini: str, f100_block: str, stats_map: dict) -> str:
    out = loco_ini
    for role_name, stats in stats_map.items():
        name = stats["loco"]
        block = make_loco(f100_block, name, stats)
        if re.search(rf"(?m)^Locomotor\s+{re.escape(name)}\s*$", out):
            out, n = re.subn(
                rf"(?ms)^Locomotor\s+{re.escape(name)}\s*\n.*?(?=^Locomotor\s|\Z)",
                block + "\n",
                out,
                count=1,
            )
            assert n == 1
        else:
            # insert after F100_PW_229
            m = re.search(
                r"(?ms)^Locomotor\s+F100_PW_229\s*\n.*?(?=^Locomotor\s|\Z)",
                out,
            )
            assert m
            out = out[: m.end()] + "\n" + block + "\n" + out[m.end() :]
    return out


def upload(path: Path) -> str:
    try:
        r = subprocess.run(
            [
                "curl",
                "-sF",
                f"file=@{path}",
                "https://litterbox.catbox.moe/resources/internals/api.php",
                "-F",
                "time=72h",
                "-F",
                "reqtype=fileupload",
            ],
            capture_output=True,
            text=True,
            timeout=600,
        )
        out = (r.stdout or "").strip()
        if out.startswith("http"):
            return out
    except Exception:
        pass
    try:
        r = subprocess.run(
            ["curl", "-sF", f"file=@{path}", "https://store1.gofile.io/uploadFile"],
            capture_output=True,
            text=True,
            timeout=900,
        )
        m = re.search(r'"downloadPage"\s*:\s*"([^"]+)"', r.stdout or "")
        if m:
            return m.group(1)
    except Exception:
        pass
    return "(upload failed)"


def main() -> None:
    data = read_big(DATA_BIG)
    art_sha = sha256(ART_BIG)
    csf_before = data[CSF_KEY]
    cs_before = data[CS_KEY]
    cb_before = data[CB_KEY]
    heavy_before = data[HEAVY_KEY]
    freeze_blobs = {k: data[k] for k in FREEZE_OBJECTS if k in data}

    # Extract F100 template
    loco_txt = data[LOCO_KEY].decode("latin1")
    m = re.search(
        r"(?ms)^Locomotor\s+F100_PW_229\s*\n.*?(?=^Locomotor\s|\Z)", loco_txt
    )
    assert m
    f100_block = m.group(0)

    stats_map = {name: compute(cfg) for name, cfg in ROLES.items()}

    # Hierarchy checks
    assert stats_map["E3"]["shroud"] > stats_map["E737"]["shroud"] > stats_map["E2"]["shroud"]
    assert stats_map["E2"]["speed"] > stats_map["E737"]["speed"] > stats_map["E3"]["speed"]
    assert stats_map["E2"]["cost"] < stats_map["E737"]["cost"] < stats_map["E3"]["cost"]

    loco2 = upsert_locomotors(loco_txt, f100_block, stats_map)

    data2 = dict(data)
    for name, cfg in ROLES.items():
        key = cfg["key"]
        text = data[key].decode("latin1")
        # freeze W3D / button / scale markers
        model_before = re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text)
        btn_before = re.search(r"(?m)^\s*ButtonImage\s*=\s*(\S+)", text).group(1)
        patched = patch_object(text, stats_map[name], cfg["freeze_scale"])
        model_after = re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", patched)
        btn_after = re.search(r"(?m)^\s*ButtonImage\s*=\s*(\S+)", patched).group(1)
        assert model_before == model_after
        assert btn_before == btn_after
        assert f"Locomotor = SET_NORMAL {stats_map[name]['loco']}" in patched
        assert "StealthDetectorUpdate" in patched
        assert "REVEALS_ENEMY_PATHS" in patched
        data2[key] = patched.replace("\r\n", "\n").encode("latin1")
        # sync loose source (key uses Windows separators)
        SRC_DIR.mkdir(parents=True, exist_ok=True)
        loose_name = key.replace("\\", "/").split("/")[-1]
        (SRC_DIR / loose_name).write_bytes(data2[key])

    data2[LOCO_KEY] = loco2.replace("\r\n", "\n").encode("latin1")
    data2[CSF_KEY] = csf_before
    data2[CS_KEY] = cs_before
    data2[CB_KEY] = cb_before
    data2[HEAVY_KEY] = heavy_before
    for k, v in freeze_blobs.items():
        data2[k] = v

    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    write_tree(data2, STAGE / "in")
    DATA_BIG.write_bytes(build_big(data2))

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    dv = read_big(DATA_BIG)
    write_tree(dv, VERIFY / "out")

    assert dv[CS_KEY] == cs_before
    assert dv[CB_KEY] == cb_before
    assert dv[HEAVY_KEY] == heavy_before
    assert dv[CSF_KEY] == csf_before
    assert sha256(ART_BIG) == art_sha

    # verify stats in packed objects
    def get_num(text: str, field: str) -> float:
        m = re.search(rf"(?m)^\s*{field}\s*=\s*([0-9.]+)", text)
        assert m, field
        return float(m.group(1))

    packed = {}
    for name, cfg in ROLES.items():
        t = dv[cfg["key"]].decode("latin1")
        packed[name] = {
            "vision": get_num(t, "VisionRange"),
            "shroud": get_num(t, "ShroudClearingRange"),
            "cost": get_num(t, "BuildCost"),
            "build": get_num(t, "BuildTime"),
            "health": get_num(t, "MaxHealth"),
            "stealth": get_num(t, "DetectionRange"),
            "has_stealth": "StealthDetectorUpdate" in t,
            "reveals": "REVEALS_ENEMY_PATHS" in t,
            "no_weapon": not re.search(r"(?m)^\s*WeaponSet\b", t),
            "jetai": "JetAIUpdate" in t,
            "taxi": "BasicJetTaxiLocomotor" in t,
            "loco": re.search(
                r"(?m)^\s*Locomotor\s*=\s*SET_NORMAL\s+(\S+)", t
            ).group(1),
        }
        assert packed[name]["has_stealth"]
        assert packed[name]["reveals"]
        assert packed[name]["no_weapon"]
        assert packed[name]["jetai"] and packed[name]["taxi"]
        # loco exists
        assert re.search(
            rf"(?m)^Locomotor\s+{re.escape(packed[name]['loco'])}\s*$",
            dv[LOCO_KEY].decode("latin1"),
        )

    assert packed["E3"]["shroud"] > packed["E737"]["shroud"] > packed["E2"]["shroud"]
    assert packed["E2"]["cost"] < packed["E737"]["cost"] < packed["E3"]["cost"]

    # loco speeds
    def loco_speed(name: str) -> int:
        m = re.search(
            rf"(?ms)^Locomotor\s+{re.escape(name)}\s*\n.*?(?=^Locomotor\s|\Z)",
            dv[LOCO_KEY].decode("latin1"),
        )
        return int(re.search(r"(?m)^\s*Speed\s*=\s*(\d+)", m.group(0)).group(1))

    assert loco_speed(stats_map["E2"]["loco"]) > loco_speed(stats_map["E737"]["loco"]) > loco_speed(
        stats_map["E3"]["loco"]
    )

    data_sha = sha256(DATA_BIG)
    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DATA_BIG, "_SPEC_DATA_ONE.big")
    url = upload(OUT_ZIP)

    def fmt(s: dict) -> str:
        return (
            f"Radar/Shroud={s['shroud']}\n"
            f"Vision={s['vision']}\n"
            f"Stealth detection={s['stealth']}\n"
            f"Cost={s['cost']}\n"
            f"Build time={s['build']}\n"
            f"Health={s['health']}\n"
            f"Speed={s['speed']}\n"
            f"Acceleration={s['accel']}\n"
            f"Turn rate={s['turn']}\n"
            f"Locomotor={s['loco']}\n"
            f"Role = {s['role']}"
        )

    report = f"""USA E2/E3/E737 AWACS FUNCTIONALITY = STRUCTURAL PASS

ORIGINAL AWACS (reference):
Object = NatoJetE3AAWACS (Specter NATO AEW; same family as BritainJetE3AAWACS)
Also noted USA science variant US_E3G_AWACS (special-power/loiter — not used as flight base)
Radar radius (ShroudClearingRange) = {REF['shroud']}
Vision range = {REF['vision']}
Stealth detection = {REF['stealth']} (StealthDetectorUpdate present = YES)
Cost = {REF['cost']}
Build time = {REF['build']}
Health = {REF['health']}
Speed = {REF['speed']} (CMF56_2_Turbofan_engine)
Turn rate = {REF['turn']}
Acceleration = {REF['accel']}
Original AWACS stealth detection support = YES

Passive modules applied (no weapons / no SpecialPower):
- VisionRange / ShroudClearingRange
- StealthDetectorUpdate
- KindOf += REVEALS_ENEMY_PATHS
- Role-scaled F100-family locomotors (runway JetAIUpdate preserved)

------------------------------
E-3:
{fmt(stats_map['E3'])}

------------------------------
E-737:
{fmt(stats_map['E737'])}

------------------------------
E-2:
{fmt(stats_map['E2'])}

VALIDATION:
AmericaJetE3Visual has active AWACS functionality = YES
AmericaJetE737Visual has active AWACS functionality = YES
AmericaJetE2Visual has active AWACS functionality = YES
All three values different = YES
E-3 radar range > E-737 radar range > E-2 radar range = YES
E-2 mobility > E-737 mobility > E-3 mobility = YES
E-2 cost < E-737 cost < E-3 cost = YES
Weapons on all three = NONE
Flight system preserved = YES (JetAIUpdate + BasicJetTaxiLocomotor + F100-family)
HeavyAirBase unchanged = YES
Other aircraft unchanged = YES
ART unchanged = YES
In-game radar effectiveness = USER TEST REQUIRED

DATA sha256 = {data_sha}
ART sha256 = {art_sha}
ZIP = {OUT_ZIP.name}
URL = {url}
"""
    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={data_sha}\n"
        f"_SPEC_ART_ONE.big sha256={art_sha} (unchanged)\n"
        f"zip={OUT_ZIP.name}\n",
        encoding="utf-8",
    )
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    OUT_REPORT.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
