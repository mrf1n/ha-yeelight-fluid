"""Light platform for Yeelight Lights (BLE)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ATTR_HS_COLOR,
    ATTR_TRANSITION,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import YeelightBleConfigEntry
from .const import (
    COLOR_MODE_CT,
    COLOR_MODE_EFFECT,
    DIRECTIONS,
    EFFECT_CUSTOM,
    EFFECT_MUSIC,
    MUSIC_EFFECT_IDS,
    SPEED_MAX,
    SPEED_MIN,
    TRANSITION_MS,
)
from .coordinator import YeelightBleCoordinator
from .effects import EffectCatalog
from .entity import YeelightBleEntity, handle_errors


async def async_setup_entry(
    hass: HomeAssistant,
    entry: YeelightBleConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    async_add_entities([YeelightBleLight(coordinator)])

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_SET_EFFECT,
        {
            vol.Required("effect"): cv.string,
            vol.Optional("speed"): vol.All(
                vol.Coerce(int), vol.Range(min=SPEED_MIN, max=SPEED_MAX)
            ),
            vol.Optional("colors"): vol.All(
                cv.ensure_list,
                [vol.All(vol.ExactSequence((cv.byte, cv.byte, cv.byte)), vol.Coerce(tuple))],
            ),
            vol.Optional("direction"): vol.In(DIRECTIONS),
        },
        "async_set_effect",
    )


SERVICE_SET_EFFECT = "set_effect"


class YeelightBleLight(YeelightBleEntity, LightEntity):
    """Main light entity."""

    _attr_translation_key = "light"
    _attr_supported_features = LightEntityFeature.EFFECT | LightEntityFeature.TRANSITION

    def __init__(self, coordinator: YeelightBleCoordinator) -> None:
        super().__init__(coordinator, "light")
        product = coordinator.product
        self._catalog = EffectCatalog(product, coordinator.device)
        self._attr_supported_color_modes = (
            {ColorMode.HS, ColorMode.COLOR_TEMP} if product.supports_color_temp else {ColorMode.HS}
        )
        self._attr_min_color_temp_kelvin = product.min_kelvin
        self._attr_max_color_temp_kelvin = product.max_kelvin
        self._attr_effect_list = [*self._catalog.names, EFFECT_MUSIC]

    # State ------------------------------------------------------------ #
    @property
    def is_on(self) -> bool | None:
        return self._device.is_on

    @property
    def brightness(self) -> int | None:
        bright = self._device.state.get("bright")
        if bright is None:
            return None
        return max(1, round(int(bright) * 255 / 100))

    @property
    def color_mode(self) -> ColorMode:
        if (
            ColorMode.COLOR_TEMP in self.supported_color_modes
            and self._device.state.get("color_mode") == COLOR_MODE_CT
        ):
            return ColorMode.COLOR_TEMP
        return ColorMode.HS

    @property
    def hs_color(self) -> tuple[float, float] | None:
        hue = self._device.state.get("hue")
        sat = self._device.state.get("sat")
        if hue is None or sat is None:
            return None
        return (float(hue), float(sat))

    @property
    def color_temp_kelvin(self) -> int | None:
        ct = self._device.state.get("ct")
        return int(ct) if ct else None

    @property
    def effect(self) -> str | None:
        device = self._device
        if device.music_mode.get("on"):
            return EFFECT_MUSIC
        if device.state.get("color_mode") != COLOR_MODE_EFFECT:
            return None
        if device.effect_id in MUSIC_EFFECT_IDS:
            return EFFECT_MUSIC
        if device.effect_id:
            mode = self._catalog.by_firmware_id(device.effect_id)
            if mode:
                return mode.name
        if device.custom_id:
            return EFFECT_CUSTOM
        return None

    # Commands --------------------------------------------------------- #
    @handle_errors
    async def async_turn_on(self, **kwargs: Any) -> None:
        device = self._device
        ms = int(kwargs[ATTR_TRANSITION] * 1000) if ATTR_TRANSITION in kwargs else TRANSITION_MS

        if not device.is_on:
            await device.turn_on(ms)

        if ATTR_BRIGHTNESS in kwargs:
            await device.set_brightness(max(1, round(kwargs[ATTR_BRIGHTNESS] * 100 / 255)))

        if ATTR_EFFECT in kwargs:
            effect = kwargs[ATTR_EFFECT]
            if effect == EFFECT_MUSIC:
                await device.set_music_mode(True)
            else:
                if device.music_mode.get("on"):
                    await device.set_music_mode(False)
                mode = self._catalog.by_name(effect)
                if mode is not None:
                    await self._catalog.apply(mode)
        elif ATTR_HS_COLOR in kwargs:
            hue, sat = kwargs[ATTR_HS_COLOR]
            await self._leave_music()
            await device.set_hs(round(hue), round(sat), ms)
        elif (
            ATTR_COLOR_TEMP_KELVIN in kwargs and ColorMode.COLOR_TEMP in self.supported_color_modes
        ):
            await self._leave_music()
            await device.set_color_temp(kwargs[ATTR_COLOR_TEMP_KELVIN], ms)

    async def _leave_music(self) -> None:
        if self._device.music_mode.get("on"):
            await self._device.set_music_mode(False)

    @handle_errors
    async def async_turn_off(self, **kwargs: Any) -> None:
        ms = int(kwargs[ATTR_TRANSITION] * 1000) if ATTR_TRANSITION in kwargs else TRANSITION_MS
        await self._device.turn_off(ms)

    @handle_errors
    async def async_set_effect(
        self,
        effect: str,
        speed: int | None = None,
        colors: list[tuple[int, int, int]] | None = None,
        direction: str | None = None,
    ) -> None:
        """Service: apply an effect with options."""
        mode = self._catalog.by_key(effect) or self._catalog.by_name(effect)
        if mode is None:
            raise ServiceValidationError(f"Unknown effect: {effect}")
        if not self._device.is_on:
            await self._device.turn_on()
        await self._leave_music()
        await self._catalog.apply(mode, speed=speed, colors=colors, direction=direction)
