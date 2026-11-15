"""BLE client for Yeelight Fluid devices (no Home Assistant entity code)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import contextlib
import logging
from typing import Any

from bleak.backends.device import BLEDevice
from bleak.exc import BleakError
from bleak_retry_connector import (
    BleakClientWithServiceCache,
    establish_connection,
)

from .protocol import (
    AUTH_NOTIFY,
    AUTH_WRITE,
    CMD_AUTH_KEY,
    CMD_AUTH_SUCCESS,
    CMD_PAIR,
    CMD_READ_KEY,
    CTRL_NOTIFY,
    CTRL_WRITE,
    AuthFrame,
    AuthFrameParser,
    JsonLineParser,
    build_auth_packet,
    encode_request,
    encrypt_auth,
    mac_le,
    parse_json_prop,
)

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 5.0
AUTH_TIMEOUT = 5.0
PAIR_TIMEOUT = 60.0
RECONNECT_DELAYS = (2, 5, 10, 30, 60)

STATE_PROPS = [
    "power",
    "bright",
    "hue",
    "sat",
    "ct",
    "rgb",
    "color_mode",
    "fx_effect",
    "mic_music_mode",
    "fw_version",
    "strip_length",
    "init_power_opt",
]
INT_PROPS = {
    "bright",
    "hue",
    "sat",
    "ct",
    "rgb",
    "color_mode",
    "fw_version",
    "strip_length",
    "init_power_opt",
    "save_state",
}


class YeelightFluidError(Exception):
    """Communication error."""


class YeelightFluidAuthError(YeelightFluidError):
    """Authentication / pairing failed."""


class YeelightFluidDevice:
    """Connection + state for one Yeelight Fluid BLE device."""

    def __init__(
        self,
        ble_device: BLEDevice,
        product_id: int,
        key: bytes | None = None,
        keep_connected: bool = False,
        idle_timeout: float = 60,
    ) -> None:
        self._ble_device = ble_device
        self.product_id = product_id
        self.key = key
        self.keep_connected = keep_connected
        self.idle_timeout = idle_timeout

        self.state: dict[str, Any] = {}
        self.effect_config: dict[str, Any] = {}
        self.effect_id: int | None = None
        self.custom_id: int | None = None
        self.authenticated = False
        self.rssi: int | None = None

        self._client: BleakClientWithServiceCache | None = None
        self._connect_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()
        self._msg_id = 0
        self._pending: dict[int, asyncio.Future[Any]] = {}
        self._auth_parser = AuthFrameParser()
        self._json_parser = JsonLineParser()
        self._auth_queue: asyncio.Queue[AuthFrame] = asyncio.Queue()
        self._listeners: list[Callable[[], None]] = []
        self._idle_handle: asyncio.TimerHandle | None = None
        self._reconnect_task: asyncio.Task[None] | None = None
        self._closing = False

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #
    @property
    def address(self) -> str:
        return self._ble_device.address

    @property
    def name(self) -> str:
        return self._ble_device.name or self.address

    @property
    def connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    @property
    def is_on(self) -> bool | None:
        power = self.state.get("power")
        return None if power is None else power == "on"

    @property
    def music_mode(self) -> dict[str, Any]:
        return parse_json_prop(self.state.get("mic_music_mode"))

    def set_ble_device(self, ble_device: BLEDevice, rssi: int | None = None) -> None:
        """Update BLEDevice from a fresh advertisement."""
        self._ble_device = ble_device
        if rssi is not None:
            self.rssi = rssi

    # ------------------------------------------------------------------ #
    # Listeners
    # ------------------------------------------------------------------ #
    def register_callback(self, callback: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(callback)

        def _remove() -> None:
            with contextlib.suppress(ValueError):
                self._listeners.remove(callback)

        return _remove

    def _notify_listeners(self) -> None:
        for callback in list(self._listeners):
            try:
                callback()
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Error in state listener")

    # ------------------------------------------------------------------ #
    # Connection
    # ------------------------------------------------------------------ #
    async def connect(self) -> None:
        """Connect and authenticate if needed."""
        if self.connected:
            self._reset_idle_timer()
            return
        async with self._connect_lock:
            if self.connected:
                return
            _LOGGER.debug("%s: connecting", self.name)
            try:
                client = await establish_connection(
                    BleakClientWithServiceCache,
                    self._ble_device,
                    self.name,
                    disconnected_callback=self._on_disconnected,
                    max_attempts=3,
                )
            except (BleakError, TimeoutError) as err:
                raise YeelightFluidError(f"Failed to connect: {err}") from err
            self._client = client
            self._auth_parser = AuthFrameParser()
            self._json_parser = JsonLineParser()
            self._auth_queue = asyncio.Queue()
            try:
                await client.start_notify(CTRL_NOTIFY, self._on_ctrl_notify)
                await client.start_notify(AUTH_NOTIFY, self._on_auth_notify)
                self.authenticated = False
                if self.key:
                    await self._authenticate()
            except (BleakError, TimeoutError) as err:
                await self._disconnect()
                raise YeelightFluidError(f"Setup failed: {err}") from err
            _LOGGER.debug("%s: connected (auth=%s)", self.name, self.authenticated)
            self._reset_idle_timer()

    async def disconnect(self) -> None:
        """Disconnect on request (unload)."""
        self._closing = True
        if self._reconnect_task:
            self._reconnect_task.cancel()
            self._reconnect_task = None
        await self._disconnect()

    async def _disconnect(self) -> None:
        self._cancel_idle_timer()
        client, self._client = self._client, None
        self.authenticated = False
        self._fail_pending(YeelightFluidError("Disconnected"))
        if client is not None:
            with contextlib.suppress(BleakError, TimeoutError):
                await client.disconnect()

    def _on_disconnected(self, _client: BleakClientWithServiceCache) -> None:
        _LOGGER.debug("%s: disconnected", self.name)
        self._client = None
        self.authenticated = False
        self._fail_pending(YeelightFluidError("Disconnected"))
        self._notify_listeners()
        if self.keep_connected and not self._closing:
            self._schedule_reconnect()

    def _schedule_reconnect(self) -> None:
        if self._reconnect_task and not self._reconnect_task.done():
            return
        self._reconnect_task = asyncio.get_running_loop().create_task(self._reconnect_loop())

    async def _reconnect_loop(self) -> None:
        for attempt in range(1000):
            if self._closing or self.connected or not self.keep_connected:
                return
            delay = RECONNECT_DELAYS[min(attempt, len(RECONNECT_DELAYS) - 1)]
            await asyncio.sleep(delay)
            try:
                await self.connect()
                await self.update()
            except YeelightFluidError as err:
                _LOGGER.debug("%s: reconnect failed: %s", self.name, err)
            else:
                return

    def _reset_idle_timer(self) -> None:
        self._cancel_idle_timer()
        if self.keep_connected or self.idle_timeout <= 0:
            return
        loop = asyncio.get_running_loop()
        self._idle_handle = loop.call_later(
            self.idle_timeout, lambda: loop.create_task(self._idle_disconnect())
        )

    def _cancel_idle_timer(self) -> None:
        if self._idle_handle:
            self._idle_handle.cancel()
            self._idle_handle = None

    async def _idle_disconnect(self) -> None:
        if self.keep_connected:
            return
        _LOGGER.debug("%s: idle, disconnecting", self.name)
        await self._disconnect()

    async def set_keep_connected(self, keep: bool) -> None:
        self.keep_connected = keep
        if keep:
            self._cancel_idle_timer()
            if not self.connected:
                self._schedule_reconnect()
        elif self.connected:
            self._reset_idle_timer()

    # ------------------------------------------------------------------ #
    # Auth
    # ------------------------------------------------------------------ #
    def _on_auth_notify(self, _char: Any, data: bytearray) -> None:
        for frame in self._auth_parser.feed(bytes(data)):
            _LOGGER.debug("%s: auth <- %s", self.name, frame)
            self._auth_queue.put_nowait(frame)

    async def _auth_request(
        self, seq: int, cmd: int, data: bytes = b"", timeout: float = AUTH_TIMEOUT
    ) -> AuthFrame:
        assert self._client is not None
        while not self._auth_queue.empty():
            self._auth_queue.get_nowait()
        await self._client.write_gatt_char(
            AUTH_WRITE, build_auth_packet(seq, cmd, data), response=True
        )
        try:
            async with asyncio.timeout(timeout):
                while True:
                    frame = await self._auth_queue.get()
                    if frame.cmd == cmd:
                        return frame
        except TimeoutError as err:
            raise YeelightFluidAuthError(f"No response to auth cmd {cmd}") from err

    async def _authenticate(self) -> None:
        assert self.key is not None
        payload = encrypt_auth(self.address, self.key, self.product_id)
        frame = await self._auth_request(3, CMD_AUTH_KEY, payload)
        if frame.data and frame.data != mac_le(self.address):
            raise YeelightFluidAuthError("Unexpected AuthKey response")
        await self._auth_request(4, CMD_AUTH_SUCCESS)
        self.authenticated = True

    async def pair(self) -> bytes:
        """Run first-time pairing and return the 12-byte device key."""
        await self.connect()
        try:
            await self._auth_request(1, CMD_PAIR, timeout=PAIR_TIMEOUT)
            frame = await self._auth_request(2, CMD_READ_KEY)
        except BleakError as err:
            raise YeelightFluidError(str(err)) from err
        if len(frame.data) != 12:
            raise YeelightFluidAuthError(f"Invalid key length {len(frame.data)}")
        self.key = bytes(frame.data)
        await self._authenticate()
        return self.key

    # ------------------------------------------------------------------ #
    # Control
    # ------------------------------------------------------------------ #
    def _on_ctrl_notify(self, _char: Any, data: bytearray) -> None:
        for msg in self._json_parser.feed(bytes(data)):
            _LOGGER.debug("%s: ctrl <- %s", self.name, msg)
            msg_id = msg.get("id")
            if msg_id is not None and msg_id in self._pending:
                fut = self._pending.pop(msg_id)
                if not fut.done():
                    if "error" in msg:
                        fut.set_exception(YeelightFluidError(str(msg["error"])))
                    else:
                        fut.set_result(msg.get("result"))
                continue
            if msg.get("method") == "props" and isinstance(msg.get("params"), dict):
                self._apply_props(msg["params"])

    def _apply_props(self, props: dict[str, Any]) -> None:
        for key, value in props.items():
            if key in INT_PROPS:
                with contextlib.suppress(TypeError, ValueError):
                    value = int(value)
            self.state[key] = value
        if "fx_effect" in props:
            fx = parse_json_prop(props["fx_effect"])
            self.effect_id = fx.get("effect_id")
            self.custom_id = fx.get("custom_id")
        self._notify_listeners()

    def _fail_pending(self, exc: Exception) -> None:
        for fut in self._pending.values():
            if not fut.done():
                fut.set_exception(exc)
        self._pending.clear()

    async def request(self, method: str, params: list[Any] | None = None) -> Any:
        """Send JSON-RPC request and wait for result."""
        await self.connect()
        assert self._client is not None
        self._msg_id = (self._msg_id % 10000) + 1
        msg_id = self._msg_id
        fut: asyncio.Future[Any] = asyncio.get_running_loop().create_future()
        self._pending[msg_id] = fut
        payload = encode_request(msg_id, method, params or [])
        chunk = max(20, (self._client.mtu_size or 23) - 3)
        _LOGGER.debug("%s: ctrl -> %s", self.name, payload)
        try:
            async with self._write_lock:
                for i in range(0, len(payload), chunk):
                    await self._client.write_gatt_char(
                        CTRL_WRITE, payload[i : i + chunk], response=True
                    )
            async with asyncio.timeout(REQUEST_TIMEOUT):
                result = await fut
        except TimeoutError as err:
            raise YeelightFluidError(f"Timeout waiting for {method}") from err
        except BleakError as err:
            raise YeelightFluidError(f"Write failed: {err}") from err
        finally:
            self._pending.pop(msg_id, None)
            self._reset_idle_timer()
        return result

    async def update(self) -> None:
        """Read full state."""
        result = await self.request("get_prop", STATE_PROPS)
        if isinstance(result, list):
            props: dict[str, Any] = {}
            for key, value in zip(STATE_PROPS, result, strict=False):
                if value in ("", None):
                    continue
                props[key] = value
            self._apply_props(props)
        with contextlib.suppress(YeelightFluidError):
            fx = await self.request("get_fx_effect")
            if isinstance(fx, list) and len(fx) >= 3 and isinstance(fx[2], dict):
                self.effect_id, self.custom_id = fx[0], fx[1]
                self.effect_config = fx[2]
                self._notify_listeners()

    # Commands ------------------------------------------------------------ #
    async def turn_on(self, transition_ms: int = 500) -> None:
        await self.request("set_power", ["on", "smooth", transition_ms])
        self._apply_props({"power": "on"})

    async def turn_off(self, transition_ms: int = 500) -> None:
        await self.request("set_power", ["off", "smooth", transition_ms])
        self._apply_props({"power": "off"})

    async def set_brightness(self, percent: int, transition_ms: int = 500) -> None:
        percent = max(1, min(100, percent))
        await self.request("set_bright", [percent, "smooth", transition_ms])
        self._apply_props({"bright": percent})

    async def set_hs(self, hue: int, sat: int, transition_ms: int = 500) -> None:
        await self.request("set_hsv", [hue, sat, "smooth", transition_ms])
        self._apply_props({"hue": hue, "sat": sat, "color_mode": 3})

    async def set_color_temp(self, kelvin: int, transition_ms: int = 500) -> None:
        await self.request("set_ct_abx", [kelvin, "smooth", transition_ms])
        self._apply_props({"ct": kelvin, "color_mode": 2})

    async def set_effect(
        self,
        effect_id: int,
        rate: int | None = None,
        colors: list[int] | None = None,
        direction: int | None = None,
        intensity: int | None = None,
    ) -> None:
        cfg: dict[str, Any] = {}
        if rate is not None:
            cfg["rate"] = rate
        if colors:
            cfg["color"] = colors
        if direction is not None:
            cfg["direction"] = direction
        if intensity is not None:
            cfg["intensity"] = intensity
        await self.request("set_fx_effect", [effect_id, 0, 1, cfg])
        self.effect_id = effect_id
        self.effect_config.update(cfg)
        self._apply_props({"color_mode": 14})

    async def update_effect(self, **cfg: Any) -> None:
        cfg = {k: v for k, v in cfg.items() if v is not None}
        if not cfg:
            return
        await self.request("update_fx_effect", [cfg])
        self.effect_config.update(cfg)
        self._notify_listeners()

    async def set_music_mode(self, on: bool, effect_id: int = 0) -> None:
        value = f'{{"on":{1 if on else 0},"effect_id":{effect_id}}}'
        await self.request("set_ps", ["mic_music_mode", value])
        self._apply_props({"mic_music_mode": value})
