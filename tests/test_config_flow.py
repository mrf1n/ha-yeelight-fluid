"""Config flow tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from custom_components.yeelight_fluid.const import CONF_KEY, CONF_PRODUCT_ID, DOMAIN
from custom_components.yeelight_fluid.device import YeelightFluidAuthError
from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .conftest import ADDRESS, KEY_HEX, NAME

DEVICE = "custom_components.yeelight_fluid.config_flow.YeelightFluidDevice"


async def test_bluetooth_pair(hass: HomeAssistant, service_info, mock_ble_lookup) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "pair_menu"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "pair"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pair"

    with (
        patch(f"{DEVICE}.pair", AsyncMock(return_value=bytes.fromhex(KEY_HEX))),
        patch(f"{DEVICE}.update", AsyncMock()),
        patch(f"{DEVICE}.disconnect", AsyncMock()),
        patch("custom_components.yeelight_fluid.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == NAME
    assert result["data"] == {
        CONF_ADDRESS: ADDRESS,
        CONF_PRODUCT_ID: 0x2804,
        CONF_KEY: KEY_HEX,
    }


async def test_pair_failed(hass: HomeAssistant, service_info, mock_ble_lookup) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "pair"}
    )
    with (
        patch(f"{DEVICE}.pair", AsyncMock(side_effect=YeelightFluidAuthError("x"))),
        patch(f"{DEVICE}.disconnect", AsyncMock()),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "pair_failed"}


async def test_user_no_pair(hass: HomeAssistant, service_info, mock_ble_lookup) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS}
    )
    assert result["type"] is FlowResultType.MENU
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "no_pair"}
    )
    with (
        patch(f"{DEVICE}.update", AsyncMock()),
        patch(f"{DEVICE}.disconnect", AsyncMock()),
        patch("custom_components.yeelight_fluid.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert CONF_KEY not in result["data"]
