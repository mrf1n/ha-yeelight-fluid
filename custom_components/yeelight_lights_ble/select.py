"""Select platform: effect, direction, power-on behavior and music options."""

from __future__ import annotations

import colorsys

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import YeelightBleConfigEntry
from .const import COLOR_MODE_EFFECT, COLOR_MODE_HSV, DIRECTIONS, POWER_ON_BEHAVIORS
from .coordinator import YeelightBleCoordinator
from .custom import effect_controls
from .effects import EffectCatalog
from .entity import YeelightBleEntity, handle_errors
from .music import CUSTOM_SCHEME, MUSIC_SCHEMES, RHYTHM_EFFECTS, SCHEMES_BY_KEY
from .protocol import argb_to_rgb, rgb_to_argb


async def async_setup_entry(
    hass: HomeAssistant,
    entry: YeelightBleConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        [
            EffectSelect(coordinator),
            RecentColorSelect(coordinator),
            EffectDirectionSelect(coordinator),
            PowerOnBehaviorSelect(coordinator),
            MusicEffectSelect(coordinator),
            MusicSchemeSelect(coordinator),
        ]
    )


class EffectSelect(YeelightBleEntity, SelectEntity):
    """Predefined effect picker (keys are translatable)."""

    _attr_translation_key = "effect"

    def __init__(self, coordinator: YeelightBleCoordinator) -> None:
        super().__init__(coordinator, "effect")
        self._catalog = EffectCatalog(coordinator.product, coordinator.device)

    @property
    def options(self) -> list[str]:
        return [m.key for m in self._catalog.modes]

    @property
    def current_option(self) -> str | None:
        if self._device.state.get("color_mode") != COLOR_MODE_EFFECT:
            return None
        mode = self._catalog.current()
        return mode.key if mode else None

    @handle_errors
    async def async_select_option(self, option: str) -> None:
        mode = self._catalog.by_key(option)
        if mode is None:
            return
        if self._device.music_mode.get("on"):
            await self._device.set_music_mode(False)
        if not self._device.is_on:
            await self._device.turn_on()
        await self._catalog.apply(mode)


class EffectDirectionSelect(YeelightBleEntity, SelectEntity):
    """Direction for effects that support it."""

    _attr_translation_key = "effect_direction"
    _attr_options = list(DIRECTIONS)
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: YeelightBleCoordinator) -> None:
        super().__init__(coordinator, "effect_direction")
        self._catalog = EffectCatalog(coordinator.product, coordinator.device)

    @property
    def available(self) -> bool:
        """Only for Meteor, Waves, and custom effects with Translation or Stack."""
        return super().available and effect_controls(self._device, self._catalog)[1]

    @property
    def current_option(self) -> str | None:
        value = self._device.effect_config.get("direction")
        if value is None:
            return None
        try:
            return DIRECTIONS[int(value)]
        except (IndexError, ValueError):
            return None

    @handle_errors
    async def async_select_option(self, option: str) -> None:
        await self._device.update_effect(direction=DIRECTIONS.index(option))


class PowerOnBehaviorSelect(YeelightBleEntity, SelectEntity):
    """State the lights take when mains power returns."""

    _attr_translation_key = "power_on_behavior"
    _attr_options = list(POWER_ON_BEHAVIORS)
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: YeelightBleCoordinator) -> None:
        super().__init__(coordinator, "power_on_behavior")

    @property
    def current_option(self) -> str | None:
        value = self._device.state.get("init_power_opt")
        return next((k for k, v in POWER_ON_BEHAVIORS.items() if v == value), None)

    @handle_errors
    async def async_select_option(self, option: str) -> None:
        await self._device.set_power_on_behavior(POWER_ON_BEHAVIORS[option])


class MusicEffectSelect(YeelightBleEntity, SelectEntity, RestoreEntity):
    """Rhythm effect used by music mode."""

    _attr_translation_key = "music_effect"
    _attr_options = list(RHYTHM_EFFECTS)

    def __init__(self, coordinator: YeelightBleCoordinator) -> None:
        super().__init__(coordinator, "music_effect")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state in RHYTHM_EFFECTS:
            self._device.music_effect = last.state

    @property
    def current_option(self) -> str | None:
        return self._device.music_effect

    @handle_errors
    async def async_select_option(self, option: str) -> None:
        await self._device.set_music_options(effect=option)


class MusicSchemeSelect(YeelightBleEntity, SelectEntity, RestoreEntity):
    """Colour scheme used by music mode; "custom" comes from the set_music_mode action."""

    _attr_translation_key = "music_scheme"
    _attr_options = [s.key for s in MUSIC_SCHEMES] + [CUSTOM_SCHEME]

    def __init__(self, coordinator: YeelightBleCoordinator) -> None:
        super().__init__(coordinator, "music_scheme")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is None:
            return
        device = self._device
        if last.state in SCHEMES_BY_KEY:
            device.music_scheme = last.state
            device.music_colors = SCHEMES_BY_KEY[last.state].colors
        elif last.state == CUSTOM_SCHEME and (colors := last.attributes.get("colors")):
            try:
                device.music_colors = tuple(rgb_to_argb(tuple(c)) for c in colors)
            except (TypeError, ValueError):
                return
            device.music_scheme = CUSTOM_SCHEME

    @property
    def current_option(self) -> str | None:
        return self._device.music_scheme

    @property
    def extra_state_attributes(self) -> dict[str, list[list[int]]]:
        return {"colors": [list(argb_to_rgb(c)) for c in self._device.music_colors]}

    @handle_errors
    async def async_select_option(self, option: str) -> None:
        if option == CUSTOM_SCHEME:
            return  # custom colours come from the set_music_mode action
        await self._device.set_music_options(scheme=option)


def _hs_to_hex(hue: int, sat: int) -> str:
    r, g, b = colorsys.hsv_to_rgb(hue / 360, sat / 100, 1.0)
    return f"#{round(r * 255):02X}{round(g * 255):02X}{round(b * 255):02X}"


class RecentColorSelect(YeelightBleEntity, SelectEntity, RestoreEntity):
    """Last pure colours picked through Home Assistant; choosing one applies it again."""

    _attr_translation_key = "recent_colors"

    def __init__(self, coordinator: YeelightBleCoordinator) -> None:
        super().__init__(coordinator, "recent_colors")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is None or self._device.recent_colors:
            return
        try:
            colors = [(int(h), int(s)) for h, s in last.attributes.get("hs_colors") or []]
        except (TypeError, ValueError):
            return
        for hue, sat in reversed(colors):
            self._device.remember_color(hue, sat)

    @property
    def options(self) -> list[str]:
        return [_hs_to_hex(h, s) for h, s in self._device.recent_colors]

    @property
    def current_option(self) -> str | None:
        state = self._device.state
        if state.get("color_mode") != COLOR_MODE_HSV:
            return None
        try:
            current = (int(state["hue"]), int(state["sat"]))
        except (KeyError, TypeError, ValueError):
            return None
        return _hs_to_hex(*current) if current in self._device.recent_colors else None

    @property
    def extra_state_attributes(self) -> dict[str, list[list[int]]]:
        return {"hs_colors": [[h, s] for h, s in self._device.recent_colors]}

    @handle_errors
    async def async_select_option(self, option: str) -> None:
        for hue, sat in self._device.recent_colors:
            if _hs_to_hex(hue, sat) == option:
                device = self._device
                if device.music_mode.get("on"):
                    await device.set_music_mode(False)
                if not device.is_on:
                    await device.turn_on()
                await device.set_hs(hue, sat)
                return
