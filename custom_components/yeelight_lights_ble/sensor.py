"""Diagnostic sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import SIGNAL_STRENGTH_DECIBELS_MILLIWATT, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import YeelightBleConfigEntry
from .coordinator import YeelightBleCoordinator
from .device import YeelightBleDevice
from .entity import YeelightBleEntity


@dataclass(frozen=True, kw_only=True)
class YeelightBleSensorDescription(SensorEntityDescription):
    value_fn: Callable[[YeelightBleDevice], Any]


SENSORS: tuple[YeelightBleSensorDescription, ...] = (
    YeelightBleSensorDescription(
        key="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.rssi,
    ),
    YeelightBleSensorDescription(
        key="firmware",
        translation_key="firmware",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.state.get("fw_version"),
    ),
    YeelightBleSensorDescription(
        key="strip_length",
        translation_key="strip_length",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.state.get("strip_length"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: YeelightBleConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    async_add_entities(YeelightBleSensor(coordinator, desc) for desc in SENSORS)


class YeelightBleSensor(YeelightBleEntity, SensorEntity):
    """Diagnostic sensor."""

    entity_description: YeelightBleSensorDescription

    def __init__(
        self, coordinator: YeelightBleCoordinator, description: YeelightBleSensorDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self._device)
