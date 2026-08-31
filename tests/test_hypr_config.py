import unittest
from pathlib import Path


BINDS_PATH = (
    Path(__file__).resolve().parents[1]
    / "deployment-packages/config/hypr/config/binds.lua"
)


class HyprlandBindingsTest(unittest.TestCase):
    def test_uses_keysyms_for_screenshot_and_brightness_binds(self) -> None:
        bindings = BINDS_PATH.read_text(encoding="utf-8")

        self.assertNotRegex(bindings, r"hl\.bind\([^\n]*code:")
        for key in (
            "SHIFT + Print",
            '"Print"',
            "KP_Add",
            "KP_Subtract",
            "XF86MonBrightnessUp",
            "XF86MonBrightnessDown",
        ):
            with self.subTest(key=key):
                self.assertIn(key, bindings)
