import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

from tools.create_o2r_patch import PatchError, create_patch


class CreateO2rPatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_archive(self, name: str, entries: list[tuple[str, bytes]]) -> Path:
        path = self.root / name
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
                for entry_name, data in entries:
                    archive.writestr(entry_name, data)
        return path

    def test_writes_only_added_and_changed_resources(self) -> None:
        base = self.write_archive(
            "base.o2r",
            [
                ("version", b"base version"),
                ("portVersion", b"base port"),
                ("objects/unchanged", b"same"),
                ("text/messages", b"Japanese"),
            ],
        )
        target = self.write_archive(
            "target.o2r",
            [
                ("version", b"target version"),
                ("portVersion", b"target port"),
                ("manifest.json", b'{"name":"ignored"}'),
                ("objects/", b""),
                ("objects/unchanged", b"same"),
                ("text/messages", b"Korean"),
                ("textures/kanji/new", b"glyph"),
            ],
        )
        output = self.root / "patch.o2r"

        self.assertEqual(create_patch(base, target, output), (1, 1, 0))

        with zipfile.ZipFile(output, "r") as archive:
            self.assertEqual(archive.namelist(), ["text/messages", "textures/kanji/new"])
            self.assertEqual(archive.read("text/messages"), b"Korean")
            self.assertEqual(archive.read("textures/kanji/new"), b"glyph")
            self.assertTrue(all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist()))

    def test_rejects_removed_resources(self) -> None:
        base = self.write_archive("base.o2r", [("objects/removed", b"base")])
        target = self.write_archive("target.o2r", [("objects/added", b"target")])

        with self.assertRaisesRegex(PatchError, "cannot represent"):
            create_patch(base, target, self.root / "patch.o2r")

    def test_can_explicitly_allow_removed_resources(self) -> None:
        base = self.write_archive("base.o2r", [("objects/removed", b"base")])
        target = self.write_archive("target.o2r", [("objects/added", b"target")])
        output = self.root / "patch.o2r"

        self.assertEqual(create_patch(base, target, output, allow_removals=True), (1, 0, 1))

        with zipfile.ZipFile(output, "r") as archive:
            self.assertEqual(archive.namelist(), ["objects/added"])

    def test_rejects_duplicate_entries(self) -> None:
        base = self.write_archive("base.o2r", [])
        target = self.write_archive("target.o2r", [("duplicate", b"one"), ("duplicate", b"two")])

        with self.assertRaisesRegex(PatchError, "duplicate entries"):
            create_patch(base, target, self.root / "patch.o2r")

    def test_rejects_unsafe_entry_names(self) -> None:
        base = self.write_archive("base.o2r", [])

        for index, name in enumerate(["/absolute", "../escape", "foo//bar", "foo\\bar", "C:/drive"]):
            with self.subTest(name=name):
                target = self.write_archive(f"target-{index}.o2r", [(name, b"data")])
                with self.assertRaisesRegex(PatchError, "unsafe entry name"):
                    create_patch(base, target, self.root / f"patch-{index}.o2r")

    def test_rejects_empty_and_meta_replacements(self) -> None:
        for index, (name, data) in enumerate([("empty", b""), ("resource.meta", b"metadata")]):
            with self.subTest(name=name):
                base = self.write_archive(f"base-{index}.o2r", [])
                target = self.write_archive(f"target-{index}.o2r", [(name, data)])
                with self.assertRaises(PatchError):
                    create_patch(base, target, self.root / f"patch-{index}.o2r")

    def test_does_not_overwrite_an_existing_output(self) -> None:
        base = self.write_archive("base.o2r", [])
        target = self.write_archive("target.o2r", [("resource", b"target")])
        output = self.root / "patch.o2r"
        output.write_bytes(b"existing")

        with self.assertRaisesRegex(PatchError, "already exists"):
            create_patch(base, target, output)
        self.assertEqual(output.read_bytes(), b"existing")


if __name__ == "__main__":
    unittest.main()
