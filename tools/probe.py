#!/usr/bin/env python3
"""Yeelight BLE lights probe.

Standalone script to verify the protocol in docs/PROTOCOL.md on real hardware.

Requirements:
    pip install bleak cryptography

Usage:
    python tools/probe.py scan
    python tools/probe.py run --address AA:BB:CC:DD:EE:FF --pair
    python tools/probe.py run --address AA:BB:CC:DD:EE:FF            # reuse stored key
    python tools/probe.py run --address ... --cmd 'set_power ["on","smooth",500]'

The device key read during pairing is stored in tools/probe_state.json.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from cryptography.hazmat.primitives.ciphers.aead import AESCCM

_LOGGER = logging.getLogger("probe")

STATE_FILE = Path(__file__).with_name("probe_state.json")


def uuid16(short: str) -> str:
    return f"0000{short}-0000-1000-8000-00805f9b34fb"


AUTH_SERVICE = uuid16("fe87")
AUTH_WRITE = uuid16("fe88")
AUTH_NOTIFY = uuid16("fe89")
CTRL_SERVICE = uuid16("ae3a")
CTRL_WRITE = uuid16("ae3b")
CTRL_NOTIFY = uuid16("ae3c")

YEELIGHT_COMPANY_IDS = (0xFE87, 0x0164)
NAME_PREFIXES = ("YLBT_",)
DEFAULT_PRODUCT_ID = 16787460 - 0x01000000  # Christmas lights -> 0x2804

AUTH_HEAD = 0x59
CMD_PAIR = 1
CMD_READ_KEY = 2
CMD_AUTH_KEY = 3
CMD_AUTH_SUCCESS = 4


# --------------------------------------------------------------------------- #
# State
# --------------------------------------------------------------------------- #
def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


# --------------------------------------------------------------------------- #
# Auth framing / crypto
# --------------------------------------------------------------------------- #
def build_auth_packet(seq: int, cmd: int, data: bytes = b"") -> bytes:
    body = bytes([AUTH_HEAD, seq & 0xFF, cmd & 0xFF, len(data) & 0xFF]) + data
    return body + bytes([sum(body) & 0xFF])


def mac_le(mac: str) -> bytes:
    return bytes.fromhex(mac.replace(":", "").replace("-", ""))[::-1]


def encrypt_auth(mac: str, key12: bytes, product_id: int, pid_order: str) -> bytes:
    m = mac_le(mac)
    aes_key = key12 + bytes([4, 3, 2, 1])
    nonce = m + product_id.to_bytes(2, pid_order) + bytes([0x52, 0x27, 0x61, 0x98])
    aad = bytes([0x87, 0xFE])
    if len(aes_key) != 16:
        raise ValueError(f"device key must be 12 bytes, got {len(key12)}")
    return AESCCM(aes_key, tag_length=4).encrypt(nonce, m, aad)


class AuthChannel:
    """Collect fe89 notifications and parse 0x59 frames."""

    def __init__(self) -> None:
        self._buf = bytearray()
        self._queue: asyncio.Queue[dict] = asyncio.Queue()

    def on_notify(self, _char, data: bytearray) -> None:
        _LOGGER.info("auth <- %s", data.hex(" "))
        self._buf += data
        while True:
            try:
                start = self._buf.index(AUTH_HEAD)
            except ValueError:
                self._buf.clear()
                return
            del self._buf[:start]
            if len(self._buf) < 5:
                return
            total = 4 + self._buf[3] + 1
            if len(self._buf) < total:
                return
            frame = bytes(self._buf[:total])
            del self._buf[:total]
            if sum(frame[:-1]) & 0xFF != frame[-1]:
                _LOGGER.warning("auth checksum error: %s", frame.hex(" "))
                continue
            self._queue.put_nowait({"seq": frame[1], "cmd": frame[2], "data": frame[4:-1]})

    async def wait(self, timeout: float) -> dict | None:
        try:
            return await asyncio.wait_for(self._queue.get(), timeout)
        except TimeoutError:
            return None


class ControlChannel:
    """Collect ae3c notifications, split on CRLF, decode JSON."""

    def __init__(self) -> None:
        self._buf = bytearray()
        self.messages: asyncio.Queue[dict | str] = asyncio.Queue()

    def on_notify(self, _char, data: bytearray) -> None:
        _LOGGER.debug("ctrl <- %s", data.hex(" "))
        self._buf += data
        while b"\n" in self._buf:
            line, _, rest = bytes(self._buf).partition(b"\n")
            self._buf = bytearray(rest)
            text = line.decode("utf-8", "replace").strip()
            if not text:
                continue
            try:
                msg: dict | str = json.loads(text)
            except json.JSONDecodeError:
                msg = text
            print(f"  ctrl <- {msg}")
            self.messages.put_nowait(msg)


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
async def cmd_scan(args: argparse.Namespace) -> None:
    seen: dict[str, tuple[BLEDevice, AdvertisementData]] = {}

    def on_adv(dev: BLEDevice, adv: AdvertisementData) -> None:
        name = adv.local_name or dev.name or ""
        yeelight = name.startswith(NAME_PREFIXES) or any(
            cid in adv.manufacturer_data for cid in YEELIGHT_COMPANY_IDS
        )
        if yeelight or args.all:
            seen[dev.address] = (dev, adv)

    print(f"Scanning {args.timeout}s ...")
    async with BleakScanner(on_adv):
        await asyncio.sleep(args.timeout)

    if not seen:
        print("No Yeelight devices found.")
        return
    for address, (dev, adv) in seen.items():
        print(f"\n{address}  name={adv.local_name or dev.name!r}  rssi={adv.rssi}")
        for cid, raw in adv.manufacturer_data.items():
            print(f"  manufacturer 0x{cid:04x} ({len(raw)} B): {raw.hex(' ')}")
            if cid in YEELIGHT_COMPANY_IDS:
                pid = DEFAULT_PRODUCT_ID
                for order in ("big", "little"):
                    needle = pid.to_bytes(2, order)
                    idx = raw.find(needle)
                    if idx >= 0:
                        print(f"    productId 0x{pid:04x} found ({order}) at offset {idx}")
                ml = mac_le(address) if ":" in address else b""
                if ml and ml in raw:
                    print(f"    MAC (little-endian) at offset {raw.find(ml)}")
        for uuid, raw in adv.service_data.items():
            print(f"  service_data {uuid}: {raw.hex(' ')}")
        if adv.service_uuids:
            print(f"  service_uuids: {adv.service_uuids}")


async def do_auth(
    client: BleakClient,
    auth: AuthChannel,
    address: str,
    state: dict,
    pair: bool,
    product_id: int,
    pid_order: str,
) -> bool:
    entry = state.get(address.upper(), {})

    async def send(seq: int, cmd: int, data: bytes = b"", timeout: float = 10.0) -> dict | None:
        pkt = build_auth_packet(seq, cmd, data)
        _LOGGER.info("auth -> %s", pkt.hex(" "))
        await client.write_gatt_char(AUTH_WRITE, pkt, response=True)
        resp = await auth.wait(timeout)
        print(f"  auth cmd {cmd}: response {resp}")
        return resp

    if pair:
        print(
            "\n[pair] Sending Pair (cmd 1). If the lights blink or need a button press, do it now (60 s)."
        )
        resp = await send(1, CMD_PAIR, timeout=60)
        if resp is None:
            print("[pair] no response to Pair")
            return False
        print("[pair] Sending ReadKey (cmd 2)")
        resp = await send(2, CMD_READ_KEY)
        if not resp or not resp["data"]:
            print("[pair] no key received")
            return False
        key = bytes(resp["data"])
        print(f"[pair] device key ({len(key)} B): {key.hex()}")
        entry["key"] = key.hex()
        state[address.upper()] = entry
        save_state(state)

    if "key" not in entry:
        print("No stored key for this device. Run with --pair first.")
        return False

    key = bytes.fromhex(entry["key"])
    orders = (
        [pid_order] if pid_order != "auto" else [entry.get("pid_order", "big"), "little", "big"]
    )
    tried: set[str] = set()
    for order in orders:
        if order in tried:
            continue
        tried.add(order)
        data = encrypt_auth(address, key[:12], product_id, order)
        print(
            f"\n[auth] AuthKey (cmd 3) productId=0x{product_id:04x} order={order} data={data.hex(' ')}"
        )
        resp = await send(3, CMD_AUTH_KEY, data)
        if resp is None:
            print("[auth] no response to AuthKey")
            continue
        ok_guess = bytes(resp["data"]) == mac_le(address)
        print(f"[auth] AuthKey response data={bytes(resp['data']).hex(' ')} (looks ok: {ok_guess})")
        resp = await send(4, CMD_AUTH_SUCCESS)
        entry["pid_order"] = order
        state[address.upper()] = entry
        save_state(state)
        return True
    return False


async def send_json(
    client: BleakClient,
    ctrl: ControlChannel,
    msg_id: int,
    method: str,
    params: list,
    mtu_payload: int,
) -> None:
    line = (
        json.dumps({"id": msg_id, "method": method, "params": params}, separators=(",", ":"))
        + "\r\n"
    )
    raw = line.encode()
    print(f"  ctrl -> {line.strip()}")
    for i in range(0, len(raw), mtu_payload):
        await client.write_gatt_char(CTRL_WRITE, raw[i : i + mtu_payload], response=True)
    await asyncio.sleep(1.5)


def parse_cmd(text: str) -> tuple[str, list]:
    method, _, rest = text.strip().partition(" ")
    params = json.loads(rest) if rest.strip() else []
    if not isinstance(params, list):
        params = [params]
    return method, params


async def cmd_run(args: argparse.Namespace) -> None:
    state = load_state()
    address = args.address

    print(f"Locating {address} ...")
    device = await BleakScanner.find_device_by_address(address, timeout=args.timeout)
    if device is None:
        print("Device not found. Is it powered and not connected to the phone app?")
        return

    async with BleakClient(device, timeout=30) as client:
        print(f"Connected. MTU={client.mtu_size}")
        for service in client.services:
            print(f"  service {service.uuid}")
            for ch in service.characteristics:
                print(f"    char {ch.uuid} {ch.properties}")

        auth = AuthChannel()
        ctrl = ControlChannel()
        await client.start_notify(AUTH_NOTIFY, auth.on_notify)
        await client.start_notify(CTRL_NOTIFY, ctrl.on_notify)

        if not args.skip_auth:
            ok = await do_auth(
                client, auth, address, state, args.pair, args.product_id, args.pid_order
            )
            print(f"\nAuth result: {'OK' if ok else 'FAILED'}")
            if not ok and not args.force:
                return

        mtu_payload = max(20, (client.mtu_size or 23) - 3)
        commands = args.cmd or [
            'get_prop ["power","bright","hue","sat","ct"]',
            "get_ver",
        ]
        print("\n[control]")
        for i, text in enumerate(commands, start=1):
            method, params = parse_cmd(text)
            await send_json(client, ctrl, i, method, params, mtu_payload)

        if args.listen:
            print(f"\nListening {args.listen}s for notifications ...")
            await asyncio.sleep(args.listen)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="scan and dump advertisements")
    p_scan.add_argument("--timeout", type=float, default=10)
    p_scan.add_argument("--all", action="store_true", help="show non-Yeelight devices too")

    p_run = sub.add_parser("run", help="connect, auth, send commands")
    p_run.add_argument("--address", required=True)
    p_run.add_argument("--pair", action="store_true", help="run Pair + ReadKey first")
    p_run.add_argument("--product-id", type=lambda s: int(s, 0), default=DEFAULT_PRODUCT_ID)
    p_run.add_argument("--pid-order", choices=["auto", "big", "little"], default="auto")
    p_run.add_argument("--cmd", action="append", help='e.g. \'set_power ["on","smooth",500]\'')
    p_run.add_argument(
        "--skip-auth", action="store_true", help="send control commands without auth"
    )
    p_run.add_argument("--force", action="store_true", help="send commands even if auth failed")
    p_run.add_argument("--listen", type=float, default=0, help="seconds to keep listening")
    p_run.add_argument("--timeout", type=float, default=15)

    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    logging.getLogger("bleak").setLevel(logging.WARNING)

    asyncio.run(cmd_scan(args) if args.command == "scan" else cmd_run(args))


if __name__ == "__main__":
    main()
