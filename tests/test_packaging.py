import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ArchieTmpfilesTest(unittest.TestCase):
    def test_shared_waybar_directory_is_writable_by_the_archie_group(self) -> None:
        rules = (ROOT / "packaging/archie-cli/archie.tmpfiles").read_text(
            encoding="utf-8"
        ).splitlines()

        self.assertIn("d /var/lib/archie 2775 root archie -", rules)
        self.assertIn("f /var/lib/archie/store.sqlite3 0664 root archie - -", rules)
        self.assertIn("d /var/lib/archie/waybar 2775 root archie -", rules)
