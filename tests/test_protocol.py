"""Protocol tests (frame layouts verified on real hardware, fw 56; key/MAC synthetic)."""

from custom_components.yeelight_lights_ble.protocol import (
    AuthFrameParser,
    JsonLineParser,
    argb_to_rgb,
    build_auth_packet,
    encode_request,
    encrypt_auth,
    mac_le,
    parse_manufacturer_data,
    rate_to_speed,
    rgb_to_argb,
    speed_to_rate,
)

from .conftest import ADDRESS, KEY_HEX, MANUFACTURER_DATA


def test_auth_packets() -> None:
    assert build_auth_packet(1, 1).hex(" ") == "59 01 01 00 5b"
    assert build_auth_packet(2, 2).hex(" ") == "59 02 02 00 5d"
    assert build_auth_packet(4, 4).hex(" ") == "59 04 04 00 61"


def test_encrypt_auth_matches_capture() -> None:
    data = encrypt_auth(ADDRESS, bytes.fromhex(KEY_HEX), 0x2804)
    assert data.hex(" ") == "d6 1e 9d 2a 2f d0 42 c4 7c 24"
    assert build_auth_packet(3, 3, data).hex(" ") == (
        "59 03 03 0a d6 1e 9d 2a 2f d0 42 c4 7c 24 c9"
    )


def test_auth_parser_chunks() -> None:
    parser = AuthFrameParser()
    raw = bytes.fromhex("59830306ffeeddccbbaae0")
    assert parser.feed(raw[:3]) == []
    frames = parser.feed(raw[3:])
    assert len(frames) == 1
    assert frames[0].cmd == 3
    assert frames[0].seq == 3
    assert frames[0].data == mac_le(ADDRESS)


def test_auth_parser_bad_checksum() -> None:
    assert AuthFrameParser().feed(bytes.fromhex("5981010000")) == []


def test_manufacturer_data() -> None:
    adv = parse_manufacturer_data(MANUFACTURER_DATA)
    assert adv is not None
    assert adv.product_id == 0x2804
    assert adv.mac == ADDRESS


def test_json_lines() -> None:
    parser = JsonLineParser()
    assert parser.feed(b'{"id":1,"res') == []
    msgs = parser.feed(b'ult":["ok"]}\r\n{"method":"props","params":{"bright":30}}\r\n')
    assert msgs == [
        {"id": 1, "result": ["ok"]},
        {"method": "props", "params": {"bright": 30}},
    ]


def test_encode_request() -> None:
    assert encode_request(1, "set_bright", [30, "smooth", 500]) == (
        b'{"id":1,"method":"set_bright","params":[30,"smooth",500]}\r\n'
    )


def test_colors() -> None:
    assert argb_to_rgb(-1) == (255, 255, 255)
    assert rgb_to_argb((255, 0, 0)) == 4294901760


def test_speed_rate_conversion() -> None:
    assert rate_to_speed(128) == 51
    assert rate_to_speed(255) == 100
    assert rate_to_speed(1) == 1
    assert speed_to_rate(1) == 3
    assert speed_to_rate(51) == 131
    assert speed_to_rate(100) == 255
    assert speed_to_rate(0) == 1
