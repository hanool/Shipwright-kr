#!/usr/bin/env python3

import argparse
import sys
from collections import Counter
from pathlib import Path

if __package__:
    from tools.create_o2r_patch import PatchError, _read_entries
else:
    from create_o2r_patch import PatchError, _read_entries


EXPECTED_CHANGED_COUNTS = {
    "objects": 9,
    "scenes": 336,
    "text": 2,
    "textures": 3102,
}

EXPECTED_OBJECTS = frozenset(
    {
        "objects/object_bv/gBarinadeTitleCardTex",
        "objects/object_fhg/gPhantomGanonTitleCardTex",
        "objects/object_ganon2/gGanonTitleCardTex",
        "objects/object_goma/gGohmaTitleCardTex",
        "objects/object_kingdodongo/gKingDodongoTitleCardTex",
        "objects/object_mag/gTitleTitleJPNTex",
        "objects/object_mo/gMorphaTitleCardTex",
        "objects/object_sst/gBongoTitleCardTex",
        "objects/object_tw/gTwinrovaTitleCardTex",
    }
)

EXPECTED_TEXT = frozenset(
    {
        "text/jpn_message_data_static/jpn_message_data_static",
        "text/nes_message_data_static/ntsc_nes_message_data_static",
    }
)

EXPECTED_TEXTURE_GROUPS = frozenset(
    {
        "do_action_static",
        "icon_item_gameover_static",
        "icon_item_jpn_static",
        "icon_item_static",
        "item_name_static",
        "kanji",
        "map_name_static",
        "object_bv",
        "object_fd",
        "object_fhg",
        "object_ganon",
        "object_ganon2",
        "object_goma",
        "object_kingdodongo",
        "object_mo",
        "object_sst",
        "object_tw",
        "parameter_static",
        "title_static",
    }
)

EXPECTED_BDAN_SCENES = frozenset({"bdan_scene", "bdan_boss_scene"})


class ValidationError(Exception):
    pass


def is_expected_changed_path(name: str) -> bool:
    if name in EXPECTED_OBJECTS or name in EXPECTED_TEXT:
        return True

    parts = name.split("/")
    if len(parts) >= 3 and parts[0] == "textures":
        return parts[1].startswith("g_pn_") or parts[1] in EXPECTED_TEXTURE_GROUPS

    if len(parts) == 4 and parts[0] == "scenes":
        scene_name = parts[2]
        resource_name = parts[3]
        return scene_name in EXPECTED_BDAN_SCENES or resource_name == scene_name or resource_name.startswith(
            scene_name + "Set_"
        )

    return False


def validate_archives(
    base_path: Path,
    target_path: Path,
    expected_counts: dict[str, int] = EXPECTED_CHANGED_COUNTS,
) -> Counter:
    base_entries = _read_entries(base_path)
    target_entries = _read_entries(target_path)

    added = sorted(target_entries.keys() - base_entries.keys())
    removed = sorted(base_entries.keys() - target_entries.keys())
    if added or removed:
        raise ValidationError(f"archive paths differ: {len(added)} added, {len(removed)} removed")

    changed = sorted(name for name in base_entries if base_entries[name] != target_entries[name])
    unexpected = [name for name in changed if not is_expected_changed_path(name)]
    if unexpected:
        preview = ", ".join(unexpected[:5])
        raise ValidationError(f"unexpected changed resources: {preview}")

    counts = Counter(name.split("/", 1)[0] for name in changed)
    if counts != Counter(expected_counts):
        raise ValidationError(f"unexpected changed resource counts: {dict(sorted(counts.items()))}")

    return counts


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Hanmaru Korean O2R against its stock JP 1.1 base.")
    parser.add_argument("base", type=Path, help="Stock JP 1.1 oot.o2r")
    parser.add_argument("target", type=Path, help="Hanmaru Korean full oot.o2r")
    args = parser.parse_args(argv)

    try:
        counts = validate_archives(args.base, args.target)
    except (OSError, PatchError, RuntimeError, ValidationError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"Validated {sum(counts.values())} expected Korean resource changes; no paths were added or removed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
