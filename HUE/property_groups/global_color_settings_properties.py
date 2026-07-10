# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import BoolProperty, EnumProperty
from bpy.types import PropertyGroup


class GlobalColorSettingsProperties(PropertyGroup):
    global_color_mask_r: BoolProperty(name="R", description="Use Red Channel", default=True)
    global_color_mask_g: BoolProperty(name="G", description="Use Green Channel", default=True)
    global_color_mask_b: BoolProperty(name="B", description="Use Blue Channel", default=True)
    global_color_mask_a: BoolProperty(name="A", description="Use Alpha Channel", default=True)

    color_space: EnumProperty(
        name="Color Space",
        description=(
            "Which vertex-color channel HUE tools read and write. sRGB writes "
            "gamma-encoded colors (matches Blender's color picker); Linear writes "
            "raw linear values so shaders read them 1:1 — use this for data such "
            "as masks or region IDs"
        ),
        items=[
            ("sRGB", "sRGB", "Read/write the gamma-encoded (color_srgb) channel"),
            ("LINEAR", "Linear", "Read/write the raw linear (color) channel, unchanged for shaders"),
        ],
        default="sRGB",
    )

    def get_mask(self):
        return (self.global_color_mask_r, self.global_color_mask_g, self.global_color_mask_b, self.global_color_mask_a)

    def use_srgb(self):
        return self.color_space != "LINEAR"
