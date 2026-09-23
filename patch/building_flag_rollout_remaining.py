#!/usr/bin/env python3
"""BUILDING_FLAG_ROLLOUT remaining target countries.

Sequential isolated packages. Each country starts from the previous
audited pair. Shared donor W3Ds are never edited.

Change countries (wrong baked donor flags):
  05 UAE, 06 Syria, 07 South Africa, 08 South Korea, 09 Libya

No-change countries (US meshes, no baked *Flag.tga):
  Turkey, Ukraine, Sweden, Italy, United Kingdom, Germany, France
"""
from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

import japan_france_roster_01 as jf

STAGE04_DIR = Path("/workspace/patch/Release/BUILDING_FLAG_STAGE_04_SAUDI_ARABIA_ONLY")
STAGE04_DATA_SHA = "5aebc87bcef0c741c013a9b3e8e2133468f50d1265cc6b02efe4042d1fcf8818"
STAGE04_ART_SHA = "ea8c9ab10787b61421a7a4eaca96c765ca08755e0d110eb2138d48776cc23779"

P_DONOR_W3D = r"Art\W3D\Irq__IqFlag_Hs.W3D"
P_NK_W3D = r"Art\W3D\NKr__NKFlag_Hs.W3D"
P_JP_W3D = r"Art\W3D\JP__JPFlag_Hs.W3D"
P_VN_W3D = r"Art\W3D\VN__VNFlag_Hs.W3D"
P_SA_W3D = r"Art\W3D\SA__SAFlag_Hs.W3D"
P_IRQ_CAMP = r"Art\W3D\irq_camp.W3D"
P_IRQ_POWER = r"Art\W3D\Iraq_Powerplant.W3D"
P_IRQ_SUPPLY = r"Art\W3D\Iraq_Supply.W3D"
P_IRQ_WF = r"Art\W3D\Irq_WarFactory.W3D"
P_NK_POWER = r"Art\W3D\NKor_Powerplant.W3D"
P_NK_SUPPLY = r"Art\W3D\NKor_Supply.W3D"
P_NK_WF = r"Art\W3D\NKr_WarFactory.W3D"
P_NK_CC = r"Art\W3D\NKr_Command.W3D"
P_US_CAMP = r"Art\W3D\US_Camp.W3D"
P_IRQ_DDS = r"Art\Textures\IraqiFlag.dds"
P_DPRK_TGA = r"Art\Textures\DPRK_Flag.tga"
P_DPRK_DDS = r"Art\Textures\DPRK_Flag.dds"
P_PT = r"Data\INI\PlayerTemplate.ini"
P_PT_PATCH = r"Data\INI\PlayerTemplate_SpecterPatch.ini"
P_PAGES = r"Data\INI\MappedImages\HandCreated\Specter_FactionLogoPages.INI"
P_REMAIN = r"Data\INI\MappedImages\HandCreated\Specter_RemainingFlags.INI"
P_CAMP = r"Data\INI\MappedImages\HandCreated\Specter_CampFlags.INI"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_CMDSET = r"Data\INI\CommandSet.ini"
P_JP_BARRACKS = (
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Iraq_Barracks.ini"
)
P_VN_BARRACKS = (
    r"Data\INI\Object\Specter\Vietnam People's Armed Forces\Buildings\Iraq_Barracks.ini"
)
P_SA_BARRACKS = (
    r"Data\INI\Object\Specter\Saudi Arabia Armed Forces\Buildings\SaudiArabia_Barracks.ini"
)
P_NK_ABBAS = (
    r"Data\INI\Object\Specter\North Korea\Buildings\NorthKorea_NuclearCenter.ini"
)

DONOR_NAME = b"IRQ__IQFLAG_HS"
DONOR_TEX = b"IraqiFlag.dds"

IRQ_ADD = {
    "barracks_models": {"irq_camp"},
    "barracks_anims": {"irq_camp.irq_camp"},
    "power_models": {"Iraq_Powerplant"},
    "power_anims": {"Iraq_Powerplant.Iraq_Powerplant"},
    "supply_models": {"Iraq_Supply"},
    "supply_anims": {"Iraq_Supply.Iraq_Supply"},
    "wf_models": {"Irq_WarFactory", "UBArmDeal_DNS"},
    "wf_anims": {"Irq_WarFactory.Irq_WarFactory", "UBArmDeal_DNS.UBArmDeal_DNS"},
}


def irq_style(folder: str, stem: str, object_prefix: str, wf_object: str) -> dict:
    b = rf"Data\INI\Object\Specter\{folder}\Buildings"
    return {
        "add": (
            {
                "path": rf"{b}\{stem}_Barracks.ini",
                "object": f"Object {object_prefix}_Barracks",
                "models": IRQ_ADD["barracks_models"],
                "anims": IRQ_ADD["barracks_anims"],
            },
            {
                "path": rf"{b}\{stem}_PowerPlant.ini",
                "object": f"Object {object_prefix}_PowerPlant",
                "models": IRQ_ADD["power_models"],
                "anims": IRQ_ADD["power_anims"],
            },
            {
                "path": rf"{b}\{stem}_SupplyCenter.ini",
                "object": f"Object {object_prefix}_SupplyCenter",
                "models": IRQ_ADD["supply_models"],
                "anims": IRQ_ADD["supply_anims"],
            },
            {
                "path": rf"{b}\{stem}_WarFactory.ini",
                "object": f"Object {wf_object}",
                "models": IRQ_ADD["wf_models"],
                "anims": IRQ_ADD["wf_anims"],
            },
        ),
        "retarget": (
            {
                "path": rf"{b}\{stem}_Abbas.ini",
                "object": f"Object {object_prefix}_Abbas",
                "old": "Irq__IqFlag_Hs",
                "keep_models": {"Irq_Hussien", "Irq_Hussien_A1"},
                "keep_anims": {"Irq_Hussien_A1.Irq_Hussien_A1"},
            },
        ),
        "skip": (
            rf"{b}\{stem}_RadarStation.ini",
            rf"{b}\{stem}_CommandCenter.ini",
        ),
        "note": (
            "Barracks/Power/Supply/WF use Iraqi donor meshes with baked "
            "FLAG01/02/03. Abbas Flag_Hs pointed at Irq__IqFlag_Hs. "
            "Radar Irq_P3 and CommandCenter US_Command have no baked flags."
        ),
    }


UAE = irq_style(
    "United Arab Emirates Armed Forces", "UAE", "UAE", "UAE_WarFactory_T"
)
SYRIA = irq_style("Syrian Armed Forces", "Syria", "Syria", "Syria_WarFactory_T")
ZA = irq_style(
    "South African National Defence Force",
    "SouthAfrica",
    "SouthAfrica",
    "SouthAfrica_WarFactory_T",
)
LIBYA = irq_style("Libyan Armed Forces", "Libya", "Libya", "Libya_WarFactory_T")

SK_FOLDER = r"Data\INI\Object\Specter\South Korean Armed Forces"
SK = {
    "add": (
        {
            "path": rf"{SK_FOLDER}\Buildings\Iraq_Barracks.ini",
            "object": "Object SouthKorea_Barracks",
            "models": {"irq_camp"},
            "anims": {"irq_camp.irq_camp"},
        },
        {
            "path": rf"{SK_FOLDER}\Buildings\Iraq_PowerPlant.ini",
            "object": "Object SouthKorea_PowerPlant",
            "models": {"NKor_Powerplant"},
            "anims": {"NKor_Powerplant.NKor_Powerplant"},
        },
        {
            "path": rf"{SK_FOLDER}\SouthKorea_Systems.ini",
            "object": "Object SouthKorea_PowerPlant",
            "models": {"Iraq_Powerplant"},
            "anims": {"Iraq_Powerplant.Iraq_Powerplant"},
        },
        {
            "path": rf"{SK_FOLDER}\Buildings\Iraq_SupplyCenter.ini",
            "object": "Object SouthKorea_SupplyCenter",
            "models": {"NKor_Supply"},
            "anims": {"NKor_Supply.NKor_Supply"},
        },
        {
            "path": rf"{SK_FOLDER}\Buildings\SouthKorea_SupplyCenter.ini",
            "object": "Object SouthKorea_SupplyCenter",
            "models": {"NKor_Supply"},
            "anims": {"NKor_Supply.NKor_Supply"},
        },
        {
            "path": rf"{SK_FOLDER}\Buildings\SouthKorea_WarFactory.ini",
            "object": "Object SouthKorea_WarFactory",
            "models": {"NKr_WarFactory", "UBArmDeal_DNS"},
            "anims": {
                "NKr_WarFactory.NKr_WarFactory",
                "UBArmDeal_DNS.UBArmDeal_DNS",
            },
        },
        {
            "path": rf"{SK_FOLDER}\Buildings\SouthKorea_CommandCenter.ini",
            "object": "Object SouthKorea_CommandCenter",
            "models": {"NKr_Command"},
            "anims": {"NKr_Command.NKr_Command"},
        },
    ),
    "retarget": (
        {
            "path": rf"{SK_FOLDER}\Buildings\SouthKorea_NuclearCenter.ini",
            "object": "Object SouthKorea_Abbas",
            "old": "NKr__NKFlag_Hs",
            "keep_models": {"Irq_Hussien", "Irq_Hussien_A1"},
            "keep_anims": {"Irq_Hussien_A1.Irq_Hussien_A1"},
        },
    ),
    "skip": (
        rf"{SK_FOLDER}\Buildings\Iraq_RadarStation.ini",
        rf"{SK_FOLDER}\Buildings\SouthKorea_RadarStation.ini",
    ),
    "note": (
        "Barracks uses irq_camp (Iraqi baked flags). Power/Supply/WF/CC use "
        "NK meshes with baked DPRK flags (Power last-win also uses "
        "Iraq_Powerplant in Systems.ini). Abbas Flag_Hs is NKr__NKFlag_Hs. "
        "Radar Irq_P3 has no baked flags. North Korea files are not touched."
    ),
}

CHANGE_COUNTRIES = (
    {
        "stage": 5,
        "slug": "UAE",
        "release": "BUILDING_FLAG_STAGE_05_UAE_ONLY",
        "country": "UAE",
        "w3d": "AE__AEFlag_Hs",
        "internal": b"AE__AEFLAG_HS",
        "tex": b"UAE_Flag.tga",
        "tex_path": r"Art\Textures\UAE_Flag.tga",
        **UAE,
    },
    {
        "stage": 6,
        "slug": "SYRIA",
        "release": "BUILDING_FLAG_STAGE_06_SYRIA_ONLY",
        "country": "Syria",
        "w3d": "SY__SYFlag_Hs",
        "internal": b"SY__SYFLAG_HS",
        "tex": b"SY_Flag.tga",
        "tex_path": r"Art\Textures\SY_Flag.tga",
        **SYRIA,
    },
    {
        "stage": 7,
        "slug": "SOUTHAFRICA",
        "release": "BUILDING_FLAG_STAGE_07_SOUTH_AFRICA_ONLY",
        "country": "South Africa",
        "w3d": "ZA__ZAFlag_Hs",
        "internal": b"ZA__ZAFLAG_HS",
        "tex": b"ZA_Flag.tga",
        "tex_path": r"Art\Textures\ZA_Flag.tga",
        **ZA,
    },
    {
        "stage": 8,
        "slug": "SOUTHKOREA",
        "release": "BUILDING_FLAG_STAGE_08_SOUTH_KOREA_ONLY",
        "country": "South Korea",
        "w3d": "SK__SKFlag_Hs",
        "internal": b"SK__SKFLAG_HS",
        "tex": b"SK_Flag.tga",
        "tex_path": r"Art\Textures\SK_Flag.tga",
        **SK,
    },
    {
        "stage": 9,
        "slug": "LIBYA",
        "release": "BUILDING_FLAG_STAGE_09_LIBYA_ONLY",
        "country": "Libya",
        "w3d": "LY__LYFlag_Hs",
        "internal": b"LY__LYFLAG_HS",
        "tex": b"LY_Flag.tga",
        "tex_path": r"Art\Textures\LY_Flag.tga",
        **LIBYA,
    },
)

NOCHANGE = (
    ("10", "TURKEY", "Turkey", "Turkish Armed Forces", "US_Camp / US_Powerplant / US_Supply / US_WarFactory / US_Command"),
    ("11", "UKRAINE", "Ukraine", "Ukrainian Armed Forces", "US_Camp / US_Powerplant / US_Supply / US_WarFactory / US_Command"),
    ("12", "SWEDEN", "Sweden", "Swedish Armed Forces", "US_Camp / US_Powerplant / US_Supply / US_WarFactory / US_Command"),
    ("13", "ITALY", "Italy", "Italian Armed Forces", "US_Camp / US_Powerplant / US_Supply / US_WarFactory / US_Command"),
    ("14", "UNITED_KINGDOM", "United Kingdom", "British Armed Forces", "US_Camp / US_Powerplant / US_Supply / US_WarFactory / US_Command"),
    ("15", "GERMANY", "Germany", "German Armed Forces", "US_Camp / US_Powerplant / US_Supply / US_WarFactory / US_Command"),
    ("16", "FRANCE", "France", "French Armed Forces", "US_Camp / US_Powerplant / US_Supply / US_WarFactory / US_Command"),
)


def add_bytes(entries: list[tuple[str, bytes]], name: str, blob: bytes) -> None:
    n = jf.norm(name)
    if any(jf.norm(x).lower() == n.lower() for x, _ in entries):
        raise SystemExit(f"already packed: {name}")
    entries.append((n, bytes(blob)))


def art_of(art: list[tuple[str, bytes]], target: str) -> bytes:
    return jf.raw_of(art, target)


def replace_w3d_names(donor: bytes, old: bytes, new: bytes) -> bytes:
    if len(new) > 15:
        raise SystemExit(f"internal name too long: {new!r}")
    if len(new) > len(old):
        raise SystemExit("new container name longer than donor")
    out = bytearray(donor)
    start = 0
    count = 0
    while True:
        i = out.find(old, start)
        if i < 0:
            break
        nul = out.find(b"\x00", i)
        if nul < 0:
            raise SystemExit(f"unterminated name at {i}")
        cur = bytes(out[i:nul])
        if not cur.startswith(old):
            start = i + 1
            continue
        field_len = 32 if b"." in cur else 16
        old_field = cur + b"\x00" * (field_len - len(cur))
        if bytes(out[i : i + field_len]) != old_field:
            raise SystemExit(
                f"unexpected name field at {i}: {bytes(out[i:i + field_len])!r}"
            )
        replacement = new + cur[len(old) :]
        if len(replacement) + 1 > field_len:
            raise SystemExit(f"renamed field too long: {replacement!r}")
        padded = replacement + b"\x00" * (field_len - len(replacement))
        out[i : i + field_len] = padded
        count += 1
        start = i + field_len
    if count != 19:
        raise SystemExit(f"expected 19 container name fields, got {count}")
    if old in bytes(out):
        raise SystemExit("leftover donor container name")
    if bytes(out).count(new) != 19:
        raise SystemExit(f"new container count {bytes(out).count(new)}")
    return bytes(out)


def replace_w3d_texture(blob: bytes, old: bytes, new: bytes) -> bytes:
    field_len = len(old) + 1
    new_field = new + b"\x00"
    if len(new_field) > field_len:
        raise SystemExit(f"texture name too long: {new!r}")
    new_field += b"\x00" * (field_len - len(new_field))
    out = bytearray(blob)
    count = 0
    start = 0
    while True:
        i = out.find(old, start)
        if i < 0:
            break
        if i + len(old) < len(out) and out[i + len(old)] == 0:
            out[i : i + field_len] = new_field
            count += 1
            start = i + field_len
        else:
            start = i + 1
    if count != 3:
        raise SystemExit(f"expected 3 texture refs, got {count}")
    if old in bytes(out):
        raise SystemExit("leftover donor texture name")
    if bytes(out).count(new) != 3:
        raise SystemExit(f"new texture count {bytes(out).count(new)}")
    return bytes(out)


def make_flag_hs(donor: bytes, new_name: bytes, new_tex: bytes) -> bytes:
    named = replace_w3d_names(donor, DONOR_NAME, new_name)
    out = replace_w3d_texture(named, DONOR_TEX, new_tex)
    if len(out) != len(donor):
        raise SystemExit("W3D size changed")
    if DONOR_NAME in out or DONOR_TEX in out:
        raise SystemExit("donor strings remain in new W3D")
    if b"IRQ__IQFLAG_HS" in out or b"NKR__NKFLAG_HS" in out:
        raise SystemExit("Iraq/NK Flag_Hs container leaked into new W3D")
    if b"IraqiFlag" in out or b"DPRK_Flag" in out:
        raise SystemExit("wrong texture leaked into new W3D")
    root = out[20:36]
    expect = new_name + b"\x00" * (16 - len(new_name))
    if root != expect:
        raise SystemExit(f"root container mismatch: {root!r}")
    return out


def flag_draw(model: str) -> str:
    return f"""  ; ------------ Flag -----------------
  Draw                = W3DModelDraw ModuleTag_03
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


def object_span(text: str, object_line: str) -> tuple[int, int]:
    m = re.search(rf"(?m)^{re.escape(object_line)}\s*$", text)
    if not m:
        # allow trailing spaces
        m = re.search(rf"(?m)^{re.escape(object_line)}\b", text)
    if not m:
        raise SystemExit(f"missing {object_line}")
    nxt = re.search(r"(?m)^Object\s+\S+", text[m.end() :])
    end = m.end() + nxt.start() if nxt else len(text)
    return m.start(), end


def has_exact_moduletag_03(block: str) -> bool:
    return re.search(r"(?m)\bModuleTag_03\b", block) is not None


def patch_add_flag_draw(
    text: str,
    *,
    object_line: str,
    allowed_models: set[str],
    allowed_anims: set[str],
    model: str,
) -> str:
    start, end = object_span(text, object_line)
    block = text[start:end]
    if has_exact_moduletag_03(block):
        raise SystemExit(f"{object_line} already has ModuleTag_03")
    m = re.search(r"(?im)^[ \t]*PlacementViewAngle\s*=", block)
    if not m:
        raise SystemExit(f"{object_line} missing PlacementViewAngle insert point")
    prefix = block[: m.start()]
    models = re.findall(r"(?im)^\s*Model\s*=\s*(\S+)", prefix)
    anims = re.findall(r"(?im)^\s*Animation\s*=\s*(\S+)", prefix)
    if not models or any(val not in allowed_models for val in models):
        raise SystemExit(f"{object_line} Model retarget: {models}")
    if not anims or any(val not in allowed_anims for val in anims):
        raise SystemExit(f"{object_line} Animation retarget: {anims}")
    draw = jf.to_nl(flag_draw(model), jf.file_nl(text))
    new_block = prefix + draw + block[m.start() :]
    if new_block.count(model) != 9:
        raise SystemExit(f"{object_line} {model} refs {new_block.count(model)}")
    if len(re.findall(rf"(?m)\bModuleTag_03\b", new_block)) != 1:
        raise SystemExit(f"{object_line} expected exactly one ModuleTag_03 in object")
    if len(re.findall(rf"(?im)^\s*Model\s*=\s*{re.escape(model)}\s*$", new_block)) != 3:
        raise SystemExit(f"{object_line} expected 3 Flag_Hs Model=")
    return text[:start] + new_block + text[end:]


def patch_retarget(
    text: str,
    *,
    object_line: str,
    old: str,
    new: str,
    keep_models: set[str],
    keep_anims: set[str],
) -> str:
    start, end = object_span(text, object_line)
    block = text[start:end]
    if old not in block:
        raise SystemExit(f"{object_line} missing {old}")
    if block.count(old) != 9:
        raise SystemExit(f"{object_line} {old} refs {block.count(old)}")
    if new in block:
        raise SystemExit(f"{object_line} already retargeted")
    new_block = block.replace(old, new)
    if old in new_block:
        raise SystemExit(f"{object_line} leftover {old}")
    models = set(re.findall(r"(?im)^\s*Model\s*=\s*(\S+)", new_block))
    anims = set(re.findall(r"(?im)^\s*Animation\s*=\s*(\S+)", new_block))
    allowed_models = set(keep_models) | {new}
    allowed_anims = set(keep_anims) | {f"{new}.{new}"}
    extra_models = models - allowed_models
    extra_anims = anims - allowed_anims
    if extra_models:
        raise SystemExit(f"{object_line} unexpected models {extra_models}")
    if extra_anims:
        raise SystemExit(f"{object_line} unexpected anims {extra_anims}")
    if keep_models - models:
        raise SystemExit(f"{object_line} lost building mesh {keep_models - models}")
    return text[:start] + new_block + text[end:]


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def write_release(
    spec: dict,
    data_blob: bytes,
    art_blob: bytes,
    src_data_sha: str,
    src_art_sha: str,
    changed_paths: list[str],
    baseline_name: str,
) -> tuple[str, str, str]:
    ws = Path("/workspace/patch/Release") / spec["release"]
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "_SPEC_DATA_ONE.big").write_bytes(data_blob)
    (ws / "_SPEC_ART_ONE.big").write_bytes(art_blob)
    data_sha = sha256_bytes(data_blob)
    art_sha = sha256_bytes(art_blob)
    changed = "\n".join(
        [
            f"{spec['release']} changed files",
            "",
            "TARGET AUDIT",
            f"  Country = {spec['country']} only",
            f"  Flag_Hs W3D = {spec['w3d']}.W3D (one new file)",
            f"  Texture = {spec['tex'].decode()} (already packed, not rewritten)",
            f"  {spec['note']}",
            "",
            f"DATA ({len(changed_paths)} files)",
            *[f"  {p}" for p in changed_paths],
            "",
            "ART (1 new file)",
            f"  Art\\W3D\\{spec['w3d']}.W3D",
            f"    internal={spec['internal'].decode()} packed={spec['w3d']} MATCH",
            f"    texture={spec['tex'].decode()}",
            "",
            "UNCHANGED",
            "  shared donor building W3Ds, Iraq/NK Flag_Hs, prior country poles",
            "  PlayerTemplate HUD MappedImages faction pages CommandButton CommandSet",
        ]
    )
    audit = "\n".join(
        [
            spec["release"],
            f"BASELINE = {baseline_name}",
            f"SRC_DATA_SHA = {src_data_sha}",
            f"SRC_ART_SHA = {src_art_sha}",
            f"DATA_SHA256 = {data_sha}",
            f"ART_SHA256 = {art_sha}",
            f"COUNTRY = {spec['country']}",
            f"NEW_W3D = Art\\W3D\\{spec['w3d']}.W3D",
            f"INTERNAL_NAME = {spec['internal'].decode()}",
            f"INTERNAL_LEN = {len(spec['internal'])}",
            f"TEXTURE = {spec['tex'].decode()}",
            "BUILDING_MODEL_UNCHANGED = YES",
            "SHARED_MESH_MODIFIED = NO",
            "EXISTING_W3D_MODIFIED = NO",
            "IRAQ_NK_ASSETS_CHANGED = NO",
            "PRIOR_COUNTRY_ASSETS_CHANGED = NO",
            "UNRELATED_INI_CHANGED = NO",
            "DUPLICATE_W3D_PATH = NO",
            "PACKED_INTERNAL_MATCH = YES",
            "FIX_APPLIED = YES",
            "BOOT_SAFE = YES",
            "INGAME_TESTED = NO",
        ]
    )
    changelog = (
        f"{spec['release']}\n\n"
        f"{spec['note']}\n\n"
        f"One new W3D {spec['w3d']}.W3D from Irq__IqFlag_Hs. "
        f"Internal {spec['internal'].decode()} matches packed name. "
        f"Texture {spec['tex'].decode()} already packed. "
        "Original building Model=/Animation= unchanged. "
        "Shared donor meshes not edited.\n\n"
        "BOOT_SAFE = YES\nINGAME_TESTED = NO\n"
    )
    (ws / "CHANGED_FILES.txt").write_text(changed + "\n", encoding="utf-8")
    (ws / "audit.txt").write_text(audit + "\n", encoding="utf-8")
    (ws / "changelog.txt").write_text(changelog, encoding="utf-8")
    sha_tmp = (
        f"_SPEC_DATA_ONE.big  SHA256 {data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {art_sha}\n"
    )
    (ws / "SHA256.txt").write_text(sha_tmp, encoding="utf-8")
    zip_path = ws / f"{spec['release']}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(ws / "_SPEC_DATA_ONE.big", "_SPEC_DATA_ONE.big")
        zf.write(ws / "_SPEC_ART_ONE.big", "_SPEC_ART_ONE.big")
        zf.write(ws / "audit.txt", "audit.txt")
        zf.write(ws / "SHA256.txt", "SHA256.txt")
        zf.write(ws / "changelog.txt", "changelog.txt")
    zip_sha = jf.sha256_file(zip_path)
    sha_txt = (
        f"_SPEC_DATA_ONE.big  SHA256 {data_sha}\n"
        f"_SPEC_ART_ONE.big   SHA256 {art_sha}\n"
        f"{spec['release']}.zip  SHA256 {zip_sha}  {zip_path.stat().st_size} bytes\n"
    )
    (ws / "SHA256.txt").write_text(sha_txt, encoding="utf-8")
    print("WROTE", spec["release"], data_sha, art_sha, zip_sha)
    return data_sha, art_sha, str(ws)


def build_country(
    spec: dict,
    src_data: Path,
    src_art: Path,
    src_data_sha: str,
    src_art_sha: str,
    baseline_name: str,
    prior_w3ds: list[str],
) -> tuple[Path, Path, str, str]:
    if jf.sha256_file(src_data) != src_data_sha:
        raise SystemExit(f"{spec['release']} source DATA SHA mismatch")
    if jf.sha256_file(src_art) != src_art_sha:
        raise SystemExit(f"{spec['release']} source ART SHA mismatch")

    data = jf.read_big_list(src_data)
    art = jf.read_big_list(src_art)
    src_data_list = list(data)
    src_art_list = list(art)

    donor = art_of(art, P_DONOR_W3D)
    if len(donor) != 20341:
        raise SystemExit("donor Flag_Hs size unexpected")
    tga = art_of(art, spec["tex_path"])
    if len(tga) < 18 or tga[2] != 2:
        raise SystemExit(f"{spec['tex_path']} is not uncompressed truecolor")

    new_w3d_path = rf"Art\W3D\{spec['w3d']}.W3D"
    new_w3d = make_flag_hs(donor, spec["internal"], spec["tex"])
    add_bytes(art, new_w3d_path, new_w3d)

    for tgt in spec["add"]:
        src = jf.text_of(data, tgt["path"])
        jf.set_text(
            data,
            tgt["path"],
            patch_add_flag_draw(
                src,
                object_line=tgt["object"],
                allowed_models=tgt["models"],
                allowed_anims=tgt["anims"],
                model=spec["w3d"],
            ),
        )
    for tgt in spec["retarget"]:
        src = jf.text_of(data, tgt["path"])
        jf.set_text(
            data,
            tgt["path"],
            patch_retarget(
                src,
                object_line=tgt["object"],
                old=tgt["old"],
                new=spec["w3d"],
                keep_models=tgt["keep_models"],
                keep_anims=tgt["keep_anims"],
            ),
        )

    if len(art) != len(src_art_list) + 1:
        raise SystemExit("ART count mismatch")
    if len(data) != len(src_data_list):
        raise SystemExit("DATA file count changed")

    src_art_map = {jf.norm(n).lower(): b for n, b in src_art_list}
    src_data_map = {jf.norm(n).lower(): b for n, b in src_data_list}
    new_art_map = {jf.norm(n).lower(): b for n, b in art}
    new_data_map = {jf.norm(n).lower(): b for n, b in data}
    if len(new_art_map) != len(art) or len(new_data_map) != len(data):
        raise SystemExit("duplicate packed path")

    added_art = [n for n in new_art_map if n not in src_art_map]
    if added_art != [jf.norm(new_w3d_path).lower()]:
        raise SystemExit(f"unexpected ART adds: {added_art}")
    for key, blob in src_art_map.items():
        if new_art_map[key] != blob:
            raise SystemExit(f"existing ART modified: {key}")

    protected_art = [
        P_DONOR_W3D, P_NK_W3D, P_JP_W3D, P_VN_W3D, P_SA_W3D,
        P_IRQ_CAMP, P_IRQ_POWER, P_IRQ_SUPPLY, P_IRQ_WF,
        P_NK_POWER, P_NK_SUPPLY, P_NK_WF, P_NK_CC, P_US_CAMP,
        P_IRQ_DDS, P_DPRK_TGA, P_DPRK_DDS, spec["tex_path"],
        *prior_w3ds,
    ]
    for p in protected_art:
        key = jf.norm(p).lower()
        if key in src_art_map and new_art_map[key] != src_art_map[key]:
            raise SystemExit(f"protected ART changed: {p}")

    expected = sorted(
        {jf.norm(t["path"]).lower() for t in spec["add"]}
        | {jf.norm(t["path"]).lower() for t in spec["retarget"]}
    )
    changed = sorted(n for n, b in new_data_map.items() if src_data_map.get(n) != b)
    if changed != expected:
        raise SystemExit(f"unexpected DATA changes: {changed}")

    frozen = [
        P_PT, P_PT_PATCH, P_REMAIN, P_CAMP, P_JP_BARRACKS, P_VN_BARRACKS,
        P_SA_BARRACKS, P_NK_ABBAS, P_CMDBTN, P_CMDSET, *spec.get("skip", ()),
    ]
    for p in frozen:
        k = jf.norm(p).lower()
        if k in src_data_map and new_data_map[k] != src_data_map[k]:
            raise SystemExit(f"frozen DATA changed: {p}")
    if jf.norm(P_PAGES).lower() in new_data_map:
        raise SystemExit("faction pages INI must not appear")

    packed = art_of(art, new_w3d_path)
    if packed != new_w3d:
        raise SystemExit("packed W3D mismatch")

    data_blob = jf.build_big_ordered(data)
    art_blob = jf.build_big_ordered(art)
    changed_paths = [t["path"] for t in spec["add"]] + [t["path"] for t in spec["retarget"]]
    data_sha, art_sha, out_dir = write_release(
        spec, data_blob, art_blob, src_data_sha, src_art_sha, changed_paths, baseline_name
    )
    return Path(out_dir) / "_SPEC_DATA_ONE.big", Path(out_dir) / "_SPEC_ART_ONE.big", data_sha, art_sha


def write_nochange(last_data_sha: str, last_art_sha: str, last_release: str) -> None:
    root = Path("/workspace/patch/Release/BUILDING_FLAG_ROLLOUT_NOCHANGE_USMESH")
    root.mkdir(parents=True, exist_ok=True)
    lines = [
        "BUILDING_FLAG_ROLLOUT no-change countries",
        "",
        "These remaining target countries use US/NATO building meshes",
        "with no baked *Flag.tga / FLAG01-03 donor flags.",
        "Per rules: leave buildings with no baked flags unchanged.",
        "No Flag_Hs W3D added. No INI Draw added. No BIG rewrite.",
        "",
        f"BASELINE_PAIR = {last_release}",
        f"DATA_SHA256 = {last_data_sha}",
        f"ART_SHA256 = {last_art_sha}",
        "FIX_APPLIED = NO",
        "BOOT_SAFE = YES (unchanged bytes)",
        "INGAME_TESTED = NO",
        "",
    ]
    for num, slug, name, folder, meshes in NOCHANGE:
        rel = f"BUILDING_FLAG_STAGE_{num}_{slug}_ONLY"
        dest = Path("/workspace/patch/Release") / rel
        dest.mkdir(parents=True, exist_ok=True)
        audit = "\n".join(
            [
                rel,
                f"BASELINE = {last_release}",
                f"DATA_SHA256 = {last_data_sha} (unchanged)",
                f"ART_SHA256 = {last_art_sha} (unchanged)",
                f"COUNTRY = {name}",
                f"FOLDER = Data\\INI\\Object\\Specter\\{folder}\\Buildings",
                f"CORE_MESHES = {meshes}",
                "BAKED_DONOR_FLAGS = NO",
                "EXISTING_WRONG_FLAG_HS = NO",
                "DATA_CHANGED = NO",
                "ART_CHANGED = NO",
                "NEW_W3D_COUNT = 0",
                "FIX_APPLIED = NO (no wrong baked flags to replace)",
                "BOOT_SAFE = YES",
                "INGAME_TESTED = NO",
            ]
        )
        changelog = (
            f"{rel}\n\n"
            f"{name} core buildings use {meshes}. "
            "Those W3Ds contain no baked Iraqi/NK/country Flag.tga. "
            "No Flag_Hs Draw was added. No BIG rewrite.\n\n"
            "BOOT_SAFE = YES\nINGAME_TESTED = NO\n"
        )
        sha = (
            f"UNCHANGED FROM {last_release}\n"
            f"_SPEC_DATA_ONE.big  SHA256 {last_data_sha}\n"
            f"_SPEC_ART_ONE.big   SHA256 {last_art_sha}\n"
            "ZIP = NOT REBUILT (identical bytes; no country Flag_Hs required)\n"
        )
        (dest / "audit.txt").write_text(audit + "\n", encoding="utf-8")
        (dest / "changelog.txt").write_text(changelog, encoding="utf-8")
        (dest / "SHA256.txt").write_text(sha, encoding="utf-8")
        (dest / "CHANGED_FILES.txt").write_text(
            f"{rel}\nDATA_CHANGED = NO\nART_CHANGED = NO\n", encoding="utf-8"
        )
        lines.append(f"{rel}  FIX_APPLIED=NO  meshes={meshes}")
    (root / "audit.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("WROTE no-change audits")


def main() -> int:
    src_data = STAGE04_DIR / "_SPEC_DATA_ONE.big"
    src_art = STAGE04_DIR / "_SPEC_ART_ONE.big"
    src_data_sha = STAGE04_DATA_SHA
    src_art_sha = STAGE04_ART_SHA
    baseline = "BUILDING_FLAG_STAGE_04_SAUDI_ARABIA_ONLY"
    prior_w3ds: list[str] = []
    last_release = baseline
    last_data_sha = src_data_sha
    last_art_sha = src_art_sha

    for spec in CHANGE_COUNTRIES:
        print("====", spec["release"], "====")
        src_data, src_art, src_data_sha, src_art_sha = build_country(
            spec,
            src_data,
            src_art,
            src_data_sha,
            src_art_sha,
            baseline,
            prior_w3ds,
        )
        prior_w3ds.append(rf"Art\W3D\{spec['w3d']}.W3D")
        baseline = spec["release"]
        last_release = spec["release"]
        last_data_sha = src_data_sha
        last_art_sha = src_art_sha

    write_nochange(last_data_sha, last_art_sha, last_release)

    summary = Path("/workspace/patch/Release/BUILDING_FLAG_ROLLOUT_REMAINING_SUMMARY")
    summary.mkdir(parents=True, exist_ok=True)
    text = "\n".join(
        [
            "BUILDING_FLAG_ROLLOUT remaining targets",
            "BASELINE = BUILDING_FLAG_STAGE_04_SAUDI_ARABIA_ONLY",
            "",
            "CHANGED",
            "  05 UAE  06 Syria  07 South Africa  08 South Korea  09 Libya",
            "",
            "NO CHANGE (US meshes, no baked donor flags)",
            "  Turkey Ukraine Sweden Italy United Kingdom Germany France",
            "",
            f"FINAL_DATA_SHA = {last_data_sha}",
            f"FINAL_ART_SHA = {last_art_sha}",
            "BOOT_SAFE = YES",
            "INGAME_TESTED = NO",
        ]
    )
    (summary / "audit.txt").write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
