#!/usr/bin/env python3
"""National ground visual identity: codes, camo tones, muted markings."""

from __future__ import annotations

from PIL import Image, ImageDraw

# nation key -> (2-letter code, flag style, RGB multiply tone)
IDENTITY = {
    "Japan": ("JP", "japan", (0.96, 1.02, 0.90)),
    "SouthKorea": ("SK", "korea", (0.93, 1.03, 0.90)),
    "Germany": ("DE", "germany", (0.92, 0.96, 0.90)),
    "France": ("FR", "france", (0.90, 1.02, 0.88)),
    "Britain": ("GB", "britain", (0.94, 0.98, 0.88)),
    "Italy": ("IT", "italy", (0.92, 1.00, 0.88)),
    "Turkey": ("TR", "turkey", (0.98, 0.96, 0.86)),
    "Ukraine": ("UA", "ukraine", (0.90, 1.02, 0.86)),
    "Sweden": ("SE", "sweden", (0.90, 0.96, 0.92)),
    "India": ("IN", "india", (1.02, 1.00, 0.86)),
    "Pakistan": ("PK", "pakistan", (1.00, 0.98, 0.84)),
    "SaudiArabia": ("SA", "saudi", (1.08, 1.02, 0.82)),
    "UAE": ("AE", "uae", (1.06, 1.00, 0.80)),
    "Vietnam": ("VN", "vietnam", (0.88, 1.04, 0.82)),
    "Syria": ("SY", "syria", (1.04, 0.98, 0.82)),
    "Libya": ("LY", "libya", (1.08, 1.00, 0.78)),
    "SouthAfrica": ("ZA", "southafrica", (0.96, 0.98, 0.82)),
}

PROTECTED_SIDES = {
    "America",
    "USA",
    "Russia",
    "China",
    "PLA",
    "Iran",
    "Iraq",
    "Egypt",
    "Israel",
    "NorthKorea",
    "NATO",
    "Nato",
}

PROTECTED_ART_STEMS = {
    "us_m1a2sep2",
    "rus_t90a",
    "chi_ztz99a2",
    "irq_t72m1",
}

SKIP_TEX = (
    "track",
    "tread",
    "wheel",
    "tire",
    "glass",
    "window",
    "lamp",
    "light",
    "exhaust",
    "spec_",
    "normal",
    "shadow",
    "fx_",
    "smoke",
    "fire",
)


def muted_flag(style: str, size=(128, 64)) -> Image.Image:
    w, h = size
    im = Image.new("RGB", (w, h), (90, 95, 85))
    d = ImageDraw.Draw(im)

    def sx(x):
        return int(x * w / 128)

    def sy(y):
        return int(y * h / 64)

    if style == "japan":
        im.paste((214, 214, 210), [0, 0, w, h])
        d.ellipse((sx(44), sy(12), sx(84), sy(52)), fill=(150, 36, 36))
    elif style == "korea":
        im.paste((214, 214, 210), [0, 0, w, h])
        d.ellipse((sx(48), sy(16), sx(80), sy(48)), fill=(150, 40, 40))
        d.pieslice((sx(48), sy(16), sx(80), sy(48)), 90, 270, fill=(32, 56, 92))
    elif style == "germany":
        d.rectangle((0, 0, w, sy(21)), fill=(28, 28, 28))
        d.rectangle((0, sy(21), w, sy(43)), fill=(120, 36, 36))
        d.rectangle((0, sy(43), w, h), fill=(168, 132, 48))
    elif style == "france":
        d.rectangle((0, 0, sx(42), h), fill=(36, 56, 96))
        d.rectangle((sx(42), 0, sx(86), h), fill=(220, 216, 200))
        d.rectangle((sx(86), 0, w, h), fill=(132, 40, 40))
    elif style == "britain":
        im.paste((36, 52, 92), [0, 0, w, h])
        d.rectangle((sx(54), 0, sx(74), h), fill=(214, 214, 210))
        d.rectangle((0, sy(24), w, sy(40)), fill=(214, 214, 210))
        d.rectangle((sx(58), 0, sx(70), h), fill=(140, 36, 36))
        d.rectangle((0, sy(28), w, sy(36)), fill=(140, 36, 36))
    elif style == "italy":
        d.rectangle((0, 0, sx(42), h), fill=(40, 96, 52))
        d.rectangle((sx(42), 0, sx(86), h), fill=(220, 216, 200))
        d.rectangle((sx(86), 0, w, h), fill=(140, 40, 40))
    elif style == "turkey":
        im.paste((132, 32, 36), [0, 0, w, h])
        d.ellipse((sx(40), sy(16), sx(80), sy(48)), fill=(220, 216, 200))
        d.ellipse((sx(48), sy(20), sx(82), sy(44)), fill=(132, 32, 36))
        d.regular_polygon((sx(86), sy(32), max(3, sx(7))), 5, fill=(220, 216, 200))
    elif style == "ukraine":
        d.rectangle((0, 0, w, sy(32)), fill=(36, 72, 120))
        d.rectangle((0, sy(32), w, h), fill=(176, 148, 48))
    elif style == "sweden":
        im.paste((36, 72, 110), [0, 0, w, h])
        d.rectangle((sx(40), 0, sx(56), h), fill=(188, 160, 52))
        d.rectangle((0, sy(26), w, sy(38)), fill=(188, 160, 52))
    elif style == "india":
        d.rectangle((0, 0, w, sy(21)), fill=(166, 92, 38))
        d.rectangle((0, sy(21), w, sy(43)), fill=(220, 216, 200))
        d.rectangle((0, sy(43), w, h), fill=(46, 92, 52))
        d.ellipse((sx(56), sy(24), sx(72), sy(40)), outline=(30, 48, 88), width=max(1, w // 64))
    elif style == "pakistan":
        d.rectangle((0, 0, sx(22), h), fill=(220, 216, 200))
        d.rectangle((sx(22), 0, w, h), fill=(28, 78, 48))
        d.ellipse((sx(58), sy(16), sx(96), sy(48)), fill=(220, 216, 200))
        d.ellipse((sx(66), sy(20), sx(100), sy(44)), fill=(28, 78, 48))
        d.regular_polygon((sx(104), sy(32), max(3, sx(6))), 5, fill=(220, 216, 200))
    elif style == "saudi":
        im.paste((36, 78, 42), [0, 0, w, h])
        d.rectangle((sx(18), sy(22), sx(110), sy(30)), fill=(214, 214, 200))
        d.rectangle((sx(28), sy(36), sx(100), sy(40)), fill=(214, 214, 200))
        d.polygon([(sx(100), sy(36)), (sx(112), sy(38)), (sx(100), sy(40))], fill=(214, 214, 200))
    elif style == "uae":
        d.rectangle((0, 0, sx(28), h), fill=(132, 36, 36))
        d.rectangle((sx(28), 0, w, sy(21)), fill=(46, 92, 52))
        d.rectangle((sx(28), sy(21), w, sy(43)), fill=(220, 216, 200))
        d.rectangle((sx(28), sy(43), w, h), fill=(36, 36, 36))
    elif style == "vietnam":
        im.paste((140, 36, 36), [0, 0, w, h])
        d.regular_polygon((sx(64), sy(32), max(8, sx(16))), 5, fill=(196, 168, 48))
    elif style == "syria":
        d.rectangle((0, 0, w, sy(21)), fill=(132, 36, 36))
        d.rectangle((0, sy(21), w, sy(43)), fill=(220, 216, 200))
        d.rectangle((0, sy(43), w, h), fill=(28, 28, 28))
        d.regular_polygon((sx(50), sy(32), max(3, sx(6))), 5, fill=(40, 92, 48))
        d.regular_polygon((sx(78), sy(32), max(3, sx(6))), 5, fill=(40, 92, 48))
    elif style == "libya":
        d.rectangle((0, 0, w, sy(21)), fill=(132, 36, 36))
        d.rectangle((0, sy(21), w, sy(43)), fill=(28, 28, 28))
        d.rectangle((0, sy(43), w, h), fill=(40, 92, 48))
        d.ellipse((sx(52), sy(22), sx(76), sy(42)), outline=(220, 216, 200), width=max(1, w // 64))
        d.regular_polygon((sx(82), sy(32), max(3, sx(5))), 5, fill=(220, 216, 200))
    elif style == "southafrica":
        im.paste((36, 52, 92), [0, 0, w, h])
        d.rectangle((0, 0, w, sy(16)), fill=(132, 36, 36))
        d.rectangle((0, sy(48), w, h), fill=(36, 36, 36))
        d.polygon([(0, 0), (sx(48), sy(32)), (0, h)], fill=(40, 92, 48))
        d.polygon([(0, sy(16)), (sx(32), sy(32)), (0, sy(48))], fill=(196, 168, 48))
    else:
        im.paste((90, 95, 85), [0, 0, w, h])
    return im


def skip_texture(name: str) -> bool:
    low = name.lower()
    return any(tok in low for tok in SKIP_TEX)
