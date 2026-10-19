<!-- Exported from the working Claude Doc on 2026-10-19. Source package: https://archive.org/details/win3_Endorfun. Game content is copyright 1995 onesong partners, inc.; this document describes it and does not reproduce it. -->

# Endorfun Design Document

19 October 2026 · Rai Ostrowski

## Summary

Endorfun is a 1995 Windows puzzle game by onesong partners, inc. that ships as a 94 MB folder of two game executables (16-bit `ENDORFUN.EXE` for Windows 3.x and 32-bit `ENDORF95.EXE` for Windows 95), a CD launcher, two WinHelp manuals, 42 level files called "experiences", 273 rhythm loops, 23 sound effects, 349 Deluxe Paint images, and a 588-line list of affirmations. This document reverse-engineers that package with REA (static analysis of the shipped artefact only, nothing was executed) so that another agent can rebuild the game or write tools for its data.

Source artefact: `win3_Endorfun.zip`, 94,116,626 bytes, SHA-256 `6a2ebf7f16a092af1b86b1e9edf0f6a9e1e9cb1ca0563fcbd237ab37fa0ff2fc`, 768 member files. Newest file dates are 17 September 1995 (both executables) and 21 September 1995 (README). The zip was extracted to a scratch directory for analysis; nothing in it was run.

How to read the labels used below:

- **Observed**: taken directly from file bytes, headers, resource tables or decoded chunks. Each carries an Evidence ID or a file offset.
- **Inferred**: a conclusion that follows from several observations but was not read as a single fact (for example, a field's meaning deduced from the values it takes across 42 files).
- **Unknown**: not recoverable from this package by static analysis. Listed explicitly so the rebuilding agent does not invent it.

REA session facts: target opened as `zip` archive, SHA-256 as above. Native decompilation of the executables depends on which engine the host has; the executable section states what was and was not decompiled.

## Package inventory

The zip is a flat copy of the installed game folder: 11 files at the root plus four asset folders. REA's archive graph recorded 756 nodes and 773 edges (Evidence `ev_c04aa83f…`, root manifest `agm_e4953f54…`); the counts below come from the extracted tree.

| Path | Files | Format (observed) | Role |
| --- | --- | --- | --- |
| `ENDORFUN.EXE` | 1 | NE 16-bit Windows executable, 238,080 B, Borland C++ 4.x runtime | Game, Windows 3.1 build |
| `ENDORF95.EXE` | 1 | PE32 i386 GUI, 218,112 B, linker 2.50 (Microsoft Visual C++ 2.x), subsystem 4.0 | Game, Windows 95 build. Same resources and strings as the 16-bit build |
| `CD_EFUN.EXE` | 1 | NE 16-bit, 45,568 B, Borland C++ | CD launcher: reads `Endorfun.ini` keys `CD ROM Volume` and `Executable`, runs `endorfun\Endorfun.exe` from the CD |
| `ENDORFUN.HLP`, `ENDORF95.HLP` | 2 | WinHelp 4.0, text stored uncompressed | Manuals for the two builds. Text differs only in the uninstall topic |
| `ENDORF95.CNT`, `ENDORF95.FTS` | 2 | WinHelp contents file, full-text index | Help navigation |
| `ENDORFUN.INI` | 1 | 36 B text | Only `[Window] Maximized=1` survived in this copy |
| `ENDORFUN.BVW` | 1 | 412 B binary, magic `ECFG` + `EBVW` | 20 camera presets for the 3D board view |
| `ENDOISMS.TXT` | 1 | 588 lines, 247 distinct | Affirmations shown after play |
| `README.TXT` | 1 | 557 B text, dated 21 Sep 1995 | Video-driver note only |
| `ELVRL/*.ELV` | 42 | Custom binary, magic `ELVD` | "Experiences": each is a set of levels with its own art, music and messages |
| `RLOOPS/*.WAV` | 273 | RIFF PCM, stereo; 272 real loops + `NOSOUND.WAV` (7-byte placeholder containing the text `nosound`) | Rhythm loops, one per level |
| `SFX/*.WAV` | 23 | RIFF PCM 8-bit mono (one stereo), 22 kHz | Capture and event sounds |
| `ART/*.LBM` | 69 | IFF `PBM` (Deluxe Paint II chunky 8-bit), 640x480 except 5 files at 320x480/320x240 | Boards, title, win/lose screens, textures |
| `ART/*.BBM` | 280 | IFF `PBM`, 12x13 (or 12x12), uncompressed | Palette brushes: block and cube colour ramps |
| `ART/WIN/*.LBM` | 70 | IFF `PBM` 640x480; `WIN11.LBM` is a PCX file misnamed | Win screens picked per experience |

Audio formats in `RLOOPS`: 128 files are 8-bit stereo 22,255 Hz, 83 are 8-bit stereo 22,050 Hz, 55 are 8-bit 22,254 Hz, 4 are 16-bit 22,255 Hz, 1 is 8-bit 44,100 Hz, 1 is 16-bit 22,050 Hz. Loop lengths run from 1.3 s to 17.0 s, mean 6.9 s, 31.2 minutes in total. The odd sample rates are what the files declare; a player must honour the per-file rate.

SHA-256 of the executables and data files: `ENDORFUN.EXE` `d99266d0…e3d18e`, `ENDORF95.EXE` `0df2b7b6…747fe1`, `CD_EFUN.EXE` `6f6bb877…30e566`, `ENDORFUN.BVW` `2c09b60d…0c22`, `ENDOISMS.TXT` `39a69a60…763db`. Full digests are in the evidence bundle named in the last section.

## Executable architecture

Both game executables are one C code base built twice: a 16-bit build with Borland C++ 4.x for Windows 3.1 and a 32-bit build with Microsoft Visual C++ 2.x for Windows 95. Their menus, 13 dialogs, string tables, accelerators, icon and version block are byte-for-byte the same design, generated by WindowsMAKER Professional (the tool embeds its resource script, `ENDORFUN.RC`, author "geh", as a custom resource of type 32 in the PE). Neither binary was decompiled: the host has no Ghidra, Hopper or IDA, so REA's native providers were unavailable (`binary_session` lists only macOS, artifact-graph and .NET providers). Code facts below come from `llvm-objdump` disassembly of the PE plus resource parsing, and are cited by virtual address.

**Build facts (observed).** PE: linker 2.50, subsystem 4.0, entry `0x41f401`, `.text` 154,598 B, 203 imports from `KERNEL32`, `USER32`, `GDI32`, `comdlg32`, `WINMM`; exports nine WindowsMAKER window procedures (`BLDMainWndProc`, `BLD_overcoatWndProc`, `BLD_ef_scoreWndProc`, `BLD_ef_scoreClient1ClProc`, `BLD_FunctionDlgProc` and four dialog procs). NE: 15 code segments plus one 42,898 B data segment, imports `COMMDLG`, `GDI`, `KERNEL`, `KEYBOARD`, `MMSYSTEM`, `USER`, `WIN87EM` (floating-point emulator, so the 3D maths is float). Version block: "Endorfun the Game" 1.0, onesong partners, inc., trademark line, `Endorfun.exe`.

**Source modules (observed in the 16-bit build's assertion strings).** `gdrv.c`, `memory.c` and `polygon.c`; the polygon module asserts `Texture->x`/`y` are powers of two, `BitsPerPixel == 8`, `Bits != NULL`, `Background != NULL`. The About box credits "Graphics Technology: Cinematronics" for this software rasteriser.

**Subsystems and where they live in the PE:**

- **Window layer.** Main frame window class `BLDENDORFUN` with menu `IDR_ENDFUN`; a child "overcoat" game window; an "ef\_score" status-bar window with three layouts (`SCBD_CLIENT`, `_LONG`, `_SHORT`); a `QP_CLIENT` dialog holding the two Quick Play buttons (Replay, Select New Game). Custom control class `WMP3DBUTTON`. Message loop uses `PeekMessage` (game loop, not blocking).
- **Level loader.** Walks `ELVRL\*.ELV`; records are 463 bytes (`mov eax, 0x1cf` at `0x41a650`, backwards walk `sub eax, 0x1cf` at `0x41a6ad`); field reads at record offsets `+0x78` (message), `+0xa0` (board mask, `0x415838`), `+0xdd`/`+0xdf` (Life Force table, `0x41ab37`, `0x41ad68`). The Select New Game list is filled from `\ELVRL` + `*.elv` through a hidden listbox (`0x410498`).
- **File-name mapper.** At `0x40f0ba` every `-` in a resolved asset name becomes `_` and every `!` becomes `X`, when a global flag at `0x42c6d8` is set. Level files use the authoring names (`m-gb-k1.lbm`, `!102rhyt.wav`); the CD carries ISO-9660 names (`M_GB_K1.LBM`, `X102RHYT.WAV`). A rebuild must apply the same mapping.
- **Image loader.** Reads IFF `PBM` files with `OpenFile`/`_lread` (`0x402bd0` region), builds a logical palette (`CreatePalette`, `RealizePalette`) and blits with `StretchDIBits`. Colour cycling from the files' `CRNG` chunks runs through `AnimatePalette` (`0x403465`), toggled by the "Color Animation" option.
- **3D cube renderer.** `polygon.c`: texture-mapped cube drawn into an 8-bit DIB; the "Textured Cube" option switches the texture off for speed. Camera presets come from `ENDORFUN.BVW`.
- **Audio.** WAV files are read with `mmioOpen`/`mmioRead` (`0x40ec6d`) into memory and started with `sndPlaySound` (`0x40ead6`, `0x40ec25`; `sndPlaySound(NULL, SND_ASYNC)` at `0x40eb04` stops playback). CD audio uses `mciSendCommand` with `MCI_SET` (time format), `MCI_STATUS`, `MCI_PLAY` (`MCI_FROM|MCI_TO`), `MCI_STOP`, `MCI_CLOSE` (`0x40e47b` to `0x40e928`), which is what the editor's "CD Track" field drives.
- **Timing.** `timeGetTime` at `0x40e448` (audio) and five sites in `0x41928e`..`0x41a404` (level timer, block spawning, cube animation period).
- **Settings and persistence.** `GetPrivateProfileString`/`Int` and `WritePrivateProfileString` on `Endorfun.ini` in the Windows directory (`GetWindowsDirectory` imported); writers at `0x40f93b`..`0x40fd4c`, readers around `0x410461`. `ENDOISMS.TXT` is read at `0x410fa7`; an INI section `[Win Messages]` is touched at `0x411049`.
- **Help.** `WinHelp` at `0x40c7e4` opens `ENDORF95.HLP` (`ENDORFUN.HLP` in the 16-bit build).
- **Level editor (compiled in, shipped).** Menus `IDR_LEVEL_EDITOR`, `IDR_BV_MENU`, `IDR_ELV_POPUPS` and dialogs `CLIENT` ("Edit Game Levels", 115 controls), `ED_GAME_TITLE` ("Experience Settings"), `BD_VIEW` ("Board View"), `ANISPEED` are present in both binaries, loaded by name at `0x41daad`/`0x41dacf`. The user action that opens the editor was not recovered (unknown).

&#91;embedded content: engine architecture: 5 data sources, 5 engine modules, 5 presentation surfaces\]

Each data folder feeds one engine module on the same row; the level loader and the cube renderer draw into the game window, and the loop and settings module owns the main window. The audio module has no window of its own.

**Launcher.** `CD_EFUN.EXE` (Borland) reads `[Options]` keys `CD ROM Volume` and `Executable` from `Endorfun.ini`, runs `endorfun\Endorfun.exe` on the CD, and shows "Unable to run Endorfun. Make sure the Endorfun CD is properly inserted" on failure.

## Game design as recovered

Endorfun is a single-player puzzle game: the player rolls a six-coloured cube (the Light Body) across an 11x11 grid (the Unified Field), landing on pulsing Life Force squares with the matching colour face-up, while coloured Blocks spawn on a schedule and a per-level timer counts down. Rules below come from the help text (observed), the level data (observed) and the level editor's control labels; anything that needed code was not decompiled and is marked.

**Pieces**

- **Light Body.** The cube. Its six faces carry six colours: red, yellow, green, cyan, blue, magenta (observed in the texture atlas). It rolls one square per move, driven by mouse motion or four remappable keys (default arrow keys). Rolling onto a coloured square whose colour does not match the cube's top face is refused: the move is blocked. Landing with the matching face "merges" with the square and removes it.
- **Unified Field.** An 11x11 board (inferred: cell indices run 0..120 and the per-level mask holds 121 cells). Each level carries a mask of removed or opaque squares, so the field changes shape per level, and a camera preset (one of 20) that sets the 3D view over a 640x480 animated background.
- **Life Force.** Pulsing squares. A level has 1 to 30 of them (5 or 10 in most levels) but only one is on the field at a time; capturing one spawns the next. Capturing the last one shows "Transcending..." and advances to the next level. Each entry has a capture value (10 units, shown as 1,000 points, in most levels), either a fixed cell or random placement, and per the editor a capture sound, a "Time Til Jump" and a "Jump Distance" (the Life Force relocates after a while: inferred from labels).
- **Simple Blocks.** Spawn every N..M seconds; after a delay the interval can shrink (the help's "rate of Block appearance has been increasing"). Worth their capture value x100 in Abundance games; otherwise they only block. A "% Carry Over" field carries part of the leftover blocks into the next level (the Karma experience is built on this).
- **Multiplier Blocks.** Spots show the multiplier: five spots = 5 x the simple-block value (help example: 500 when a simple block is 100). Per level: enabled flag, start delay, spawn interval range, lifetime range.
- **Timer Blocks** ("Clock Block" in the editor). Each division is worth 5 seconds, 10 to 50 seconds per block; no points; merging one also slows block spawning. Same schedule fields as multipliers.
- **Global Blocks.** Merging one removes every square of its colour, including multiplier and timer blocks; the player receives the points of all removed blocks but not the timer blocks' time.

**Experience types and difficulty.** Each `.ELV` is one experience of one type (inferred byte mapping, see Data formats): Quickening ("Beat the Clock": finish all levels fastest, tracked on the Best Times board, status bar shows level count and elapsed time), Longevity ("Staying Alive": survive as long as possible), Abundance ("Keeping Score": most points, tracked on High Scores). Difficulty is Easy, Harder or Hardest, colour-coded blue, red, black in the Select New Game list.

**Timer.** Every level has a play time of 1 to 1,800 s (120 s is the norm; the two Beginner experiences use 1,800 s). The status-bar timer blinks under 30 s. When it expires the field rapidly fills with blocks and the game is lost; in a bonus round the field disappears instead. Being trapped by blocks with no legal move also loses.

**Bonus and Challenge rounds.** A level can flag a bonus round with a threshold (the editor's "Time" field, 6 to 600) and the index of a bonus level stored in the file's `LVBN` set; the status bar shows an asterisk next to the timer or score while the round is reachable and highlights the score once earned. Bonus levels show "Bonus" or "Challenge" instead of the level number. The package holds 663 game levels and 131 bonus levels; Kaleidoscope alone has 108 game levels.

**Scoring.** The display format is `Score:%8ld00`, so the engine counts in units of 100 points. Typical values: Life Force 10 units, simple block 1 unit, multiplier = spots x simple value. The exact rules for combos, level completion bonuses, Quickening time bonuses and the bonus-round threshold comparison are unknown (not decompiled).

**End of a game.** Win: a win screen chosen from `ART\WIN` (the executable enumerates `\art\win\*.lbm`; inferred random or rotating pick) and the experience's win loop. Lose: the experience's lose screen. Either way a positive message appears: the level's own 40-byte message when present, otherwise one from `ENDOISMS.TXT` (inferred from the branch at `0x41aa91`). Then the Quick Play buttons (Replay, Select New Game) and the menu bar return.

&#91;embedded content: play flow: 7 steps, 1 decision, 2 loops\]

Clearing a level loops back into play until the experience's last level, which opens the win screen; running out of time or being trapped opens the lose screen. Both paths end on the positive message and the Quick Play buttons, which replay the same experience or return to the selection dialog. A bonus round sits on the "more levels" loop when the level earned one.

**Gambits (help text).** The U: when beside a matching square, roll around it in a U. The Fence: in line with the square, tip one square off the line, roll alongside, tip back onto it. The Double-U: diagonal neighbour, two U moves. The 3-Space: three squares apart in a straight line, roll straight (four rolls return the same face to the top). The diagonal: one square apart diagonally, two sideways then toward.

**Controls.** Pause: Esc, Space, Enter or left click. Resume: F3, Enter or click in the window. F2 new game, F5 replay, F1 help, Ctrl+F4 exit; r, n, p for replay, new, play saved while the menu bar shows. Saved games use the `*.ESG` extension (format unknown).

**Experience catalogue** (type and difficulty are the inferred byte mapping; timer and Life Force columns are ranges over the game levels; Loops = distinct rhythm loops used):

| File | Title | Type | Difficulty | Levels | Bonus | Timer s | LF per level | Loops |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `BEGINNER.ELV` | Beginner1 | Quickening | Easy | 3 | 1 | 1800 | 30 | 3 |
| `BEGINER2.ELV` | Beginner2 | Quickening | Easy | 3 | 1 | 1800 | 30 | 3 |
| `ONESONG.ELV` | Endorfun | Quickening | Easy | 24 | 1 | 120 | 5-7 | 24 |
| `FLUTETHG.ELV` | Flute Thing | Quickening | Easy | 7 | 1 | 180 | 8 | 6 |
| `LAGOS2.ELV` | Lagos | Quickening | Easy | 12 | 1 | 120 | 5 | 12 |
| `SLOE.ELV` | Sloe | Quickening | Easy | 10 | 1 | 120 | 5 | 10 |
| `TWIDEMO2.ELV` | TranceDance | Quickening | Easy | 8 | 6 | 180 | 6 | 8 |
| `HROCKIN4.ELV` | Harmonic Dissonance | Abundance | Easy | 8 | 2 | 90-120 | 5-16 | 8 |
| `IBO.ELV` | Ibo | Abundance | Easy | 12 | 1 | 120 | 5 | 12 |
| `HUPBT4.ELV` | Mutability | Abundance | Easy | 21 | 1 | 60 | 5 | 20 |
| `SPIRIT.ELV` | Spirit Masters | Abundance | Easy | 12 | 7 | 120 | 5 | 9 |
| `ALLWELL.ELV` | All Is Well | Longevity | Easy | 36 | 1 | 120 | 3-5 | 6 |
| `FLUTEFVR.ELV` | Wind | Longevity | Easy | 25 | 1 | 120 | 5 | 23 |
| `NEWCLRS1.ELV` | Heart Beat | Quickening | Harder | 10 | 1 | 120 | 6-10 | 9 |
| `HEARTSDE.ELV` | Heart's Desire | Quickening | Harder | 15 | 2 | 45-120 | 4-7 | 13 |
| `LFF.ELV` | Life Force Flowing So Fine | Quickening | Harder | 16 | 16 | 120 | 8 | 16 |
| `NEWLOOPS.ELV` | Parasamgate Bodhi Svaha | Quickening | Harder | 8 | 1 | 14-150 | 8 | 7 |
| `FIRST.ELV` | Phast | Quickening | Harder | 6 | 1 | 120 | 10 | 6 |
| `TILT.ELV` | Tilt | Quickening | Harder | 12 | 1 | 120 | 10 | 12 |
| `XTC.ELV` | XTC | Quickening | Harder | 15 | 16 | 120 | 5 | 8 |
| `HENDLESS.ELV` | Endless One | Abundance | Harder | 7 | 1 | 120 | 7 | 7 |
| `HUPBT2.ELV` | Exclamation | Abundance | Harder | 24 | 2 | 15-75 | 5 | 7 |
| `HUPBT3.ELV` | Flower Crystal | Abundance | Harder | 18 | 1 | 15-60 | 3 | 12 |
| `HKARMA1.ELV` | Karma | Abundance | Harder | 20 | 1 | 30-90 | 5 | 5 |
| `HMED2.ELV` | Simplicity | Abundance | Harder | 10 | 1 | 30-90 | 5 | 5 |
| `RAOUL.ELV` | Endangered Species | Longevity | Harder | 1 | 31 | 10 | 1 | 1 |
| `SYNTH.ELV` | Synth Concerto for Cube | Longevity | Harder | 24 | 1 | 30 | 1 | 12 |
| `FOCUS.ELV` | Diamonds of Focus | Quickening | Hardest | 11 | 1 | 60-90 | 5-6 | 9 |
| `TWIDEMO.ELV` | Kaleidoscope | Quickening | Hardest | 108 | 6 | 1-96 | 5-20 | 8 |
| `DESIRE.ELV` | onesong | Quickening | Hardest | 15 | 2 | 60-120 | 5-15 | 14 |
| `HALSTEST.ELV` | Phaster | Quickening | Hardest | 5 | 1 | 120 | 10 | 5 |
| `BONUS.ELV` | Short and Suite | Quickening | Hardest | 5 | 3 | 120 | 5 | 4 |
| `TRUHART2.ELV` | True Heart | Quickening | Hardest | 9 | 1 | 120 | 5-7 | 9 |
| `XCELENT.ELV` | X-treme | Quickening | Hardest | 16 | 1 | 120 | 5-6 | 16 |
| `ZOOOOM.ELV` | Zoooooom | Quickening | Hardest | 11 | 1 | 71 | 11-16 | 11 |
| `HLIFEF.ELV` | Much Life Force | Abundance | Hardest | 16 | 1 | 120 | 10-25 | 14 |
| `HKARMA2.ELV` | Reincarnation | Abundance | Hardest | 20 | 1 | 30-90 | 5 | 10 |
| `HROCKIN3.ELV` | Rollercoaster | Abundance | Hardest | 10 | 8 | 120 | 5 | 10 |
| `HSEPARAT.ELV` | Separation | Abundance | Hardest | 10 | 1 | 60 | 5 | 5 |
| `HPURIST.ELV` | The Purist | Abundance | Hardest | 20 | 1 | 30-60 | 10 | 6 |
| `IAMFREE.ELV` | I Am Free | Longevity | Hardest | 14 | 1 | 120 | 8 | 1 |
| `MAGIC.ELV` | Magic of the Universe | Longevity | Hardest | 26 | 1 | 60 | 5 | 1 |

## Data formats

Six formats matter for a rebuild: the `.ELV` experience file (custom, fully decoded below), the `.BVW` camera presets (custom, decoded), IFF `PBM` images, RIFF WAV audio, `Endorfun.ini` and `ENDOISMS.TXT`. Every number here is little-endian. Labels: Observed = read from bytes or code; Inferred = deduced from values across files or from editor labels; Unknown = not recoverable statically.

**ELV container (Observed).** A sequence of chunks, each `4-char tag` + `u16 length` + data. The four chunks appear in a fixed order and were verified across all 42 files with no slack bytes (every assertion in `elv3.py` held).

| Chunk | u16 after tag | Data | Notes |
| --- | --- | --- | --- |
| `ELVD` | 8 | byte 6 = game-level count, byte 7 = bonus-level count | File offset 0. The 8 is constant (version or header size, Unknown) |
| `LVTL` | 257 | experience header (table below) | File offset 8, data at 14 |
| `LVDS` | n\_game × 463 | game-level records | File offset 0x10f, data at 0x115 |
| `LVBN` | n\_bonus × 463 | bonus-level records | Follows LVDS; ends at end of file |

**LVTL layout (Observed; type and difficulty bytes Inferred).** Offsets are relative to the chunk data (file offset 14); the file offset is in the second column.

| Data offset | File offset | Size | Field | Values seen |
| --- | --- | --- | --- | --- |
| +0x00 | 0x0e | 30 | Experience title, NUL-terminated | "Phast", "Kaleidoscope" |
| +0x1e | 0x2c | 13 | Win screen name | `r_classi.lbm`, `ef_win.lbm` (names not on disk; see Audio and video) |
| +0x2b | 0x39 | 13 | Lose screen name | `winnot-f.lbm`, `image-05.lbm` |
| +0x38 | 0x46 | 13 | Win loop WAV | `nosound.wav`, `722rhyth.wav` |
| +0x45 | 0x53 | 13 | Lose loop WAV | `nosound.wav`, `90rhyth.wav` |
| +0x52 | 0x60 | 13 | Texture file | `textur21.lbm`, `texture.lbm` |
| +0x5f | 0x6d | 1 | Play type: 0 Quickening, 1 Abundance, 2 Longevity (Inferred from descriptions) | 22 / 14 / 6 files |
| +0x60 | 0x6e | 1 | Difficulty: 0 Easy, 1 Harder, 2 Hardest (Inferred) | 13 / 14 / 15 files |
| +0x61 | 0x6f | 160 | Description, NUL-terminated | shown in Select New Game |

**Level record, 463 bytes (Observed layout; field meanings Inferred from the shipped level editor's "Edit Game Levels" dialog and value ranges).** Offsets are relative to the record start. Values are u16 unless stated. The record loader reads records at a 0x1cf stride (`0x41a650`, `0x41a6ad`).

| Offset | Field | Values seen / meaning |
| --- | --- | --- |
| +0x00 | u8 flag A | 0 or 1; one of the "Sub Level" / "Solid Board Squares" checkboxes (which is which: Unknown) |
| +0x01 | u8 flag B | 0 or 1; the other checkbox |
| +0x02 | Play time, seconds | 1..1800; 120 typical; 1800 in the Beginner sets |
| +0x04 | Cube roll period, ms | 0 = default; 165..400 seen; editor range 50 to 1000 |
| +0x06 | Light Body start cell | 0..120, or 0xFFFF = random/default |
| +0x08 / +0x0a | Simple Block spawn interval min / max, s | 1..9990 (9990 = effectively never) |
| +0x0c | Simple Block capture value | 1 typical, 0..30; shown ×100 ("Score:%8ld00") |
| +0x0e | % carry over | 0..100; blocks carried into the next level |
| +0x10 | "After" seconds before rate decrease | 0..50 |
| +0x12 / +0x14 | Decreased interval min / max, s | 0..900 / 0..100 (assignment among +0x10..+0x14 inferred from the editor group: Every N to M; After X during decrease to Every N' to M'; Capture Value; % Carry Over) |
| +0x16 | Multiplier Block enabled | 0/1 |
| +0x18 | Multiplier "after", s | 0..90 |
| +0x1a / +0x1c | Multiplier every min / max, s | default 250 / 250 |
| +0x1e / +0x20 | Multiplier duration min / max, s | default 50 / 50 |
| +0x22 .. +0x2c | Global Block group, same six fields | defaults 350 / 350 every, 25 / 25 duration |
| +0x2e .. +0x38 | Clock (Timer) Block group, same six fields | defaults 350 / 350, 25 / 25 |
| +0x3a | Bonus round enabled | 0/1 |
| +0x3c | Bonus threshold ("Time") | 6..600 |
| +0x3e | Bonus level index ("goto level") | 0..15, index into LVBN |
| +0x40 | Board view index | 0..19, selects an `ENDORFUN.BVW` preset |
| +0x42 | Background image name, 11 B + NUL | `m-gb-k1.lbm`, `image-07.lbm` |
| +0x4d | Palette brush name, 15 B | `brush-45.bbm`, `k1.bbm`, `ax10.bbm` |
| +0x5c | Texture name, 13 B | always `texture.lbm` |
| +0x69 | Rhythm loop WAV, 15 B | `620rhyth.wav`, `!102rhyt.wav` |
| +0x78 | Losing / positive message, 40 B, NUL-terminated | In 374 of 794 records byte +0x78 is 0 and the text at +0x79 lacks its first letter. The game tests byte +0x78 at `0x41aa91` and falls back to `ENDOISMS.TXT` when it is 0, so treat those as "no message" |
| +0xa0 | Board mask, 61 bytes = 121 nibbles | One nibble per cell of an 11×11 grid, row-major, value 0 or 1. 1 marks a removed/opaque square (Inferred: Light Body start cells land on 0 in 248 of 267 cases, fixed Life Force positions in 703 of 730). 62 records have an all-zero mask = full board |
| +0xdd | Life Force count | 1..30; 5 and 10 most common |
| +0xdf | 30 × 8-byte Life Force entries | see below; entries past the count are stale editor data in 166 records |

Life Force entry (8 bytes): u16 capture value (10 typical; 40 and 1000 seen), u16 cell (0..120 or 0xFFFF = random), u16 packed pair (low byte 0..5, high byte 0..8; candidates are colour index, capture-SFX index and jump distance, unresolved), u16 seconds-like value (0, 50, 30, 530, 20, 40; candidate "Time Til Jump"). The cell index convention `row * 11 + col` is an inference. The editor's Life Force group holds: Total for level, Capture Value, Capture SFX, Start X, Start Y, Time Til Jump, Jump Distance.

**ENDORFUN.BVW (Observed).** `ECFG` u16 1, `EBVW` u16 400, then 20 records × 5 float32: rotation X, Y, Z (radian-like, -0.9..7.0), field of view (10..70), distance (129..1034). The level record's board view index picks one.

| # | rotX | rotY | rotZ | FOV | Dist |
| --- | --- | --- | --- | --- | --- |
| 0 | -0.8 | -0.1 | 0.1 | 50 | 161 |
| 1 | -0.8 | -0.4 | 0.0 | 50 | 163 |
| 2 | -0.8 | 0.0 | 0.2 | 50 | 171 |
| 3 | -0.9 | -0.1 | 0.0 | 67 | 129 |
| 4 | -0.8 | 0.1 | 0.0 | 50 | 159 |
| 5 | -0.8 | 0.0 | -0.1 | 50 | 161 |
| 6 | -0.8 | -0.5 | 0.1 | 50 | 167 |
| 7 | -0.1 | 0.9 | 0.2 | 50 | 216 |
| 8 | -0.8 | 7.0 | 0.0 | 50 | 170 |
| 9 | -0.8 | 0.9 | 0.4 | 30 | 281 |
| 10 | 0.8 | 0.0 | 0.0 | 50 | 168 |
| 11 | 0.2 | 0.1 | -0.1 | 50 | 203 |
| 12 | 0.1 | 0.1 | 0.1 | 10 | 1034.1 |
| 13 | -0.5 | -0.1 | 0.1 | 50 | 184 |
| 14 | 0.5 | 0.1 | 0.1 | 50 | 190 |
| 15 | -0.7 | -0.3 | 0.3 | 70 | 133 |
| 16 | -0.8 | -0.8 | 0.1 | 50 | 183 |
| 17 | 0.8 | -0.8 | 0.1 | 50 | 183 |
| 18 | -0.8 | -0.5 | 0.3 | 50 | 192 |
| 19 | -0.8 | 0.0 | 0.0 | 50 | 161 |

**IFF images (Observed).** `FORM` / ` PBM  ` files from Deluxe Paint II (chunky 8-bit). Chunks: `BMHD`, `CMAP` (256 × RGB), `GRAB` or `DPPS`, 16 `CRNG` colour-cycling ranges (the active ones cover palette ranges 210-215, 216-221, 222-227, 228-233, 234-239 and 240-245 at rate 0; the title and win screens add more), `TINY` thumbnail, `BODY`. Full-screen `.LBM` bodies use ByteRun1 (compression = 1); the 12×13 `.BBM` brushes are uncompressed (compression = 0). All brushes carry the same pixel index pattern (indices 108..201) and differ only in `CMAP`, so a brush is a palette carrier for the block and cube colour ramps. `ART/WIN/WIN11.LBM` is a PCX file (header `0A 05 01 08`, 640×480) with the wrong extension.

**WAV (Observed).** RIFF PCM. Rhythm loops are stereo 8-bit at 22,255, 22,254 or 22,050 Hz (4 files are 16-bit, 1 is 44,100 Hz). Sound effects are mono 8-bit at about 22 kHz. `NOSOUND.WAV` is the 7-byte text `nosound`, used in level files as a null placeholder.

**Endorfun.ini (Observed keys; purposes Inferred from names).**

| Section | Keys |
| --- | --- |
| `[Endorfun Options]` | Show Game Status, Save Game Alert, Sound Status, Color Animation, Textured Cube, Record Winning Times, Mouse Sensitivity, Play Mode Showing, Quick Play Buttons, Cube Left, Cube Right, Cube Up, Cube Down, Last Game Played, Install Directory |
| `[Window]` | Maximized, Right, Bottom |
| `[Options]` | CD ROM Volume, Executable (read by the launcher) |
| `[Win Messages]` | purpose Inferred: tracks which affirmations have been shown |

Saved games use the `*.ESG` extension ("Saved Game Files (\*.ESG)" filter); their format is Unknown, no sample shipped. Where best times and high scores are stored is Unknown.

**ENDOISMS.TXT (Observed).** 588 lines, 247 distinct affirmations, plain text, one per line.

The parsed dump of all 42 files is at `<hand-off folder>/data/elv_dump.json` and the parser at `<hand-off folder>/scripts/elv3.py`; both use the Life Force offsets given above (`+0xdd` count, `+0xdf` entries).

## Audio and video

Every sound is a plain PCM WAV played through the Windows multimedia API, and every picture is an 8-bit palettised IFF `PBM` image at 640x480; there is no video codec, no MIDI and no custom audio format. All asset names go through the same file-name mapping as level files: `-` becomes `_` and `!` becomes `X` (code at `0x40f0ba`), so `!102rhyt.wav` on a level record means `X102RHYT.WAV` on disk.

&#91;image: Title screen, TITLE.LBM 640x480\]

**Rhythm loops (observed).** `RLOOPS` holds 272 real loops plus the 7-byte `NOSOUND.WAV` placeholder. Formats: 128 files 8-bit stereo 22,255 Hz, 83 at 22,050 Hz, 55 at 22,254 Hz, 4 16-bit at 22,255 Hz, 1 8-bit at 44,100 Hz, 1 16-bit at 22,050 Hz. Lengths run 1.3 s to 17.0 s (mean 6.9 s), 31.2 minutes in all. Each level record names one loop at offset `+0x69`; 88 distinct loops are referenced by shipped levels, the other 184 are on disk but unreferenced. The experience header also names a win loop and a lose loop (`nosound.wav` in all but three experiences). Loops are read with `mmioOpen`/`mmioRead` (`0x40ec6d`) into memory and started with `sndPlaySound` (`0x40ead6`, `0x40ec25`); `sndPlaySound(NULL, SND_ASYNC)` at `0x40eb04` stops them. That they play with `SND_LOOP` while a level runs is inferred from the loop lengths and the single-start pattern, not read from the flag bits.

**CD audio (observed calls, unknown use).** The executable opens the `cdaudio` MCI device (`MCI_OPEN` at `0x40e398`) and issues `MCI_SET` (time format), `MCI_STATUS`, `MCI_PLAY` with `MCI_FROM|MCI_TO`, `MCI_STOP` and `MCI_CLOSE` (`0x40e47b` to `0x40e928`). The level editor's "CD Track" field is the only input that could drive it. No shipped level is known to select a CD track; which record field would carry the track number is unknown.

**Sound effects (observed).** `SFX` holds 23 files, 8-bit mono at about 22 kHz (one stereo), 0.0 s to 6.5 s. The executable's capture-SFX list has 17 names in this order: 1A, 1B, 1C, 2A, 2B, 3A, 3B, 4A, 5A, 6A, 7A, 7B, 7C, 7D, 7E, 7F, 8A (each `<name>SFX.WAV`). The six remaining files on disk (3C, 3D, 3E, 4B, 5B, 6B) are not in that list. The Options menu offers three sound modes: Music, Sound Effects, No Sound; the help text says playing without Music also removes the subliminal messages.

**Subliminal messages.** The help file states that the music carries subliminal messages and that a positive message appears on screen after every game. What ships is: `ENDOISMS.TXT`, 588 lines (247 distinct) read at `0x410fa7`; a 40-byte per-level message at record offset `+0x78` (used only when its first byte is non-zero; otherwise the code at `0x41aa91` falls through to the `ENDOISMS` provider); and an INI section `[Win Messages]` written at `0x411049`, which is where the game appears to track which message to show next (inferred). Whether the WAV loops contain embedded speech cannot be established statically (unknown).

**Images (observed).** All 419 art files are IFF `FORM PBM` (Deluxe Paint II chunky 8-bit) with `BMHD`, `CMAP`, `CRNG` (16 ranges), `TINY` and `BODY` chunks; full-screen images use ByteRun1 compression, brushes are stored raw. Classes:

| Files | Size | Role |
| --- | --- | --- |
| `M_GB_A1`..`M_GB_L1` | 640x480 | The 12 main board backgrounds named by level records (`m-gb-k1.lbm` and so on) |
| `IMAGE_01`..`IMAGE_11`, `M_BONUS`, `S2A01`, `S2B01` | 640x480 | Further backgrounds; `IMAGE_*` also serve as lose screens for five experiences |
| `A1_QRT`, `ABLAND_1`, `CBLAND_1`, `DBLAND_1`, `EBLAND_1` | 320x240 | Quarter-size boards used by five experiences |
| `ART\WIN\WIN1`..`WIN70` | 640x480 | 69 win screens (`WIN11.LBM` is a PCX file); the game enumerates `\art\win\*.lbm` at `0x4105eb` and picks one, because the names in level files (`r_wired.lbm`, `ef_win.lbm`) do not exist on disk. Random or sequential choice: inferred, not read |
| `WINNOT_2`..`WINNOT_M`, `EF_NOWIN`, `EF_NOWN1` | 640x480 | Lose screens named per experience |
| `TITLE` | 640x480 | Title screen (above) |
| `TEXTURE`, `TEXTUR04`..`TEXTUR22` | 640x480 | Texture atlases of 64x64 tiles (below) |
| 280 `*.BBM` brushes | 12x13 or 12x12 | Palette carriers: the pixel grid is the same in every brush, only the `CMAP` differs |

&#91;image: Texture atlas, TEXTURE.LBM: pip tiles for Multiplier blocks, six Life Force stars, Timer-block division glyphs, six colour triangles\]

The atlas rows are: rows 0 and 1, pip patterns for Multiplier blocks; row 2, the six Life Force stars in red, yellow, green, cyan, blue and magenta; rows 3 and 4, Timer-block division glyphs in dark and light variants; rows 5 and 6, triangles in the six colours. The six colours are the cube's six faces and the colour set for blocks and Life Force.

&#91;image: Board background, M\_GB\_K1.LBM, named as m-gb-k1.lbm by the Phast experience\]

**Palette and colour cycling (observed in the files, use inferred).** A level's "Palette:" brush (`+0x4d`) supplies new colours for palette indices 108 to 201, the ramp that shades blocks and the cube, so one background serves many colour schemes. Backgrounds carry six active `CRNG` ranges covering indices 210 to 245 (six ranges of six entries); the game animates them with `AnimatePalette` (`0x403465`) when Color Animation is on. The hint string reminds players that 640x480 in 256 colours is the intended mode.

## UI and configuration

The whole user interface is three menus, eleven player-facing dialogs, a status bar with three layouts and a pair of Quick Play buttons; all of it is read from the resource script embedded in the executable and the dialog templates in its resource table, so the control layout below is observed, not reconstructed.

**Menus (resource `IDR_ENDFUN`).**

| Menu | Items | Command / key |
| --- | --- | --- |
| Game | Select New Game..., Replay Game, Resume Game, Save Game, Save Game As..., Play Saved Game..., Exit | F2, F5 (greyed until a game ran), F3, (none), (none), (none), Ctrl+F4 |
| Options | Sound: Music / Sound Effects / No Sound; Display: Color Animation / Textured Cube; Show Game Status; Save Game Alert; Quick Play Buttons; Show Best Times...; Show High Scores...; Set Mouse Sensitivity...; Set Keyboard Control... | Checked items persist in the INI |
| Help | Help Topics, About Endorfun | F1 |

**Dialogs.**

| Resource | Title | Controls that matter |
| --- | --- | --- |
| `SEL_GAME_EXP` | Select New Game | Listbox of experiences; radio filter Quickening / Longevity / Abundance / Show All ("The Play..."); description box; colour key Easy (blue), Harder (red), Hardest (black); Play / Cancel |
| `HIGH_SCORES` | Endorfun Winning Times (also used as High Scores) | Experience combo; 10 rows x 3 columns; Record Winning Times checkbox; Clear Times; OK |
| `KEYMAP` | Set Keyboard Control | Four combos Cube Up / Left / Right / Down; Default (arrow keys); rejects a key already in use |
| `MOUSE_SENSITIVITY` | Set Mouse Sensitivity | One scrollbar, Low to High |
| `ANISPEED` | Set Animation Speed | Milliseconds for the cube to roll one square (editor-facing; the level field accepts 50 to 1000) |
| `EF_ABOUT` | Endorfun About | Credits, version 1.0, publisher |
| `QP_CLIENT` | (none) | Two large buttons: Replay, Select New Game |
| `SCBD_CLIENT`, `SCBD_CLIENT_LONG`, `SCBD_CLIENT_SHORT` | (status bar) | Five, five and four static fields; the game picks the layout that fits the window width |
| `CLIENT` | Edit Game Levels | Level editor: groups Game Board, Level, Life Force, Light Body, Simple Block, Multiplying Block, Global Block, Clock Block, Bonus Round, R-Loop .WAV, CD Track, Losing Message |
| `ED_GAME_TITLE` | Experience Settings | Title, description; The Challenge: Easy / Harder / Hardest; The Play: Beat the Clock / Staying Alive / Keeping Score; Win Screen, Lose Screen, Win Rloop, Lose Rloop, Textures |
| `BD_VIEW` | Board View | Rotation X / Y / Z, Field of View, Distance, View Count, Fit Board to Window, Redraw Board |

**Credits (observed in `EF_ABOUT`).** Designed and produced by Michael Jai Feinberg; software design and programming Greg Hospelhorn; graphic artist Robert Charles Dotinga; music and rhythms Onye Onyemaechi and the "O Band" (Paul Sihon, Sid the Kid, Kendrick Freeman, Alice Johnson, Mark Moran); graphics technology Cinematronics (Mike Sandige, David Stafford, Kevin Gliner); sound engineering Paul White / Transformations; narration Blair Hardman and Linda Weber; associate producer and designer Hal Jordy III; executive producers Noah Clemence Zim and Michael Jai Feinberg; published by Time Warner Interactive, Burbank, CA; copyright 1995 onesong partners, inc. of Calistoga and San Francisco.

**Status bar strings (string table ids 48 to 91).** `Life Force: %2d`, `Level: %3d`, `of %3d`, `Timer %02d:%02d`, `Elapsed Time %02d:%02d`, `Score:%8ld00` (two literal zeros appended, so the score is stored in hundreds), `Challenge!`, `Bonus Level`, `Transcending...`, `Ascending...`, plus the hint "To enjoy Endorfun to the fullest, screen resolution should be 640x480 256 colors." and the prompt "Click left mouse button or hit spacebar to continue...". Saved games use the filter `Saved Game Files (*.ESG)`; level sets use `Level Set Files (*.ELV)`.

**Keyboard and mouse (help text and accelerator tables).**

- Move the cube with the mouse or the four mapped keys (defaults: arrow keys; Home, End, Page Up, Page Down are also offered).
- Pause: Esc, Space, Enter, or a left click. Resume: F3, Enter, or a left click in the game window.
- With the menu bar showing: `r` replay, `n` new game, `p` play saved game (accelerator table 2: q, t, r, Ctrl+s, Alt+p are also bound to commands 4000 to 4019).
- Level editor accelerators: Alt+C copy level, Alt+V paste level.

**Persistence (observed key names; `Endorfun.ini` in the Windows directory).** Section `[Endorfun Options]`: `Show Game Status`, `Save Game Alert`, `Sound Status`, `Color Animation`, `Textured Cube`, `Record Winning Times`, `Mouse Sensitivity`, `Play Mode Showing`, `Quick Play Buttons`, `Cube Left`, `Cube Right`, `Cube Up`, `Cube Down`, `Last Game Played`, `Install Directory`. Section `[Window]`: `Maximized`, `Right`, `Bottom`. Section `[Win Messages]`: written by the message code, keys not recovered. Section `[Options]` (launcher): `CD ROM Volume`, `Executable`. Where best times and high scores are stored is unknown; the only candidates are further INI sections or a file next to the saved games.

## Reconstruction guide for another agent

A faithful rebuild needs seven modules; the first four are fully specified by this document, the last three carry open questions that must be answered by play-testing the original or by decompiling it. Build in the order below so each step can be checked against shipped data.

1. **Asset pipeline.** Convert IFF `PBM` to RGBA while keeping the 8-bit index data: the game recolours ranges at runtime (brush palettes for indices 108..201, colour cycling for 210..245), so store indices plus the file's CMAP, not baked RGB. Split `TEXTURE.LBM` and `TEXTUR04..22.LBM` into 64x64 tiles (row 0..1 multiplier pips, row 2 Life Force stars in the six colours, rows 3..4 timer-block division glyphs, rows 5..6 colour triangles). Load WAV at each file's declared rate. Apply the name map (`-` to `_`, `!` to `X`, case-insensitive) when resolving names from level files. Reference converter: `<hand-off folder>/scripts/lbm2png.py`.
2. **Level parser.** Implement the `ELVD`/`LVTL`/`LVDS`/`LVBN` reader from the Data formats section (6-byte chunk header, 463-byte records). Validate against the whole set: 42 files, 663 game levels, 131 bonus levels, no slack bytes. Treat a record whose message byte at `+0x78` is 0 as "no message". Unit fixtures: `BEGINNER.ELV` (3 levels, 1800 s timer, 30 Life Force, full board), `FOCUS.ELV` level 1 (3x3 central mask), `TWIDEMO.ELV` (108 levels), `RAOUL.ELV` (1 game level, 31 bonus levels).
3. **Board and camera.** 11x11 grid, cell index = row x 11 + column (inferred), per-level mask of 1-cells removed. Camera from `ENDORFUN.BVW` preset `+0x40`: three rotation values, field of view, distance. Render order: background image (with cycling), board squares (opaque or transparent per the flag bytes), blocks and Life Force as textured tiles, cube on top. A 640x480 8-bit palette look is the fidelity target; the cube roll takes the level's period in milliseconds (`+0x04`, default when 0).
4. **Cube model.** Track the cube's orientation as one of 24 rotations; a roll in one of four directions permutes the faces. A move onto a coloured square is legal only when the top face colour equals the square colour; a legal move onto Life Force or a Block removes the square (merge). Four rolls in a line restore the top face (the 3-Space gambit is a cheap test).
5. **Spawn scheduler and timer.** Per level: countdown from play time (`+0x02`); Simple Blocks every random(min..max) s with a later faster interval; Multiplier, Global and Timer blocks each with enabled flag, start delay, interval range and lifetime range; Timer blocks grant 5 s per division (2..10 divisions) and slow spawning. Open questions: the exact random distribution, how a block's colour and position are chosen, what "% carry over" carries, and how the two record flag bytes (`+0x00`, `+0x01`) map to "Sub Level" and "Solid Board Squares".
6. **Scoring and experience types.** Count in units of 100. Life Force and block capture values come from the record; multiplier = pips x simple value; Global pays for everything it removes except timer time. Quickening ranks by elapsed time, Longevity by survival, Abundance by score; the bonus-round threshold (`+0x3c`) is compared against time or score depending on type (inferred). Open: combo or level-clear bonuses, how Best Times and High Scores are stored, the saved-game `.ESG` format.
7. **Shell.** Menus, dialogs, status-bar layouts and INI keys are listed in UI and configuration; reproduce the three status bars and the Quick Play buttons. The level editor is optional but its dialog is the best specification of the record fields.

**Unknowns to resolve before claiming fidelity** (none of these are recoverable from the package by static analysis):

- How the editor is opened in the shipped build.
- Meaning of the Life Force entry's packed pair (`lo` 0..5, `hi` 0..8) and the seconds-like fourth field.
- Whether mask value 1 means "square absent", "opaque square" or "pre-placed block" (the start-cell test favours absent, 19 counter-examples exist).
- Win-screen selection rule (random or rotating through `ART\WIN`).
- Whether any shipped level actually drives CD audio.
- The claim that the music carries subliminal messages.

**Legal note for a rebuild.** The executables, art, audio loops, level data, help text and affirmations are copyright 1995 onesong partners, inc. (published by Time Warner Interactive). Use them locally for study; a public rebuild should ship new art, audio and level content and read the original files only when the user supplies them.

## Evidence ledger

Everything above rests on three REA evidence records, the extracted files themselves, and one disassembly listing. Nothing was executed.

| Evidence | What it covers | Confidence |
| --- | --- | --- |
| REA `open_binary` on `win3_Endorfun.zip` (SHA-256 `6a2ebf7f16a092af1b86b1e9edf0f6a9e1e9cb1ca0563fcbd237ab37fa0ff2fc`) | Archive bound as the active target | observed |
| `ev_c04aa83f16a08dc975e88cecf39e6e87691fd69c1361edacb7a76d93acc1cf07` (`inspect_artifact`) with root-manifest observation `ev_d6fe52627ce0d4a53ab9909d8744169ed1b4d45181313fac3f4bae56fb746f3e` | Member inventory: 756 nodes, 773 edges, graph SHA-256 `7c5e40d7...583d2c`; central-directory entries only | observed |
| `ev_03b465e95511be554c22f11a7378fe4be715c281d5fffd3a6359a09244acb096` (`inspect_pe_resources` on `ENDORF95.EXE`, SHA-256 `0df2b7b6ce9d545c62d077cac447d203620579a2b5d206649ae47e5cbd747fe1`) | 27 resources: icon, 4 menus, 13 dialogs, 4 string blocks, 2 accelerator tables, version info, type-32 RC text; coverage complete | observed |
| Exported bundle `<hand-off folder>/data/rea-evidence-endorfun-zip.json` (1,736,383 B, 3 records, 0 unknowns) | Portable copy of the three records above | observed |
| `llvm-objdump -d` of `ENDORF95.EXE` (72,989 lines, `<hand-off folder>/data/dis95.txt`) | Addresses cited in the architecture section | observed instruction bytes; function boundaries approximate |
| Python parsers in `<hand-off folder>/scripts/` (`peres.py`, `elv3.py`, `lbm2png.py`, `funcs.py`) | Resource dump, level statistics, image conversion, import usage | reproducible |

**Claim classes used in this document**

- Observed: file bytes, headers, chunk layouts, resource contents, help text, string tables, disassembly at a cited address.
- Inferred: 11x11 board; cell index convention; play-type and difficulty bytes; mask meaning; Life Force entry fields beyond value and position; win-screen selection; loop playback flags; CD audio driven by the editor's CD Track field; the `[Win Messages]` purpose; the fallback from an empty level message to `ENDOISMS.TXT`.
- Unknown: everything listed at the end of the reconstruction guide, plus the `.ESG` save format and the high-score store.

**Coverage limits.** No native decompiler was available, so no function was read for semantics beyond short probes (name mapping at `0x40f0ba`, message fallback at `0x41aa91`, record stride at `0x41a6ad`, MCI and sound call sites). The 16-bit build was inspected for strings, segments and imports only. The help files were read as raw strings (their text is stored uncompressed); illustrations in the help were not decoded. `ENDORF95.FTS` and the icon bitmaps were not examined. Audio content was not listened to or analysed for embedded speech.

**Hand-off folder.** `<hand-off folder>/` holds the scripts, the parsed level dump (`data/elv_dump.json`, 503 KB), the experience catalogue (`data/experiences.csv`), the embedded RC script, the help-file strings, the disassembly, the evidence bundle and 18 rendered PNGs under `renders/`. The extracted game files stay in the session scratch directory and in the original zip. A copy without any copyrighted game content (scripts, catalogue, evidence bundle, this document as Markdown) is pushed to the GitHub repository named in the chat hand-off.
