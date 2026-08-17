#!/usr/bin/env python3
"""Add proven Pakistan Large/Heavy airbases to Iraq, Russia, China, Israel, UAE.

Pakistan = READ-ONLY structural donor only.
Each faction keeps its OWN aircraft roster.
DATA-only. ART reused (TheAirPort + HXUSABigAirPort).
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace/patch")
DATA_BIG = ROOT / "Release/SPECTER_MASTER/_SPEC_DATA_ONE.big"
ART_BIG = ROOT / "Release/SPECTER_MASTER/_SPEC_ART_ONE.big"
OUT_DIR = ROOT / "Release/SPECTER_MASTER"
ZIP_PATH = ROOT / "Release/SPECTER_MASTER_DATA_FIVE_FACTION_DUAL_AIRBASE.zip"
NOTE = OUT_DIR / "DATA_FIVE_FACTION_DUAL_AIRBASE_HASHES.txt"
DL = OUT_DIR / "DATA_FIVE_FACTION_DUAL_AIRBASE_DOWNLOAD.txt"

BASE_DATA = "575d9010b7ab138db8592ac1ba85faad3ec0f107497cbd8acb86cfc2890f452f"
BASE_ART = "74a411b72c19fafaafcd48a45d2aa76731d8dbd13e919e4f73f8b989e90d4822"

# Per-faction config
FACTIONS = {
    "Iraq": {
        "side": "Iraq",
        "builder_obj": "Iraq_VT72B",
        "builder_cs": "Iraq_VT72BCommandSet",
        "airfield_btn": "Command_ConstructIraq_Airfield_T",
        "airfield_btn_extra": ["Command_ConstructIraqMilitaryAirfield"],  # also retarget
        "old_airfield_obj": "Iraq_Airfield_T",
        "lab": "Iraq_LargeAirBase",
        "hab": "Iraq_HeavyAirBase",
        "lab_cs": "Iraq_LargeAirBaseCommandSet",
        "hab_cs": "Iraq_HeavyAirBaseCommandSet",
        "lab_btn": "Command_ConstructIraq_LargeAirBase",  # unused; retarget existing
        "hab_btn": "Command_ConstructIraq_HeavyAirBase",
        "supply": "Iraq_SupplyCenter",
        "lab_path": r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_LargeAirBase.ini",
        "hab_path": r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_HeavyAirBase.ini",
        "large_roster": [
            "Command_ConstructIraq_Su-25K",
            "Command_ConstructIraq_Mig-23ML",
            "Command_ConstructIraq_Mi-35M3",
            "Command_ConstructIraq_Mi-28NE",
            "Command_ConstructIraq_Mig-29A",
            "Command_ConstructIraq_Mig-25BM",
            "Command_ConstructIraq_Su-22M3",
            "Command_ConstructIraq_Mi-8T",
            "Command_ConstructIraq_mirageF1Bq",
            "Command_UpgradeAmericaCountermeasures",
        ],
        "heavy_roster": [
            "Command_ConstructIraq_Su-24MK",
            "Command_ConstructIraq_Tu-22M3",
            "Command_ConstructIraq_Su-24MR",
            "Command_ConstructIraq_Tu-22M3_AI",
        ],
        # Stop slot 13 -> Heavy; move Stop to slot 18 (was MilitaryAirfield)
        "heavy_slot": 13,
        "stop_move_to_slot": 18,
    },
    "Russia": {
        "side": "Russia",
        "builder_obj": "RussiaVehicleDozer",
        "builder_cs": "RussiaDozerCommandSet",
        "airfield_btn": "Command_ConstructRussiaAirfield",
        "airfield_btn_extra": [],
        "old_airfield_obj": "RussiaAirfield",
        "lab": "Russia_LargeAirBase",
        "hab": "Russia_HeavyAirBase",
        "lab_cs": "Russia_LargeAirBaseCommandSet",
        "hab_cs": "Russia_HeavyAirBaseCommandSet",
        "hab_btn": "Command_ConstructRussia_HeavyAirBase",
        "supply": "RussiaSupplyCenter",
        "lab_path": r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\Russia_LargeAirBase.ini",
        "hab_path": r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Buildings\Russia_HeavyAirBase.ini",
        "large_roster": [
            "Command_ConstructRussiaJetSu75Checkmate",
            "Command_ConstructRussiaJetSu35S",
            "Command_ConstructRussiaJetSu30SM2",
            "Command_ConstructRussiaJetSU25T",
            "Command_ConstructRussiaJetSu35AG",
            "Command_ConstructRussiaJetMig31K",
            "Command_ConstructRussiaHelicopterMi28N",
            "Command_ConstructRussiaHelicopterKA52",
            "Command_ConstructRussiaJetSu57AA",
        ],
        "heavy_roster": [
            "Command_ConstructRussiaJetSu34",
            "Command_ConstructRussiaJetSU24M2",
            "Command_ConstructRussiaJetSu47Recon",
            "Command_ConstructRussiaJetSU24MP",
            "Command_ConstructRussiaJetTu22M3M",
        ],
        "heavy_slot": 13,  # free
    },
    "China": {
        "side": "China",
        "builder_obj": "ChinaVehicleDozer",
        "builder_cs": "PLADozerCommandSet",
        "airfield_btn": "Command_ConstructChinaAirfield",
        "airfield_btn_extra": [],
        "old_airfield_obj": "ChinaAirfield",
        "lab": "China_LargeAirBase",
        "hab": "China_HeavyAirBase",
        "lab_cs": "China_LargeAirBaseCommandSet",
        "hab_cs": "China_HeavyAirBaseCommandSet",
        "hab_btn": "Command_ConstructChina_HeavyAirBase",
        "supply": "ChinaSupplyCenter",
        "lab_path": r"Data\INI\Object\Specter\PLA\Buildings\China_LargeAirBase.ini",
        "hab_path": r"Data\INI\Object\Specter\PLA\Buildings\China_HeavyAirBase.ini",
        "large_roster": [
            "Command_ConstructChinaJetJ20B_AG",
            "Command_ConstructChinaJetJ50",
            "Command_ConstructChinaJetJ16D",
            "Command_ConstructChinaHelicopterWZ10ME",
            "Command_ConstructChinaJetJ16BBunker",
            "Command_ConstructChinaJetJ20B_AA",
            "Command_ConstructChinaJetJ10C",
            "Command_ConstructChinaJetJ20B_AA_AI",
        ],
        "heavy_roster": [
            "Command_ConstructChinaAircraftKJ500",
            "Command_ConstructChinaJetJH7BHeavy",
            "Command_ConstructChinaJetJH7A2",
            "Command_ConstructChinaHelicopterZ18A",
        ],
        "heavy_slot": 2,  # free (commented InternetCenter)
    },
    "Israel": {
        "side": "AmericaAirForceGeneral",
        "builder_obj": "AirF_AmericaVehicleDozer",
        "builder_cs": "AirF_AmericaDozerCommandSet",
        "airfield_btn": "AirF_Command_ConstructAmericaAirfield",
        "airfield_btn_extra": [],
        "old_airfield_obj": "AirF_AmericaAirfield",
        "lab": "Israel_LargeAirBase",
        "hab": "Israel_HeavyAirBase",
        "lab_cs": "Israel_LargeAirBaseCommandSet",
        "hab_cs": "Israel_HeavyAirBaseCommandSet",
        "hab_btn": "Command_ConstructIsrael_HeavyAirBase",
        "supply": "AirF_AmericaSupplyCenter",
        "lab_path": r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_LargeAirBase.ini",
        "hab_path": r"Data\INI\Object\Specter\Israel Defense Forces\Buildings\Israel_HeavyAirBase.ini",
        "iron_dome_btn": "Command_ConstructIsraelIronDomeBattery",
        "iron_dome_obj": "AirF_AmericaPatriotBattery",
        "iron_dome_slot": 4,
        "large_roster": [
            "AirF_Command_ConstructAmericaJetRaptor",
            "AirF_Command_ConstructAmericaVehicleComanche",
            "AirF_Command_ConstructAmericaJetAurora",
            "AirF_Command_ConstructAmericaJetStealthFighter",
            "Command_ConstructIsraelJetF35I_AA",
            "Command_ConstructIsrael_F16I_AG",
            "Command_ConstructIsraelJetF15IRaamDeepStrike",
            "Command_ConstructIsraelJetF35IAdirPenetrator",
            "Command_UpgradeAmericaCountermeasures",
            "Command_ConstructIsraelJetF16ISufaPrecision",
            "Command_ConstructIsrael_F15I_AA",
        ],
        "heavy_roster": [
            "Command_ConstructIsraelJetF15BazHeavyBomber",
            "Command_ConstructIsraelJetG550Eitam",
        ],
        "heavy_slot": 4,  # Iron Dome slot
    },
    "UAE": {
        "side": "UAE",
        "builder_obj": "UAE_Dozer",
        "builder_cs": "UAEDozerCommandSet",
        "airfield_btn": "Command_ConstructUAE_Airfield_T",
        "airfield_btn_extra": [],
        "old_airfield_obj": "UAE_LargeAirBase",  # already retargeted
        "lab": "UAE_LargeAirBase",
        "hab": "UAE_HeavyAirBase",
        "lab_cs": "UAE_AirfieldCommandSet",  # existing
        "hab_cs": "UAE_HeavyAirBaseCommandSet",
        "hab_btn": "Command_ConstructUAE_HeavyAirBase",
        "supply": "UAE_SupplyCenter",
        "lab_path": r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_LargeAirBase.ini",
        "hab_path": r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_HeavyAirBase.ini",
        "already_exists": True,
        "large_roster": [
            "Command_ConstructUAE_Mig-29A",
            "Command_ConstructUAE_MirageF1_Bq",
            "Command_ConstructUAE_Su-25K",
            "Command_ConstructUAE_Mi-8T",
            "Command_ConstructUAE_F16Blk52",
        ],
        "heavy_roster": [
            "Command_ConstructUAE_IL-76",
        ],
        "heavy_slot": 5,  # already
    },
}


def sha256(p: Path | bytes) -> str:
    b = p if isinstance(p, bytes) else Path(p).read_bytes()
    return hashlib.sha256(b).hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
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


def norm(n: str) -> str:
    return n.replace("/", "\\").lower()


def csf_label_set(csf: bytes) -> set[str]:
    nlabels = struct.unpack_from("<I", csf, 8)[0]
    pos = 24
    labels: set[str] = set()
    for _ in range(nlabels):
        if pos + 12 > len(csf) or csf[pos : pos + 4] != b" LBL":
            break
        namelen = struct.unpack_from("<I", csf, pos + 8)[0]
        numvals = struct.unpack_from("<I", csf, pos + 4)[0]
        pos += 12
        label = csf[pos : pos + namelen].decode("ascii", errors="replace")
        pos += namelen
        labels.add(label)
        for _v in range(numvals):
            vtag = csf[pos : pos + 4]
            pos += 4
            strlen = struct.unpack_from("<I", csf, pos)[0]
            pos += 4 + strlen * 2
            if vtag == b"WRTS":
                elen = struct.unpack_from("<I", csf, pos)[0]
                pos += 4 + elen
    return labels


def append_csf_label(csf: bytes, label: str, value: str) -> bytes:
    if label in csf_label_set(csf):
        return csf
    assert value.isascii(), value
    utf16 = value.encode("utf-16-le")
    char_count = len(utf16) // 2
    xored = bytes(b ^ 0xFF for b in utf16)
    label_b = label.encode("ascii")
    entry = bytearray()
    entry += b" LBL"
    entry += struct.pack("<I", 1)
    entry += struct.pack("<I", len(label_b))
    entry += label_b
    entry += b" RTS"
    entry += struct.pack("<I", char_count)
    entry += xored
    data = bytearray(csf)
    nlabels = struct.unpack_from("<I", data, 8)[0]
    nstrings = struct.unpack_from("<I", data, 12)[0]
    struct.pack_into("<I", data, 8, nlabels + 1)
    struct.pack_into("<I", data, 12, nstrings + 1)
    return bytes(data) + bytes(entry)


def parse_csf_ok(csf: bytes) -> tuple[int, int, list[str]]:
    nlabels = struct.unpack_from("<I", csf, 8)[0]
    pos = 24
    labels = []
    errors = []
    for i in range(nlabels):
        if pos + 12 > len(csf) or csf[pos : pos + 4] != b" LBL":
            errors.append(f"bad at {i}")
            break
        numvals = struct.unpack_from("<I", csf, pos + 4)[0]
        namelen = struct.unpack_from("<I", csf, pos + 8)[0]
        pos += 12
        lab = csf[pos : pos + namelen].decode("ascii", errors="replace")
        pos += namelen
        labels.append(lab)
        for _ in range(numvals):
            vtag = csf[pos : pos + 4]
            pos += 4
            strlen = struct.unpack_from("<I", csf, pos)[0]
            pos += 4 + strlen * 2
            if vtag == b"WRTS":
                elen = struct.unpack_from("<I", csf, pos)[0]
                pos += 4 + elen
    return nlabels, len(labels), errors


def clone_pak(pak_text: str, new_obj: str, side: str, supply: str, command_set: str, kind: str) -> str:
    out = pak_text
    if kind == "large":
        out = out.replace("Object Pakistan_LargeAirBase", f"Object {new_obj}")
        out = out.replace("Pakistan LARGE", f"{side} LARGE")
        out = out.replace("Pakistan_AirfieldCommandSet", command_set)
        out = out.replace("Pakistan_LargeAirBase", new_obj)
    else:
        out = out.replace("Object Pakistan_HeavyAirBase", f"Object {new_obj}")
        out = out.replace("Pakistan HEAVY", f"{side} HEAVY")
        out = out.replace("Pakistan_HeavyAirBaseCommandSet", command_set)
        out = out.replace("Pakistan_HeavyAirBase", new_obj)
    out = re.sub(r"(Side\s*=\s*)Pakistan\b", rf"\1{side}", out)
    out = re.sub(r"(Object\s*=\s*)Pakistan_SupplyCenter\b", rf"\1{supply}", out)
    out = re.sub(r"(CommandSet\s*=\s*)\S+", rf"\1{command_set}", out, count=1)
    assert f"Side             = {side}" in out or re.search(rf"Side\s*=\s*{re.escape(side)}\b", out)
    assert supply in out
    assert "Pakistan_SupplyCenter" not in out
    assert "Side             = Pakistan" not in out
    return out


def upsert_commandbutton(cb_text: str, name: str, block: str) -> str:
    m = re.search(rf"^CommandButton\s+{re.escape(name)}\b.*?^End\s*$", cb_text, re.M | re.S)
    if m:
        return cb_text[: m.start()] + block.rstrip() + "\n" + cb_text[m.end() :]
    return cb_text.rstrip() + "\n\n" + block.rstrip() + "\n"


def upsert_commandset(cs_text: str, name: str, block: str) -> str:
    m = re.search(rf"^CommandSet\s+{re.escape(name)}\b.*?^End\s*$", cs_text, re.M | re.S)
    if m:
        return cs_text[: m.start()] + block.rstrip() + "\n" + cs_text[m.end() :]
    return cs_text.rstrip() + "\n\n" + block.rstrip() + "\n"


def retarget_button_object(cb_text: str, btn_name: str, new_obj: str) -> str:
    """Replace Object= line inside an existing construct button; keep rest."""
    m = re.search(rf"^CommandButton\s+{re.escape(btn_name)}\b.*?^End\s*$", cb_text, re.M | re.S)
    assert m, btn_name
    block = m.group(0)
    block2, n = re.subn(r"(Object\s*=\s*)\S+", rf"\1{new_obj}", block, count=1)
    assert n == 1, btn_name
    return cb_text[: m.start()] + block2 + cb_text[m.end() :]


def make_roster_cs(name: str, buttons: list[str]) -> str:
    lines = [f"CommandSet {name}"]
    for i, btn in enumerate(buttons, 1):
        lines.append(f"  {i}  = {btn}")
    lines += ["  13 = Command_SetRallyPoint", "  14 = Command_Sell", "End", ""]
    return "\n".join(lines)


def object_exists(fmap: dict[str, bytes], obj: str) -> bool:
    for b in fmap.values():
        if re.search(rf"^Object\s+{re.escape(obj)}\b", b.decode("latin1", errors="replace"), re.M):
            return True
    return False


def object_count(fmap: dict[str, bytes], obj: str) -> int:
    return sum(
        1
        for b in fmap.values()
        if re.search(rf"^Object\s+{re.escape(obj)}\b", b.decode("latin1", errors="replace"), re.M)
    )


def main() -> None:
    assert sha256(DATA_BIG) == BASE_DATA, sha256(DATA_BIG)
    assert sha256(ART_BIG) == BASE_ART

    art_entries, _ = read_big(ART_BIG)
    art_names = {n.replace("/", "\\").lower() for n, _, _ in art_entries}
    assert any("theairport.w3d" in n for n in art_names)
    assert any("hxusabigairport.w3d" in n for n in art_names)

    entries, raw = read_big(DATA_BIG)
    fmap: dict[str, bytes] = {}
    disp: dict[str, str] = {}
    for name, off, size in entries:
        k = norm(name)
        if k not in fmap:
            disp[k] = name.replace("/", "\\")
        fmap[k] = raw[off : off + size]

    pak_lab_path = r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_LargeAirBase.ini"
    pak_hab_path = r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_HeavyAirBase.ini"
    pak_lab = fmap[norm(pak_lab_path)].decode("latin1")
    pak_hab = fmap[norm(pak_hab_path)].decode("latin1")
    pak_lab_bytes = fmap[norm(pak_lab_path)]
    pak_hab_bytes = fmap[norm(pak_hab_path)]
    assert "Model              = TheAirPort" in pak_lab
    assert "NumRows                 = 4" in pak_lab and "NumCols                 = 4" in pak_lab
    assert "Model              = HXUSABigAirPort" in pak_hab
    assert "NumRows                 = 2" in pak_hab and "NumCols                 = 3" in pak_hab

    # Freeze other factions' airbases / USA
    freeze_paths = {
        "pak_lab": pak_lab_path,
        "pak_hab": pak_hab_path,
        "usa_lab": r"Data\INI\Object\Specter\United States Of America\Buildings\America_LargeAirBase.ini",
        "usa_hab": r"Data\INI\Object\Specter\United States Of America\Buildings\America_HeavyAirBase.ini",
        "nato_lab": r"Data\INI\Object\Specter\NATO\Buildings\Nato_LargeAirBase.ini",
        "nk_lab": r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_LargeAirBase.ini",
        "egypt_lab": r"Data\INI\Object\Specter\Egyptian Armed Forces\Buildings\Egypt_LargeAirBase.ini",
    }
    freeze = {k: fmap[norm(p)] for k, p in freeze_paths.items() if norm(p) in fmap}

    cs_path = norm(r"Data\INI\CommandSet.ini")
    cb_path = norm(r"Data\INI\CommandButton.ini")
    pt_path = norm(r"Data\INI\PlayerTemplate.ini")
    pt_before = fmap[pt_path]
    cs_text = fmap[cs_path].decode("latin1")
    cb_text = fmap[cb_path].decode("latin1")
    # generals.csf intentionally untouched — reuse existing America HeavyAirBase labels

    # Freeze non-target PlayerTemplates
    freeze_pts = {}
    for name in (
        "FactionPakistan",
        "FactionAmerica",
        "FactionNato",
        "FactionEgypt",
        "FactionNorthKorea",
        "FactionSaudiArabia",
        "FactionIran",
    ):
        m = re.search(rf"^PlayerTemplate\s+{name}\b.*?^End\s*$", pt_before.decode("latin1"), re.M | re.S)
        if m:
            freeze_pts[name] = m.group(0)

    report_rows = {}

    for fac, cfg in FACTIONS.items():
        builder_cs = re.search(
            rf"^CommandSet\s+{re.escape(cfg['builder_cs'])}\b.*?^End\s*$", cs_text, re.M | re.S
        )
        assert builder_cs, cfg["builder_cs"]
        bcs = builder_cs.group(0)
        assert cfg["airfield_btn"] in bcs or cfg.get("already_exists"), (fac, cfg["airfield_btn"])

        # --- Objects ---
        if not cfg.get("already_exists"):
            lab_obj = clone_pak(pak_lab, cfg["lab"], cfg["side"], cfg["supply"], cfg["lab_cs"], "large")
            hab_obj = clone_pak(pak_hab, cfg["hab"], cfg["side"], cfg["supply"], cfg["hab_cs"], "heavy")
            assert "TheAirPort" in lab_obj and "HXUSABigAirPort" in hab_obj
            assert "Science" not in lab_obj.split("Prerequisites")[1].split("End")[0]
            assert "Science" not in hab_obj.split("Prerequisites")[1].split("End")[0]
            assert "IronDome" not in hab_obj and "Patriot" not in hab_obj
            assert norm(cfg["lab_path"]) not in fmap
            assert norm(cfg["hab_path"]) not in fmap
            fmap[norm(cfg["lab_path"])] = lab_obj.encode("latin1")
            disp[norm(cfg["lab_path"])] = cfg["lab_path"]
            fmap[norm(cfg["hab_path"])] = hab_obj.encode("latin1")
            disp[norm(cfg["hab_path"])] = cfg["hab_path"]
        else:
            # UAE: verify existing objects
            lab_existing = fmap[norm(cfg["lab_path"])].decode("latin1")
            hab_existing = fmap[norm(cfg["hab_path"])].decode("latin1")
            assert "TheAirPort" in lab_existing and "NumRows                 = 4" in lab_existing
            assert "HXUSABigAirPort" in hab_existing
            assert f"Side             = {cfg['side']}" in lab_existing

        # --- CommandSets (rosters) ---
        cs_text = upsert_commandset(cs_text, cfg["lab_cs"], make_roster_cs(cfg["lab_cs"], cfg["large_roster"]))
        cs_text = upsert_commandset(cs_text, cfg["hab_cs"], make_roster_cs(cfg["hab_cs"], cfg["heavy_roster"]))

        # UAE LargeAirBase object already points to UAE_AirfieldCommandSet (= lab_cs) — OK
        # For new objects CommandSet already set in clone.

        # --- Retarget airfield construct buttons ---
        cb_text = retarget_button_object(cb_text, cfg["airfield_btn"], cfg["lab"])
        for extra in cfg.get("airfield_btn_extra", []):
            if re.search(rf"^CommandButton\s+{re.escape(extra)}\b", cb_text, re.M):
                cb_text = retarget_button_object(cb_text, extra, cfg["lab"])

        # --- Heavy construct button ---
        if not cfg.get("already_exists") or cfg["hab_btn"] not in cb_text:
            # Always upsert Heavy button for non-UAE; UAE already has it
            pass
        # Reuse existing America HeavyAirBase CSF labels — do NOT append to generals.csf
        heavy_btn_block = f"""CommandButton {cfg['hab_btn']}
  Command       = DOZER_CONSTRUCT
  Object        = {cfg['hab']}
  TextLabel     = CONTROLBAR:ConstructAmerica_HeavyAirBase
  ButtonImage   = us_airfield
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipConstructAmerica_HeavyAirBase
End
"""
        if fac != "UAE":
            cb_text = upsert_commandbutton(cb_text, cfg["hab_btn"], heavy_btn_block)
        else:
            # ensure UAE heavy button still points to UAE_HeavyAirBase
            cb_text = retarget_button_object(cb_text, cfg["hab_btn"], cfg["hab"])

        # --- Wire builder CommandSet slots ---
        def patch_builder(m: re.Match, fac=fac, cfg=cfg) -> str:
            block = m.group(0)
            if fac == "Iraq":
                # slot 13 Stop -> Heavy; slot 18 -> Stop
                block = re.sub(
                    rf"({cfg['heavy_slot']}\s*=\s*)Command_Stop\b",
                    rf"\1{cfg['hab_btn']}",
                    block,
                )
                block = re.sub(
                    rf"({cfg['stop_move_to_slot']}\s*=\s*)Command_ConstructIraqMilitaryAirfield\b",
                    r"\1Command_Stop",
                    block,
                )
            elif fac == "Israel":
                block = re.sub(
                    rf"({cfg['iron_dome_slot']}\s*=\s*){re.escape(cfg['iron_dome_btn'])}\b",
                    rf"\1{cfg['hab_btn']}",
                    block,
                )
            elif fac == "UAE":
                # already has Heavy at slot 5; ensure still present
                assert cfg["hab_btn"] in block
            else:
                # Russia / China: insert/set free slot to Heavy
                slot = cfg["heavy_slot"]
                if re.search(rf"{slot}\s*=\s*", block):
                    # China slot 2 is commented — replace commented line or add
                    if fac == "China":
                        # Remove commented slot 2 line if present; set slot 2
                        block = re.sub(
                            r";\s*2\s*=\s*Command_ConstructChinaInternetCenter\s*\n",
                            f"  2  = {cfg['hab_btn']}\n",
                            block,
                        )
                        if f"{cfg['hab_btn']}" not in block:
                            # insert after slot 1
                            block = re.sub(
                                r"(1\s*=\s*Command_ConstructChinaPowerPlant\s*\n)",
                                rf"\1  2  = {cfg['hab_btn']}\n",
                                block,
                            )
                    else:
                        block = re.sub(
                            rf"({slot}\s*=\s*)\S+",
                            rf"\1{cfg['hab_btn']}",
                            block,
                            count=1,
                        )
                else:
                    # Russia: append slot before End
                    block = re.sub(
                        r"^End\s*$",
                        f" {slot} = {cfg['hab_btn']}\nEnd",
                        block,
                        count=1,
                        flags=re.M,
                    )
            return block

        cs_text2, nsub = re.subn(
            rf"^CommandSet\s+{re.escape(cfg['builder_cs'])}\b.*?^End\s*$",
            patch_builder,
            cs_text,
            count=1,
            flags=re.M | re.S,
        )
        assert nsub == 1, fac
        cs_text = cs_text2

        # Verify builder wiring
        bcs2 = re.search(
            rf"^CommandSet\s+{re.escape(cfg['builder_cs'])}\b.*?^End\s*$", cs_text, re.M | re.S
        ).group(0)
        assert cfg["hab_btn"] in bcs2, (fac, bcs2)
        if fac == "Iraq":
            assert "Command_Stop" in bcs2
            assert re.search(r"13\s*=\s*Command_ConstructIraq_HeavyAirBase", bcs2)
            assert re.search(r"18\s*=\s*Command_Stop", bcs2)
        if fac == "Israel":
            assert cfg["iron_dome_btn"] not in bcs2
            assert re.search(r"4\s*=\s*Command_ConstructIsrael_HeavyAirBase", bcs2)

        # Airfield button now points to Large
        bb = re.search(
            rf"^CommandButton\s+{re.escape(cfg['airfield_btn'])}\b.*?^End\s*$", cb_text, re.M | re.S
        ).group(0)
        assert re.search(rf"Object\s*=\s*{re.escape(cfg['lab'])}\b", bb), (fac, bb)

        report_rows[fac] = {
            "old": cfg["old_airfield_obj"],
            "lab": cfg["lab"],
            "hab": cfg["hab"],
            "heavy_slot": cfg["heavy_slot"],
            "large_roster": cfg["large_roster"],
            "heavy_roster": cfg["heavy_roster"],
            "airfield_btn": cfg["airfield_btn"],
            "builder_cs": cfg["builder_cs"],
            "builder_obj": cfg["builder_obj"],
            "side": cfg["side"],
        }

    fmap[cs_path] = cs_text.encode("latin1")
    fmap[cb_path] = cb_text.encode("latin1")

    # Freeze asserts
    for k, p in freeze_paths.items():
        if k in freeze:
            assert fmap[norm(p)] == freeze[k], k
    assert fmap[norm(pak_lab_path)] == pak_lab_bytes
    assert fmap[norm(pak_hab_path)] == pak_hab_bytes
    assert fmap[pt_path] == pt_before

    # Iron Dome object still exists
    assert object_exists(fmap, "AirF_AmericaPatriotBattery")

    DATA_BIG.write_bytes(build_big({disp[k]: v for k, v in fmap.items()}))
    data_sha = sha256(DATA_BIG)
    art_sha = sha256(ART_BIG)
    assert art_sha == BASE_ART

    # -------- RE-EXTRACT FINAL BIG --------
    e2, r2 = read_big(DATA_BIG)
    f2 = {norm(n): r2[o : o + s] for n, o, s in e2}
    cs2 = f2[cs_path].decode("latin1")
    cb2 = f2[cb_path].decode("latin1")

    undef_cs = undef_cb = undef_obj = 0
    for fac, cfg in FACTIONS.items():
        assert object_count(f2, cfg["lab"]) == 1, (fac, cfg["lab"], object_count(f2, cfg["lab"]))
        assert object_count(f2, cfg["hab"]) == 1, (fac, cfg["hab"])
        # Airfield button -> Large
        bb = re.search(
            rf"^CommandButton\s+{re.escape(cfg['airfield_btn'])}\b.*?^End\s*$", cb2, re.M | re.S
        ).group(0)
        assert re.search(rf"Object\s*=\s*{re.escape(cfg['lab'])}\b", bb)
        assert len(re.findall(rf"^CommandButton\s+{re.escape(cfg['airfield_btn'])}\b", cb2, re.M)) == 1
        # Heavy button
        assert len(re.findall(rf"^CommandButton\s+{re.escape(cfg['hab_btn'])}\b", cb2, re.M)) == 1
        hb = re.search(
            rf"^CommandButton\s+{re.escape(cfg['hab_btn'])}\b.*?^End\s*$", cb2, re.M | re.S
        ).group(0)
        assert re.search(rf"Object\s*=\s*{re.escape(cfg['hab'])}\b", hb)
        # Builder has heavy
        bcs = re.search(
            rf"^CommandSet\s+{re.escape(cfg['builder_cs'])}\b.*?^End\s*$", cs2, re.M | re.S
        ).group(0)
        assert cfg["hab_btn"] in bcs
        # Object properties
        lab = next(
            b.decode("latin1", errors="replace")
            for b in f2.values()
            if re.search(rf"^Object\s+{re.escape(cfg['lab'])}\b", b.decode("latin1", errors="replace"), re.M)
        )
        assert "Model              = TheAirPort" in lab
        assert "NumRows                 = 4" in lab and "NumCols                 = 4" in lab
        assert re.search(rf"Side\s*=\s*{re.escape(cfg['side'])}\b", lab)
        assert cfg["lab_cs"] in lab or (fac == "UAE" and "UAE_AirfieldCommandSet" in lab)
        hab = next(
            b.decode("latin1", errors="replace")
            for b in f2.values()
            if re.search(rf"^Object\s+{re.escape(cfg['hab'])}\b", b.decode("latin1", errors="replace"), re.M)
        )
        assert "HXUSABigAirPort" in hab
        assert "NumRows                 = 2" in hab and "NumCols                 = 3" in hab
        # Roster chains
        for cs_name, roster in ((cfg["lab_cs"], cfg["large_roster"]), (cfg["hab_cs"], cfg["heavy_roster"])):
            if cs_name not in cs2:
                undef_cs += 1
                continue
            csb = re.search(rf"^CommandSet\s+{re.escape(cs_name)}\b.*?^End\s*$", cs2, re.M | re.S).group(0)
            for btn in roster:
                assert btn in csb, (fac, btn)
                if btn not in cb2:
                    undef_cb += 1
                    continue
                abb = re.search(rf"^CommandButton\s+{re.escape(btn)}\b.*?^End\s*$", cb2, re.M | re.S)
                if not abb:
                    undef_cb += 1
                    continue
                if btn.startswith("Command_Upgrade") or btn.startswith("AirF_Command_Upgrade"):
                    continue
                om = re.search(r"Object\s*=\s*(\S+)", abb.group(0))
                if not om or not object_exists(f2, om.group(1)):
                    undef_obj += 1

    assert undef_cs == 0 and undef_cb == 0 and undef_obj == 0

    # Iraq stop preserved
    iraq_bcs = re.search(r"^CommandSet\s+Iraq_VT72BCommandSet\b.*?^End\s*$", cs2, re.M | re.S).group(0)
    assert "Command_Stop" in iraq_bcs
    assert "Command_ConstructIraq_HeavyAirBase" in iraq_bcs

    # Israel iron dome not on builder, object remains
    israel_bcs = re.search(r"^CommandSet\s+AirF_AmericaDozerCommandSet\b.*?^End\s*$", cs2, re.M | re.S).group(0)
    assert "Command_ConstructIsraelIronDomeBattery" not in israel_bcs
    assert object_exists(f2, "AirF_AmericaPatriotBattery")

    # Pakistan / USA frozen
    assert f2[norm(pak_lab_path)] == pak_lab_bytes
    assert f2[norm(pak_hab_path)] == pak_hab_bytes
    assert f2[pt_path] == pt_before
    for k, p in freeze_paths.items():
        if k in freeze:
            assert f2[norm(p)] == freeze[k], k

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")

    # Build report
    lines = ["FIVE-FACTION DUAL AIRBASE CONVERSION = PASS", ""]
    for fac, row in report_rows.items():
        lines.append(f"=== {fac.upper()} ===")
        lines.append(f"Builder Object = {row['builder_obj']}")
        lines.append(f"Active Builder CommandSet = {row['builder_cs']}")
        lines.append(f"Side = {row['side']}")
        lines.append(f"Old Airfield Object = {row['old']}")
        lines.append(f"Airfield ConstructButton = {row['airfield_btn']} -> {row['lab']}")
        lines.append(f"New LargeAirBase = {row['lab']}")
        lines.append(f"LargeAirBase W3D = TheAirPort.W3D")
        lines.append(f"Capacity = 16")
        lines.append(f"HeavyAirBase = {row['hab']}")
        lines.append(f"HeavyAirBase W3D = HXUSABigAirPort.W3D")
        lines.append(f"HeavyAirBase slot = {row['heavy_slot']}")
        lines.append(f"Heavy roster = {', '.join(row['heavy_roster'])}")
        if fac == "Iraq":
            lines.append("Stop functionality preserved = YES (moved to slot 18)")
        if fac == "Israel":
            lines.append("Exact Iron Dome ConstructButton = Command_ConstructIsraelIronDomeBattery")
            lines.append("Exact Iron Dome Object = AirF_AmericaPatriotBattery")
            lines.append("Iron Dome removed from builder slot = YES")
            lines.append("Iron Dome globally deleted = NO")
        if fac in ("Russia", "China", "UAE"):
            lines.append(f"Free slot used = {row['heavy_slot']}")
        lines.append("")
    lines += [
        "ALL FIVE LARGE AIRBASES USE TheAirPort.W3D = YES",
        "ALL FIVE LARGE AIRBASE CAPACITY = 16 = YES",
        "",
        "PAKISTAN CHANGED = NO",
        "USA CHANGED = NO",
        "OTHER FACTIONS CHANGED = NO",
        "ART CHANGED = NO",
        "",
        "ACTIVE FILES CHANGED:",
        "- Data\\INI\\CommandSet.ini",
        "- Data\\INI\\CommandButton.ini",
        "- Iraq_LargeAirBase.ini / Iraq_HeavyAirBase.ini (NEW)",
        "- Russia_LargeAirBase.ini / Russia_HeavyAirBase.ini (NEW)",
        "- China_LargeAirBase.ini / China_HeavyAirBase.ini (NEW)",
        "- Israel_LargeAirBase.ini / Israel_HeavyAirBase.ini (NEW)",
        "- UAE Large/Heavy objects preserved; CommandSets roster-split updated",
        "- Data\\English\\generals.csf UNCHANGED (reuses America HeavyAirBase labels)",
        "",
        f"DATA sha256 = {data_sha}",
        f"ART sha256  = {art_sha} (UNCHANGED)",
        f"ZIP sha256  = {sha256(ZIP_PATH)}",
        f"ZIP path    = {ZIP_PATH}",
        f"ZIP size    = {ZIP_PATH.stat().st_size}",
    ]
    report = "\n".join(lines) + "\n"
    NOTE.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
