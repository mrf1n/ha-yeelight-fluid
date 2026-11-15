"""Number platform: effect speed."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import YeelightFluidConfigEntry
from .const import SPEED_MAX, SPEED_MIN
from .coordinator import YeelightFluidCoordinator
from .entity import YeelightFluidEntity, handle_errors


async def async_setup_entry(
    hass: HomeAssistant,
    entry: YeelightFluidConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([EffectSpeedNumber(entry.runtime_data.coordinator)])


class EffectSpeedNumber(YeelightFluidEntity, NumberEntity):
    """Speed (rate) of the running effect."""

    _attr_translation_key = "effect_speed"
    _attr_native_min_value = SPEED_MIN
    _attr_native_max_value = SPEED_MAX
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: YeelightFluidCoordinator) -> None:
        super().__init__(coordinator, "effect_speed")

    @property
    def native_value(self) -> float | None:
        rate = self._device.effect_config.get("rate")
        return float(rate) if rate is not None else None

    @handle_errors
    async def async_set_native_value(self, value: float) -> None:
        await self._device.update_effect(rate=int(value))
