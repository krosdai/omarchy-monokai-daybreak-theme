"""Keep the theme faithful to Monokai Pro Light and installable from git."""

import re
import shutil
import subprocess
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COLORS = tomllib.loads((ROOT / "colors.toml").read_text())

# Monokai Pro Light, "Sun" filter: shades lightest to darkest, then the six accents.
MONOKAI_PRO_SUN = {
    "#fdf7f3", "#f8efe7", "#eee5de", "#ded5d0", "#d2c9c4",
    "#beb5b3", "#a59c9c", "#92898a", "#72696d", "#2c232e",
    "#ce4770", "#d4572b", "#b16803", "#218871", "#2473b6", "#6851a2",
}  # fmt: skip
# Omarchy asks for brown, which Monokai Pro lacks: orange mixed 50% with black.
DERIVED = {"brown": "#6a2c16"}
REQUIRED = {
    "accent", "selection", "muted",
    "background", "dark_background", "darker_background", "lighter_background",
    "foreground", "dark_foreground", "light_foreground", "bright_foreground",
    "red", "yellow", "orange", "green", "cyan", "blue", "magenta", "brown",
    "bright_red", "bright_yellow", "bright_green",
    "bright_cyan", "bright_blue", "bright_magenta",
}  # fmt: skip
# `omarchy-theme-set` drops these from a theme cloned by `omarchy theme install`.
DENIED_NAMES = {
    "alacritty.toml",
    "foot.ini",
    "ghostty.conf",
    "kitty.conf",
    "vscode.json",
}
YARU = re.compile(
    r"Yaru(-(blue|dark|magenta|olive|prussiangreen|purple|red|sage|wartybrown|yellow))?"
)


def shipped_files():
    return [
        path
        for path in ROOT.rglob("*")
        if ".git" not in path.relative_to(ROOT).parts
        and "__pycache__" not in path.parts
    ]


class ThemeTest(unittest.TestCase):
    def test_palette_is_complete_light_and_monokai_pro_sun(self):
        self.assertEqual(COLORS.pop("mode"), "light")
        self.assertEqual(set(COLORS), REQUIRED)
        for key, value in COLORS.items():
            with self.subTest(key=key):
                self.assertRegex(value, r"^#[0-9a-f]{6}$")
                self.assertIn(value, MONOKAI_PRO_SUN | {DERIVED.get(key)})
        COLORS["mode"] = "light"

    def test_terminal_mapping_follows_official_palette(self):
        self.assertEqual(COLORS["background"], "#f8efe7")
        self.assertEqual(COLORS["foreground"], "#2c232e")
        self.assertEqual(COLORS["blue"], COLORS["orange"])
        for name in ("red", "yellow", "green", "cyan", "blue", "magenta"):
            self.assertEqual(COLORS[f"bright_{name}"], COLORS[name])

    def test_ships_only_what_an_installed_theme_keeps(self):
        for path in shipped_files():
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertFalse(path.is_symlink())
                self.assertNotEqual(path.suffix, ".lua")
                self.assertNotIn(path.name, DENIED_NAMES)

    def test_assets(self):
        self.assertRegex(
            (ROOT / "icons.theme").read_text().strip(), f"^{YARU.pattern}$"
        )
        backgrounds = sorted((ROOT / "backgrounds").iterdir())
        self.assertTrue(backgrounds)
        # Switching to the theme starts on its first background in sorted order.
        self.assertEqual(backgrounds[0].name, "1-kite.webp")
        for path in backgrounds:
            self.assertIn(path.suffix, {".jpg", ".png", ".webp"})

    @unittest.skipUnless(
        shutil.which("omarchy-theme-color"), "Omarchy is not installed"
    )
    def test_omarchy_resolves_the_palette(self):
        output = subprocess.run(
            ["omarchy-theme-color", "--file", str(ROOT / "colors.toml"), "--all"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        resolved = dict(line.split("\t", 1) for line in output.splitlines())
        self.assertEqual(resolved["color0"], "#f8efe7")
        self.assertEqual(resolved["color4"], "#d4572b")
        self.assertEqual(resolved["color8"], "#a59c9c")
        self.assertEqual(resolved["cursor"], "#2c232e")
        self.assertEqual(resolved["theme_type"], "light")


if __name__ == "__main__":
    unittest.main()
