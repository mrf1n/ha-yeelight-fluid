"""Diagnostics for Yeelight Lights (BLE)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import YeelightBleConfigEntry
from .const import CONF_KEY

TO_REDACT = {CONF_KEY}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: YeelightBleConfigEntry
) -> dict[str, Any]:
    device = entry.runtime_data.coordinator.device
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "options": dict(entry.options),
        "connected": device.connected,
        "authenticated": device.authenticated,
        "rssi": device.rssi,
        "state": device.state,
        "effect_id": device.effect_id,
        "custom_id": device.custom_id,
        "effect_config": device.effect_config,
    }
