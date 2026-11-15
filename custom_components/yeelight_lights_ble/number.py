"""Number platform: effect speed."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import YeelightBleConfigEntry
from .const import SPEED_MAX, SPEED_MIN
from .coordinator import YeelightBleCoordinator
from .entity import YeelightBleEntity, handle_errors
from .protocol import rate_to_speed, speed_to_rate


async def async_setup_entry(
    hass: HomeAssistant,
    entry: YeelightBleConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([EffectSpeedNumber(entry.runtime_data.coordinator)])


class EffectSpeedNumber(YeelightBleEntity, NumberEntity):
    """Speed of the running effect, in percent (firmware rate 1-255)."""

    _attr_translation_key = "effect_speed"
    _attr_native_min_value = SPEED_MIN
    _attr_native_max_value = SPEED_MAX
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: YeelightBleCoordinator) -> None:
        super().__init__(coordinator, "effect_speed")

    @property
    def native_value(self) -> float | None:
        rate = self._device.effect_config.get("rate")
        return float(rate_to_speed(rate)) if rate is not None else None

    @handle_errors
    async def async_set_native_value(self, value: float) -> None:
        await self._device.update_effect(rate=speed_to_rate(value))
