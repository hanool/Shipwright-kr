import tempfile
import unittest
import zipfile
from pathlib import Path

from tools.validate_korean_o2r import ValidationError, is_expected_changed_path, validate_archives


class ValidateKoreanO2rTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_archive(self, name: str, entries: dict[str, bytes]) -> Path:
        path = self.root / name
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
            for entry_name, data in entries.items():
                archive.writestr(entry_name, data)
        return path

    def test_accepts_expected_resource_groups(self) -> None:
        expected = [
            "objects/object_bv/gBarinadeTitleCardTex",
            "scenes/shared/spot00_scene/spot00_scene",
            "scenes/nonmq/bdan_scene/bdan_room_0DL_001000",
            "text/jpn_message_data_static/jpn_message_data_static",
            "textures/kanji/gMsgKanji0000Tex",
        ]

        self.assertTrue(all(is_expected_changed_path(name) for name in expected))

    def test_rejects_shift_prone_resource_groups(self) -> None:
        unexpected = [
            "code/z_fbdemo_circle/sTransCircleVtx",
            "overlays/ovl_Magic_Wind/sAnim",
            "scenes/shared/link_home_scene/link_home_room_0",
            "textures/unclassified/resource",
        ]

        self.assertTrue(all(not is_expected_changed_path(name) for name in unexpected))

    def test_validates_expected_diff(self) -> None:
        base = self.write_archive("base.o2r", {"textures/kanji/gMsgKanji0000Tex": b"base"})
        target = self.write_archive("target.o2r", {"textures/kanji/gMsgKanji0000Tex": b"target"})

        counts = validate_archives(base, target, {"textures": 1})

        self.assertEqual(counts, {"textures": 1})

    def test_rejects_added_or_removed_paths(self) -> None:
        base = self.write_archive("base.o2r", {"textures/kanji/old": b"base"})
        target = self.write_archive("target.o2r", {"textures/kanji/new": b"target"})

        with self.assertRaisesRegex(ValidationError, "paths differ"):
            validate_archives(base, target, {"textures": 1})

    def test_rejects_unexpected_changed_path(self) -> None:
        base = self.write_archive("base.o2r", {"overlays/ovl_Magic_Wind/sAnim": b"base"})
        target = self.write_archive("target.o2r", {"overlays/ovl_Magic_Wind/sAnim": b"target"})

        with self.assertRaisesRegex(ValidationError, "unexpected changed resources"):
            validate_archives(base, target, {"overlays": 1})


if __name__ == "__main__":
    unittest.main()
