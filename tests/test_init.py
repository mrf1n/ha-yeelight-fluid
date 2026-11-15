"""Setup + entity tests with a fake device."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.yeelight_lights_ble.const import (
    CONF_KEY,
    CONF_PRODUCT_ID,
    DOMAIN,
)
from custom_components.yeelight_lights_ble.custom import pattern_colors
from custom_components.yeelight_lights_ble.device import YeelightBleDevice
from custom_components.yeelight_lights_ble.music import SCHEMES_BY_KEY
from custom_components.yeelight_lights_ble.protocol import encode_custom_data, encode_music_mode
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

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
    "init_power_opt": 0,
}


async def _fake_update(self: YeelightBleDevice) -> None:
    self._apply_props(dict(STATE))
    self.effect_config = {"rate": 128, "direction": 0}


async def test_setup_and_entities(hass: HomeAssistant, mock_ble_lookup) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=ADDRESS,
        data={CONF_ADDRESS: ADDRESS, CONF_PRODUCT_ID: 0x2804, CONF_KEY: KEY_HEX},
    )
    entry.add_to_hass(hass)
    request = AsyncMock(return_value=["ok"])
    with (
        patch.object(YeelightBleDevice, "update", _fake_update),
        patch.object(YeelightBleDevice, "request", request),
        patch.object(YeelightBleDevice, "disconnect", AsyncMock()),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        light = hass.states.get("light.ylbt_chri_eeff_light")
        assert light is not None
        assert light.state == "on"
        assert light.attributes["effect"] == "Christmas"
        assert light.attributes["brightness"] == 97

        assert hass.states.get("select.ylbt_chri_eeff_effect").state == "christmas"
        assert hass.states.get("number.ylbt_chri_eeff_effect_speed").state == "51.0"
        # Christmas has speed but no direction
        assert hass.states.get("select.ylbt_chri_eeff_effect_direction").state == "unavailable"
        assert hass.states.get("switch.ylbt_chri_eeff_music_mode").state == "off"

        registry = er.async_get(hass)
        for sensor in ("signal_strength", "firmware", "led_count"):
            entity = registry.async_get(f"sensor.ylbt_chri_eeff_{sensor}")
            assert entity is not None, sensor
            assert entity.disabled_by is er.RegistryEntryDisabler.INTEGRATION

        await hass.services.async_call(
            "light",
            "turn_on",
            {"entity_id": "light.ylbt_chri_eeff_light", "brightness": 128},
            blocking=True,
        )
        request.assert_awaited_with("set_scene", ["bright", 50, 0])

        # pure colour: picked colours are remembered, newest first, max 7, no duplicates
        recent = "select.ylbt_chri_eeff_recent_colours"
        for hue in (0, 120, 240, 0, 30, 60, 90, 150, 180):
            await hass.services.async_call(
                "light",
                "turn_on",
                {"entity_id": "light.ylbt_chri_eeff_light", "hs_color": [hue, 100]},
                blocking=True,
            )
        state = hass.states.get(recent)
        assert state.attributes["options"] == [
            "#00FFFF",
            "#00FF80",
            "#80FF00",
            "#FFFF00",
            "#FF8000",
            "#0000FF",
            "#00FF00",
        ]
        assert state.state == "#00FFFF"
        favorites = registry.async_get("light.ylbt_chri_eeff_light").options["light"]
        assert favorites["favorite_colors"] == [
            {"hs_color": [h, 100]} for h in (180, 150, 90, 60, 30, 240, 120)
        ]
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": recent, "option": "#0000FF"},
            blocking=True,
        )
        request.assert_awaited_with("set_hsv", [240, 100, "smooth", 500])
        assert hass.states.get(recent).state == "#0000FF"

        await hass.services.async_call(
            DOMAIN,
            "set_effect",
            {
                "entity_id": "light.ylbt_chri_eeff_light",
                "effect": "meteor",
                "speed": 70,
                "colors": [[255, 0, 0]],
                "direction": "down",
            },
            blocking=True,
        )
        request.assert_awaited_with(
            "set_fx_effect", [47, 0, 1, {"rate": 179, "color": [4294901760], "direction": 1}]
        )
        assert hass.states.get("select.ylbt_chri_eeff_effect_direction").state == "down"

        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": "select.ylbt_chri_eeff_effect", "option": "christmas"},
            blocking=True,
        )
        request.assert_awaited_with("set_fx_effect", [81, 0, 1, {"rate": 179}])

        power_on = "select.ylbt_chri_eeff_default_state_after_power_on"
        assert hass.states.get(power_on).state == "restore"
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": power_on, "option": "off"},
            blocking=True,
        )
        request.assert_awaited_with("set_ps", ["cfg_init_power", 2])
        assert hass.states.get(power_on).state == "off"

        await hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": "switch.ylbt_chri_eeff_music_mode"},
            blocking=True,
        )
        request.assert_awaited_with(
            "set_ps",
            ["mic_music_mode", encode_music_mode(True, 84, SCHEMES_BY_KEY["happy"].colors)],
        )
        assert hass.states.get("light.ylbt_chri_eeff_light").attributes["effect"] == "Music"
        # no speed or direction in music mode
        assert hass.states.get("number.ylbt_chri_eeff_effect_speed").state == "unavailable"
        assert hass.states.get("select.ylbt_chri_eeff_effect_direction").state == "unavailable"

        # changing music options while music mode runs resends them
        assert hass.states.get("select.ylbt_chri_eeff_music_rhythm_effect").state == "breath"
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": "select.ylbt_chri_eeff_music_rhythm_effect", "option": "spectrum"},
            blocking=True,
        )
        request.assert_awaited_with(
            "set_ps",
            ["mic_music_mode", encode_music_mode(True, 86, SCHEMES_BY_KEY["happy"].colors)],
        )
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": "select.ylbt_chri_eeff_music_colour_scheme", "option": "christmas"},
            blocking=True,
        )
        request.assert_awaited_with(
            "set_ps",
            ["mic_music_mode", encode_music_mode(True, 86, SCHEMES_BY_KEY["christmas"].colors)],
        )

        # custom colours via the action
        await hass.services.async_call(
            DOMAIN,
            "set_music_mode",
            {
                "entity_id": "light.ylbt_chri_eeff_light",
                "effect": "converge",
                "colors": [[255, 0, 0], [0, 0, 255]],
            },
            blocking=True,
        )
        request.assert_awaited_with(
            "set_ps", ["mic_music_mode", encode_music_mode(True, 83, [0xFFFF0000, 0xFF0000FF])]
        )
        scheme = hass.states.get("select.ylbt_chri_eeff_music_colour_scheme")
        assert scheme.state == "custom"
        assert scheme.attributes["colors"] == [[255, 0, 0], [0, 0, 255]]

        # DIY / custom: pattern repeated over the 200 LEDs, with a dynamic effect
        await hass.services.async_call(
            DOMAIN,
            "set_custom_effect",
            {
                "entity_id": "light.ylbt_chri_eeff_light",
                "colors": [[255, 0, 0], [0, 0, 255]],
                "dynamic_effect": "translation",
                "speed": 50,
                "direction": "down",
            },
            blocking=True,
        )
        data = encode_custom_data(pattern_colors([0xFFFF0000, 0xFF0000FF], 200))
        request.assert_awaited_with(
            "set_fx_effect",
            [36, 0, 1, {"mixer": 2, "rate": 128, "direction": 1, "data": data}],
        )
        assert hass.states.get("light.ylbt_chri_eeff_light").attributes["effect"] == "Custom"
        # 50 % -> rate 128 -> shown as 51 %, same rounding as the app
        assert hass.states.get("number.ylbt_chri_eeff_effect_speed").state == "51.0"
        assert hass.states.get("select.ylbt_chri_eeff_effect_direction").state == "down"

        # static custom pattern: no speed or direction
        await hass.services.async_call(
            DOMAIN,
            "set_custom_effect",
            {"entity_id": "light.ylbt_chri_eeff_light", "random": True},
            blocking=True,
        )
        args = request.await_args.args
        assert args[0] == "set_fx_effect"
        assert args[1][:3] == [36, 0, 1]
        assert list(args[1][3]) == ["data"]
        assert hass.states.get("number.ylbt_chri_eeff_effect_speed").state == "unavailable"

        assert await hass.config_entries.async_unload(entry.entry_id)
