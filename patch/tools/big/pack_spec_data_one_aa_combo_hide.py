#!/usr/bin/env python3
"""Hide Arabic Alliance from the skirmish/MP country combo.

Root cause of remove-arabic-alliance: GUIUtil.cpp
PopulatePlayerTemplateComboBox does NOT read PlayableSide or DisplayName.
It lists every PlayerTemplate whose StartingBuilding is non-empty, then
labels the row with CSF SIDE:<Side>. FactionGLA has StartingBuilding =
GLACommandCenter and Side = GLA, so SIDE:GLA ("Arabic Alliance") stayed
in the list even after PlayableSide = No / OldFaction = No.

This packer:
  * comments out StartingBuilding on PlayerTemplate FactionGLA
    (same empty-field hide Civilian/Observer already use)
  * keeps PlayableSide = No and OldFaction = No
  * keeps the FactionGLA block so maps/scripts still resolve the name
  * does not touch CommandSet.ini, CommandButton.ini, Shahed, Vietnam
    radar, ART, or 0_ overlays
  * does not edit generals.csf (SIDE:GLA stays "Arabic Alliance" but
    the row is no longer added)

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
OUT_DIR = ROOT / "Release/AA_COMBO_HIDE"
OUT_BIG = OUT_DIR / "_SPEC_DATA_ONE.big"

K_PT = r"Data\INI\PlayerTemplate.ini"
K_PT_DEFAULT = r"Data\INI\Default\PlayerTemplate.ini"
K_PT_PATCH = r"Data\INI\PlayerTemplate_SpecterPatch.ini"
K_CS = r"Data\INI\CommandSet.ini"
K_CB = r"Data\INI\CommandButton.ini"
K_WPN = r"Data\INI\Weapon.ini"
K_UAV = r"Data\INI\Object\Specter\SpecterRadarUavs.ini"
K_VN = (
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Vietnam_RadarStation.ini"
)
K_CSF = r"Data\English\generals.csf"

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

STARTING_RE = re.compile(r"^(\s*)StartingBuilding\s*=\s*(\S*)\s*$", re.M)
SIDE_RE = re.compile(r"^\s*Side\s*=\s*(\S+)", re.M)
PLAY_RE = re.compile(r"PlayableSide\s*=\s*(\S+)")


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


def nl_of(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def starting_of(body: str) -> str | None:
    m = STARTING_RE.search(body)
    return None if m is None else m.group(2)


def playable_of(text: str, name: str) -> str:
    body = block(text, "PlayerTemplate", name)
    m = PLAY_RE.search(body)
    require(m is not None, f"{name} has no PlayableSide")
    return m.group(1)


def decode_csf_label(blob: bytes, wanted: str) -> str | None:
    if len(blob) < 24:
        return None
    magic, _ver, nlab, _nstr, _unk, _lang = struct.unpack_from("<4sIIIII", blob, 0)
    if magic not in (b"CSF ", b" FSC"):
        return None
    off = 24
    for _ in range(nlab):
        _tag, nstrings, namelen = struct.unpack_from("<4sII", blob, off)
        off += 12
        name = blob[off : off + namelen].decode("ascii", "replace").rstrip("\x00")
        off += namelen
        value = ""
        for _s in range(nstrings):
            stag = blob[off : off + 4]
            off += 4
            slen = struct.unpack_from("<I", blob, off)[0]
            off += 4
            raw = blob[off : off + slen * 2]
            off += slen * 2
            if stag == b"WRTS":
                extra_len = struct.unpack_from("<I", blob, off)[0]
                off += 4 + extra_len
            chars = []
            for i in range(0, len(raw), 2):
                u = struct.unpack_from("<H", raw, i)[0] ^ 0xFFFF
                chars.append(chr(u) if u else "")
            if not value:
                value = "".join(chars).rstrip("\x00")
        if name == wanted:
            return value
    return None


def combo_visible(body: str) -> bool:
    """True if GUIUtil.cpp would add this template to the country combo."""
    start = starting_of(body)
    return bool(start)


def patch_pt(raw: bytes) -> bytes:
    text = raw.decode("latin1")
    gla = block(text, "PlayerTemplate", "FactionGLA")
    require("PlayableSide      = Yes" in gla, "FactionGLA not playable in source")
    require("OldFaction        = Yes" in gla, "FactionGLA OldFaction missing")
    require("DisplayName       = INI:FactionGLA" in gla, "FactionGLA display")
    require("Side              = GLA" in gla, "FactionGLA side")
    require("StartingBuilding  = GLACommandCenter" in gla, "source StartingBuilding")
    nl = nl_of(gla)
    new_gla = gla.replace("PlayableSide      = Yes", "PlayableSide      = No", 1)
    new_gla = new_gla.replace("OldFaction        = Yes", "OldFaction        = No", 1)
    old_line = f"  StartingBuilding  = GLACommandCenter{nl}"
    new_line = (
        "  ;StartingBuilding  = GLACommandCenter"
        "  ; SPECTER_PATCH AA_COMBO_HIDE"
        f"{nl}"
    )
    require(old_line in new_gla, "StartingBuilding line not found for comment-out")
    new_gla = new_gla.replace(old_line, new_line, 1)
    require("PlayableSide      = No" in new_gla, "PlayableSide not No")
    require("PlayableSide      = Yes" not in new_gla, "PlayableSide still Yes")
    require(STARTING_RE.search(new_gla) is None, "StartingBuilding still active")
    require(text.count(gla) == 1, "duplicate FactionGLA block")
    return text.replace(gla, new_gla, 1).encode("latin1")


def validate(orig: dict[str, bytes], new: dict[str, bytes]) -> None:
    require(orig[K_CS] == new[K_CS], "CommandSet.ini changed")
    require(orig[K_CB] == new[K_CB], "CommandButton.ini changed")
    require(orig[K_WPN] == new[K_WPN], "Weapon.ini changed")
    require(orig[K_UAV] == new[K_UAV], "Shahed UAV file changed")
    require(orig[K_VN] == new[K_VN], "Vietnam radar changed")
    require(orig[K_CSF] == new[K_CSF], "CSF changed")
    require(orig[K_PT_DEFAULT] == new[K_PT_DEFAULT], "Default PlayerTemplate changed")
    require(orig[K_PT_PATCH] == new[K_PT_PATCH], "SpecterPatch PlayerTemplate changed")
    changed = [k for k in orig if orig[k] != new[k]]
    require(changed == [K_PT], f"unexpected files changed: {changed}")

    orig_pt = orig[K_PT].decode("latin1")
    new_pt = new[K_PT].decode("latin1")
    gla = block(new_pt, "PlayerTemplate", "FactionGLA")
    require(playable_of(new_pt, "FactionGLA") == "No", "GLA still PlayableSide Yes")
    require("OldFaction        = No" in gla, "OldFaction")
    require(STARTING_RE.search(gla) is None, "GLA StartingBuilding still parsed")
    require("SPECTER_PATCH AA_COMBO_HIDE" in gla, "installer marker missing")
    require("Side              = GLA" in gla, "GLA Side lost")
    require("PlayerTemplate FactionGLA" in new_pt, "FactionGLA template deleted")
    require(not combo_visible(gla), "GLA would still appear in combo")

    # No other template with Side=GLA and a StartingBuilding can steal SIDE:GLA.
    names = re.findall(r"^PlayerTemplate (\S+)", new_pt, re.M)
    require(len(names) == len(set(names)), f"duplicate templates {names}")
    gla_sides = []
    combo_sides = []
    for name in names:
        body = block(new_pt, "PlayerTemplate", name)
        sm = SIDE_RE.search(body)
        require(sm is not None, f"{name} has no Side")
        side = sm.group(1)
        if side == "GLA":
            gla_sides.append(name)
            require(name == "FactionGLA", f"extra Side=GLA template {name}")
            require(not combo_visible(body), f"{name} still combo-visible")
        if combo_visible(body):
            combo_sides.append((name, side))
    require(gla_sides == ["FactionGLA"], f"GLA side templates {gla_sides}")
    require(
        all(side != "GLA" for _n, side in combo_sides),
        f"combo still has SIDE:GLA via {combo_sides}",
    )

    for name in KEEP_PLAYABLE:
        require(playable_of(orig_pt, name) == "Yes", f"{name} was not playable")
        require(playable_of(new_pt, name) == "Yes", f"{name} lost playable")
        require(
            block(orig_pt, "PlayerTemplate", name) == block(new_pt, "PlayerTemplate", name),
            f"{name} template edited",
        )
        require(combo_visible(block(new_pt, "PlayerTemplate", name)), f"{name} lost StartingBuilding")

    # Default PT is a header only — no second FactionGLA to restore StartingBuilding.
    default_pt = new[K_PT_DEFAULT].decode("latin1")
    require("PlayerTemplate " not in default_pt, "Default PlayerTemplate defines a template")

    patch_pt_txt = new[K_PT_PATCH].decode("latin1")
    require("PlayerTemplate FactionGLA" not in patch_pt_txt, "SpecterPatch redefines FactionGLA")
    require("PlayerTemplate FactionEgypt" in patch_pt_txt, "Egypt overlay")

    # Engine does not load SpecterPatch (PlayerTemplateStore has no dirpath),
    # but Egypt/Israel must not have Side=GLA if some overlay concatenates them.
    for extra in ("FactionEgypt", "FactionIsrael"):
        body = block(patch_pt_txt, "PlayerTemplate", extra)
        sm = SIDE_RE.search(body)
        require(sm is not None and sm.group(1) != "GLA", f"{extra} Side is GLA")

    cs = new[K_CS].decode("latin1")
    require(
        "12 = Command_ConstructSpecterRadarShahedLauncher"
        in block(cs, "CommandSet", "Vietnam_RadarStationCommandSet"),
        "VN Shahed",
    )
    uav = block(new[K_UAV].decode("latin1"), "Object", "SpecterRadar_ShahedLauncher")
    require("BuildCost       = 8000" in uav, "Shahed cost")
    require("IranShahed136FireCommandSet" in uav, "Shahed Fire")
    require("Command_ConstructIraq_RadarStation" in cs, "Iraq radar CS")
    require("PlayerTemplate FactionIraq" in new_pt, "Iraq template")
    aa_files = [k for k in new if "\\Arabic Alliance\\" in k]
    require(len(aa_files) > 50, f"Arabic Alliance object folder stripped ({len(aa_files)})")
    require("CommandSet EgyptDozerCommandSet" in cs, "Egypt dozer")
    require(
        "Command_ConstructArabicArmy_WarFactory"
        in block(cs, "CommandSet", "EgyptDozerCommandSet"),
        "Egypt lost AA WF",
    )

    side_gla = decode_csf_label(new[K_CSF], "SIDE:GLA")
    ini_gla = decode_csf_label(new[K_CSF], "INI:FactionGLA")
    require(side_gla == "Arabic Alliance", f"SIDE:GLA is {side_gla!r}")
    require(ini_gla == "Arabic Alliance", f"INI:FactionGLA is {ini_gla!r}")


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
    print("PT", sha256(new[K_PT]), "bytes", len(new[K_PT]))
    print("CS", sha256(new[K_CS]))
    print("CB", sha256(new[K_CB]))
    print("leftover Arabic Alliance string files", len(left))
    gla = block(new[K_PT].decode("latin1"), "PlayerTemplate", "FactionGLA")
    print("--- FactionGLA ---")
    print(gla)


if __name__ == "__main__":
    main()
