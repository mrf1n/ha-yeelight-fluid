"""Fixtures for Yeelight Fluid tests."""

from __future__ import annotations

from unittest.mock import patch

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
import pytest

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

ADDRESS = "AA:BB:CC:DD:EE:FF"
NAME = "YLBT_CHRI_EEFF"
KEY_HEX = "000102030405060708090a0b"
MANUFACTURER_DATA = bytes.fromhex("042801010700ffeeddccbbaa01000000")


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations."""
    return


@pytest.fixture(autouse=True)
def skip_bluetooth_setup(hass):
    """Pretend bluetooth dependencies are loaded."""
    hass.config.components.add("bluetooth")
    hass.config.components.add("bluetooth_adapters")


def make_service_info() -> BluetoothServiceInfoBleak:
    device = BLEDevice(ADDRESS, NAME, {})
    adv = AdvertisementData(
        local_name=NAME,
        manufacturer_data={0x0164: MANUFACTURER_DATA},
        service_data={},
        service_uuids=["0000fe87-0000-1000-8000-00805f9b34fb"],
        tx_power=None,
        rssi=-40,
        platform_data=(),
    )
    return BluetoothServiceInfoBleak(
        name=NAME,
        address=ADDRESS,
        rssi=-40,
        manufacturer_data=adv.manufacturer_data,
        service_data={},
        service_uuids=adv.service_uuids,
        source="local",
        device=device,
        advertisement=adv,
        connectable=True,
        time=0,
        tx_power=None,
    )


@pytest.fixture
def service_info() -> BluetoothServiceInfoBleak:
    return make_service_info()


@pytest.fixture
def mock_ble_lookup(service_info):
    """Patch BLEDevice lookups."""
    with (
        patch(
            "homeassistant.components.bluetooth.async_ble_device_from_address",
            return_value=service_info.device,
        ),
        patch(
            "custom_components.yeelight_fluid_ble.config_flow.async_ble_device_from_address",
            return_value=service_info.device,
        ),
        patch(
            "custom_components.yeelight_fluid_ble.config_flow.async_discovered_service_info",
            return_value=[service_info],
        ),
        patch(
            "homeassistant.components.bluetooth.async_register_callback",
            return_value=lambda: None,
        ),
    ):
        yield
