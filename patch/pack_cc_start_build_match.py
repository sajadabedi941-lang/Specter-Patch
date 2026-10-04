#!/usr/bin/env python3
"""Match constructible Command Centers to starting MilitaryHQ for 7 countries.

Starting building is *_MilitaryHQ (PlayerTemplate StartingBuilding).
Constructible building is *_CommandCenter (dozer/worker construct button).

DATA-only. Reuses existing country Flag_HsCU meshes and flag TGAs.
Does not modify ART, construction buttons, or unrelated countries.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/IRAN_BUILDING_FLAGS/_SPEC_DATA_ONE.big")
SRC_ART = Path("/workspace/patch/Release/IRAN_BUILDING_FLAGS/_SPEC_ART_ONE.big")
EXPECTED_DATA_SHA = "6d31c347d790cd18e6ea8e20696e49cdeb0f9013da3d940f89b4f70f196f170a"
EXPECTED_ART_SHA = "ec4f5bdcc8f9e9171a8d9fb0d9523cffa41089eded03b330f0f1738aaf555760"
RELEASE = Path("/workspace/patch/Release/CC_START_BUILD_MATCH")
PAYLOAD = RELEASE / "payload"

HIDE = "      HideSubObject = F1 F2 F3 FPOLE HOUSECOLOR04 HOUSECOLOR05 HOUSECOLOR06"
CS_PACKED = r"Data\INI\CommandSet_ZZZZ_CommandCenterMatchStart.ini"

# Each country is patched from its own live MHQ / CC pair.
COUNTRIES = [
    {
        "id": "SaudiArabia",
        "mhq": r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_MilitaryHQ.ini",
        "cc": r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_CommandCenter.ini",
        "mhq_obj": "SaudiArabia_MilitaryHQ",
        "cc_obj": "SaudiArabia_CommandCenter",
        "flag": "SA__SAFlag_HsCU",
        "tex": b"SA_Flag.tga",
        "mhq_cs": "SaudiArabia_MilitaryHQCommandSet",
        "cc_cs": "SaudiArabia_CommandCenterCommandSet",
        "buttons": {
            "1": "Command_ConstructSaudiArabia_Worker",
            "2": "Command_ConstructSaudiArabia_VT72B",
            "12": "Command_ConstructSaudiArabia_IL-76",
            "13": "Command_SetRallyPoint",
            "14": "Command_Sell",
            "15": "Command_ConstructSaudiArabia_Alhussaien",
        },
    },
    {
        "id": "UAE",
        "mhq": r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_MilitaryHQ.ini",
        "cc": r"Data\INI\Object\Specter\United Arab Emirates Armed Forces\Buildings\UAE_CommandCenter.ini",
        "mhq_obj": "UAE_MilitaryHQ",
        "cc_obj": "UAE_CommandCenter",
        "flag": "AE__AEFlag_HsCU",
        "tex": b"UAE_Flag.tga",
        "mhq_cs": "UAE_MilitaryHQCommandSet",
        "cc_cs": "UAE_CommandCenterCommandSet",
        "buttons": {
            "1": "Command_ConstructUAE_Worker",
            "2": "Command_ConstructUAE_VT72B",
            "12": "Command_ConstructUAE_IL-76",
            "13": "Command_SetRallyPoint",
            "14": "Command_Sell",
            "15": "Command_ConstructUAE_Alhussaien",
        },
    },
    {
        "id": "Syria",
        "mhq": r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_MilitaryHQ.ini",
        "cc": r"Data\INI\Object\Specter\Syrian Armed Forces\Buildings\Syria_CommandCenter.ini",
        "mhq_obj": "Syria_MilitaryHQ",
        "cc_obj": "Syria_CommandCenter",
        "flag": "SY__SYFlag_HsCU",
        "tex": b"SY_Flag.tga",
        "mhq_cs": "Syria_MilitaryHQCommandSet",
        "cc_cs": "Syria_CommandCenterCommandSet",
        "buttons": {
            "1": "Command_ConstructSyria_Worker",
            "2": "Command_ConstructSyria_VT72B",
            "12": "Command_ConstructSyria_IL-76",
            "13": "Command_SetRallyPoint",
            "14": "Command_Sell",
            "15": "Command_ConstructSyria_Alhussaien",
        },
    },
    {
        "id": "India",
        "mhq": r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_MilitaryHQ.ini",
        "cc": r"Data\INI\Object\Specter\Indian Armed Forces\Buildings\India_CommandCenter.ini",
        "mhq_obj": "India_MilitaryHQ",
        "cc_obj": "India_CommandCenter",
        "flag": "IN__INFlag_HsCU",
        "tex": b"IN_Flag.tga",
        "mhq_cs": "India_MilitaryHQCommandSet",
        "cc_cs": "India_CommandCenterCommandSet",
        "buttons": {
            "1": "Command_ConstructIndia_Worker",
            "2": "Command_ConstructIndia_VT72B",
            "12": "Command_ConstructIndia_IL-76",
            "13": "Command_SetRallyPoint",
            "14": "Command_Sell",
            "15": "Command_ConstructIndia_Alhussaien",
        },
    },
    {
        "id": "Pakistan",
        "mhq": r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_MilitaryHQ.ini",
        "cc": r"Data\INI\Object\Specter\Pakistan Armed Forces\Buildings\Pakistan_CommandCenter.ini",
        "mhq_obj": "Pakistan_MilitaryHQ",
        "cc_obj": "Pakistan_CommandCenter",
        "flag": "PK__PKFlag_HsCU",
        "tex": b"PK_Flag.tga",
        "mhq_cs": "Pakistan_MilitaryHQCommandSet",
        "cc_cs": "Pakistan_CommandCenterCommandSet",
        "buttons": {
            "1": "Command_ConstructPakistan_Worker",
            "2": "Command_ConstructPakistan_VT72B",
            "12": "Command_ConstructPakistan_IL-76",
            "13": "Command_SetRallyPoint",
            "14": "Command_Sell",
            "15": "Command_ConstructPakistan_Alhussaien",
        },
    },
    {
        "id": "SouthAfrica",
        "mhq": r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_MilitaryHQ.ini",
        "cc": r"Data\INI\Object\Specter\South African National Defence Force\Buildings\SouthAfrica_CommandCenter.ini",
        "mhq_obj": "SouthAfrica_MilitaryHQ",
        "cc_obj": "SouthAfrica_CommandCenter",
        "flag": "ZA__ZAFlag_HsCU",
        "tex": b"ZA_Flag.tga",
        "mhq_cs": "SouthAfrica_MilitaryHQCommandSet",
        "cc_cs": "SouthAfrica_CommandCenterCommandSet",
        "buttons": {
            "1": "Command_ConstructSouthAfrica_Worker",
            "2": "Command_ConstructSouthAfrica_VT72B",
            "12": "Command_ConstructSouthAfrica_IL-76",
            "13": "Command_SetRallyPoint",
            "14": "Command_Sell",
            "15": "Command_ConstructSouthAfrica_Alhussaien",
        },
    },
    {
        "id": "Libya",
        "mhq": r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_MilitaryHQ.ini",
        "cc": r"Data\INI\Object\Specter\Libyan Armed Forces\Buildings\Libya_CommandCenter.ini",
        "mhq_obj": "Libya_MilitaryHQ",
        "cc_obj": "Libya_CommandCenter",
        "flag": "LY__LYFlag_HsCU",
        "tex": b"LY_Flag.tga",
        "mhq_cs": "Libya_MilitaryHQCommandSet",
        "cc_cs": "Libya_CommandCenterCommandSet",
        "buttons": {
            "1": "Command_ConstructLibya_Worker",
            "2": "Command_ConstructLibya_VT72B",
            "12": "Command_ConstructLibya_IL-76",
            "13": "Command_SetRallyPoint",
            "14": "Command_Sell",
            "15": "Command_ConstructLibya_Alhussaien",
        },
    },
]

# Missing constructible features copied from that country's own starting MHQ.
COPY_TAGS = [
    "ModuleTag_14",
    "ModuleTag_17",
    "ModuleTag_bgm",
    "ModuleTag_20",
    "ModuleTag_21",
    "ModuleTag_22",
    "ModuleTag_24",
    "ModuleTag_25",
    "ModuleTag_26",
    "ModuleTag_27",
    "ModuleTag_E3G",
    "ModuleTag_E3GS",
    "ModuleTag_MMT",
    "ModuleTag_32",
    "ModuleTag_33",
    "ModuleTag_34",
    "ModuleTag_Science",
    "ModuleTag_KillMarker",
    "ModuleTag_KillMarker2",
]

REQUIRED_SPECIALS = [
    "SuperweaponBGM109Strike",
    "SuperweaponDaisyCutter",
    "SpecialPowerSpyDrone",
    "SuperweaponParadropAmerica",
    "SpecialPowerSpySatellite",
    "SuperweaponCrateDrop",
    "SuperweaponA10ThunderboltMissileStrike",
    "SuperweaponEmergencyRepair",
    "SuperweaponAmerica_AWACS",
    "SuperweaponSpectreGunship",
    "SuperweaponLeafletDrop",
]

FROZEN_OBJECTS = [
    "Egypt_MilitaryHQ",
    "Egypt_CommandCenter",
    "Japan_Barracks",
    "SouthKorea_Barracks",
    "Vietnam_Barracks",
    "IranBarracks",
    "IranCommandCenter",
    "TurkeyCommandCenter",
    "BritainCommandCenter",
    "FranceCommandCenter",
    "GermanyCommandCenter",
    "ItalyCommandCenter",
    "SwedenCommandCenter",
    "UkraineCommandCenter",
    "Iraq_Barracks",
    "India_Barracks",
    "Pakistan_Barracks",
    "Libya_Barracks",
]

FROZEN_FILES = [
    r"Data\INI\CommandSet_ZZZZ_OilCapture_Class2.ini",
    r"Data\INI\CommandSet_ZZZZ_OilCapture_BarracksAndRifles.ini",
    r"Data\INI\CommandSet_ZZZZ_OilCapture_SoldierCommand.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_SAUAESYINPK.ini",
    r"Data\INI\CommandSet_ZZZZ_FighterRoster_Next14.ini",
    r"Data\INI\CommandButton.ini",
    r"Data\INI\CommandButton_Pakistan.ini",
]

OBJ_RE = re.compile(r"(?im)^Object\s+(\S+)")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def build_big_ordered(entries):
    header_size = 16
    encoded = [n.encode("latin1", errors="replace") for n, _ in entries]
    for nb in encoded:
        header_size += 8 + len(nb) + 1
    offset = header_size
    out = bytearray(b"BIGF")
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded):
        content = bytes(content)
        index.append((offset, len(content), nb))
        blobs.append(content)
        offset += len(content)
    total = offset
    out += struct.pack(">I", total)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for off, size, nb in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def find_index(entries, packed: str) -> int:
    want = packed.replace("/", "\\").lower()
    for i, (n, _) in enumerate(entries):
        if n.replace("/", "\\").lower() == want:
            return i
    raise SystemExit(f"missing {packed}")


def object_spans(text: str):
    ms = list(OBJ_RE.finditer(text))
    out = []
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        out.append((m.group(1), m.start(), end))
    return out


def last_objects(entries):
    last = {}
    for name, blob in entries:
        if not name.lower().endswith(".ini"):
            continue
        text = blob.decode("latin1", errors="replace")
        for obj, start, end in object_spans(text):
            last[obj] = text[start:end]
    return last


def nl_of(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def extract_block(text: str, pattern: str) -> str:
    m = re.search(pattern, text, flags=re.M | re.S)
    if not m:
        raise SystemExit(f"block not found: {pattern}")
    return m.group(0)


def extract_behavior(text: str, tag: str) -> str:
    return extract_block(
        text,
        rf"^  Behavior\s+=\s+\S+\s+{re.escape(tag)}\s*\n.*?^  End\s*$",
    )


def extract_strobe(mhq: str) -> str:
    block = extract_block(
        mhq,
        r"^  Draw\s+=\s+W3DModelDraw ModuleTag_03\s*\n.*?^  End\s*$",
    )
    if "US_COM_Strb" not in block:
        raise SystemExit("MHQ ModuleTag_03 is not the strobe draw")
    return block.replace("ModuleTag_03", "ModuleTag_Strb")


def flag_draw(model: str, tag: str, nl: str) -> str:
    block = f"""  ; ------------ Flag -----------------
  Draw                = W3DModelDraw {tag}
    ConditionState    = None
      Model           = {model}
      Animation       = {model}.{model}
      AnimationMode   = LOOP
    End
    AliasConditionState = NIGHT
    AliasConditionState = SNOW
    AliasConditionState = NIGHT SNOW

    ConditionState    = DAMAGED
      Model           = {model}
      Animation       = {model}.{model}
      AnimationMode   = LOOP
    End
    AliasConditionState = NIGHT DAMAGED
    AliasConditionState = SNOW DAMAGED
    AliasConditionState = NIGHT SNOW DAMAGED

    ConditionState    = REALLYDAMAGED RUBBLE
      Model           = {model}
      Animation       = {model}.{model}
      AnimationMode   = LOOP
    End
  End
"""
    return block.replace("\n", nl)


def add_hides_to_command_draw(text: str) -> str:
    if HIDE.strip() in text and text.count(HIDE.strip()) >= 3:
        return text
    nl = nl_of(text)
    lines = text.splitlines(keepends=True)
    out = []
    in_cmd = False
    state_lines: list[str] = []
    added = 0
    for line in lines:
        stripped = line.strip()
        if re.match(r"^  Draw\s+=\s+W3DModelDraw", line):
            in_cmd = True
            state_lines = []
            out.append(line)
            continue
        if in_cmd and re.match(r"^\s+ConditionState", line):
            state_lines = [line]
            out.append(line)
            continue
        if in_cmd and state_lines and stripped == "End":
            window = "".join(state_lines)
            if "US_Command" in window and "HideSubObject" not in window:
                out.append(HIDE + nl)
                added += 1
            out.append(line)
            state_lines = []
            continue
        if in_cmd and re.match(r"^  End\s*$", line):
            in_cmd = False
            state_lines = []
        if state_lines:
            state_lines.append(line)
        out.append(line)
    if added < 3:
        raise SystemExit(f"expected 3 HideSubObject inserts, got {added}")
    return "".join(out)


def patch_object(text: str, obj: str, transform) -> str:
    spans = object_spans(text)
    pieces = []
    last = 0
    found = False
    for name, start, end in spans:
        pieces.append(text[last:start])
        body = text[start:end]
        if name == obj:
            body = transform(body)
            found = True
        pieces.append(body)
        last = end
    pieces.append(text[last:])
    if not found:
        raise SystemExit(f"object {obj} missing")
    return "".join(pieces)


def patch_mhq(body: str, flag: str) -> str:
    if flag in body and HIDE.strip() in body:
        return body
    nl = nl_of(body)
    body = add_hides_to_command_draw(body)
    if flag not in body:
        # insert national Flag_Hs after the strobe draw
        m = re.search(
            r"^  Draw\s+=\s+W3DModelDraw ModuleTag_03\s*\n.*?^  End\s*$",
            body,
            flags=re.M | re.S,
        )
        if not m:
            raise SystemExit("MHQ strobe draw missing")
        body = body[: m.end()] + nl + flag_draw(flag, "ModuleTag_Flag", nl) + body[m.end() :]
    return body


def patch_cc(body: str, mhq: str, flag: str) -> str:
    if flag not in body:
        raise SystemExit("constructible CC lost its Flag_Hs")
    nl = nl_of(body)
    if "US_COM_Strb" not in body:
        strobe = extract_strobe(mhq).replace("\r\n", "\n").replace("\n", nl)
        m = re.search(r"(?im)^[ \t]*PlacementViewAngle\s*=", body)
        if not m:
            raise SystemExit("CC PlacementViewAngle missing")
        body = body[: m.start()] + strobe + nl + body[m.start() :]
    def has_tag(src: str, tag: str) -> bool:
        return re.search(rf"(?m)\b{re.escape(tag)}\b", src) is not None

    missing = []
    for tag in COPY_TAGS:
        if not has_tag(body, tag):
            missing.append(extract_behavior(mhq, tag))
    if missing:
        block = nl.join(missing) + nl
        m = re.search(r"(?im)^  Geometry\s+=", body)
        if not m:
            raise SystemExit("CC Geometry missing")
        body = body[: m.start()] + block + body[m.start() :]
    body = re.sub(
        r"(?im)^(\s+VoiceSelect\s+=\s+)\S+",
        r"\1CommandCenterUSASelect",
        body,
        count=1,
    )
    return body


def commandset_overlay() -> str:
    parts = [
        "; SPECTER last-win: constructible CommandCenter CommandSets match starting MilitaryHQ production.",
        "; Construction cost/time/geometry stay on the CommandCenter object. Dozer is not copied;",
        "; starting HQs produce Worker + VT72B + IL-76 + Alhussaien.",
        "",
    ]
    for c in COUNTRIES:
        parts.append(f"CommandSet {c['cc_cs']}")
        for slot, btn in c["buttons"].items():
            parts.append(f"  {slot} = {btn}")
        parts.append("End")
        parts.append("")
    return "\n".join(parts) + "\n"


def last_win_commandset(entries, name: str):
    pat = re.compile(
        rf"(?is)^CommandSet\s+{re.escape(name)}\s*\n(.*?)(?=^CommandSet\s|\Z)",
        re.M,
    )
    last = None
    src = None
    for n, blob in entries:
        if not n.lower().endswith(".ini") or "commandset" not in n.lower():
            continue
        text = blob.decode("latin1", errors="replace")
        for m in pat.finditer(text):
            last = m.group(0)
            src = n
    return src, last


def collect_buttons_and_objects(entries):
    buttons = {}
    objects = set()
    btn_re = re.compile(
        r"(?is)^CommandButton\s+(\S+)\s*\n(.*?)(?=^CommandButton\s|\Z)",
        re.M,
    )
    for n, blob in entries:
        if not n.lower().endswith(".ini"):
            continue
        text = blob.decode("latin1", errors="replace")
        for obj, _, _ in object_spans(text):
            objects.add(obj)
        if "commandbutton" not in n.lower():
            continue
        for m in btn_re.finditer(text):
            om = re.search(r"(?im)^  Object\s+=\s+(\S+)", m.group(2))
            buttons[m.group(1)] = om.group(1) if om else ""
    return buttons, objects


def field(text: str, pat: str) -> str:
    m = re.search(pat, text, flags=re.I | re.M)
    return m.group(1).strip() if m else ""


def write_payload(data_repl: dict[str, bytes]) -> None:
    if PAYLOAD.exists():
        for p in PAYLOAD.rglob("*"):
            if p.is_file():
                p.unlink()
    for name, blob in data_repl.items():
        dest = PAYLOAD / name.replace("\\", "/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)


def validate(art_entries, orig_data, new_data, data_repl) -> None:
    art_map = {n.replace("/", "\\").lower(): (n, b) for n, b in art_entries}
    orig_last = last_objects(orig_data)
    new_last = last_objects(new_data)
    buttons, objects = collect_buttons_and_objects(new_data)

    for obj in FROZEN_OBJECTS:
        if new_last.get(obj) != orig_last.get(obj):
            raise SystemExit(f"frozen object changed: {obj}")

    orig_map = {n.replace("/", "\\").lower(): b for n, b in orig_data}
    new_map = {n.replace("/", "\\").lower(): b for n, b in new_data}
    for packed in FROZEN_FILES:
        key = packed.replace("/", "\\").lower()
        if orig_map[key] != new_map[key]:
            raise SystemExit(f"frozen file changed: {packed}")

    # ART untouched
    if [n for n, _ in art_entries] != [n for n, _ in art_entries]:
        raise SystemExit("ART mutated")

    for c in COUNTRIES:
        mhq = new_last[c["mhq_obj"]]
        cc = new_last[c["cc_obj"]]
        flag = c["flag"]
        if flag not in mhq or flag not in cc:
            raise SystemExit(f"{c['id']}: Flag_Hs {flag} missing")
        if HIDE.strip() not in mhq or HIDE.strip() not in cc:
            raise SystemExit(f"{c['id']}: USA-flag hide missing")
        if "US_COM_Strb" not in mhq or "US_COM_Strb" not in cc:
            raise SystemExit(f"{c['id']}: strobe missing")
        if "BaseRegenerateUpdate" not in cc:
            raise SystemExit(f"{c['id']}: BaseRegenerateUpdate missing on CC")
        if not re.search(r"(?m)\bModuleTag_14\b", cc):
            raise SystemExit(f"{c['id']}: ModuleTag_14 missing on CC")
        if "ModuleTag_Flag" not in mhq:
            raise SystemExit(f"{c['id']}: MHQ ModuleTag_Flag missing")
        if "ModuleTag_Strb" not in cc:
            raise SystemExit(f"{c['id']}: CC ModuleTag_Strb missing")
        for sp in REQUIRED_SPECIALS:
            if sp not in mhq or sp not in cc:
                raise SystemExit(f"{c['id']}: special {sp} missing")
        # construction-specific values preserved on CC
        if field(cc, r"^Scale\s+=\s+(\S+)") != "0.9":
            raise SystemExit(f"{c['id']}: CC scale changed")
        if field(cc, r"^  BuildTime\s+=\s+(\S+)") != "4.0":
            raise SystemExit(f"{c['id']}: CC BuildTime changed")
        if field(cc, r"^  BuildCost\s+=\s+(\S+)") != "2000":
            raise SystemExit(f"{c['id']}: CC BuildCost changed")
        if field(cc, r"^\s+MaxHealth\s+=\s+(\S+)") != "2000.0":
            raise SystemExit(f"{c['id']}: CC HP changed")
        if field(cc, r"^  GeometryMajorRadius\s+=\s+(\S+)") != "65.0":
            raise SystemExit(f"{c['id']}: CC geometry changed")
        if field(cc, r"^  CommandSet\s+=\s+(\S+)") != c["cc_cs"]:
            raise SystemExit(f"{c['id']}: CC CommandSet name changed")
        # starting identity preserved
        if field(mhq, r"^  CommandSet\s+=\s+(\S+)") != c["mhq_cs"]:
            raise SystemExit(f"{c['id']}: MHQ CommandSet name changed")
        if field(mhq, r"^Scale\s+=\s+(\S+)") != "0.8":
            raise SystemExit(f"{c['id']}: MHQ scale changed")
        if field(mhq, r"^  BuildTime\s+=\s+(\S+)") != "45.0":
            raise SystemExit(f"{c['id']}: MHQ BuildTime changed")
        if field(mhq, r"^\s+MaxHealth\s+=\s+(\S+)") != "5000.0":
            raise SystemExit(f"{c['id']}: MHQ HP changed")
        if field(mhq, r"^  GeometryMajorRadius\s+=\s+(\S+)") != "110.0":
            raise SystemExit(f"{c['id']}: MHQ geometry changed")

        w3d_key = f"art\\w3d\\{flag.lower()}.w3d"
        if w3d_key not in art_map:
            raise SystemExit(f"missing {flag}.W3D")
        if c["tex"] not in art_map[w3d_key][1]:
            raise SystemExit(f"{flag} missing texture {c['tex']}")
        tex_key = f"art\\textures\\{c['tex'].decode().lower()}"
        if tex_key not in art_map:
            raise SystemExit(f"missing texture {c['tex']}")

        src, body = last_win_commandset(new_data, c["cc_cs"])
        if not body or CS_PACKED.split("\\")[-1].lower() not in src.lower():
            raise SystemExit(f"{c['id']}: CC CommandSet last-win is {src}")
        slots = dict(re.findall(r"(?im)^\s+(\d+)\s+=\s+(\S+)", body))
        if slots != c["buttons"]:
            raise SystemExit(f"{c['id']}: CC CommandSet slots {slots}")
        src_m, body_m = last_win_commandset(new_data, c["mhq_cs"])
        mhq_slots = dict(re.findall(r"(?im)^\s+(\d+)\s+=\s+(\S+)", body_m or ""))
        if mhq_slots != c["buttons"]:
            raise SystemExit(f"{c['id']}: starting CommandSet drifted {mhq_slots}")
        for btn in c["buttons"].values():
            if btn not in buttons:
                raise SystemExit(f"missing CommandButton {btn}")
            obj = buttons[btn]
            if obj and obj not in objects:
                raise SystemExit(f"missing Object {obj} for {btn}")

        construct = f"Command_Construct{c['id']}_CommandCenter"
        if buttons.get(construct) != c["cc_obj"]:
            raise SystemExit(f"{construct} retargeted to {buttons.get(construct)}")

    # no duplicate objects introduced
    seen = {}
    for n, blob in new_data:
        if not n.lower().endswith(".ini"):
            continue
        text = blob.decode("latin1", errors="replace")
        for obj, _, _ in object_spans(text):
            seen.setdefault(obj, []).append(n)
    # last-win duplicates are allowed for overlays; the 7 CC/MHQ objects must remain single-file
    for c in COUNTRIES:
        for obj in (c["mhq_obj"], c["cc_obj"]):
            files = {x.replace("/", "\\").lower() for x in seen.get(obj, [])}
            if len(files) != 1:
                raise SystemExit(f"{obj} defined in {files}")

    print("STATIC VALIDATION: PASS")
    print("  7 starting MilitaryHQ: national Flag_Hs + USA-flag hide")
    print("  7 constructible CommandCenter: Flag_Hs kept, strobes + starting powers restored")
    print("  CommandSets match starting Worker/VT72B/IL-76/Alhussaien")
    print("  Construction cost/time/geometry/HP preserved on CommandCenter")
    print("  ART unchanged; unrelated objects/files frozen")


def write_docs(data_sha: str) -> None:
    RELEASE.mkdir(parents=True, exist_ok=True)
    (RELEASE / "AUDIT.txt").write_text(
        "CC_START_BUILD_MATCH\n"
        f"SOURCE_DATA_SHA = {EXPECTED_DATA_SHA}\n"
        f"SOURCE_ART_SHA = {EXPECTED_ART_SHA}\n"
        "COUNTRIES = SaudiArabia UAE Syria India Pakistan SouthAfrica Libya\n"
        "STARTING = *_MilitaryHQ (PlayerTemplate StartingBuilding)\n"
        "CONSTRUCTIBLE = *_CommandCenter (Command_Construct*_CommandCenter)\n"
        "ROOT_CAUSE = Egypt-clone CommandCenter strip: Dozer-only CommandSet, no specials, no strobes;\n"
        "             starting MHQ has USA baked F1/F2/F3 and no national Flag_Hs.\n"
        "PAKISTAN_NOTE = CC already produced Worker; still missed vehicles/powers/strobes/flag-on-start.\n"
        "ART = UNCHANGED (reuse existing *Flag_HsCU + country TGA)\n"
        "DATA_REQUIRED = YES (Draw + behaviors + CommandSet last-win)\n"
        "INGAME_TESTED = NO\n",
        encoding="utf-8",
    )
    (RELEASE / "CHANGED_FILES.txt").write_text(
        "DATA replaced\n"
        + "\n".join(f"  {c['mhq']}\n  {c['cc']}" for c in COUNTRIES)
        + f"\nDATA added\n  {CS_PACKED}\n"
        "ART\n  NONE\n",
        encoding="utf-8",
    )
    (RELEASE / "CHANGELOG.txt").write_text(
        "CC_START_BUILD_MATCH\n\n"
        "Starting MilitaryHQ now hides US_Command F1/F2/F3 and attaches the existing\n"
        "country Flag_HsCU. Constructible CommandCenter keeps that Flag_Hs, gains the\n"
        "starting strobe draw and starting special-power modules, and its CommandSet\n"
        "matches the starting Worker/VT72B/IL-76/Alhussaien production.\n\n"
        "Preserved on constructible: Object name, CommandSet name, BuildCost 2000,\n"
        "BuildTime 4.0, Scale 0.9, HP 2000, 65x65 geometry, construct button target.\n"
        "Preserved on starting: Object name, CommandSet name, Scale 0.8, HP 5000,\n"
        "BuildTime 45.0, 110x90 geometry, strobes, specials.\n"
        "In-game test: NOT PERFORMED.\n",
        encoding="utf-8",
    )
    if data_sha:
        (RELEASE / "SHA256.txt").write_text(
            f"_SPEC_DATA_ONE.big {data_sha}\nART unchanged (IRAN_BUILDING_FLAGS ART SHA {EXPECTED_ART_SHA})\n",
            encoding="utf-8",
        )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", action="store_true")
    args = ap.parse_args()

    if sha256_file(SRC_DATA) != EXPECTED_DATA_SHA:
        raise SystemExit("source DATA SHA mismatch")
    if sha256_file(SRC_ART) != EXPECTED_ART_SHA:
        raise SystemExit("source ART SHA mismatch")

    art_entries = read_big(SRC_ART)
    data_entries = read_big(SRC_DATA)
    data_work = list(data_entries)
    data_repl: dict[str, bytes] = {}

    for c in COUNTRIES:
        mhq_i = find_index(data_work, c["mhq"])
        cc_i = find_index(data_work, c["cc"])
        mhq_name, mhq_blob = data_work[mhq_i]
        cc_name, cc_blob = data_work[cc_i]
        mhq_text = mhq_blob.decode("latin1", errors="replace")
        cc_text = cc_blob.decode("latin1", errors="replace")
        new_mhq = patch_object(mhq_text, c["mhq_obj"], lambda body, fl=c["flag"]: patch_mhq(body, fl))
        # CC transform needs the patched MHQ body for strobe/specials
        mhq_body = next(body for obj, s, e in object_spans(new_mhq) if obj == c["mhq_obj"] for body in [new_mhq[s:e]])
        new_cc = patch_object(
            cc_text,
            c["cc_obj"],
            lambda body, mh=mhq_body, fl=c["flag"]: patch_cc(body, mh, fl),
        )
        data_work[mhq_i] = (mhq_name, new_mhq.encode("latin1", errors="replace"))
        data_work[cc_i] = (cc_name, new_cc.encode("latin1", errors="replace"))
        data_repl[mhq_name] = data_work[mhq_i][1]
        data_repl[cc_name] = data_work[cc_i][1]
        print(f"PATCH {c['id']} MHQ+CC flag={c['flag']}")

    overlay = commandset_overlay().encode("latin1", errors="replace")
    data_work.append((CS_PACKED, overlay))
    data_repl[CS_PACKED] = overlay
    print("ADD", CS_PACKED)

    write_payload(data_repl)
    validate(art_entries, data_entries, data_work, data_repl)
    write_docs("")

    if args.pack:
        data_out = RELEASE / "_SPEC_DATA_ONE.big"
        data_out.write_bytes(build_big_ordered(data_work))
        sha = sha256_file(data_out)
        print("PACKED", data_out, sha, "bytes", data_out.stat().st_size)
        write_docs(sha)

        # post-pack: only intended DATA keys changed/added
        packed = read_big(data_out)
        src_map = {n.replace("/", "\\").lower(): b for n, b in data_entries}
        new_map = {n.replace("/", "\\").lower(): b for n, b in packed}
        added = sorted(set(new_map) - set(src_map))
        removed = sorted(set(src_map) - set(new_map))
        changed = sorted(k for k in src_map if k in new_map and src_map[k] != new_map[k])
        expect_changed = {c["mhq"].lower() for c in COUNTRIES} | {c["cc"].lower() for c in COUNTRIES}
        expect_added = {CS_PACKED.lower()}
        if set(added) != expect_added or removed or set(changed) != expect_changed:
            raise SystemExit(f"post-pack scope fail added={added} removed={removed} changed={changed}")
        print("POST-PACK SCOPE: PASS (14 INIs replaced, 1 CommandSet overlay added)")
    else:
        print("Payload written; BIG not packed (pass --pack after validation).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
