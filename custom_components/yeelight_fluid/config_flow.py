"""Config flow for Yeelight Fluid."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_ble_device_from_address,
    async_discovered_service_info,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback

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
    NAME_PREFIX,
    YEELIGHT_MANUFACTURER_ID,
    product_for,
)
from .device import YeelightFluidAuthError, YeelightFluidDevice, YeelightFluidError
from .protocol import parse_manufacturer_data

_LOGGER = logging.getLogger(__name__)


def _is_supported(info: BluetoothServiceInfoBleak) -> bool:
    return (info.name or "").startswith(NAME_PREFIX) or (
        YEELIGHT_MANUFACTURER_ID in info.manufacturer_data
    )


def _product_id(info: BluetoothServiceInfoBleak) -> int:
    raw = info.manufacturer_data.get(YEELIGHT_MANUFACTURER_ID)
    adv = parse_manufacturer_data(raw) if raw else None
    if adv is not None:
        return adv.product_id
    return product_for(None, info.name).product_id


class YeelightFluidConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovery: BluetoothServiceInfoBleak | None = None
        self._discovered: dict[str, BluetoothServiceInfoBleak] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return YeelightFluidOptionsFlow()

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address.upper())
        self._abort_if_unique_id_configured()
        if not _is_supported(discovery_info):
            return self.async_abort(reason="not_supported")
        self._discovery = discovery_info
        self.context["title_placeholders"] = {"name": discovery_info.name}
        return await self.async_step_pair_menu()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Pick a discovered device."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address.upper(), raise_on_progress=False)
            self._abort_if_unique_id_configured()
            self._discovery = self._discovered[address]
            return await self.async_step_pair_menu()

        current = self._async_current_ids(include_ignore=False)
        for info in async_discovered_service_info(self.hass, connectable=True):
            if info.address.upper() in current or not _is_supported(info):
                continue
            self._discovered[info.address] = info
        if not self._discovered:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {addr: f"{info.name} ({addr})" for addr, info in self._discovered.items()}
                    )
                }
            ),
        )

    async def async_step_pair_menu(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Offer pairing or skipping it."""
        assert self._discovery is not None
        return self.async_show_menu(
            step_id="pair_menu",
            menu_options=["pair", "no_pair"],
            description_placeholders={"name": self._discovery.name},
        )

    async def async_step_pair(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Run pairing (Pair + ReadKey + AuthKey)."""
        assert self._discovery is not None
        errors: dict[str, str] = {}
        if user_input is not None:
            device = self._make_device()
            if device is None:
                return self.async_abort(reason="cannot_connect")
            try:
                key = await device.pair()
                await device.update()
            except YeelightFluidAuthError as err:
                _LOGGER.debug("Pairing failed: %s", err)
                errors["base"] = "pair_failed"
            except YeelightFluidError as err:
                _LOGGER.debug("Connection failed: %s", err)
                errors["base"] = "cannot_connect"
            else:
                return self._create(device, key)
            finally:
                await device.disconnect()

        return self.async_show_form(
            step_id="pair",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={"name": self._discovery.name},
        )

    async def async_step_no_pair(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add without pairing (works on firmware that does not enforce auth)."""
        assert self._discovery is not None
        errors: dict[str, str] = {}
        if user_input is not None:
            device = self._make_device()
            if device is None:
                return self.async_abort(reason="cannot_connect")
            try:
                await device.update()
            except YeelightFluidError as err:
                _LOGGER.debug("Connection failed: %s", err)
                errors["base"] = "cannot_connect"
            else:
                return self._create(device, None)
            finally:
                await device.disconnect()

        return self.async_show_form(
            step_id="no_pair",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={"name": self._discovery.name},
        )

    def _make_device(self) -> YeelightFluidDevice | None:
        assert self._discovery is not None
        ble_device = async_ble_device_from_address(
            self.hass, self._discovery.address, connectable=True
        )
        if ble_device is None:
            return None
        return YeelightFluidDevice(ble_device, product_id=_product_id(self._discovery))

    def _create(self, device: YeelightFluidDevice, key: bytes | None) -> ConfigFlowResult:
        assert self._discovery is not None
        data: dict[str, Any] = {
            CONF_ADDRESS: self._discovery.address,
            CONF_PRODUCT_ID: device.product_id,
        }
        if key:
            data[CONF_KEY] = key.hex()
        return self.async_create_entry(title=self._discovery.name or device.name, data=data)


class YeelightFluidOptionsFlow(OptionsFlow):
    """Options: connection strategy."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        options = self.config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_KEEP_CONNECTED,
                        default=options.get(CONF_KEEP_CONNECTED, DEFAULT_KEEP_CONNECTED),
                    ): bool,
                    vol.Required(
                        CONF_IDLE_TIMEOUT,
                        default=options.get(CONF_IDLE_TIMEOUT, DEFAULT_IDLE_TIMEOUT),
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=3600)),
                    vol.Required(
                        CONF_POLL_INTERVAL,
                        default=options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
                    ): vol.All(vol.Coerce(int), vol.Range(min=30, max=86400)),
                }
            ),
        )
