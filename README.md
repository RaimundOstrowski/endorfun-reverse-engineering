# Endorfun (1995) reverse-engineering notes

Static analysis of the Windows 3.1 / Windows 95 puzzle game **Endorfun** by onesong partners, inc.
(published by Time Warner Interactive), done with [REA](https://github.com/morluto/rea) and small
Python parsers. The deliverable is `DESIGN.md`: a design document that describes the shipped package,
the executables' architecture, the recovered game rules, and the data formats (`.ELV` level files,
`.BVW` camera presets, IFF `PBM` art, palette brushes, WAV loops, INI keys) in enough detail for
someone to build tools or a re-implementation.

## Source material

The analysed package is `win3_Endorfun.zip` from the Internet Archive:
<https://archive.org/details/win3_Endorfun>
(SHA-256 `6a2ebf7f16a092af1b86b1e9edf0f6a9e1e9cb1ca0563fcbd237ab37fa0ff2fc`, 94,116,626 bytes, 768 files).

## What is deliberately not in this repository

The game's executables, help files, art (`.LBM`/`.BBM`), audio (`.WAV`), level files (`.ELV`),
affirmation text and any renders, extracted text or disassembly derived from them are copyright
1995 onesong partners, inc. They are **not** redistributed here. The design document quotes only
short identifiers, numbers and structural facts needed to describe the formats. To run the scripts,
download the zip from the link above and point them at the extracted folder.

## Contents

| Path | What it is |
| --- | --- |
| `DESIGN.md` | The design document (Markdown export of the working document) |
| `scripts/elv3.py` | Parses every `ELVRL/*.ELV` level file, prints field statistics, writes `elv_dump.json` |
| `scripts/peres.py` | Dumps PE resources (dialogs, string tables, accelerators, version info) from `ENDORF95.EXE` |
| `scripts/lbm2png.py` | Converts IFF `PBM` (Deluxe Paint II chunky) images to PNG; also a `load()` helper |
| `scripts/funcs.py` | Maps import-table usage onto functions in an `llvm-objdump` listing of the PE |
| `data/experiences-catalogue.csv` | The 42 experiences: file, title, type and difficulty bytes, level counts, timer and Life Force ranges, asset names |
| `data/rea-evidence-endorfun-zip.json` | REA evidence bundle: archive member graph with hashes and the PE resource inventory (metadata only) |

## Usage

```sh
unzip win3_Endorfun.zip -d endorfun-src
python3 -I scripts/elv3.py endorfun-src/ELVRL
python3 -I scripts/peres.py endorfun-src/ENDORF95.EXE
python3 -I scripts/lbm2png.py out/ endorfun-src/ART/TITLE.LBM
```

The scripts need only the Python standard library. Treat the extracted files as untrusted input.

## Status of the findings

Observations are labelled in `DESIGN.md` as observed, inferred or unknown. No code was decompiled
(no Ghidra/IDA/Hopper was available); native facts come from `llvm-objdump` disassembly and resource
parsing. Open questions are listed at the end of the reconstruction guide.

## Note on the Markdown export

`DESIGN.md` is a Markdown export of the working document. The two architecture/flow diagrams and the three
reference images (title screen, texture atlas, a board background) exist only in the working document; the
images are game art and are not redistributed here.
