# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Unit tests for utilities/palette_utilities.py.

Runs inside Blender via::

    blender -b --factory-startup -P Tests/conftest.py --python-exit-code 1
"""

import sys
import unittest
from pathlib import Path

_tests_dir = Path(__file__).resolve().parent
_addon_root = _tests_dir.parent / "HUE"
for p in (_tests_dir, _addon_root):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

import bpy

from utilities.palette_utilities import (
    DEFAULT_PALETTE_NAME,
    _linear_to_srgb,
    cleanup_previews,
    get_color_icon,
)


class TestLinearToSrgb(unittest.TestCase):
    """Pure function — no Blender data needed."""

    def test_zero(self):
        self.assertAlmostEqual(_linear_to_srgb(0.0), 0.0)

    def test_one(self):
        self.assertAlmostEqual(_linear_to_srgb(1.0), 1.0)

    def test_low_linear_value(self):
        # Below 0.0031308 → linear region: c * 12.92
        self.assertAlmostEqual(_linear_to_srgb(0.001), 0.001 * 12.92, places=6)

    def test_mid_value(self):
        # 0.5 linear ≈ 0.735 sRGB (standard formula)
        result = _linear_to_srgb(0.5)
        expected = 1.055 * (0.5 ** (1.0 / 2.4)) - 0.055
        self.assertAlmostEqual(result, expected, places=6)

    def test_monotonic(self):
        """sRGB conversion should be monotonically increasing."""
        prev = _linear_to_srgb(0.0)
        for i in range(1, 101):
            val = i / 100.0
            curr = _linear_to_srgb(val)
            self.assertGreater(curr, prev)
            prev = curr


class TestDefaultPaletteName(unittest.TestCase):
    """The persistent palette library seeds a palette with this name."""

    def test_name_is_non_empty_string(self):
        self.assertIsInstance(DEFAULT_PALETTE_NAME, str)
        self.assertTrue(DEFAULT_PALETTE_NAME)


class TestGetColorIcon(unittest.TestCase):
    def tearDown(self):
        cleanup_previews()

    def test_returns_int_icon_id(self):
        icon_id = get_color_icon(1.0, 0.0, 0.0)
        self.assertIsInstance(icon_id, int)

    def test_same_color_returns_same_id(self):
        id1 = get_color_icon(0.5, 0.5, 0.5)
        id2 = get_color_icon(0.5, 0.5, 0.5)
        self.assertEqual(id1, id2)

    def test_clamps_out_of_range(self):
        # Should not crash with out-of-range linear values
        icon_id = get_color_icon(2.0, -0.5, 0.5)
        self.assertIsInstance(icon_id, int)

    def test_linear_space_differs_from_srgb(self):
        # The color-space view aid should render a mid value differently.
        srgb_id = get_color_icon(0.5, 0.5, 0.5, color_space="sRGB")
        linear_id = get_color_icon(0.5, 0.5, 0.5, color_space="LINEAR")
        self.assertNotEqual(srgb_id, linear_id)


if __name__ == "__main__":
    unittest.main()
