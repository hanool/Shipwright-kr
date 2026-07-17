#!/usr/bin/env python3

import argparse
import sys
import zipfile
from collections import Counter
from pathlib import Path


IGNORED_ENTRIES = frozenset({"version", "portVersion", "manifest.json"})
FIXED_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class PatchError(Exception):
    pass


def _validate_entry_name(name: str) -> None:
    parts = name.split("/")
    if (
        not name
        or name.startswith("/")
        or "\\" in name
        or "\0" in name
        or any(part in {"", ".", ".."} for part in parts)
        or (len(parts[0]) == 2 and parts[0][1] == ":")
    ):
        raise PatchError(f"archive contains an unsafe entry name: {name!r}")


def _read_entries(path: Path) -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(path, "r") as archive:
            files = [info for info in archive.infolist() if not info.is_dir()]
            names = [info.filename for info in files]
            duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
            if duplicates:
                raise PatchError(f"{path} contains duplicate entries: {', '.join(duplicates)}")

            entries = {}
            for info in files:
                _validate_entry_name(info.filename)
                if info.filename not in IGNORED_ENTRIES:
                    entries[info.filename] = archive.read(info)
            return entries
    except zipfile.BadZipFile as error:
        raise PatchError(f"{path} is not a valid O2R archive: {error}") from error


def create_patch(
    base_path: Path, target_path: Path, output_path: Path, allow_removals: bool = False
) -> tuple[int, int, int]:
    if output_path.suffix.lower() != ".o2r":
        raise PatchError("the output filename must use the .o2r extension")
    if output_path.exists():
        raise PatchError(f"output already exists: {output_path}")
    if not output_path.parent.is_dir():
        raise PatchError(f"output directory does not exist: {output_path.parent}")

    base_entries = _read_entries(base_path)
    target_entries = _read_entries(target_path)

    removed = sorted(base_entries.keys() - target_entries.keys())
    if removed and not allow_removals:
        preview = ", ".join(removed[:5])
        raise PatchError(
            f"the target removes {len(removed)} entries, which an O2R override cannot represent: {preview}"
        )

    added = sorted(target_entries.keys() - base_entries.keys())
    changed = sorted(
        name for name in target_entries.keys() & base_entries.keys() if target_entries[name] != base_entries[name]
    )
    selected = sorted(added + changed)
    if not selected:
        raise PatchError("the archives contain no resource changes")

    for name in selected:
        if not target_entries[name]:
            raise PatchError(f"changed entry is empty and would mask the base resource: {name}")
        if name.endswith(".meta"):
            raise PatchError(f"resource .meta sidecars are not safe in override archives: {name}")

    created_output = False
    try:
        with zipfile.ZipFile(output_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            created_output = True
            for name in selected:
                info = zipfile.ZipInfo(name, FIXED_TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, target_entries[name], compresslevel=9)

        written_entries = _read_entries(output_path)
        expected_entries = {name: target_entries[name] for name in selected}
        if written_entries != expected_entries:
            raise PatchError("the generated patch failed verification")
    except Exception:
        if created_output:
            output_path.unlink(missing_ok=True)
        raise

    return len(added), len(changed), len(removed)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a differential O2R mod from base and modified full O2R archives."
    )
    parser.add_argument("base", type=Path, help="Unmodified base oot.o2r")
    parser.add_argument("target", type=Path, help="Modified full oot.o2r")
    parser.add_argument("output", type=Path, help="Output mod archive ending in .o2r")
    parser.add_argument(
        "--allow-removals",
        action="store_true",
        help="Create the patch even when target omissions will remain available from the base archive",
    )
    args = parser.parse_args(argv)

    try:
        added, changed, removed = create_patch(args.base, args.target, args.output, args.allow_removals)
    except (OSError, PatchError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(
        f"Created {args.output} with {added} added and {changed} changed resources; "
        f"{removed} target removals remain available from the base archive."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
