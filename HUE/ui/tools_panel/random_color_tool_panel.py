# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Menu, Panel

from ..base_panel_info import BasePanelInfo
from ...utilities.palette_utilities import SWATCH_COLS, get_color_icon, get_prefs


class HUE_MT_random_palette_select(Menu):
    """Dropdown listing every palette in the persistent library."""

    bl_idname = "HUE_MT_random_palette_select"
    bl_label = "Select Palette"

    def draw(self, context):
        layout = self.layout
        prefs = get_prefs()
        if prefs is None or len(prefs.palettes) == 0:
            layout.label(text="No palettes")
            return
        for i, pal in enumerate(prefs.palettes):
            op = layout.operator(
                "hue.select_random_palette",
                text=f"{pal.name}  [{pal.mask_label()}]",
                icon="COLOR",
            )
            op.index = i


class HUE_PT_random_color_tool_panel(BasePanelInfo, Panel):
    bl_label = "Randomize"
    bl_idname = "HUE_PT_random_color_tool_panel"
    bl_parent_id = "HUE_PT_tools_panel"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 1

    def draw(self, context):
        layout = self.layout

        random_color_tool = context.scene.hue_random_color_tool

        mesh_count = sum(1 for obj in context.selected_objects if obj.type == "MESH")
        show_element_type = True
        obj = context.active_object

        if obj is not None and mesh_count <= 1:
            color_attribute = obj.data.color_attributes.active_color

            if color_attribute is not None:
                if color_attribute.domain == "POINT":
                    show_element_type = False

        if show_element_type:
            row = layout.row()
            row.prop(random_color_tool, "element_type")

        else:
            row = layout.row()
            row.label(
                text="Active color attribute uses Point domain."
                " Switch to Face Corner domain to choose element type.",
                icon="INFO")

        row = layout.row()
        row.label(text="Color Generation Method:")
        row.prop(random_color_tool, "color_mode", expand=True)

        if random_color_tool.color_mode == "Palette":
            prefs = get_prefs()
            idx = random_color_tool.random_palette_index
            pal = prefs.palettes[idx] if prefs and 0 <= idx < len(prefs.palettes) else None
            # Swatches follow the Fill tool's color-space view aid so palettes
            # read consistently across the whole HUE editor.
            color_space = context.scene.hue_simple_fill_tool.color_space

            box = layout.box()
            box.label(text="Palette", icon="COLOR")
            row = box.row(align=True)
            row.menu(
                "HUE_MT_random_palette_select",
                text=pal.name if pal else "No palette",
                icon="COLOR",
            )

            if pal and len(pal.swatches) > 0:
                for i, sw in enumerate(pal.swatches):
                    if i % SWATCH_COLS == 0:
                        row = box.row(align=True)
                        row.alignment = 'LEFT'
                    icon_id = get_color_icon(*sw.color[:3], color_space=color_space)
                    row.label(text="", icon_value=icon_id)

        row = layout.row()
        row.operator("hue.add_random_color", icon="SHADERFX")
