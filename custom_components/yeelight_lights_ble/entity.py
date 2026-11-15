"""Base entity for Yeelight Lights (BLE)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Coroutine
from functools import wraps
from typing import Any, Concatenate

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import YeelightBleCoordinator
from .device import YeelightBleError


class YeelightBleEntity(CoordinatorEntity[YeelightBleCoordinator]):
    """Common entity base."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: YeelightBleCoordinator, key: str) -> None:
        super().__init__(coordinator)
        device = coordinator.device
        self._device = device
        self._attr_unique_id = f"{device.address}_{key}"
        fw = device.state.get("fw_version")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.address)},
            connections={(dr.CONNECTION_BLUETOOTH, device.address)},
            manufacturer=MANUFACTURER,
            model=coordinator.product.name,
            model_id=str(coordinator.product.yee_pid),
            name=device.name,
            sw_version=str(fw) if fw is not None else None,
        )

    @property
    def available(self) -> bool:
        if self._device.keep_connected:
            return self._device.connected or super().available
        return super().available


def handle_errors[E: YeelightBleEntity, **P](
    func: Callable[Concatenate[E, P], Awaitable[Any]],
) -> Callable[Concatenate[E, P], Coroutine[Any, Any, None]]:
    """Translate device errors into HomeAssistantError."""

    @wraps(func)
    async def wrapper(self: E, *args: P.args, **kwargs: P.kwargs) -> None:
        try:
            await func(self, *args, **kwargs)
        except YeelightBleError as err:
            raise HomeAssistantError(f"{self._device.name}: {err}") from err

    return wrapper
