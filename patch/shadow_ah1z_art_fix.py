#!/usr/bin/env python3
"""SPECTER1 ART fix: F-35B/EA-6B volume-shadow spikes + AH-1Z missing model.

Baseline ART: USA Update 01 _SPEC_ART_ONE.big (original SPECTER1 ART + AH-1Z donor assets).
Baseline DATA: crashfix-test (unchanged; this pack is ART only).

Sets W3D HIDDEN on the thin FX/hook meshes that still cast SHADOW_VOLUME
even when INI HideSubObject is set. Does not rewrite mesh geometry.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path

SRC_ART = Path("/tmp/SPECTER1_USA_UPDATE_01/_SPEC_ART_ONE.big")
EXPECTED_ART_SHA = "8f024c3454d6e8783cfb50d140933c98236aeb7129287dbf3ee73f356a3bacbe"
SRC_DATA = Path("/workspace/patch/Release/SPECTER1_AIRFRAME_STD_01_CRASHFIX_TEST/_SPEC_DATA_ONE.big")
EXPECTED_DATA_SHA = "f29f31e6555ffc4d6c95951a9624210bd8dfe30ee055604a3535206e71e582db"
OUT_DIR = Path("/tmp/SPECTER1_SHADOW_AH1Z_ART_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_SHADOW_AH1Z_ART_01")

CONTAINER = 0x80000000
W3D_CHUNK_MESH_HEADER3 = 0x0000001F
W3D_MESH_FLAG_HIDDEN = 0x00001000

P_AV = r"Art\W3D\AVLightn.W3D"
P_AVD = r"Art\W3D\AVLightn_D.W3D"
P_EA6 = r"Art\W3D\EA6.W3D"

F35_HIDE = ("JAFTERBURNED", "CYLINDER02", "CYLINDER03", "TURBO", "EX01", "EX02")
EA6_HIDE = ("HOOK",)

AH1Z_REQUIRED = [
    r"Art\W3D\LSFAH1Z.W3D",
    r"Art\W3D\LSFAH1Zd.W3D",
    r"Art\W3D\LSFAH1Zk.W3D",
    r"Art\W3D\LSFAH1ZAIM9.W3D",
    r"Art\Textures\LSFAH1Z.dds",
    r"Art\Textures\LSFAH1Zd.dds",
    r"Art\Textures\LSFAH1Zk.dds",
    r"Art\Textures\AH1ZTB.tga",
]


def norm(name: str) -> str:
    return name.replace("/", "\\")


def read_big_list(path: Path) -> list[tuple[str, bytes]]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries: list[tuple[str, bytes]] = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def build_big_ordered(entries: list[tuple[str, bytes]]) -> bytes:
    header_size = 16
    encoded_names: list[bytes] = []
    for name, _ in entries:
        nb = name.encode("latin1", errors="replace")
        encoded_names.append(nb)
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded_names):
        content = bytes(content)
        index.append((nb, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def find_index(entries: list[tuple[str, bytes]], target: str) -> int:
    t = norm(target).lower()
    hits = [i for i, (n, _) in enumerate(entries) if norm(n).lower() == t]
    if len(hits) != 1:
        raise SystemExit(f"{target}: expected 1 packed path, got {len(hits)}")
    return hits[0]


def mesh_name_at(blob: bytes, header_payload: int) -> str:
    return blob[header_payload + 8 : header_payload + 24].split(b"\x00", 1)[0].decode("latin1", errors="replace")


def set_hidden_on_meshes(blob: bytes, names: tuple[str, ...]) -> tuple[bytes, list[str]]:
    data = bytearray(blob)
    found: dict[str, int] = {n: 0 for n in names}

    def walk(start: int, end: int) -> None:
        pos = start
        while pos + 8 <= end:
            ctype, raw = struct.unpack_from("<II", data, pos)
            is_cont = bool(raw & CONTAINER)
            csize = raw & 0x7FFFFFFF
            p0 = pos + 8
            p1 = min(p0 + csize, end)
            if ctype == W3D_CHUNK_MESH_HEADER3 and csize >= 24:
                name = mesh_name_at(bytes(data), p0)
                if name in found:
                    attrs_off = p0 + 4
                    attrs = struct.unpack_from("<I", data, attrs_off)[0]
                    new_attrs = attrs | W3D_MESH_FLAG_HIDDEN
                    struct.pack_into("<I", data, attrs_off, new_attrs)
                    found[name] += 1
            if is_cont:
                walk(p0, p1)
            if p1 <= pos:
                break
            pos = p1

    walk(0, len(data))
    missing = [n for n, c in found.items() if c == 0]
    if missing:
        raise SystemExit(f"meshes not found: {missing}")
    hit = [f"{n} x{c}" for n, c in found.items()]
    if bytes(data) == blob:
        raise SystemExit(f"no bytes changed for {names}")
    if len(data) != len(blob):
        raise SystemExit("W3D size changed; in-place flag edit expected")
    return bytes(data), hit


def hidden_names(blob: bytes) -> list[str]:
    out = []

    def walk(start: int, end: int) -> None:
        pos = start
        while pos + 8 <= end:
            ctype, raw = struct.unpack_from("<II", blob, pos)
            is_cont = bool(raw & CONTAINER)
            csize = raw & 0x7FFFFFFF
            p0 = pos + 8
            p1 = min(p0 + csize, end)
            if ctype == W3D_CHUNK_MESH_HEADER3 and csize >= 24:
                name = mesh_name_at(blob, p0)
                attrs = struct.unpack_from("<I", blob, p0 + 4)[0]
                if attrs & W3D_MESH_FLAG_HIDDEN:
                    out.append(name)
            if is_cont:
                walk(p0, p1)
            pos = p1

    walk(0, len(blob))
    return out


def main() -> int:
    if not SRC_ART.is_file():
        raise SystemExit("missing USA Update 01 ART")
    art_raw = SRC_ART.read_bytes()
    art_sha = hashlib.sha256(art_raw).hexdigest()
    if art_sha != EXPECTED_ART_SHA:
        raise SystemExit(f"ART SHA mismatch {art_sha}")
    if SRC_DATA.is_file():
        data_sha = hashlib.sha256(SRC_DATA.read_bytes()).hexdigest()
        if data_sha != EXPECTED_DATA_SHA:
            raise SystemExit(f"DATA baseline SHA mismatch {data_sha} (must be crashfix-test)")
    else:
        data_sha = EXPECTED_DATA_SHA

    entries = read_big_list(SRC_ART)
    orig_names = [n for n, _ in entries]
    orig_hashes = {norm(n).lower(): hashlib.sha256(b).hexdigest() for n, b in entries}

    for req in AH1Z_REQUIRED:
        find_index(entries, req)

    reports = []
    for path, hide in ((P_AV, F35_HIDE), (P_AVD, F35_HIDE), (P_EA6, EA6_HIDE)):
        i = find_index(entries, path)
        new_blob, hit = set_hidden_on_meshes(entries[i][1], hide)
        hid = hidden_names(new_blob)
        for name in hide:
            if name not in hid:
                raise SystemExit(f"{path}: {name} not HIDDEN after patch")
        entries[i] = (entries[i][0], new_blob)
        reports.append(f"{path}: set HIDDEN on {', '.join(hit)}; now_hidden={hid}")

    if [n for n, _ in entries] != orig_names:
        raise SystemExit("ART path order changed")

    changed = []
    unchanged_count = 0
    for n, b in entries:
        k = norm(n).lower()
        h = hashlib.sha256(b).hexdigest()
        if h != orig_hashes[k]:
            changed.append(n)
        else:
            unchanged_count += 1
    if set(map(norm, changed)) != {P_AV, P_AVD, P_EA6}:
        raise SystemExit(f"unexpected ART changes: {changed}")

    print("Packing ART...")
    blob = build_big_ordered(entries)
    rt = read_big_list
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    out_big = OUT_DIR / "_SPEC_ART_ONE.big"
    out_big.write_bytes(blob)
    rt_entries = rt(out_big)
    if [n for n, _ in rt_entries] != orig_names:
        raise SystemExit("round-trip name mismatch")
    for path in (P_AV, P_AVD, P_EA6):
        i = find_index(rt_entries, path)
        hid = hidden_names(rt_entries[i][1])
        want = F35_HIDE if "AVLightn" in path else EA6_HIDE
        for name in want:
            if name not in hid:
                raise SystemExit(f"packed {path} missing HIDDEN {name}")
    for req in AH1Z_REQUIRED:
        find_index(rt_entries, req)
        i = find_index(entries, req)
        if hashlib.sha256(rt_entries[find_index(rt_entries, req)][1]).hexdigest() != orig_hashes[norm(req).lower()]:
            raise SystemExit(f"AH-1Z asset mutated: {req}")

    sha = hashlib.sha256(blob).hexdigest()
    audit = f"""SPECTER1 SHADOW + AH-1Z ART FIX AUDIT
BASELINE_DATA = SPECTER1_Aircraft_Standardization_01_CRASHFIX_TEST
BASELINE_DATA_SHA256 = {data_sha}
BASELINE_ART = SPECTER1_USA_Update_01 _SPEC_ART_ONE.big (original SPECTER1 ART + AH-1Z donor files)
BASELINE_ART_SHA256 = {art_sha}
NEW_ART_SHA256 = {sha}
NEW_ART_BYTES = {len(blob)}
NEW_ART_FILE_COUNT = {len(entries)}
DATA_CHANGED = NO
ART_CHANGED = YES
INGAME_TESTED = NO

CRASHFIX_COMMANDSET_OVERLAY_PRESERVED = YES (DATA not modified)
AIRCRAFT_STANDARDIZATION_44_TARGETS_PRESERVED = YES (DATA not modified)
PREVIOUS_IRAQ_CHANGES_PRESERVED = YES
PREVIOUS_USA_CHANGES_PRESERVED = YES
PREVIOUS_CHINA_CHANGES_PRESERVED = YES
PREVIOUS_RUSSIA_CHANGES_PRESERVED = YES
IRAQ_SU24MR_UNCHANGED = YES
AIRBASE_ARCHITECTURE_CHANGED = NO

F35BJSF_OBJECT = AmericaJetF35BJSF
F35BJSF_DISPLAY = OBJECT:AmericaJetF35BJSF (CSF F-35B JSF)
F35BJSF_BUTTON_IMAGE = AmericaF35BJSF
F35BJSF_MODEL = AVLightn
F35BJSF_SHADOW_TYPE = SHADOW_VOLUME (unchanged)
F35BJSF_ROOT_CAUSE = AVLightn.W3D thin FX meshes EX01/EX02 (23-unit strips), JAFTERBURNED (vertical cone to z=14.1), CYLINDER02/03, TURBO still participate in volume-shadow even with INI HideSubObject. Shared W3D also used by Britain/Italy/Japan/NATO/SK F-35B and Lightning clones.
F35BJSF_FIX = Set W3D_MESH_FLAG_HIDDEN on those meshes in AVLightn.W3D and AVLightn_D.W3D. Mesh vertices not rewritten.

EA6B_OBJECT = AmericaJetF18Prowler
EA6B_DISPLAY = OBJECT:AmericaJetF18Prowler (CSF EA-6B Prowler)
EA6B_BUTTON_IMAGE = EA6Prowler
EA6B_MODEL = EA6
EA6B_SHADOW_TYPE = SHADOW_VOLUME (unchanged)
EA6B_ROOT_CAUSE = EA6.W3D HOOK mesh sits at y=-21..-26 as a 0.47-tall strip. INI HideSubObject=HOOK hides the render mesh but SHADOW_VOLUME still extruded the hook across the terrain. Shared by JapanJetEA6B.
EA6B_FIX = Set W3D_MESH_FLAG_HIDDEN on HOOK in EA6.W3D.

AH1Z_OBJECT = AmericaHelicopterAH1Z
AH1Z_DISPLAY = OBJECT:AmericaHelicopterAH1Z (CSF AH-1Z Viper)
AH1Z_BUTTON = Command_ConstructAmericaHelicopterAH1Z
AH1Z_CAMEO = AH1ZTB
AH1Z_MODEL = LSFAH1Z / LSFAH1Zd / LSFAH1Zk
AH1Z_ROOT_CAUSE = Crashfix-test and later DATA-only ZIPs never shipped ART. Original SPECTER1 ART has no LSFAH1Z.W3D or AH1ZTB.tga, so the live object had no drawable model.
AH1Z_FIX = Ship the USA Update 01 donor ART family (already in this ART baseline) as _SPEC_ART_ONE.big alongside the crashfix DATA.

W3D_PATCH_REPORT =
  {reports[0]}
  {reports[1]}
  {reports[2]}

ART_CHANGED_PATHS =
  {P_AV}
  {P_AVD}
  {P_EA6}
ART_ADDED_PATHS_VS_ORIGINAL_SPECTER1 =
  {chr(10).join('  ' + p for p in AH1Z_REQUIRED)}
UNCHANGED_ART_FILES = {unchanged_count}
DATA_INI_FILES_CHANGED = NONE
"""
    changelog = """SPECTER1 F-35B / EA-6B shadow + AH-1Z ART fix

ART only. Uses crashfix-test DATA unchanged. Does not overwrite the crashfix DATA release.

1. F-35B JSF (AmericaJetF35BJSF, model AVLightn): volume-shadow line came from thin FX submeshes (EX01/EX02, JAFTERBURNED, CYLINDER02/03, TURBO). INI HideSubObject did not stop SHADOW_VOLUME. Set W3D HIDDEN on those meshes in AVLightn.W3D and AVLightn_D.W3D.
2. EA-6B (AmericaJetF18Prowler, model EA6): same class of bug from the HOOK mesh. Set W3D HIDDEN on HOOK in EA6.W3D.
3. AH-1Z Viper (AmericaHelicopterAH1Z, model LSFAH1Z): missing from original SPECTER1 ART. This ART BIG includes the donor LSFAH1Z W3D/textures and AH1ZTB cameo.

No DATA edits. No airbase/runway changes. No Iraq Su-24MR change. No Weapon.ini change.
"""
    (OUT_DIR / "audit.txt").write_text(audit, encoding="utf-8")
    (OUT_DIR / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "_SPEC_ART_ONE.big").write_bytes(blob)
    (WS_OUT / "audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")
    print(audit)
    print("WROTE", out_big, len(blob), sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
