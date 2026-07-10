# Copyright (C) 2024 Kai Fardreamer <tojynick@protonmail.com>
# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import numpy as np

from .base_operators import BaseOperator
from ..ui.settings_panel.display_settings_panel import HUE_PT_display_settings_panel
from ..utilities.color_utilities import (
    bulk_get_colors, bulk_set_colors, get_active_color_attribute,
)


# Single-channel display modes and the channel index they read.
_CHANNEL_INDEX = {"R": 0, "G": 1, "B": 2, "Alpha": 3}
_CHANNEL_MODES = set(_CHANNEL_INDEX)

# Guard so the temp-attribute write inside the depsgraph handler doesn't make
# the handler re-enter itself.
_syncing = False
# obj_name -> checksum of the source channel data last written to the temp
# attribute. Lets the live handler skip no-op writes and avoid a feedback loop.
_sync_cache = {}


def update_display(context):
    """Core display-mode logic, callable without an operator instance."""
    settings = context.scene.hue_display_settings
    mode = settings.display_mode

    if mode == "Off":
        _deactivate(context)
        return

    _activate_shading(context)
    if mode == "RGB":
        _teardown_channel_preview(context)
    elif mode in _CHANNEL_MODES:
        _setup_channel_preview(context, mode)
    _set_vertex_shading(context)


# ---------------------------------------------------------------------------
# Shading state
# ---------------------------------------------------------------------------

def _activate_shading(context):
    """Save the viewport shading once, when first entering a HUE display mode."""
    settings = context.scene.hue_display_settings
    if settings.display_active:
        return
    shading = context.space_data.shading
    settings.previous_shading_type = shading.type
    settings.previous_color_type = shading.color_type
    settings.previous_light_type = shading.light
    settings.display_active = True


def _set_vertex_shading(context):
    shading = context.space_data.shading
    shading.type = "SOLID"
    shading.color_type = "VERTEX"
    shading.light = "FLAT"


def _deactivate(context):
    """Leave every HUE display mode: restore attributes and shading."""
    settings = context.scene.hue_display_settings
    _teardown_channel_preview(context)
    if settings.display_active:
        shading = context.space_data.shading
        shading.type = settings.previous_shading_type
        shading.color_type = settings.previous_color_type
        shading.light = settings.previous_light_type
        settings.display_active = False


# ---------------------------------------------------------------------------
# Channel preview (temporary render color attribute, no material)
# ---------------------------------------------------------------------------

def _color_attr_index(color_attributes, attr):
    for i, a in enumerate(color_attributes):
        if a == attr:
            return i
    return -1


def _set_render_color(color_attributes, attr):
    """Set the render color attribute (what Solid shading displays)."""
    try:
        idx = _color_attr_index(color_attributes, attr)
        if idx >= 0:
            color_attributes.render_color_index = idx
    except (AttributeError, TypeError):
        try:
            color_attributes.render_color_name = attr.name
        except (AttributeError, TypeError):
            pass


def _set_active_color(color_attributes, attr):
    """Set the active color attribute (what painting and tools target)."""
    try:
        color_attributes.active_color = attr
    except (AttributeError, TypeError):
        try:
            color_attributes.active_color_index = _color_attr_index(color_attributes, attr)
        except (AttributeError, TypeError):
            pass


def _write_channel(temp_attr, source_attr, channel):
    """Fill *temp_attr* with grayscale = source's *channel*, and cache it."""
    src = bulk_get_colors(source_attr)
    ch = _CHANNEL_INDEX[channel]
    gray = np.ascontiguousarray(src[:, ch])
    out = np.empty_like(src)
    out[:, 0] = gray
    out[:, 1] = gray
    out[:, 2] = gray
    out[:, 3] = 1.0
    bulk_set_colors(temp_attr, out)
    return hash(gray.tobytes())


def _setup_channel_preview(context, channel):
    """Show *channel* as grayscale on the active mesh via a temp render attribute.

    The user's own color attribute stays the *active* one (so painting and the
    HUE tools keep targeting it); the temporary grayscale attribute is only set
    as the *render* color attribute, which is what Solid shading displays.
    """
    settings = context.scene.hue_display_settings
    obj = context.active_object
    if obj is None or obj.type != "MESH":
        return

    color_attributes = obj.data.color_attributes
    temp_name = settings.channel_preview_attr

    # Reuse the captured source if this object is already being previewed;
    # otherwise tear down any previous preview and capture the current source.
    if settings.channel_preview_object == obj.name and settings.channel_preview_source:
        source = color_attributes.get(settings.channel_preview_source)
    else:
        _teardown_channel_preview(context)
        source = color_attributes.active_color or get_active_color_attribute(obj)
        color_attributes = obj.data.color_attributes
        settings.channel_preview_source = source.name
        settings.channel_preview_object = obj.name

    if source is None or source.name == temp_name:
        return

    temp = color_attributes.get(temp_name)
    if temp is not None and (temp.domain != source.domain or temp.data_type != source.data_type):
        color_attributes.remove(temp)
        temp = None
    if temp is None:
        temp = color_attributes.new(name=temp_name, type=source.data_type, domain=source.domain)

    _sync_cache[obj.name] = _write_channel(temp, source, channel)

    # Keep the user's attribute active for editing; display the temp attribute.
    _set_active_color(color_attributes, source)
    _set_render_color(color_attributes, temp)


def _teardown_channel_preview(context):
    """Remove the temp attribute everywhere and restore the source as render."""
    settings = context.scene.hue_display_settings
    temp_name = settings.channel_preview_attr
    src_name = settings.channel_preview_source
    obj_name = settings.channel_preview_object

    for obj in context.scene.objects:
        if obj.type != "MESH":
            continue
        color_attributes = obj.data.color_attributes
        temp = color_attributes.get(temp_name)
        if temp is not None:
            color_attributes.remove(temp)
        if obj.name == obj_name and src_name:
            source = color_attributes.get(src_name)
            if source is not None:
                _set_active_color(color_attributes, source)
                _set_render_color(color_attributes, source)

    settings.channel_preview_source = ""
    settings.channel_preview_object = ""
    _sync_cache.clear()


# ---------------------------------------------------------------------------
# Live update handler
# ---------------------------------------------------------------------------

@bpy.app.handlers.persistent
def _channel_preview_sync(scene, depsgraph=None):
    """Re-derive the temp grayscale attribute whenever its source changes."""
    global _syncing
    if _syncing:
        return
    settings = getattr(scene, "hue_display_settings", None)
    if settings is None or settings.display_mode not in _CHANNEL_MODES:
        return

    obj = bpy.data.objects.get(settings.channel_preview_object)
    if obj is None or obj.type != "MESH":
        return

    color_attributes = obj.data.color_attributes
    source = color_attributes.get(settings.channel_preview_source)
    temp = color_attributes.get(settings.channel_preview_attr)
    if source is None or temp is None or source == temp:
        return

    try:
        src = bulk_get_colors(source)
        gray = np.ascontiguousarray(src[:, _CHANNEL_INDEX[settings.display_mode]])
        checksum = hash(gray.tobytes())
        if _sync_cache.get(obj.name) == checksum:
            return  # Source unchanged — skip the write (and the feedback loop).
        _sync_cache[obj.name] = checksum

        out = np.empty_like(src)
        out[:, 0] = gray
        out[:, 1] = gray
        out[:, 2] = gray
        out[:, 3] = 1.0

        _syncing = True
        bulk_set_colors(temp, out)
        obj.data.update()
    except (ReferenceError, RuntimeError):
        pass
    finally:
        _syncing = False


def add_depsgraph_handler():
    if _channel_preview_sync not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_channel_preview_sync)


def remove_depsgraph_handler():
    if _channel_preview_sync in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_channel_preview_sync)


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

class HUE_OT_display_vertex_colors(BaseOperator):
    """Toggles vertex color display mode in the viewport"""

    bl_label = "Display Vertex Colors"
    bl_idname = "hue.display_vertex_colors"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        update_display(context)
        return {"FINISHED"}


class HUE_OT_enable_rgb_display(BaseOperator):
    bl_label = "Enable Attribute View"
    bl_description = f"Switches the viewport to show vertex colors (RGB mode), the same as clicking RGB in the {HUE_PT_display_settings_panel.bl_label} panel"
    bl_idname = "hue.enable_rgb_display"
    bl_options = {'REGISTER'}

    def execute(self, context):
        settings = context.scene.hue_display_settings
        # Find a 3D viewport and apply with a proper context so the
        # display_mode update callback can set shading correctly.
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                with context.temp_override(area=area, space_data=area.spaces.active):
                    settings.display_mode = "RGB"
                break
        else:
            # No 3D viewport visible — set the mode anyway for when one opens.
            settings.display_mode = "RGB"
        return {"FINISHED"}
