"""Yeelight Fluid BLE integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_IDLE_TIMEOUT,
    CONF_KEEP_CONNECTED,
    CONF_KEY,
    CONF_POLL_INTERVAL,
    CONF_PRODUCT_ID,
    DEFAULT_IDLE_TIMEOUT,
    DEFAULT_KEEP_CONNECTED,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    product_for,
)
from .coordinator import YeelightFluidCoordinator
from .device import YeelightFluidDevice, YeelightFluidError

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


@dataclass
class RuntimeData:
    """Runtime data stored on the config entry."""

    coordinator: YeelightFluidCoordinator


type YeelightFluidConfigEntry = ConfigEntry[RuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: YeelightFluidConfigEntry) -> bool:
    """Set up from a config entry."""
    address: str = entry.data[CONF_ADDRESS]
    ble_device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
    if ble_device is None:
        raise ConfigEntryNotReady(f"Could not find Yeelight device {address}")

    product = product_for(entry.data.get(CONF_PRODUCT_ID), ble_device.name)
    key_hex: str | None = entry.data.get(CONF_KEY)
    options = entry.options
    keep_connected = options.get(CONF_KEEP_CONNECTED, DEFAULT_KEEP_CONNECTED)

    device = YeelightFluidDevice(
        ble_device,
        product_id=entry.data.get(CONF_PRODUCT_ID, product.product_id),
        key=bytes.fromhex(key_hex) if key_hex else None,
        keep_connected=keep_connected,
        idle_timeout=options.get(CONF_IDLE_TIMEOUT, DEFAULT_IDLE_TIMEOUT),
    )

    try:
        await device.update()
    except YeelightFluidError as err:
        await device.disconnect()
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = YeelightFluidCoordinator(
        hass,
        entry,
        device,
        product,
        options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
    )
    entry.runtime_data = RuntimeData(coordinator)

    @callback
    def _async_on_advertisement(
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        device.set_ble_device(service_info.device, service_info.rssi)

    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            _async_on_advertisement,
            bluetooth.BluetoothCallbackMatcher(address=address, connectable=True),
            bluetooth.BluetoothScanningMode.PASSIVE,
        )
    )
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: YeelightFluidConfigEntry) -> None:
    """Reload on options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: YeelightFluidConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.coordinator.async_shutdown()
    return unload_ok
