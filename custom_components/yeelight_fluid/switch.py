"""Switch platform: music mode (device microphone)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import YeelightFluidConfigEntry
from .coordinator import YeelightFluidCoordinator
from .entity import YeelightFluidEntity, handle_errors


async def async_setup_entry(
    hass: HomeAssistant,
    entry: YeelightFluidConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([MusicModeSwitch(entry.runtime_data.coordinator)])


class MusicModeSwitch(YeelightFluidEntity, SwitchEntity):
    """Toggle mic music mode."""

    _attr_translation_key = "music_mode"

    def __init__(self, coordinator: YeelightFluidCoordinator) -> None:
        super().__init__(coordinator, "music_mode")

    @property
    def is_on(self) -> bool:
        return bool(self._device.music_mode.get("on"))

    @handle_errors
    async def async_turn_on(self, **kwargs: Any) -> None:
        if not self._device.is_on:
            await self._device.turn_on()
        await self._device.set_music_mode(True)

    @handle_errors
    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._device.set_music_mode(False)
