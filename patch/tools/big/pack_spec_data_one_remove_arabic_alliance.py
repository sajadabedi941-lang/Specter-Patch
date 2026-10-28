#!/usr/bin/env python3
"""Remove Arabic Alliance from playable faction lists.

SPECTER maps the GLA PlayerTemplate slot to display name INI:FactionGLA
= "Arabic Alliance". This packer sets that template unplayable so it
disappears from skirmish / multiplayer / old-faction country lists.

Does not delete ArabicArmy objects (EgyptDozerCommandSet still builds
them), Iraq/SaudiArabia/UAE/Syria/Libya templates, CommandSet.ini menus,
Shahed Fire, Vietnam radar, ART, or 0_ overlays.

Source: vietnam-radar-minimap _SPEC_DATA_ONE.big
(SHA a71c3f902af8c08d18d1db9bbbcc2d231fafd77d2dde3f2bf7c6e8268f132c82).
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_BIG = ROOT / "Release/VIETNAM_RADAR_MINIMAP/_SPEC_DATA_ONE.big"
SRC_SHA = "a71c3f902af8c08d18d1db9bbbcc2d231fafd77d2dde3f2bf7c6e8268f132c82"
OUT_DIR = ROOT / "Release/REMOVE_ARABIC_ALLIANCE"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"

K_PT = r"Data\INI\PlayerTemplate.ini"
K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_WPN = r"Data\INI\Weapon.ini"
K_UAV = r"Data\INI\Object\Specter\SpecterRadarUavs.ini"
K_VN = (
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_RadarStation.ini"
)

KEEP_PLAYABLE = (
    "FactionIraq",
    "FactionSaudiArabia",
    "FactionUAE",
    "FactionSyria",
    "FactionLibya",
    "FactionAmerica",
    "FactionRussia",
    "FactionChina",
    "FactionIran",
    "FactionJapan",
    "FactionVietnam",
    "FactionNorthKorea",
    "FactionNato",
    "FactionPakistan",
    "FactionIndia",
    "FactionGermany",
    "FactionFrance",
    "FactionBritain",
    "FactionItaly",
    "FactionSweden",
    "FactionUkraine",
    "FactionTurkey",
    "FactionSouthAfrica",
    "FactionSouthKorea",
    "FactionBossGeneral",
    "FactionAmericaAirForceGeneral",
)


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    _, n, _ = struct.unpack_from(">III", data, 4)
    entries: dict[str, bytes] = {}
    off = 16
    for _ in range(n):
        eoff, esize = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    index, blobs, offset = [], [], header_size
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def block(text: str, kind: str, name: str) -> str:
    m = re.search(rf"^{kind} {re.escape(name)}\s*\r?\n", text, re.M)
    if not m:
        raise SystemExit(f"missing {kind} {name}")
    n2 = re.search(rf"^{kind} ", text[m.end() :], re.M)
    end = m.end() + n2.start() if n2 else len(text)
    return text[m.start() : end]


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("VALIDATE FAIL: " + msg)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_pt(raw: bytes) -> bytes:
    text = raw.decode("latin1")
    gla = block(text, "PlayerTemplate", "FactionGLA")
    require("PlayableSide      = Yes" in gla, "FactionGLA not playable")
    require("OldFaction        = Yes" in gla, "FactionGLA OldFaction missing")
    require("DisplayName       = INI:FactionGLA" in gla, "FactionGLA display")
    require("Side              = GLA" in gla, "FactionGLA side")
    new_gla = gla.replace("PlayableSide      = Yes", "PlayableSide      = No", 1)
    new_gla = new_gla.replace("OldFaction        = Yes", "OldFaction        = No", 1)
    require("PlayableSide      = No" in new_gla, "PlayableSide not No")
    require("PlayableSide      = Yes" not in new_gla, "PlayableSide still Yes")
    require(new_gla.count("OldFaction        = No") == 1, "OldFaction")
    require(text.count(gla) == 1, "duplicate FactionGLA block")
    return text.replace(gla, new_gla, 1).encode("latin1")


def playable_of(text: str, name: str) -> str:
    body = block(text, "PlayerTemplate", name)
    m = re.search(r"PlayableSide\s*=\s*(\S+)", body)
    require(m is not None, f"{name} has no PlayableSide")
    return m.group(1)


def validate(orig: dict[str, bytes], new: dict[str, bytes]) -> None:
    require(orig[K_CS] == new[K_CS], "CommandSet.ini changed")
    require(orig[K_CB] == new[K_CB], "CommandButton.ini changed")
    require(orig[K_WPN] == new[K_WPN], "Weapon.ini changed")
    require(orig[K_UAV] == new[K_UAV], "Shahed UAV file changed")
    require(orig[K_VN] == new[K_VN], "Vietnam radar changed")
    changed = [k for k in orig if orig[k] != new[k]]
    require(changed == [K_PT], f"unexpected files changed: {changed}")

    orig_pt = orig[K_PT].decode("latin1")
    new_pt = new[K_PT].decode("latin1")
    require(playable_of(new_pt, "FactionGLA") == "No", "GLA still playable")
    require("OldFaction        = No" in block(new_pt, "PlayerTemplate", "FactionGLA"), "OldFaction")
    for name in KEEP_PLAYABLE:
        require(playable_of(orig_pt, name) == "Yes", f"{name} was not playable")
        require(playable_of(new_pt, name) == "Yes", f"{name} lost playable")
        require(
            block(orig_pt, "PlayerTemplate", name) == block(new_pt, "PlayerTemplate", name),
            f"{name} template edited",
        )
    require("PlayerTemplate FactionEgypt" in orig.get(r"Data\INI\PlayerTemplate_SpecterPatch.ini", b"").decode("latin1"), "Egypt overlay")
    cs = new[K_CS].decode("latin1")
    require("12 = Command_ConstructSpecterRadarShahedLauncher" in block(cs, "CommandSet", "Vietnam_RadarStationCommandSet"), "VN Shahed")
    uav = block(new[K_UAV].decode("latin1"), "Object", "SpecterRadar_ShahedLauncher")
    require("BuildCost       = 8000" in uav, "Shahed cost")
    require("IranShahed136FireCommandSet" in uav, "Shahed Fire")
    require("Command_ConstructIraq_RadarStation" in cs, "Iraq radar CS")
    require("PlayerTemplate FactionIraq" in new_pt, "Iraq template")
    # ArabicArmy objects still present for Egypt
    aa_files = [k for k in new if "\\Arabic Alliance\\" in k]
    require(len(aa_files) > 50, f"Arabic Alliance object folder stripped ({len(aa_files)})")
    require("CommandSet EgyptDozerCommandSet" in cs, "Egypt dozer")
    require("Command_ConstructArabicArmy_WarFactory" in block(cs, "CommandSet", "EgyptDozerCommandSet"), "Egypt lost AA WF")


def leftover_report(entries: dict[str, bytes]) -> list[str]:
    lines = []
    for k, v in sorted(entries.items()):
        if b"Arabic Alliance" in v or b"ArabicAlliance" in v:
            lines.append(k)
    return lines


def main() -> None:
    if not SRC_BIG.is_file():
        raise SystemExit(f"missing source BIG {SRC_BIG}")
    blob = SRC_BIG.read_bytes()
    require(sha256(blob) == SRC_SHA, "source BIG sha mismatch")
    orig = read_big(SRC_BIG)
    new = dict(orig)
    new[K_PT] = patch_pt(orig[K_PT])
    validate(orig, new)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_blob = build_big(new)
    digest = sha256(out_blob)
    OUT_BIG.write_bytes(out_blob)
    (OUT_DIR / "_SPEC_DATA_ONE.big.sha256").write_text(digest + "\n", encoding="ascii")
    lines = [f"{digest}  _SPEC_DATA_ONE.big"]
    copies = (
        ("CommandSet.ini", K_CS),
        ("CommandButton.ini", K_CB),
        ("PlayerTemplate.ini", K_PT),
    )
    for name, key in copies:
        (OUT_DIR / name).write_bytes(new[key])
        h = sha256(new[key])
        (OUT_DIR / f"{name}.sha256").write_text(h + "\n", encoding="ascii")
        lines.append(f"{h}  {name}")
    (OUT_DIR / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="ascii")
    left = leftover_report(new)
    (OUT_DIR / "LEFTOVER_ARABIC_ALLIANCE.txt").write_text(
        "\n".join(left) + "\n", encoding="ascii"
    )
    print("wrote", OUT_BIG, "bytes", len(out_blob), "sha256", digest)
    print("PT", sha256(new[K_PT]))
    print("leftover Arabic Alliance string files", len(left))
    for k in left:
        print(" ", k)


if __name__ == "__main__":
    main()
