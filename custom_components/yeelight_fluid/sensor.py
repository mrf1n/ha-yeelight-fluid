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

from . import YeelightFluidConfigEntry
from .coordinator import YeelightFluidCoordinator
from .device import YeelightFluidDevice
from .entity import YeelightFluidEntity


@dataclass(frozen=True, kw_only=True)
class FluidSensorDescription(SensorEntityDescription):
    value_fn: Callable[[YeelightFluidDevice], Any]


SENSORS: tuple[FluidSensorDescription, ...] = (
    FluidSensorDescription(
        key="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.rssi,
    ),
    FluidSensorDescription(
        key="firmware",
        translation_key="firmware",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.state.get("fw_version"),
    ),
    FluidSensorDescription(
        key="strip_length",
        translation_key="strip_length",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.state.get("strip_length"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: YeelightFluidConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    async_add_entities(FluidSensor(coordinator, desc) for desc in SENSORS)


class FluidSensor(YeelightFluidEntity, SensorEntity):
    """Diagnostic sensor."""

    entity_description: FluidSensorDescription

    def __init__(
        self, coordinator: YeelightFluidCoordinator, description: FluidSensorDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self._device)
