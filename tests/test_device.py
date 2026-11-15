"""Request handling of the device object (no Bluetooth)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from bleak.backends.device import BLEDevice
import pytest

from custom_components.yeelight_lights_ble.device import (
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
        pytest.raises(YeelightBleError, match="Timeout waiting for set_power"),
    ):
        await device.request("set_power", ["on", "smooth", 500])
    assert once.await_count == 2
