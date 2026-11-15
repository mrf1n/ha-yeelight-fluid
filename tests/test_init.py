"""Setup + entity tests with a fake device."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.yeelight_fluid_ble.const import CONF_KEY, CONF_PRODUCT_ID, DOMAIN
from custom_components.yeelight_fluid_ble.device import YeelightFluidDevice
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant

from .conftest import ADDRESS, KEY_HEX

STATE = {
    "power": "on",
    "bright": 38,
    "hue": 0,
    "sat": 33,
    "ct": 4000,
    "color_mode": 14,
    "fx_effect": '{"effect_id":81,"custom_id":0}',
    "mic_music_mode": '{"on":0,"effect_id":0}',
    "fw_version": 56,
    "strip_length": 200,
}


async def _fake_update(self: YeelightFluidDevice) -> None:
    self._apply_props(dict(STATE))
    self.effect_config = {"rate": 50, "direction": 0}


async def test_setup_and_entities(hass: HomeAssistant, mock_ble_lookup) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=ADDRESS,
        data={CONF_ADDRESS: ADDRESS, CONF_PRODUCT_ID: 0x2804, CONF_KEY: KEY_HEX},
    )
    entry.add_to_hass(hass)
    request = AsyncMock(return_value=["ok"])
    with (
        patch.object(YeelightFluidDevice, "update", _fake_update),
        patch.object(YeelightFluidDevice, "request", request),
        patch.object(YeelightFluidDevice, "disconnect", AsyncMock()),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        light = hass.states.get("light.ylbt_chri_eeff")
        assert light is not None
        assert light.state == "on"
        assert light.attributes["effect"] == "Christmas"
        assert light.attributes["brightness"] == 97

        assert hass.states.get("select.ylbt_chri_eeff_effect").state == "christmas"
        assert hass.states.get("number.ylbt_chri_eeff_effect_speed").state == "50.0"
        assert hass.states.get("switch.ylbt_chri_eeff_music_mode").state == "off"
        assert hass.states.get("sensor.ylbt_chri_eeff_firmware").state == "56"

        await hass.services.async_call(
            "light",
            "turn_on",
            {"entity_id": "light.ylbt_chri_eeff", "brightness": 128},
            blocking=True,
        )
        request.assert_awaited_with("set_bright", [50, "smooth", 500])

        await hass.services.async_call(
            DOMAIN,
            "set_effect",
            {
                "entity_id": "light.ylbt_chri_eeff",
                "effect": "meteor",
                "speed": 70,
                "colors": [[255, 0, 0]],
                "direction": "down",
            },
            blocking=True,
        )
        request.assert_awaited_with(
            "set_fx_effect", [47, 0, 1, {"rate": 70, "color": [4294901760], "direction": 1}]
        )

        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": "select.ylbt_chri_eeff_effect", "option": "christmas"},
            blocking=True,
        )
        request.assert_awaited_with("set_fx_effect", [81, 0, 1, {"rate": 70}])

        await hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": "switch.ylbt_chri_eeff_music_mode"},
            blocking=True,
        )
        request.assert_awaited_with("set_ps", ["mic_music_mode", '{"on":1,"effect_id":0}'])
        assert hass.states.get("light.ylbt_chri_eeff").attributes["effect"] == "Music"

        assert await hass.config_entries.async_unload(entry.entry_id)
