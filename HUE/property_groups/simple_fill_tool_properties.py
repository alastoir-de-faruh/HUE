# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import (
    BoolProperty, EnumProperty, FloatVectorProperty, IntProperty,
)
from bpy.types import PropertyGroup


def _on_palette_selected(self, context):
    """Apply the newly selected palette's channel mask to the scene mask."""
    scene = getattr(context, "scene", None)
    if scene is None:
        return
    gcs = getattr(scene, "hue_global_color_settings", None)
    if gcs is None:
        return
    from ..utilities.palette_utilities import get_active_fill_palette
    pal = get_active_fill_palette(scene)
    if pal is None:
        return
    gcs.global_color_mask_r = pal.mask_r
    gcs.global_color_mask_g = pal.mask_g
    gcs.global_color_mask_b = pal.mask_b
    gcs.global_color_mask_a = pal.mask_a


# The sRGB/Linear switch is a *view* aid only: both color properties hold the
# exact same numbers. The switch merely changes how those numbers are shown —
# a COLOR_GAMMA widget reads them as sRGB, a COLOR widget reads them as
# scene-linear — so the artist can inspect the same triple in either space.
# The stored value, and therefore the color applied to the mesh, never changes.
#
# Guard against the two properties triggering each other's update callbacks in
# an infinite loop while we mirror them.
_syncing = False


def _mirror(self, src_attr, dst_attr):
    """Copy one color property onto the other verbatim (no gamma math).

    Both properties always hold identical numbers; only the widget subtype
    used to display them differs.
    """
    global _syncing
    if _syncing:
        return
    _syncing = True
    try:
        setattr(self, dst_attr, tuple(getattr(self, src_attr)))
    finally:
        _syncing = False


def _sync_from_srgb(self, context):
    """Keep the linear-view property in step with the sRGB-view property."""
    _mirror(self, "selected_color", "selected_color_linear")


def _sync_from_linear(self, context):
    """Keep the sRGB-view property in step with the linear-view property."""
    _mirror(self, "selected_color_linear", "selected_color")


class SimpleFillToolProperties(PropertyGroup):
    color_space: EnumProperty(
        name="Color Space",
        description=(
            "How the active color and palette swatches are displayed. This is "
            "a view aid only — it changes neither the stored color nor the "
            "color applied to the mesh"
        ),
        items=[
            ("sRGB", "sRGB", "Show the values interpreted as sRGB (gamma) space"),
            ("LINEAR", "Linear", "Show the same values interpreted as Linear RGB"),
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

    active_palette_index: IntProperty(
        name="Active Palette",
        description="Index into the persistent palette library",
        default=0,
        update=_on_palette_selected,
    )

    quick_fill: BoolProperty(
        name="Quick Fill",
        description="When enabled, clicking a palette swatch immediately fills the object with that color",
        default=False,
    )
