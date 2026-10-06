#!/usr/bin/env python3
"""Add universal missile_factory ButtonImage ART and point the Iraq construct button at it.

Live baselines:
  DATA s-iraq-factory-slot14
    366368036 SHA 281b68c4659d9181202783d9911e552ec3d3ffce5b51443ae8fef375505c5073
  ART  s-iraq-alfahd500
    1262233475 SHA d6ee44bbf52d9afba505c72e4e01fb0cbafb0b55f9483252fd645e9299dd58c0

DATA change is ButtonImage + new MappedImage INI only.
ART change is Art\\Textures\\missile_factory.tga only.
Static validation only. The game is not launched.
"""
from __future__ import annotations

import hashlib
import io
import re
import shutil
import struct
from pathlib import Path

from PIL import Image, ImageFilter, ImageEnhance

ROOT = Path("/workspace")
SRC_DATA = ROOT / "patch/Release/SPECTER_IRAQ_FACTORY_SLOT14/_SPEC_DATA_ONE.big"
SRC_ART = ROOT / "patch/Release/SPECTER_IRAQ_ALFAHD500/_SPEC_ART_ONE.big"
SRC_PNG = ROOT / "patch/Art/Textures/UI/missile_factory.png"
OUT = ROOT / "patch/Release/SPECTER_MISSILE_FACTORY_BUTTON"

LIVE_DATA_SHA = "281b68c4659d9181202783d9911e552ec3d3ffce5b51443ae8fef375505c5073"
LIVE_DATA_SIZE = 366368036
LIVE_ART_SHA = "d6ee44bbf52d9afba505c72e4e01fb0cbafb0b55f9483252fd645e9299dd58c0"
LIVE_ART_SIZE = 1262233475

MAPPED_KEY = r"Data\INI\MappedImages\HandCreated\MissileFactory_Images.INI"
MAPPED_INI = (
    "; SPECTER universal Missile Factory command-button cameo.\r\n"
    "; Shared ButtonImage for every country that builds a Missile Factory.\r\n"
    "; Not country-specific. No flags or faction marks in the texture.\r\n"
    "\r\n"
    "MappedImage missile_factory\r\n"
    "  Texture = missile_factory.tga\r\n"
    "  TextureWidth = 128\r\n"
    "  TextureHeight = 128\r\n"
    "  Coords = Left:0 Top:0 Right:128 Bottom:128\r\n"
    "  Status = NONE\r\n"
    "End\r\n"
)

BTN_OLD = (
    "CommandButton Command_ConstructIraq_AlFahdMissileFactory\r\n"
    "  Command          = DOZER_CONSTRUCT\r\n"
    "  Object           = Iraq_AlFahdMissileFactory\r\n"
    "  TextLabel        = CONTROLBAR:ConstructIraqAlFahdMissileFactory\r\n"
    "  ButtonImage      = irq_warfctry\r\n"
    "  ButtonBorderType = BUILD\r\n"
    "  DescriptLabel    = CONTROLBAR:ToolTipIraqAlFahdMissileFactory\r\n"
    "End"
)
BTN_NEW = BTN_OLD.replace(
    "  ButtonImage      = irq_warfctry\r\n",
    "  ButtonImage      = missile_factory\r\n",
)

OLD_RESIDUE = [
    b"Iraq_AlHussein_New",
    b"Object Iraq_MissileFactory",
    b"Iraq_MissileFactoryCommandSet",
]


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(8 * 1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def parse_big(data: bytes) -> dict[str, bytes]:
    if data[:4] != b"BIGF":
        raise ValueError("not BIGF")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name.replace("/", "\\")] = data[off : off + size]
    return files


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1")) + 1
    index = []
    blobs = []
    offset = header_size
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


def make_tga() -> bytes:
    im = Image.open(SRC_PNG).convert("RGBA")
    if im.size != (128, 128):
        im = im.resize((128, 128), Image.Resampling.LANCZOS)
        im = ImageEnhance.Contrast(im).enhance(1.1)
        im = im.filter(ImageFilter.UnsharpMask(radius=1.1, percent=120, threshold=2))
    buf = io.BytesIO()
    im.save(buf, format="TGA")
    return buf.getvalue()


def commandset_block(cs: str, name: str) -> str | None:
    m = re.search(rf"(?ms)^CommandSet {re.escape(name)}\r?\n.*?^End", cs)
    return m.group(0) if m else None


def validate(data: dict[str, bytes], art: dict[str, bytes], src_data: dict[str, bytes], src_art: dict[str, bytes], tga: bytes) -> list[str]:
    fails: list[str] = []
    all_ini = b"\n".join(v for k, v in data.items() if k.lower().endswith(".ini"))
    for needle in OLD_RESIDUE:
        if needle in all_ini:
            fails.append(f"old residue {needle.decode('ascii')}")

    tex_key = r"Art\Textures\missile_factory.tga"
    if tex_key not in art:
        fails.append("ART missing missile_factory.tga")
    elif art[tex_key] != tga:
        fails.append("packed TGA mismatch")
    else:
        try:
            im = Image.open(io.BytesIO(art[tex_key]))
            im.load()
            if im.size != (128, 128):
                fails.append(f"TGA size {im.size}")
        except Exception as exc:
            fails.append(f"TGA unreadable {exc}")

    if all_ini.count(b"MappedImage missile_factory") != 1:
        fails.append("MappedImage missile_factory count")
    if b"MappedImage specter_missile_factory" in all_ini:
        fails.append("unexpected specter_missile_factory name")

    cb = data[r"Data\INI\CommandButton.ini"].decode("latin1")
    btn = re.search(
        r"(?ms)^CommandButton Command_ConstructIraq_AlFahdMissileFactory\r?\n.*?^End", cb
    )
    if not btn:
        fails.append("construct button missing")
    else:
        body = btn.group(0)
        if "ButtonImage      = missile_factory" not in body:
            fails.append("construct ButtonImage not missile_factory")
        if "Command          = DOZER_CONSTRUCT" not in body:
            fails.append("Command mutated")
        if "Object           = Iraq_AlFahdMissileFactory" not in body:
            fails.append("Object mutated")
        if re.search(r"(?m)^\s*(Science|Upgrade|SpecialPower)\s*=", body):
            fails.append("hide fields added")
    if cb.count("ButtonImage      = missile_factory") != 1:
        fails.append("unexpected extra missile_factory ButtonImage")

    # irq_warfctry must remain for other buttons
    if "irq_warfctry" not in cb:
        fails.append("irq_warfctry stripped from other buttons")

    mapped = data[MAPPED_KEY].decode("latin1")
    if "MappedImage missile_factory" not in mapped:
        fails.append("MappedImage INI missing definition")
    if "Iraq" in mapped or "AlFahd" in mapped:
        fails.append("country-specific name in MappedImage INI")

    # CommandSet / gameplay files unchanged except CommandButton + new mapped INI
    cs = data[r"Data\INI\CommandSet.ini"]
    if cs != src_data[r"Data\INI\CommandSet.ini"]:
        fails.append("CommandSet.ini mutated")
    vt = commandset_block(cs.decode("latin1"), "Iraq_VT72BCommandSet")
    if not vt or "14 = Command_ConstructIraq_AlFahdMissileFactory" not in vt:
        fails.append("VT72B slot 14 factory lost")
    if vt and "19 =" in vt:
        fails.append("slot 19 reintroduced")

    for key in [
        r"Data\INI\Object\Specter\Iraq Army\Wheeled\Iraq_AlFahd500.ini",
        r"Data\INI\Weapon_Iraq_AlFahd500.ini",
        r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_AlFahdMissileFactory.ini",
        r"Data\INI\Object\Specter\Iraq Army\Wheeled\9P117.ini",
    ]:
        if data[key] != src_data[key]:
            fails.append(f"{key} mutated")

    extra_d = sorted(k for k in data if k not in src_data)
    extra_a = sorted(k for k in art if k not in src_art)
    missing_a = sorted(k for k in src_art if k not in art)
    missing_d = sorted(k for k in src_data if k not in data)
    if extra_d != [MAPPED_KEY]:
        fails.append(f"unexpected extra DATA {extra_d}")
    if extra_a != [tex_key]:
        fails.append(f"unexpected extra ART {extra_a}")
    if missing_a:
        fails.append(f"ART removed {missing_a[:4]}")
    if missing_d:
        fails.append(f"DATA removed {missing_d[:4]}")
    changed_d = sorted(k for k in data if k in src_data and data[k] != src_data[k])
    if changed_d != [r"Data\INI\CommandButton.ini"]:
        fails.append(f"unexpected DATA mutations {changed_d}")
    changed_a = sorted(k for k in art if k in src_art and art[k] != src_art[k])
    if changed_a:
        fails.append(f"existing ART mutated {changed_a[:4]}")

    # broken MappedImage texture refs for the new image only
    if r"Art\Textures\missile_factory.tga" not in art:
        fails.append("texture path missing")

    fac = commandset_block(cs.decode("latin1"), "Iraq_AlFahdMissileFactoryCommandSet")
    if not fac or "Command_ConstructIraq_AlFahd500" not in fac:
        fails.append("factory production lost")
    return fails


def main() -> int:
    if SRC_DATA.stat().st_size != LIVE_DATA_SIZE or sha256_path(SRC_DATA) != LIVE_DATA_SHA:
        raise SystemExit("live DATA baseline mismatch")
    if SRC_ART.stat().st_size != LIVE_ART_SIZE or sha256_path(SRC_ART) != LIVE_ART_SHA:
        raise SystemExit("live ART baseline mismatch")
    if not SRC_PNG.is_file():
        raise SystemExit("source PNG missing")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    src_data = parse_big(SRC_DATA.read_bytes())
    src_art = parse_big(SRC_ART.read_bytes())
    data = dict(src_data)
    art = dict(src_art)

    tga = make_tga()
    art[r"Art\Textures\missile_factory.tga"] = tga
    data[MAPPED_KEY] = MAPPED_INI.encode("latin1")

    cb = data[r"Data\INI\CommandButton.ini"].decode("latin1")
    if cb.count(BTN_OLD) != 1:
        raise SystemExit(f"construct button block count={cb.count(BTN_OLD)}")
    data[r"Data\INI\CommandButton.ini"] = cb.replace(BTN_OLD, BTN_NEW, 1).encode("latin1")

    packed_data = build_big(data)
    packed_art = build_big(art)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_data.write_bytes(packed_data)
    out_art.write_bytes(packed_art)

    extracted_d = parse_big(out_data.read_bytes())
    extracted_a = parse_big(out_art.read_bytes())
    fails = validate(extracted_d, extracted_a, src_data, src_art, tga)

    report = [
        "# Universal missile_factory CommandButton ART",
        "",
        "Static packed last-wins. The game was not launched.",
        "",
        "ButtonImage identifier: missile_factory",
        "Texture: Art\\Textures\\missile_factory.tga (128x128 TGA)",
        "MappedImage: Data\\INI\\MappedImages\\HandCreated\\MissileFactory_Images.INI",
        "CommandButton Command_ConstructIraq_AlFahdMissileFactory ButtonImage only",
        "Gameplay Command/Object/production unchanged. irq_warfctry kept for other buttons.",
        "No country flag or Iraq-specific marking in the cameo.",
        "",
        f"- DATA size: {out_data.stat().st_size}",
        f"- DATA SHA256: {sha256_path(out_data)}",
        f"- DATA files: {len(extracted_d)}",
        f"- ART size: {out_art.stat().st_size}",
        f"- ART SHA256: {sha256_path(out_art)}",
        f"- ART files: {len(extracted_a)}",
        "",
    ]
    if fails:
        report.append("## VALIDATION FAIL")
        report.extend(f"- {f}" for f in fails)
        (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="ascii")
        print("\n".join(report))
        return 1
    report += [
        "## VALIDATION PASS (static / packed last-wins)",
        "- missile_factory MappedImage unique; TGA readable 128x128",
        "- construct button ButtonImage = missile_factory; Object/Command unchanged",
        "- factory still produces Iraq_AlFahd500; VT72B slot 14 factory kept; no slot 19",
        "- no unrelated ART removed; existing ART blobs byte-identical",
        "- no old 8-missile / Iraq_MissileFactory residue",
        "",
        "RUNTIME_TEST=NOT RUN",
    ]
    (OUT / "VALIDATE_REPORT.txt").write_text("\n".join(report) + "\n", encoding="ascii")
    (OUT / "HASHES.txt").write_text(
        f"DATA_FILE=_SPEC_DATA_ONE.big\n"
        f"DATA_SIZE={out_data.stat().st_size}\n"
        f"DATA_SHA256={sha256_path(out_data)}\n"
        f"DATA_FILES={len(extracted_d)}\n"
        f"ART_FILE=_SPEC_ART_ONE.big\n"
        f"ART_SIZE={out_art.stat().st_size}\n"
        f"ART_SHA256={sha256_path(out_art)}\n"
        f"ART_FILES={len(extracted_a)}\n"
        f"BUTTONIMAGE=missile_factory\n"
        f"TEXTURE=Art\\Textures\\missile_factory.tga\n"
        f"BASELINE_DATA=s-iraq-factory-slot14\n"
        f"BASELINE_ART=s-iraq-alfahd500\n"
        f"STATIC_VALIDATION=PASS\n"
        f"RUNTIME_TEST=NOT RUN\n",
        encoding="ascii",
    )
    (OUT / "README.txt").write_text(
        "SPECTER universal Missile Factory command-button artwork\n"
        "\n"
        "Install complete _SPEC_ART_ONE.big and _SPEC_DATA_ONE.big over current live s.\n"
        "ButtonImage identifier: missile_factory (shared, not Iraq-specific).\n"
        "\n"
        "Static validation only. The game was not launched.\n",
        encoding="ascii",
    )
    (OUT / "DOWNLOAD.txt").write_text(
        "Complete replacement BIGs:\n"
        "  _SPEC_ART_ONE.big\n"
        "  _SPEC_DATA_ONE.big\n"
        f"  ART_SIZE={out_art.stat().st_size}\n"
        f"  ART_SHA256={sha256_path(out_art)}\n"
        f"  DATA_SIZE={out_data.stat().st_size}\n"
        f"  DATA_SHA256={sha256_path(out_data)}\n",
        encoding="ascii",
    )
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
