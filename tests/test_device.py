"""Request handling of the device object (no Bluetooth)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from bleak.backends.device import BLEDevice
import pytest

from custom_components.yeelight_lights_ble.device import (
    YeelightBleConnectionError,
    YeelightBleDevice,
    YeelightBleError,
    YeelightBleTimeout,
)

from .conftest import ADDRESS, NAME


def _device() -> YeelightBleDevice:
    return YeelightBleDevice(BLEDevice(ADDRESS, NAME, {}), 0x2804)


async def test_props_notification_completes_request() -> None:
    """set_power from off may be answered only by a props notification."""
    device = _device()
    fut = asyncio.get_running_loop().create_future()
    device._pending[7] = fut
    device._confirm[7] = {"power": "on"}

    device._on_ctrl_notify(None, bytearray(b'{"method":"props","params":{"bright":"40"}}\r\n'))
    assert not fut.done()

    device._on_ctrl_notify(None, bytearray(b'{"method":"props","params":{"power":"on"}}\r\n'))
    assert fut.result() == ["ok"]
    assert device.state["power"] == "on"
    assert 7 not in device._pending
    assert 7 not in device._confirm


async def test_timeout_reconnects_and_retries_once() -> None:
    device = _device()
    once = AsyncMock(side_effect=[YeelightBleTimeout("Timeout waiting for set_power"), ["ok"]])
    with (
        patch.object(device, "_request_once", once),
        patch.object(device, "_disconnect", AsyncMock()) as disconnect,
        patch("custom_components.yeelight_lights_ble.device.RECONNECT_DELAY", 0),
    ):
        assert await device.request("set_power", ["on", "smooth", 500]) == ["ok"]
    assert once.await_count == 2
    disconnect.assert_awaited_once()


async def test_second_timeout_is_reported() -> None:
    device = _device()
    once = AsyncMock(side_effect=YeelightBleTimeout("Timeout waiting for set_power"))
    with (
        patch.object(device, "_request_once", once),
        patch.object(device, "_disconnect", AsyncMock()),
        patch("custom_components.yeelight_lights_ble.device.RECONNECT_DELAY", 0),
        pytest.raises(YeelightBleError, match="Timeout waiting for set_power"),
    ):
        await device.request("set_power", ["on", "smooth", 500])
    assert once.await_count == 2


async def test_dropped_link_is_retried() -> None:
    device = _device()
    once = AsyncMock(
        side_effect=[YeelightBleConnectionError("Setup failed: Not Connected"), ["ok"]]
    )
    with (
        patch.object(device, "_request_once", once),
        patch.object(device, "_disconnect", AsyncMock()),
        patch("custom_components.yeelight_lights_ble.device.RECONNECT_DELAY", 0),
    ):
        assert await device.request("get_prop", ["power"]) == ["ok"]
    assert once.await_count == 2


async def test_turn_on_falls_back_to_set_scene() -> None:
    """While off the lights may ignore set_power; brightness turns them on."""
    device = _device()
    device.state["bright"] = 40
    calls = []

    async def fake_request(method, params=None, confirm=None, retry=True):
        calls.append((method, params, retry))
        if method == "set_power":
            raise YeelightBleTimeout("Timeout waiting for set_power")
        return ["ok"]

    with patch.object(device, "request", side_effect=fake_request):
        await device.turn_on()
    assert calls == [
        ("set_power", ["on", "smooth", 500], False),
        ("set_scene", ["bright", 40, 0], True),
    ]
    assert device.state["power"] == "on"


async def test_request_uses_one_write_with_large_mtu() -> None:
    """Each command goes out in a single write when the MTU allows, like the app."""
    device = _device()
    client = AsyncMock()
    client.is_connected = True
    client.mtu_size = 247
    device._client = client

    async def answer(_char, data, response=True):
        device._on_ctrl_notify(None, bytearray(b'{"id":1,"result":["ok"]}\r\n'))

    client.write_gatt_char.side_effect = answer
    assert await device.request("set_power", ["on", "smooth", 500]) == ["ok"]
    assert client.write_gatt_char.await_count == 1
