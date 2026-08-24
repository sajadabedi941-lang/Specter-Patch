#!/usr/bin/env python3
"""Surgical Russia aircraft CommandButton + CSF helpers.

Does not rewrite stock aircraft objects. Adds missing construct-button
labels and updates ButtonImage / missing CommandButton blocks only.
"""
from __future__ import annotations

import re
import struct

NEW_CONSTRUCT_BUTTONS = {
    "Command_ConstructRussiaJetSu47Berkut": {
        "Object": "RussiaJetSu47Berkut",
        "TextLabel": "CONTROLBAR:ConstructRussiaJetSu47Berkut",
        "ButtonImage": "SU47",
        "DescriptLabel": "CONTROLBAR:ToolTipRussiaJetSu47Berkut",
    },
    "Command_ConstructRussiaJetSu75": {
        "Object": "RussiaJetSu75",
        "TextLabel": "CONTROLBAR:ConstructRussiaJetSu75",
        "ButtonImage": "SU75",
        "DescriptLabel": "CONTROLBAR:ToolTipRussiaJetSu75",
    },
    "Command_ConstructRussiaJetSu39": {
        "Object": "RussiaJetSu39",
        "TextLabel": "CONTROLBAR:ConstructRussiaJetSu39",
        "ButtonImage": "rus_su39",
        "DescriptLabel": "CONTROLBAR:ToolTipRussiaJetSu39",
    },
    "Command_ConstructRussiaJetDozor600": {
        "Object": "RussiaJetDozor600",
        "TextLabel": "CONTROLBAR:ConstructRussiaJetDozor600",
        "ButtonImage": "Dozor600",
        "DescriptLabel": "CONTROLBAR:ToolTipRussiaJetDozor600",
    },
    "Command_ConstructRussiaJetSu57Felon": {
        "Object": "RussiaJetSu57Felon",
        "TextLabel": "CONTROLBAR:ConstructRussiaJetSu57Felon",
        "ButtonImage": "rus_su57",
        "DescriptLabel": "CONTROLBAR:ToolTipRussiaJetSu57Felon",
    },
    "Command_ConstructRussiaJetSuT75": {
        "Object": "RussiaJetSuT75",
        "TextLabel": "CONTROLBAR:ConstructRussiaJetSuT75",
        "ButtonImage": "SU75",
        "DescriptLabel": "CONTROLBAR:ToolTipRussiaJetSuT75",
    },
    "Command_ConstructRussiaJetSuT50PAKFA": {
        "Object": "RussiaJetSuT50PAKFA",
        "TextLabel": "CONTROLBAR:ConstructRussiaJetSuT50PAKFA",
        "ButtonImage": "T50",
        "DescriptLabel": "CONTROLBAR:ToolTipRussiaJetSuT50PAKFA",
    },
    "Command_ConstructRussiaJetSu35Flanker": {
        "Object": "RussiaJetSu35Flanker",
        "TextLabel": "CONTROLBAR:ConstructRussiaJetSu35Flanker",
        "ButtonImage": "SU35",
        "DescriptLabel": "CONTROLBAR:ToolTipRussiaJetSu35Flanker",
    },
    "Command_ConstructRussiaJetSu24MR": {
        "Object": "RussiaJetSu24MR",
        "TextLabel": "CONTROLBAR:ConstructRussiaJetSu24MR",
        "ButtonImage": "SU24",
        "DescriptLabel": "CONTROLBAR:ToolTipRussiaJetSu24MR",
    },
    "Command_ConstructRussiaJetSu33": {
        "Object": "RussiaJetSu33",
        "TextLabel": "CONTROLBAR:ConstructRussiaJetSu33",
        "ButtonImage": "SU33TB",
        "DescriptLabel": "CONTROLBAR:ToolTipRussiaJetSu33",
    },
    "Command_ConstructRussiaJetSu27Flanker": {
        "Object": "RussiaJetSu27Flanker",
        "TextLabel": "CONTROLBAR:ConstructRussiaJetSu27Flanker",
        "ButtonImage": "SU27SKTB",
        "DescriptLabel": "CONTROLBAR:ToolTipRussiaJetSu27Flanker",
    },
}

# Current donor/UI icons. Object names stay the packed working aircraft.
BUTTON_IMAGE_UPDATES = {
    "Command_ConstructRussiaHelicopterKA52": "KA52",
    "Command_ConstructRussiaJetSu35S": "SU35",
    "Command_ConstructRussiaJetSu35AG": "SU35",
    "Command_ConstructRussiaJetSu34": "SU34",
    "Command_ConstructRussiaJetSU24M2": "SU24",
    "Command_ConstructRussiaJetSU24MP": "SU24",
    "Command_ConstructRussiaJetTu22M3M": "TU22M3",
    "Command_ConstructRussiaJetSu75Checkmate": "SU75",
    "Command_ConstructRussiaJetSu47Recon": "SU47",
}

CSF_STRINGS = {
    "CONTROLBAR:ConstructRussiaJetDozor600": "Dozor-600",
    "CONTROLBAR:ToolTipRussiaJetDozor600": "Build Dozor-600 UAV",
    "OBJECT:RussiaDozor600": "Dozor-600",
    "CONTROLBAR:ConstructRussiaJetSu47Berkut": "Su-47 Berkut",
    "CONTROLBAR:ToolTipRussiaJetSu47Berkut": "Build Su-47 Berkut",
    "OBJECT:RussiaSu47Berkut": "Su-47 Berkut",
    "CONTROLBAR:ConstructRussiaJetSu75": "Su-75 Checkmate",
    "CONTROLBAR:ToolTipRussiaJetSu75": "Build Su-75 Checkmate",
    "CONTROLBAR:ConstructRussiaJetSu39": "Su-39",
    "CONTROLBAR:ToolTipRussiaJetSu39": "Build Su-39",
    "OBJECT:RussiaSu39": "Su-39",
    "CONTROLBAR:ConstructRussiaJetSu75Checkmate": "Su-75 Checkmate",
    "CONTROLBAR:ToolTipRussiaJetSu75Checkmate": "Build Su-75 Checkmate",
    "OBJECT:RussiaSu75Checkmate": "Su-75 Checkmate",
    "CONTROLBAR:ConstructRussiaJetSu57Felon": "Su-57 Felon",
    "CONTROLBAR:ToolTipRussiaJetSu57Felon": "Build Su-57 Felon",
    "OBJECT:RussiaSu57Felon": "Su-57 Felon",
    "CONTROLBAR:ConstructRussiaJetSuT75": "Su-T75",
    "CONTROLBAR:ToolTipRussiaJetSuT75": "Build Su-T75",
    "OBJECT:RussiaSuT75": "Su-T75",
    "CONTROLBAR:ConstructRussiaJetSuT50PAKFA": "Su-T50 PAK FA",
    "CONTROLBAR:ToolTipRussiaJetSuT50PAKFA": "Build Su-T50 PAK FA",
    "OBJECT:RussiaSuT50PAKFA": "Su-T50 PAK FA",
    "CONTROLBAR:ConstructRussiaJetSu35Flanker": "Su-35 Flanker",
    "CONTROLBAR:ToolTipRussiaJetSu35Flanker": "Build Su-35 Flanker",
    "OBJECT:RussiaSu35Flanker": "Su-35 Flanker",
    "CONTROLBAR:ConstructRussiaJetSu24MR": "Su-24MR",
    "CONTROLBAR:ToolTipRussiaJetSu24MR": "Build Su-24MR",
    "OBJECT:RussiaSu24MR": "Su-24MR",
    "CONTROLBAR:ConstructRussiaJetSu33": "Su-33",
    "CONTROLBAR:ToolTipRussiaJetSu33": "Build Su-33 Naval Flanker",
    "OBJECT:RussiaSu33": "Su-33",
    "CONTROLBAR:ConstructRussiaJetSu27Flanker": "Su-27 Flanker",
    "CONTROLBAR:ToolTipRussiaJetSu27Flanker": "Build Su-27 Flanker",
    "OBJECT:RussiaSu27Flanker": "Su-27 Flanker",
}


def _commandbutton_block(name: str, spec: dict) -> str:
    return (
        f"CommandButton {name}\n"
        f"  Command          = UNIT_BUILD\n"
        f"  Object           = {spec['Object']}\n"
        f"  TextLabel        = {spec['TextLabel']}\n"
        f"  ButtonImage      = {spec['ButtonImage']}\n"
        f"  ButtonBorderType = BUILD\n"
        f"  DescriptLabel    = {spec['DescriptLabel']}\n"
        f"End\n"
    )


def parse_commandbutton_block(text: str, name: str) -> dict | None:
    m = re.search(
        rf"^CommandButton {re.escape(name)}\s*\n(?P<body>.*?)(?:\nEnd)(?=\n|$)",
        text,
        re.M | re.S,
    )
    if not m:
        return None
    fields = {}
    for line in m.group("body").splitlines():
        raw = line.split(";", 1)[0]
        kv = re.match(r"^\s+(\S+)\s+=\s+(\S+)\s*$", raw)
        if kv:
            fields[kv.group(1)] = kv.group(2)
    fields["_block"] = text[m.start() : m.end()]
    return fields


def patch_commandbutton_ini(raw: bytes) -> bytes:
    text = raw.decode("latin1")
    if "\r\n" in text:
        raise SystemExit("parser FAIL: CommandButton.ini has CRLF")
    for name, image in BUTTON_IMAGE_UPDATES.items():
        parsed = parse_commandbutton_block(text, name)
        if not parsed:
            raise SystemExit(f"parser FAIL: missing packed CommandButton {name}")
        old = parsed["_block"]
        new = re.sub(
            r"^(\s+ButtonImage\s+=\s+)\S+(\s*)$",
            rf"\1{image}\2",
            old,
            count=1,
            flags=re.M,
        )
        if new == old and parsed.get("ButtonImage") != image:
            raise SystemExit(f"parser FAIL: could not update ButtonImage on {name}")
        text = text.replace(old, new, 1)
    insert_at = None
    for name, spec in NEW_CONSTRUCT_BUTTONS.items():
        parsed = parse_commandbutton_block(text, name)
        block = _commandbutton_block(name, spec).rstrip("\n")
        if parsed:
            if parsed.get("Object") != spec["Object"]:
                raise SystemExit(
                    f"parser FAIL: {name} Object {parsed.get('Object')} != {spec['Object']}"
                )
            text = text.replace(parsed["_block"], block, 1)
        else:
            if insert_at is None:
                insert_at = text.find("CommandButton Command_ConstructRussiaJetSu47Recon")
                if insert_at < 0:
                    insert_at = len(text)
            text = text[:insert_at] + block + "\n" + text[insert_at:]
            insert_at += len(block) + 1
    out = text.encode("latin1")
    if b"\r\n" in out:
        raise SystemExit("parser FAIL: CommandButton.ini gained CRLF")
    return out


def decode_csf_labels(blob: bytes) -> set[str]:
    if blob[:4] != b" FSC":
        raise SystemExit("parser FAIL: generals.csf magic is not FSC")
    _ver, nlabels, _nstrings, _unused, _lang = struct.unpack_from("<IIIII", blob, 4)
    pos = 24
    names = set()
    for _ in range(nlabels):
        if blob[pos : pos + 4] != b" LBL":
            raise SystemExit("parser FAIL: generals.csf LBL sync lost")
        pos += 4
        count, namelen = struct.unpack_from("<II", blob, pos)
        pos += 8
        names.add(blob[pos : pos + namelen].decode("latin1"))
        pos += namelen
        for _i in range(count):
            kind = blob[pos : pos + 4]
            pos += 4
            slen = struct.unpack_from("<I", blob, pos)[0]
            pos += 4 + slen * 2
            if kind == b"WRTS":
                elen = struct.unpack_from("<I", blob, pos)[0]
                pos += 4 + elen
    return names


def _xor_utf16(text: str) -> bytes:
    return struct.pack("<" + "H" * len(text), *[ord(c) ^ 0xFFFF for c in text])


def _encode_csf_label(name: str, text: str) -> bytes:
    nb = name.encode("latin1")
    out = b" LBL" + struct.pack("<II", 1, len(nb)) + nb
    out += b" RTS" + struct.pack("<I", len(text)) + _xor_utf16(text)
    return out


def add_csf_strings(blob: bytes, strings: dict[str, str] | None = None) -> bytes:
    strings = CSF_STRINGS if strings is None else strings
    existing = decode_csf_labels(blob)
    to_add = {k: v for k, v in strings.items() if k not in existing}
    if not to_add:
        return blob
    ver, nlabels, nstrings, unused, lang = struct.unpack_from("<IIIII", blob, 4)
    extra = b"".join(_encode_csf_label(k, v) for k, v in to_add.items())
    header = b" FSC" + struct.pack(
        "<IIIII", ver, nlabels + len(to_add), nstrings + len(to_add), unused, lang
    )
    out = header + blob[24:] + extra
    if decode_csf_labels(out) < existing | set(to_add):
        raise SystemExit("parser FAIL: CSF append lost labels")
    for key in to_add:
        if key not in decode_csf_labels(out):
            raise SystemExit(f"parser FAIL: CSF missing added {key}")
    print(f"CSF ADD PASS: {len(to_add)} labels")
    return out


def render_live_commandset_buttons() -> str:
    return "".join(
        _commandbutton_block(name, spec) + "\n" for name, spec in NEW_CONSTRUCT_BUTTONS.items()
    )
