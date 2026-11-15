"""Select platform: effect and direction."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import YeelightBleConfigEntry
from .const import COLOR_MODE_EFFECT, DIRECTIONS
from .coordinator import YeelightBleCoordinator
from .effects import EffectCatalog
from .entity import YeelightBleEntity, handle_errors


async def async_setup_entry(
    hass: HomeAssistant,
    entry: YeelightBleConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    async_add_entities([EffectSelect(coordinator), EffectDirectionSelect(coordinator)])


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
