import unittest
from unittest.mock import patch

from archie.version import applet_update_required, installed_archie_version


class ArchieVersionTest(unittest.TestCase):
    @patch("archie.version.version", return_value="1.2.3")
    def test_reads_installed_distribution_version(self, version) -> None:
        self.assertEqual(installed_archie_version(), "1.2.3")
        version.assert_called_once_with("archie")

    def test_update_is_required_only_when_a_running_applet_is_stale(self) -> None:
        self.assertTrue(applet_update_required("1.2.3", "1.2.4"))
        self.assertFalse(applet_update_required("1.2.3", "1.2.3"))
        self.assertFalse(applet_update_required(None, "1.2.4"))
