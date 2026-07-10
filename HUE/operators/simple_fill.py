# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

from ..utilities.palette_utilities import get_active_fill_palette, get_prefs
from ..utilities.color_utilities import (
    apply_mask_constant, bulk_get_colors, bulk_set_colors,
    ensure_object_mode, get_active_color_attribute, get_selected_color_indices,
)
from .base_operators import BaseColorOperator, BaseOperator


def _apply_fill(obj, color, mask, select_mode):
    """Apply color fill using numpy bulk operations (requires object mode).

    When *select_mode* is ``None`` (object mode), all elements are colored.
    """
    color_attribute = get_active_color_attribute(obj)
    indices = get_selected_color_indices(obj, select_mode, color_attribute.domain)
    colors = bulk_get_colors(color_attribute)
    apply_mask_constant(colors, color, mask, indices)
    bulk_set_colors(color_attribute, colors)
    obj.data.update()


def execute_simple_fill(context):
    """Core simple fill logic, callable without an operator instance.

    Returns (success, message) tuple.
    """
    scene = context.scene
    global_color_settings = scene.hue_global_color_settings
    simple_fill_tool = scene.hue_simple_fill_tool
    mask = global_color_settings.get_mask()
    # In Linear mode the fill value is the linear picker (written straight to the
    # linear channel by bulk_set_colors); in sRGB mode it is the gamma picker.
    if global_color_settings.use_srgb():
        color = simple_fill_tool.selected_color
    else:
        color = simple_fill_tool.selected_color_linear
    select_mode = context.tool_settings.mesh_select_mode if context.mode == 'EDIT_MESH' else None

    for obj in context.selected_objects:
        if obj.type != "MESH":
            continue

        with ensure_object_mode(obj):
            _apply_fill(obj, color, mask, select_mode)

    return True, "Vertex colors assigned successfully!"


class HUE_OT_simple_fill(BaseColorOperator):
    """Applies a selected color to selected object(s) or part of the mesh"""

    bl_label = "Apply Color"
    bl_idname = "hue.simple_fill"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        success, msg = execute_simple_fill(context)
        if not success:
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}
        self.report({"INFO"}, msg)
        return {"FINISHED"}


class HUE_OT_add_preset_color(BaseOperator):
    """Saves the current active color as a new swatch in the active palette"""

    bl_label = "Add Preset Color"
    bl_idname = "hue.add_preset_color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pal = get_active_fill_palette(context.scene)
        if pal is None:
            self.report({"WARNING"}, "No palette selected")
            return {"CANCELLED"}
        color = context.scene.hue_simple_fill_tool.selected_color
        sw = pal.swatches.add()
        sw.color = (color[0], color[1], color[2], color[3])
        pal.active_swatch_index = len(pal.swatches) - 1
        return {"FINISHED"}


class HUE_OT_remove_preset_color(BaseOperator):
    """Removes the currently selected swatch from the active palette"""

    bl_label = "Remove Preset Color"
    bl_idname = "hue.remove_preset_color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pal = get_active_fill_palette(context.scene)
        if pal is None or len(pal.swatches) == 0:
            self.report({"WARNING"}, "No preset colors to remove")
            return {"CANCELLED"}
        idx = min(pal.active_swatch_index, len(pal.swatches) - 1)
        pal.swatches.remove(idx)
        pal.active_swatch_index = min(idx, len(pal.swatches) - 1) if len(pal.swatches) else 0
        return {"FINISHED"}


class HUE_OT_new_palette(BaseOperator):
    """Creates a new palette in the persistent library"""

    bl_label = "New Palette"
    bl_idname = "hue.new_palette"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        prefs = get_prefs()
        if prefs is None:
            self.report({"ERROR"}, "Add-on preferences unavailable")
            return {"CANCELLED"}
        prefs.palettes.add().name = "Palette"
        # Selecting the new palette also applies its (default) mask.
        context.scene.hue_simple_fill_tool.active_palette_index = len(prefs.palettes) - 1
        return {"FINISHED"}


class HUE_OT_rename_palette(BaseOperator):
    """Renames the currently selected palette"""

    bl_label = "Rename Palette"
    bl_idname = "hue.rename_palette"
    bl_options = {'REGISTER', 'UNDO'}

    new_name: bpy.props.StringProperty(name="Name")

    def invoke(self, context, event):
        pal = get_active_fill_palette(context.scene)
        if pal is None:
            self.report({"WARNING"}, "No palette selected")
            return {"CANCELLED"}
        self.new_name = pal.name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, "new_name", text="")

    def execute(self, context):
        pal = get_active_fill_palette(context.scene)
        if pal is None:
            return {"CANCELLED"}
        if not self.new_name.strip():
            self.report({"WARNING"}, "Name cannot be empty")
            return {"CANCELLED"}
        pal.name = self.new_name.strip()
        return {"FINISHED"}


class HUE_OT_delete_palette(BaseOperator):
    """Deletes the currently selected palette from the library"""

    bl_label = "Delete Palette"
    bl_idname = "hue.delete_palette"
    bl_options = {'REGISTER', 'UNDO'}

    palette_name: bpy.props.StringProperty(options={'SKIP_SAVE'})

    def invoke(self, context, event):
        prefs = get_prefs()
        if prefs is None or len(prefs.palettes) == 0:
            self.report({"WARNING"}, "No palette selected")
            return {"CANCELLED"}
        if len(prefs.palettes) <= 1:
            self.report({"WARNING"}, "Cannot delete the last palette!")
            return {"CANCELLED"}
        self.palette_name = get_active_fill_palette(context.scene).name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(text=f"Delete \"{self.palette_name}\" palette?")

    def execute(self, context):
        prefs = get_prefs()
        tool = context.scene.hue_simple_fill_tool
        if prefs is None or len(prefs.palettes) <= 1:
            self.report({"WARNING"}, "Cannot delete the last palette!")
            return {"CANCELLED"}
        idx = max(0, min(tool.active_palette_index, len(prefs.palettes) - 1))
        prefs.palettes.remove(idx)
        # Re-select (clamped) — also re-applies the mask of the new active palette.
        tool.active_palette_index = min(idx, len(prefs.palettes) - 1)
        return {"FINISHED"}


class HUE_OT_select_palette(BaseOperator):
    """Makes this the active palette and applies its channel mask"""

    warn_visibility_check = False

    bl_label = "Select Palette"
    bl_idname = "hue.select_palette"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty()

    def execute(self, context):
        prefs = get_prefs()
        if prefs is None or not (0 <= self.index < len(prefs.palettes)):
            return {"CANCELLED"}
        # Assigning the index triggers the mask sync via its update callback.
        context.scene.hue_simple_fill_tool.active_palette_index = self.index
        return {"FINISHED"}


class HUE_OT_edit_swatch_description(BaseOperator):
    """Edit the description shown when hovering this swatch"""

    warn_visibility_check = False

    bl_label = "Edit Swatch Description"
    bl_idname = "hue.edit_swatch_description"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty()
    description_text: bpy.props.StringProperty(name="Description")

    def invoke(self, context, event):
        pal = get_active_fill_palette(context.scene)
        if pal is None or not (0 <= self.index < len(pal.swatches)):
            self.report({"WARNING"}, "No swatch selected")
            return {"CANCELLED"}
        self.description_text = pal.swatches[self.index].description
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, "description_text", text="")

    def execute(self, context):
        pal = get_active_fill_palette(context.scene)
        if pal is None or not (0 <= self.index < len(pal.swatches)):
            return {"CANCELLED"}
        pal.swatches[self.index].description = self.description_text
        return {"FINISHED"}


class HUE_OT_use_preset_color(BaseOperator):
    """Selects this preset and sets it as the active color. With Quick Fill enabled, also immediately fills the object."""

    warn_visibility_check = False

    bl_label = "Use Preset Color"
    bl_idname = "hue.use_preset_color"
    bl_options = {'REGISTER', 'UNDO'}

    index: bpy.props.IntProperty()

    @classmethod
    def description(cls, context, properties):
        pal = get_active_fill_palette(context.scene)
        if pal is not None and 0 <= properties.index < len(pal.swatches):
            note = pal.swatches[properties.index].description
            if note:
                return note
        return "Set this preset as the active color"

    def execute(self, context):
        simple_fill_tool = context.scene.hue_simple_fill_tool
        pal = get_active_fill_palette(context.scene)
        if pal is None or self.index >= len(pal.swatches):
            return {"CANCELLED"}
        color = pal.swatches[self.index].color
        # Full-tuple assignment keeps the sRGB/linear view mirror in sync.
        simple_fill_tool.selected_color = (color[0], color[1], color[2], color[3])
        pal.active_swatch_index = self.index

        if simple_fill_tool.quick_fill:
            success, msg = execute_simple_fill(context)
            if not success:
                self.report({"ERROR"}, msg)
                return {"CANCELLED"}
            self.report({"INFO"}, msg)

        return {"FINISHED"}
