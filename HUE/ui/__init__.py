# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from . import about_panel
from .settings_panel import (
    color_attributes_settings_panel,
    display_settings_panel,
    global_color_settings_panel,
    settings_panel,
)
from .tools_panel import (
    adjust_panel,
    attribute_transfer_tool_panel,
    color_adjustments_tool_panel,
    color_by_position_tool_panel,
    color_by_selection_tool_panel,
    random_color_tool_panel,
    simple_fill_tool_panel,
    smooth_tool_panel,
    symmetrize_tool_panel,
    tools_panel,
)

classes = [
    # Menus
    simple_fill_tool_panel.HUE_MT_fill_palette_select,
    random_color_tool_panel.HUE_MT_random_palette_select,

    # Parent panels first (children reference these via bl_parent_id)
    display_settings_panel.HUE_PT_display_settings_panel,
    tools_panel.HUE_PT_tools_panel,
    simple_fill_tool_panel.HUE_PT_simple_fill_tool_panel,
    random_color_tool_panel.HUE_PT_random_color_tool_panel,
    color_by_position_tool_panel.HUE_PT_color_by_position_tool_panel,
    color_by_selection_tool_panel.HUE_PT_color_by_selection_tool_panel,
    adjust_panel.HUE_PT_adjust_panel,
    smooth_tool_panel.HUE_PT_smooth_tool_panel,
    color_adjustments_tool_panel.HUE_PT_color_adjustments_tool_panel,
    symmetrize_tool_panel.HUE_PT_symmetrize_tool_panel,
    attribute_transfer_tool_panel.HUE_PT_attribute_transfer_tool_panel,

    settings_panel.HUE_PT_settings_panel,
    global_color_settings_panel.HUE_PT_global_color_settings_panel,
    color_attributes_settings_panel.HUE_PT_color_attributes_settings_panel,

    about_panel.HUE_PT_about_panel,
]


def _swatch_context_menu(self, context):
    """Add an "Edit Swatch Description" entry when right-clicking a swatch."""
    op = getattr(context, "button_operator", None)
    if op is None or op.bl_rna.identifier != "HUE_OT_use_preset_color":
        return
    layout = self.layout
    layout.separator()
    props = layout.operator(
        "hue.edit_swatch_description", text="Edit Swatch Description", icon="TEXT"
    )
    props.index = op.index


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.UI_MT_button_context_menu.append(_swatch_context_menu)


def unregister():
    bpy.types.UI_MT_button_context_menu.remove(_swatch_context_menu)

    for cls in classes:
        bpy.utils.unregister_class(cls)

    from ..utilities.palette_utilities import cleanup_previews
    cleanup_previews()
