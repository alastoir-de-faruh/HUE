# Copyright (C) 2026 Clonephaze
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
import bpy.utils.previews

_preset_previews = {}

SWATCH_COLS = 8
_SWATCH_SIZE = 32

DEFAULT_PALETTE_NAME = "Default_Palette"
_DEFAULT_COLORS = [
    (1.0, 0.0, 0.0),
    (1.0, 0.5, 0.0),
    (1.0, 1.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 1.0, 1.0),
    (0.0, 0.0, 1.0),
    (0.5, 0.0, 1.0),
    (1.0, 0.0, 0.5),
    (1.0, 1.0, 1.0),
    (0.75, 0.75, 0.75),
    (0.25, 0.25, 0.25),
    (0.0, 0.0, 0.0),
]


def _linear_to_srgb(c):
    """Convert a single linear-space float to sRGB."""
    if c <= 0.0031308:
        return c * 12.92
    return 1.055 * (c ** (1.0 / 2.4)) - 0.055


def get_color_icon(r, g, b, color_space="sRGB"):
    """Get or create a colored swatch icon, fully in-memory.

    *color_space* selects how the stored RGB numbers are rendered. "sRGB"
    shows them directly (they are display-referred already); "LINEAR" treats
    them as scene-linear and applies the linear->sRGB transform, matching how
    a Linear color widget shows the same numbers. Display only — the stored
    palette color is never modified.
    """
    if "main" not in _preset_previews:
        _preset_previews["main"] = bpy.utils.previews.new()
    pcoll = _preset_previews["main"]

    if color_space == "LINEAR":
        r, g, b = _linear_to_srgb(r), _linear_to_srgb(g), _linear_to_srgb(b)

    ri, gi, bi = int(r * 255), int(g * 255), int(b * 255)
    key = f"hue_{ri:03d}_{gi:03d}_{bi:03d}"

    if key not in pcoll:
        icon = pcoll.new(key)
        icon.icon_size = (_SWATCH_SIZE, _SWATCH_SIZE)
        pixel = [r, g, b, 1.0]
        icon.icon_pixels_float = pixel * (_SWATCH_SIZE * _SWATCH_SIZE)

    return pcoll[key].icon_id


# ---------------------------------------------------------------------------
# Persistent palette library access
# ---------------------------------------------------------------------------
#
# Palettes are stored on the add-on preferences (see preferences.HUEPalette),
# so they persist across sessions and are shared by every .blend file.


def _addon_package():
    """Root add-on package name (e.g. "HUE"), used as the preferences key."""
    return __package__.split(".")[0]


def get_prefs():
    """Return the add-on preferences, or None if unavailable."""
    try:
        return bpy.context.preferences.addons[_addon_package()].preferences
    except (KeyError, AttributeError):
        return None


def get_palettes():
    """Return the persistent palette collection, or None."""
    prefs = get_prefs()
    return prefs.palettes if prefs is not None else None


def get_active_fill_palette(scene):
    """Return the palette currently selected by the Fill tool, or None."""
    prefs = get_prefs()
    if prefs is None or len(prefs.palettes) == 0:
        return None
    fill = getattr(scene, "hue_simple_fill_tool", None)
    if fill is None:
        return None
    idx = max(0, min(fill.active_palette_index, len(prefs.palettes) - 1))
    return prefs.palettes[idx]


def cleanup_previews():
    """Remove preview collections. Called from ui unregister."""
    for pcoll in _preset_previews.values():
        bpy.utils.previews.remove(pcoll)
    _preset_previews.clear()


@bpy.app.handlers.persistent
def _ensure_library(_=None):
    """Make sure at least the default palette exists and tool indices are valid.

    Registered as a load_post handler and called once from register().
    """
    prefs = get_prefs()
    if prefs is None:
        return

    if len(prefs.palettes) == 0:
        pal = prefs.palettes.add()
        pal.name = DEFAULT_PALETTE_NAME
        for color in _DEFAULT_COLORS:
            sw = pal.swatches.add()
            sw.color = (color[0], color[1], color[2], 1.0)

    last = len(prefs.palettes) - 1
    scene = bpy.context.scene
    fill = getattr(scene, "hue_simple_fill_tool", None)
    if fill is not None and fill.active_palette_index > last:
        fill.active_palette_index = 0
    random_tool = getattr(scene, "hue_random_color_tool", None)
    if random_tool is not None and random_tool.random_palette_index > last:
        random_tool.random_palette_index = 0


def register_handlers():
    """Register load_post handler and schedule initial library check."""
    bpy.app.handlers.load_post.append(_ensure_library)
    bpy.app.timers.register(_ensure_library, first_interval=0)


def unregister_handlers():
    """Remove load_post handler."""
    if _ensure_library in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_ensure_library)
