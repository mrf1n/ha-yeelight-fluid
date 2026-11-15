"""Coordinator for Yeelight Lights (BLE)."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, ProductInfo
from .device import YeelightBleDevice, YeelightBleError

_LOGGER = logging.getLogger(__name__)


class YeelightBleCoordinator(DataUpdateCoordinator[None]):
    """Polls state when not kept connected; relays push updates otherwise."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        device: YeelightBleDevice,
        product: ProductInfo,
        poll_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{device.address}",
            update_interval=timedelta(seconds=poll_interval),
        )
        self.device = device
        self.product = product
        self._unsub_device = device.register_callback(self._on_device_update)

    @callback
    def _on_device_update(self) -> None:
        self.async_update_listeners()

    async def _async_update_data(self) -> None:
        if self.device.keep_connected and self.device.connected:
            return
        try:
            await self.device.update()
        except YeelightBleError as err:
            raise UpdateFailed(str(err)) from err

    async def async_shutdown(self) -> None:
        self._unsub_device()
        await super().async_shutdown()
        await self.device.disconnect()
