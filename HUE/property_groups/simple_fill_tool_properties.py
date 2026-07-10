# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.props import (
    BoolProperty, EnumProperty, FloatVectorProperty, IntProperty, PointerProperty,
)
from bpy.types import PropertyGroup

from ..utilities.color_utilities import linear_to_srgb, srgb_to_linear

# Guard against the two color properties triggering each other's update
# callbacks in an infinite loop while we keep them in sync.
_syncing = False


def _sync_from_srgb(self, context):
    """Mirror the sRGB picker value into the linear picker."""
    global _syncing
    if _syncing:
        return
    _syncing = True
    try:
        src = self.selected_color
        self.selected_color_linear = (
            srgb_to_linear(src[0]),
            srgb_to_linear(src[1]),
            srgb_to_linear(src[2]),
            src[3],  # alpha is not gamma-corrected
        )
    finally:
        _syncing = False


def _sync_from_linear(self, context):
    """Mirror the linear picker value into the sRGB picker."""
    global _syncing
    if _syncing:
        return
    _syncing = True
    try:
        src = self.selected_color_linear
        self.selected_color = (
            linear_to_srgb(src[0]),
            linear_to_srgb(src[1]),
            linear_to_srgb(src[2]),
            src[3],  # alpha is not gamma-corrected
        )
    finally:
        _syncing = False


class SimpleFillToolProperties(PropertyGroup):
    color_space: EnumProperty(
        name="Color Space",
        description=(
            "Choose whether the numeric color fields are shown in sRGB or "
            "Linear space. The resulting fill color is identical either way"
        ),
        items=[
            ("sRGB", "sRGB", "Enter and view color values in sRGB (gamma) space"),
            ("LINEAR", "Linear", "Enter and view color values in Linear RGB space"),
        ],
        default="sRGB",
    )

    selected_color: FloatVectorProperty(
        name="Color",
        description="Choose a color (sRGB)",
        subtype="COLOR_GAMMA",
        default=(1, 1, 1, 1),
        min=0,
        max=1,
        size=4,
        update=_sync_from_srgb,
    )

    selected_color_linear: FloatVectorProperty(
        name="Color (Linear)",
        description="Choose a color (Linear RGB)",
        subtype="COLOR",
        default=(1, 1, 1, 1),
        min=0,
        max=1,
        size=4,
        update=_sync_from_linear,
    )

    preset_palette: PointerProperty(
        type=bpy.types.Palette,
        name="Preset Palette",
        description="Palette of saved color presets",
    )

    active_preset_index: IntProperty(
        name="Active Preset Index",
        default=0,
    )

    quick_fill: BoolProperty(
        name="Quick Fill",
        description="When enabled, clicking a palette swatch immediately fills the object with that color",
        default=False,
    )
