"""Constants for the Yeelight Lights (BLE) integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

DOMAIN: Final = "yeelight_lights_ble"
MANUFACTURER: Final = "Yeelight"

CONF_KEY: Final = "key"
CONF_PRODUCT_ID: Final = "product_id"
CONF_KEEP_CONNECTED: Final = "keep_connected"
CONF_IDLE_TIMEOUT: Final = "idle_timeout"
CONF_POLL_INTERVAL: Final = "poll_interval"

DEFAULT_KEEP_CONNECTED: Final = False
DEFAULT_IDLE_TIMEOUT: Final = 60  # seconds
DEFAULT_POLL_INTERVAL: Final = 300  # seconds, only used when not kept connected

# Bluetooth advertisement
YEELIGHT_MANUFACTURER_ID: Final = 0x0164
NAME_PREFIX: Final = "YLBT_"

# yeePid = YEE_PID_BASE + productId
YEE_PID_BASE: Final = 0x01000000


@dataclass(frozen=True)
class EffectMode:
    """An effect mode as defined in the app's device config."""

    key: str
    name: str
    value: int
    capabilities: tuple[str, ...] = ("speed",)
    directions: tuple[str, ...] = ()
    min_firmware: int = 0


@dataclass(frozen=True)
class ProductInfo:
    """Static description of a supported product."""

    yee_pid: int
    name: str
    name_prefix: str
    effects: tuple[EffectMode, ...] = field(default_factory=tuple)
    # app effect id -> firmware effect id
    effect_mapping: dict[int, int] = field(default_factory=dict)
    supports_color_temp: bool = True
    min_kelvin: int = 2700
    max_kelvin: int = 6500
    per_segment_count: int = 20

    @property
    def product_id(self) -> int:
        return self.yee_pid - YEE_PID_BASE


CHRISTMAS_LIGHTS = ProductInfo(
    yee_pid=16787460,
    name="Christmas String Lights",
    name_prefix="YLBT_CHRI",
    effect_mapping={82: 81},
    supports_color_temp=False,
    effects=(
        EffectMode("warm_glow", "Warm Glow", 97, min_firmware=52),
        EffectMode("snow_white", "Snow White", 98, min_firmware=52),
        EffectMode("candy_cane", "Candy Cane", 99, min_firmware=52),
        EffectMode("christmas", "Christmas", 82),
        EffectMode("halloween", "Halloween", 72),
        EffectMode("valentines_day", "Valentine's Day", 73),
        EffectMode("birthday", "Birthday", 74),
        EffectMode("independence_day", "Independence Day", 80),
        EffectMode("meteor", "Meteor", 47, ("speed", "color"), ("up", "down")),
        EffectMode("waves", "Waves", 42, ("speed", "color"), ("up", "down")),
        EffectMode("rainbow", "Rainbow", 39, ("speed", "color")),
        EffectMode("dream", "Dream", 79),
        EffectMode("starry_sky", "Starry Sky", 5, ("speed", "color")),
        EffectMode("summer", "Summer", 76),
        EffectMode("winter", "Winter", 77),
        EffectMode("warm", "Warm", 78),
        EffectMode("flower_sea", "Flower Sea", 91),
        EffectMode("wonderland", "Wonderland", 94),
        EffectMode("magic", "Magic", 92),
        EffectMode("moonlight", "Moonlight", 93),
        EffectMode("palette", "Palette", 96),
        EffectMode("kaleidoscope", "Kaleidoscope", 95),
        EffectMode("neon", "Neon", 90),
    ),
)

PRODUCTS: Final[dict[int, ProductInfo]] = {
    CHRISTMAS_LIGHTS.product_id: CHRISTMAS_LIGHTS,
}

# Pseudo effects
EFFECT_MUSIC: Final = "Music"
EFFECT_CUSTOM: Final = "Custom"
MUSIC_EFFECT_ID: Final = 44

# color_mode values reported by the device
COLOR_MODE_CT: Final = 2
COLOR_MODE_HSV: Final = 3
COLOR_MODE_EFFECT: Final = 14

DIRECTIONS: Final = ("up", "down")

# init_power_opt / cfg_init_power values
POWER_ON_BEHAVIORS: Final = {"on": 1, "off": 2, "restore": 0}

SPEED_MIN: Final = 1
SPEED_MAX: Final = 100
# firmware effect rate is 1-255; the app's default is 128 (shown as 51 %)
DEFAULT_RATE: Final = 128

TRANSITION_MS: Final = 500


def product_for(product_id: int | None, name: str | None) -> ProductInfo:
    """Return product info by product id, falling back to name prefix."""
    if product_id is not None and product_id in PRODUCTS:
        return PRODUCTS[product_id]
    if name:
        for product in PRODUCTS.values():
            if name.startswith(product.name_prefix):
                return product
    return CHRISTMAS_LIGHTS
