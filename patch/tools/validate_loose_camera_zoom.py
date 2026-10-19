#!/usr/bin/env python3
"""Static checks for the loose SPECTER camera-zoom package.

This does not launch Zero Hour. It checks the packaged GameData.ini, the
zip layout, and the install/uninstall decision table implemented by the
batch files.
"""
from __future__ import annotations

import hashlib
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "patch" / "Release" / "SPECTER_CAMERA_ZOOM_LOOSE"
ZIP = ROOT / "patch" / "Release" / "SPECTER_CAMERA_ZOOM_LOOSE.zip"
INI = PKG / "Data" / "INI" / "GameData.ini"

SOURCE_SHA = "da7ab8448b91a04cedb6affe1f6acda28960b82e643b4e94f843df4e511319cd"
PACKED_SHA = "35b1ee7cbdd38949900d10e4fe9fe090f60db5f589cb86428032da0152c96fd4"
OLD = b"  MaxCameraHeight = 310.0"
NEW = b"  MaxCameraHeight = 620.0"


def fail(msg: str) -> None:
    raise SystemExit(f"FAIL: {msg}")


def check_ini() -> None:
    data = INI.read_bytes()
    if len(data) != 21181:
        fail(f"size {len(data)}")
    digest = hashlib.sha256(data).hexdigest()
    if digest != PACKED_SHA:
        fail(f"sha256 {digest}")
    if data.count(NEW) != 1 or data.count(OLD) != 0:
        fail("MaxCameraHeight assignment")
    restored = data.replace(NEW, OLD)
    if hashlib.sha256(restored).hexdigest() != SOURCE_SHA:
        fail("restored source hash")
    diffs = [i for i, (a, b) in enumerate(zip(restored, data)) if a != b]
    if restored[diffs[0] : diffs[-1] + 1] != b"31" or data[diffs[0] : diffs[-1] + 1] != b"62":
        fail(f"unexpected byte diff {diffs}")
    if b"\t" in data or b"\n" not in data or data.count(b"\r\n") != data.count(b"\n"):
        fail("line endings or tabs")
    lines = data.split(b"\r\n")
    if lines[1] != b"; FILE: GameData.ini (SYSTEM) /////////////////////////////////////////////////":
        fail("header")
    block = [ln for ln in lines if ln in (b"GameData", b"End")]
    if block != [b"GameData", b"End"]:
        fail(f"blocks {block}")
    required = {
        b"  CameraPitch = 37.5": 1,
        b"  CameraHeight = 232.0": 1,
        b"  MaxCameraHeight = 620.0": 1,
        b"  MinCameraHeight = 120.0": 1,
        b"  CameraAdjustSpeed = 0.3      ; between 0 and 1 - this is how fast the camera snaps to the desired height": 1,
        b"  EnforceMaxCameraHeight = No      ; Obey max camera height while scrolling?": 1,
    }
    for line, count in required.items():
        if data.split(b"\r\n").count(line) != count:
            fail(f"missing line {line!r}")
    print("ini_structure=PASS")
    print(f"ini_sha256={digest}")
    print("changed_line=MaxCameraHeight = 620.0")
    print("byte_identity_except_310_to_620=PASS")


def check_zip() -> None:
    expected = {
        "INSTALL.txt",
        "HASHES.txt",
        "Install_Loose_GameData.bat",
        "Uninstall_Loose_GameData.bat",
        "Data/INI/GameData.ini",
    }
    with zipfile.ZipFile(ZIP) as zf:
        names = set(zf.namelist())
        if names != expected:
            fail(f"zip names {sorted(names)}")
        if any(name.lower().endswith(".big") for name in names):
            fail("zip contains a BIG")
        packed = zf.read("Data/INI/GameData.ini")
        if packed != INI.read_bytes():
            fail("zip ini bytes differ")
    print("zip_relative_path=Data/INI/GameData.ini")
    print("zip_contains_big=no")
    print("zip_layout=PASS")


def apply_install(game: Path, package_ini: bytes, prior: bytes | None, marker: str | None) -> dict:
    """Mirror Install_Loose_GameData.bat."""
    dest = game / "Data" / "INI" / "GameData.ini"
    mark = game / "Data" / "INI" / "SPECTER_CameraZoom_install.txt"
    backup = game / "Data" / "INI" / "GameData.ini.specter-zoom-backup"
    (game / "Data" / "INI").mkdir(parents=True, exist_ok=True)
    if prior is not None and not dest.exists():
        dest.write_bytes(prior)
    if marker is not None:
        mark.write_bytes(f"SPECTER_CAMERA_ZOOM_LOOSE\r\naction={marker}\r\n".encode())
    if dest.exists():
        if mark.exists():
            dest.write_bytes(package_ini)
        elif dest.read_bytes() != package_ini:
            backup.write_bytes(dest.read_bytes())
            mark.write_bytes(b"SPECTER_CAMERA_ZOOM_LOOSE\r\naction=replaced\r\n")
            dest.write_bytes(package_ini)
        else:
            mark.write_bytes(b"SPECTER_CAMERA_ZOOM_LOOSE\r\naction=created\r\n")
            dest.write_bytes(package_ini)
    else:
        dest.write_bytes(package_ini)
        if not mark.exists():
            mark.write_bytes(b"SPECTER_CAMERA_ZOOM_LOOSE\r\naction=created\r\n")
    if dest.read_bytes() != package_ini:
        fail("install simulation mismatch")
    return {"dest": dest.read_bytes(), "marker": mark.read_bytes(), "backup": backup.read_bytes() if backup.exists() else None}


def apply_uninstall(game: Path) -> str:
    """Mirror Uninstall_Loose_GameData.bat. Returns the action taken."""
    dest = game / "Data" / "INI" / "GameData.ini"
    mark = game / "Data" / "INI" / "SPECTER_CameraZoom_install.txt"
    backup = game / "Data" / "INI" / "GameData.ini.specter-zoom-backup"
    if not mark.exists():
        return "left-unmarked"
    text = mark.read_bytes()
    if b"action=created" in text.splitlines():
        if dest.exists():
            dest.unlink()
        mark.unlink()
        return "deleted"
    if b"action=replaced" in text.splitlines():
        if not backup.exists():
            return "backup-missing"
        dest.write_bytes(backup.read_bytes())
        backup.unlink()
        mark.unlink()
        return "restored"
    return "unrecognized"


def check_install_table() -> None:
    package = INI.read_bytes()
    install_bat = (PKG / "Install_Loose_GameData.bat").read_bytes()
    uninstall_bat = (PKG / "Uninstall_Loose_GameData.bat").read_bytes()
    for blob, label in ((install_bat, "install"), (uninstall_bat, "uninstall")):
        if b"\n" in blob.replace(b"\r\n", b"") or not blob.endswith(b"\r\n"):
            fail(f"{label} bat line endings")
    for token in (
        b"action=created",
        b"action=replaced",
        b"GameData.ini.specter-zoom-backup",
        b"SPECTER_CameraZoom_install.txt",
        b"goto backup_user",
    ):
        if token not in install_bat:
            fail(f"install bat missing {token!r}")
    if b"del /f \"%DEST%\"" not in uninstall_bat:
        fail("uninstall bat missing created-file delete")
    if uninstall_bat.count(b"del /f \"%DEST%\"") != 1:
        fail("uninstall deletes the loose file more than once")

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        # clean extract: create, then uninstall deletes only the new file
        game = base / "clean"
        game.mkdir()
        result = apply_install(game, package, None, None)
        if b"action=created" not in result["marker"] or result["backup"] is not None:
            fail("clean install marker")
        if apply_uninstall(game) != "deleted":
            fail("clean uninstall")
        if (game / "Data" / "INI" / "GameData.ini").exists():
            fail("clean uninstall left the file")
        if (game / "Data" / "INI" / "SPECTER_CameraZoom_install.txt").exists():
            fail("clean uninstall left the marker")

        # pre-existing loose file is backed up and restored
        game = base / "prior"
        game.mkdir()
        prior = b"; user file\r\nGameData\r\n  MaxCameraHeight = 400.0\r\nEnd\r\n"
        result = apply_install(game, package, prior, None)
        if result["backup"] != prior or b"action=replaced" not in result["marker"]:
            fail("backup path")
        if apply_uninstall(game) != "restored":
            fail("restore path")
        restored = (game / "Data" / "INI" / "GameData.ini").read_bytes()
        if restored != prior:
            fail("restored bytes")
        if (game / "Data" / "INI" / "GameData.ini.specter-zoom-backup").exists():
            fail("backup left behind")

        # unmarked file is not deleted
        game = base / "unmarked"
        (game / "Data" / "INI").mkdir(parents=True)
        (game / "Data" / "INI" / "GameData.ini").write_bytes(prior)
        if apply_uninstall(game) != "left-unmarked":
            fail("unmarked delete")
        if (game / "Data" / "INI" / "GameData.ini").read_bytes() != prior:
            fail("unmarked file changed")

        # reinstall keeps the original backup
        game = base / "reinstall"
        game.mkdir()
        apply_install(game, package, prior, None)
        edited = package.replace(b"620.0", b"111.0")
        (game / "Data" / "INI" / "GameData.ini").write_bytes(edited)
        result = apply_install(game, package, None, None)
        if result["backup"] != prior or result["dest"] != package:
            fail("reinstall disturbed the backup")
    print("install_uninstall_table=PASS")


def main() -> int:
    check_ini()
    check_zip()
    check_install_table()
    print("static_validation=PASS")
    print("runtime_game_test=NOT_RUN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
