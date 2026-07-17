# Hanmaru Korean Patch

This branch supports extracting assets from the Hanmaru Korean patch v1.102
applied to the Japanese Ocarina of Time N64 1.1 ROM. The patch and ROM are not
included. Use a legally acquired dump and apply the patch yourself.

## Supported ROM

Verify the patched ROM before extraction:

| Property | Expected value |
| - | - |
| Size | `33554432` bytes |
| MD5 | `d4091f8260a0e1aa5eb8681f1021c314` |
| SHA-1 | `ccbb74e30bd87f3da9b0dac9f05609ad33175f26` |
| N64 CRC1 | `1F29ED87` |
| CRC32C | `C0AE6EBD` |

On macOS, the size and cryptographic hashes can be checked with:

```bash
stat -f '%z bytes' "/path/to/patched-rom.z64"
md5 "/path/to/patched-rom.z64"
shasum "/path/to/patched-rom.z64"
```

## Build On macOS

Install the dependencies and initialize the submodules:

```bash
brew install sdl2 sdl2_net libpng glew ninja cmake tinyxml2 nlohmann-json libzip opusfile libvorbis
git submodule update --init
```

Configure and build Ship of Harkinian:

```bash
cmake -S . -B build-cmake -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build-cmake --target GenerateSohOtr
cmake --build build-cmake
```

## Extract And Launch

Run the executable from its output directory so it can find `soh.o2r`:

```bash
cd build-cmake/soh
./soh-macos
```

When prompted, select the verified Korean-patched ROM. Extraction writes
`oot.o2r` beside the executable and then starts the game. If `oot.o2r` already
exists, move it aside before launching when you need to extract it again.

The extractor does not modify the selected ROM. It creates a private temporary
copy with the Japanese 1.1 CRC1 expected by ZAPD, adjusts the Korean patch's
overlay extraction ranges and audio table offsets in private XML copies, and
deletes the temporary working directory afterward.

The generated archive can be checked independently:

```bash
unzip -t oot.o2r
zipinfo -1 oot.o2r | rg '^text/|^textures/kanji/'
```

## Create A Differential Mod

SoH ZIP-based mods use the `.o2r` extension. The legacy `.otr` extension is an
MPQ archive and must not be used for a renamed ZIP file.

Create two full archives with the same SoH build:

1. Extract `oot-jp11.o2r` from an unmodified NTSC Japanese 1.1 ROM. Its SHA-1
   is `dbfc81f655187dc6fefd93fa6798face770d579d`.
2. Extract `oot-korean.o2r` from the supported Hanmaru-patched ROM described
   above.

The extractor always names its output `oot.o2r`, so move or rename each output
before extracting the next ROM. Then create the differential mod:

```bash
python3 tools/create_o2r_patch.py \
  --allow-removals \
  "/path/to/oot-jp11.o2r" \
  "/path/to/oot-korean.o2r" \
  "build-cmake/soh/mods/hanmaru-korean.o2r"
```

The tool compares decompressed resource contents and writes only added or
changed resources at their original paths. It omits the base archive control
entries `version`, `portVersion`, and `manifest.json`. It also rejects unsafe
paths, duplicate names, empty replacements, resource removals, and existing
output files by default.

The Hanmaru archive omits 44 automatically named overlay vertex resources
that exist in the base archive and adds their relocated or reclassified
resources under new names. An O2R override cannot hide the old names, so the
explicit `--allow-removals` option leaves those unused base entries available.
With the supported ROMs and this branch, the expected result is 110 added and
3569 changed resources, for 3679 entries in the generated mod.

Use the unmodified Japanese 1.1 archive as the game's base `oot.o2r` and keep
the generated patch in `mods`:

```text
build-cmake/soh/
|-- oot.o2r
|-- soh-macos
|-- soh.o2r
`-- mods/
    `-- hanmaru-korean.o2r
```

Restart SoH after adding the mod. New mod archives are enabled automatically;
the Mods menu can be used to confirm its priority over other resource mods.

Run the patch generator tests with:

```bash
python3 -m unittest discover -s tools/tests -p 'test_*.py'
```

Keep the patched ROM and generated `oot.o2r` out of source control and do not
redistribute either file.
