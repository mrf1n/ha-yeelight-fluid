"""DIY Graffiti ("Custom") mode and which effect controls apply right now.

Matches the official app: the custom effect is firmware effect 36 with one
colour per LED in "data" and an optional dynamic effect ("mixer").
"""

from __future__ import annotations

import colorsys
import random
from typing import TYPE_CHECKING, Final

from .const import COLOR_MODE_EFFECT

if TYPE_CHECKING:
    from .device import YeelightBleDevice
    from .effects import EffectCatalog

CUSTOM_EFFECT_ID: Final = 36

# Dynamic effect -> firmware "mixer" value
DYNAMIC_EFFECTS: Final = {
    "none": 0,
    "translation": 2,
    "breath": 3,
    "flashing": 4,
    "stack": 5,
}
DEFAULT_DYNAMIC_EFFECT: Final = "none"
# dynamic effects that move along the string and so have a direction
DIRECTIONAL_MIXERS: Final = frozenset({DYNAMIC_EFFECTS["translation"], DYNAMIC_EFFECTS["stack"]})

# used when the device has not reported its LED count
DEFAULT_LED_COUNT: Final = 100


def pattern_colors(colors: list[int], count: int) -> list[int]:
    """Repeat a list of colours along `count` LEDs."""
    return [colors[i % len(colors)] for i in range(count)]


def random_colors(count: int) -> list[int]:
    """One random, fully saturated ARGB colour per LED."""
    out = []
    for _ in range(count):
        r, g, b = colorsys.hsv_to_rgb(random.random(), 1.0, 1.0)
        out.append(0xFF000000 | round(r * 255) << 16 | round(g * 255) << 8 | round(b * 255))
    return out


def effect_controls(device: YeelightBleDevice, catalog: EffectCatalog) -> tuple[bool, bool]:
    """Whether (speed, direction) apply to what the lights show now.

    Speed: predefined effects, and the custom effect with a dynamic effect.
    Direction: predefined effects that have one (Meteor, Waves), and the
    custom effect with Translation or Stack.
    """
    if device.music_mode.get("on") or device.state.get("color_mode") != COLOR_MODE_EFFECT:
        return False, False
    if device.effect_id == CUSTOM_EFFECT_ID:
        try:
            mixer = int(device.effect_config.get("mixer") or 0)
        except (TypeError, ValueError):
            mixer = 0
        return mixer != 0, mixer in DIRECTIONAL_MIXERS
    mode = catalog.by_firmware_id(device.effect_id) if device.effect_id else None
    if mode is None:
        return False, False
    return "speed" in mode.capabilities, bool(mode.directions)
