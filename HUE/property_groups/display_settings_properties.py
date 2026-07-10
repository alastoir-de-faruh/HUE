# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.props import BoolProperty, EnumProperty, StringProperty
from bpy.types import PropertyGroup


def on_settings_update(self, context):
    if hasattr(context, 'space_data') and context.space_data and hasattr(context.space_data, 'shading'):
        from ..operators.display_vertex_colors import update_display
        update_display(context)


class DisplaySettingsProperties(PropertyGroup):
    previous_shading_type: StringProperty(name="Previous Shading Type", default="SOLID")
    previous_color_type: StringProperty(name="Previous Color Type", default="OBJECT")
    previous_light_type: StringProperty(name="Previous Light Type", default="STUDIO")

    # True while a HUE display mode is active (shading has been saved).
    display_active: BoolProperty(name="Display Active", default=False)

    display_mode: EnumProperty(
        name="Vertex Colors Display Mode",
        description="Determines how vertex colors will be presented",
        items=[
            ("Off", "Off", "Do not show vertex color."),
            ("RGB", "RGB", "Show the full RGB vertex colors."),
            ("R", "R", "Show only the Red channel as grayscale."),
            ("G", "G", "Show only the Green channel as grayscale."),
            ("B", "B", "Show only the Blue channel as grayscale."),
            ("Alpha", "A", "Show only the Alpha channel as grayscale."),
        ],
        default="Off",
        update=on_settings_update,
    )

    # Channel preview state (grayscale channel shown via a temporary render
    # color attribute — no material reassignment).
    channel_preview_attr: StringProperty(
        name="Channel Preview Attribute",
        default="HUE_ChannelPreview",
    )
    channel_preview_source: StringProperty(name="Channel Preview Source", default="")
    channel_preview_object: StringProperty(name="Channel Preview Object", default="")
