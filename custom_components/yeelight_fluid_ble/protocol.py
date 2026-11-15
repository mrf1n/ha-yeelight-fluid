"""Yeelight Fluid BLE protocol helpers (no Home Assistant dependencies).

See docs/PROTOCOL.md for the protocol specification.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESCCM


def uuid16(short: str) -> str:
    """Expand a 16-bit UUID."""
    return f"0000{short}-0000-1000-8000-00805f9b34fb"


AUTH_SERVICE = uuid16("fe87")
AUTH_WRITE = uuid16("fe88")
AUTH_NOTIFY = uuid16("fe89")
CTRL_SERVICE = uuid16("ae3a")
CTRL_WRITE = uuid16("ae3b")
CTRL_NOTIFY = uuid16("ae3c")

AUTH_HEAD = 0x59
CMD_PAIR = 1
CMD_READ_KEY = 2
CMD_AUTH_KEY = 3
CMD_AUTH_SUCCESS = 4

_KEY_SUFFIX = bytes([4, 3, 2, 1])
_NONCE_SUFFIX = bytes([0x52, 0x27, 0x61, 0x98])
_AAD = bytes([0x87, 0xFE])


# --------------------------------------------------------------------------- #
# Advertisement
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Advertisement:
    """Parsed Yeelight manufacturer data."""

    product_id: int
    mac: str | None
    raw: bytes


def parse_manufacturer_data(data: bytes) -> Advertisement | None:
    """Parse manufacturer data for company id 0x0164.

    Layout (16 bytes): product_id LE (2) | 4 unknown | mac LE (6) | 4 unknown.
    """
    if len(data) < 2:
        return None
    product_id = int.from_bytes(data[0:2], "little")
    mac = None
    if len(data) >= 12:
        mac = ":".join(f"{b:02X}" for b in reversed(data[6:12]))
    return Advertisement(product_id=product_id, mac=mac, raw=bytes(data))


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
def mac_le(mac: str) -> bytes:
    """MAC string to little-endian bytes."""
    return bytes.fromhex(mac.replace(":", "").replace("-", ""))[::-1]


def build_auth_packet(seq: int, cmd: int, data: bytes = b"") -> bytes:
    """Build a 0x59 auth frame."""
    body = bytes([AUTH_HEAD, seq & 0xFF, cmd & 0xFF, len(data) & 0xFF]) + data
    return body + bytes([sum(body) & 0xFF])


def encrypt_auth(mac: str, key: bytes, product_id: int) -> bytes:
    """Compute AuthKey payload: AES-CCM(mac_le), 4-byte tag."""
    if len(key) != 12:
        raise ValueError(f"device key must be 12 bytes, got {len(key)}")
    m = mac_le(mac)
    nonce = m + product_id.to_bytes(2, "big") + _NONCE_SUFFIX
    return AESCCM(key + _KEY_SUFFIX, tag_length=4).encrypt(nonce, m, _AAD)


@dataclass(frozen=True)
class AuthFrame:
    """Parsed auth response."""

    seq: int
    cmd: int
    data: bytes


class AuthFrameParser:
    """Reassemble 0x59 frames from notification chunks."""

    def __init__(self) -> None:
        self._buf = bytearray()

    def feed(self, chunk: bytes) -> list[AuthFrame]:
        self._buf += chunk
        frames: list[AuthFrame] = []
        while True:
            try:
                start = self._buf.index(AUTH_HEAD)
            except ValueError:
                self._buf.clear()
                return frames
            del self._buf[:start]
            if len(self._buf) < 5:
                return frames
            total = 5 + self._buf[3]
            if len(self._buf) < total:
                return frames
            frame = bytes(self._buf[:total])
            del self._buf[:total]
            if sum(frame[:-1]) & 0xFF != frame[-1]:
                continue
            frames.append(AuthFrame(seq=frame[1] & 0x7F, cmd=frame[2], data=frame[4:-1]))


# --------------------------------------------------------------------------- #
# Control (JSON-RPC)
# --------------------------------------------------------------------------- #
def encode_request(msg_id: int, method: str, params: list[Any]) -> bytes:
    """Encode a JSON-RPC line."""
    return (
        json.dumps({"id": msg_id, "method": method, "params": params}, separators=(",", ":"))
        + "\r\n"
    ).encode()


class JsonLineParser:
    """Split notification chunks into JSON messages."""

    def __init__(self) -> None:
        self._buf = bytearray()

    def feed(self, chunk: bytes) -> list[dict[str, Any]]:
        self._buf += chunk
        out: list[dict[str, Any]] = []
        while (idx := self._buf.find(b"\n")) >= 0:
            line = bytes(self._buf[:idx]).strip()
            del self._buf[: idx + 1]
            if not line:
                continue
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if isinstance(msg, dict):
                out.append(msg)
        if len(self._buf) > 8192:
            self._buf.clear()
        return out


def parse_json_prop(value: Any) -> dict[str, Any]:
    """Props like fx_effect are JSON strings."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except ValueError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def argb_to_rgb(value: int) -> tuple[int, int, int]:
    """Signed/unsigned ARGB int to RGB tuple."""
    value &= 0xFFFFFFFF
    return ((value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF)


def rgb_to_argb(rgb: tuple[int, int, int]) -> int:
    """RGB tuple to unsigned ARGB int with full alpha."""
    r, g, b = rgb
    return 0xFF000000 | (r << 16) | (g << 8) | b
