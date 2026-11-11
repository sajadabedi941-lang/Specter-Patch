# V25 archive health

- Generated: 2026-11-11 04:58 Asia/Tehran
- Volumes found: **159** (expected zip + z01–z157 = **158**)
- Complete for 7z: **True**
- z62 present: **True**
- Extra volumes: [158]
- Missing expected: none

## 7z test

- ok: **True**
- returncode: 0

```

7-Zip 23.01 (x64) : Copyright (c) 1999-2023 Igor Pavlov : 2023-06-20
 64-bit locale=en_US.UTF-8 Threads:4 OPEN_MAX:524288

Scanning the drive for archives:
1 file, 24301276 bytes (24 MiB)

Testing archive: /tmp/v25_src/V25.zip
--
Path = /tmp/v25_src/V25.zip
Type = zip
Physical Size = 24301276
Embedded Stub Size = 4
Total Physical Size = 3975335644
Multivolume = +
Volume Index = 157
Volumes = 158

Everything is Ok

Folders: 237
Files: 12361
Size:       7633881130
Compressed: 3975335644
```

## SPECTER FINAL baseline (read-only)

- `folder`: `/tmp/ss1/SPECTER FINAL (GeneralsMode.com)`
- `present`: `True`
- `_SPEC_DATA_ONE.big`: `{'bytes': 374093201, 'sha256': '7f8c7f63e972652e8d178c2a43b1f0102904096d630538b010dbf2d081881343'}`
- `_SPEC_ART_TWO.big`: `{'bytes': 312978491, 'sha256': '81d9a4aa10550ef8b3f4a58842f159fda3f54a1af32fcef37df185eb9b9995bf'}`
- `_SPEC_ART_ONE.big`: `not in SPECTER FINAL overlay folder`
- `loose_CommandSet.ini`: `True`
- `loose_CommandButton.ini`: `True`

Original SPECTER BIGs are not modified by this tool in stage 1.
