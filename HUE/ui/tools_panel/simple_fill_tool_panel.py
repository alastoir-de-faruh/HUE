# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Menu, Panel

from ..base_panel_info import BasePanelInfo
from ...utilities.palette_utilities import (
    SWATCH_COLS, get_active_fill_palette, get_color_icon, get_prefs,
)


class HUE_MT_fill_palette_select(Menu):
    """Dropdown listing every palette in the persistent library."""

    bl_idname = "HUE_MT_fill_palette_select"
    bl_label = "Select Palette"

    def draw(self, context):
        layout = self.layout
        prefs = get_prefs()
        if prefs is None or len(prefs.palettes) == 0:
            layout.label(text="No palettes")
            return
        for i, pal in enumerate(prefs.palettes):
            op = layout.operator(
                "hue.select_palette",
                text=f"{pal.name}  [{pal.mask_label()}]",
                icon="COLOR",
            )
            op.index = i


class HUE_PT_simple_fill_tool_panel(BasePanelInfo, Panel):
    bl_label = "Fill"
    bl_idname = "HUE_PT_simple_fill_tool_panel"
    bl_parent_id = "HUE_PT_tools_panel"
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        tool = context.scene.hue_simple_fill_tool

        # --- Active color + apply button ---
        box = layout.box()
        box.label(text="Active Color", icon="BRUSH_DATA")
        box.prop(tool, "color_space", expand=True)
        row = box.row(align=True)
        if tool.color_space == "LINEAR":
            row.prop(tool, "selected_color_linear", text="")
        else:
            row.prop(tool, "selected_color", text="")
        row.operator("hue.simple_fill", icon="CHECKMARK")

        layout.separator()

        # --- Palette library ---
        pal = get_active_fill_palette(context.scene)
        box = layout.box()
        header_row = box.row(align=False)
        header_row.label(text="Color Presets", icon="COLOR")
        header_row.prop(tool, "quick_fill", text="Quick Fill", toggle=True, icon="PLAY")

        row = box.row(align=True)
        label = f"{pal.name}  [{pal.mask_label()}]" if pal else "No palette"
        row.menu("HUE_MT_fill_palette_select", text=label, icon="COLOR")
        row.operator("hue.new_palette", icon="FILE_NEW", text="")
        if pal:
            row.operator("hue.rename_palette", icon="GREASEPENCIL", text="")
            row.operator("hue.delete_palette", icon="TRASH", text="")

        if pal:
            # Per-palette channel mask (paired with the palette; applied on select)
            mrow = box.row(align=True)
            mrow.label(text="Mask")
            mrow.prop(pal, "mask_r", toggle=True)
            mrow.prop(pal, "mask_g", toggle=True)
            mrow.prop(pal, "mask_b", toggle=True)
            mrow.prop(pal, "mask_a", toggle=True)

            # --- Swatch grid ---
            if len(pal.swatches) > 0:
                active_idx = pal.active_swatch_index
                for i, sw in enumerate(pal.swatches):
                    if i % SWATCH_COLS == 0:
                        row = box.row(align=True)
                        row.alignment = 'LEFT'
                    icon_id = get_color_icon(*sw.color[:3], color_space=tool.color_space)
                    op = row.operator(
                        "hue.use_preset_color",
                        text="",
                        icon_value=icon_id,
                        depress=(i == active_idx),
                    )
                    op.index = i

            # --- Add / Remove buttons ---
            row = box.row(align=True)
            row.operator("hue.add_preset_color", icon="ADD", text="")
            if len(pal.swatches) > 0:
                row.operator("hue.remove_preset_color", icon="REMOVE", text="")
                op = row.operator("hue.edit_swatch_description", icon="TEXT", text="")
                op.index = pal.active_swatch_index
