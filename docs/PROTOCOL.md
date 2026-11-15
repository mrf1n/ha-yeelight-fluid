# Yeelight BLE lights protocol

Local Bluetooth LE protocol used by Yeelight BLE lighting products (Christmas String Lights,
strips, Aurora Eave, curtain lights). Verified on Christmas String Lights
(`YLBT_CHRI_xxxx`, firmware 56, 200 LEDs) unless marked **VERIFY**.

The Jieli service (`ae00` / `ae01` / `ae02`) is used only for firmware updates, not for control.

## 1. Discovery

- Local name prefix: `YLBT_` (Christmas lights: `YLBT_CHRI`).
- Advertised service UUID `fe87`.
- Manufacturer data, company ID `0x0164`, 16 bytes:

  ```
  offset 0   product_id (uint16 LE)      e.g. 04 28 -> 0x2804
  offset 2   4 bytes, unknown            e.g. 01 01 07 00
  offset 6   MAC address, little-endian (6 bytes)
  offset 12  4 bytes, unknown            e.g. 01 00 00 00
  ```

- Product model id = `0x01000000 + product_id` (Christmas lights: `0x2804` -> `16787460`).

## 2. GATT

16-bit UUIDs on base `0000xxxx-0000-1000-8000-00805f9b34fb`.

| Purpose | Service | Characteristic | Properties |
|---|---|---|---|
| Auth write | `fe87` | `fe88` | write |
| Auth notify | `fe87` | `fe89` | notify |
| Control write | `ae3a` | `ae3b` | write |
| Control notify | `ae3a` | `ae3c` | notify |
| Bulk data write | `ae3a` | `ae3d` | write (XModem, optional) |
| Bulk data notify | `ae3a` | `ae3e` | notify (optional) |

MTU negotiates to 512 where supported; writes are chunked to `MTU - 3`.

## 3. Authentication (`fe88` / `fe89`)

### 3.1 Frame

```
0x59 | seq | cmd | len | data[len] | checksum
checksum = sum(all previous bytes) & 0xFF
```

Responses use the same frame with `seq | 0x80`.

### 3.2 Commands

| Name | seq | cmd | Request data | Response data |
|---|---|---|---|---|
| Pair | 1 | 1 | — | — (arrives after ~20 s confirmation window) |
| ReadKey | 2 | 2 | — | 12-byte device key |
| AuthKey | 3 | 3 | 10-byte token (§3.3) | device MAC, little-endian (6 bytes) |
| AuthSuccess | 4 | 4 | — | — |

- **First pairing:** Pair -> ReadKey (store key) -> AuthKey -> AuthSuccess.
- **Reconnect:** AuthKey -> AuthSuccess with the stored key.
- A wrong token gets no reply.
- **Firmware 56 does not enforce auth:** control commands work without it. The only difference
  observed is that the full `props` dump on connect is sent only after auth.

### 3.3 AuthKey token

```
mac_le  = MAC bytes, reversed                                  # 6 bytes
aes_key = key12 + 04 03 02 01                                  # 16 bytes
nonce   = mac_le + product_id.to_bytes(2, "big") + 52 27 61 98 # 12 bytes
aad     = 87 fe
token   = AES-CCM(aes_key, nonce, tag_len=4).encrypt(mac_le, aad)   # 6 ct + 4 tag
```

## 4. Control: JSON-RPC (`ae3b` / `ae3c`)

### 4.1 Framing

Request (UTF-8, one line):

```
{"id": n, "method": "<method>", "params": [...]}\r\n
```

- Reply: `{"id": n, "result": [...]}` (usually `["ok"]`).
- Push: `{"method": "props", "params": {...}}` after every state change.
- Error code `"201"`: stop writing and reset.
- Notifications may be split across packets; reassemble on `\n`.

### 4.2 Properties

After auth the device pushes all properties:

| Property | Notes |
|---|---|
| `power` | `"on"` / `"off"` |
| `bright` | 1–100 |
| `color_mode` | `2` = colour temperature, `3` = HSV, `14` = effect / music |
| `hue`, `sat`, `rgb` | HSV mode |
| `ct` | CT mode |
| `fx_effect` | JSON string `{"effect_id": n, "custom_id": n}` |
| `mic_music_mode` | JSON string `{"on": 0\|1, "effect_id": n, ...}` |
| `fw_version` | e.g. `56` |
| `strip_length` | number of LEDs, e.g. `200` |
| `save_state`, `init_power_opt`, `pair_succed` | config flags |

`get_prop ["power", "bright", ...]` returns values as strings in request order.

### 4.3 Methods

| Method | Params | Notes |
|---|---|---|
| `set_power` | `["on"\|"off", "smooth", ms]` | |
| `set_scene` | `["bright", 1-100, 0]` | brightness; the official app uses this, not `set_bright` |
| `set_bright` | `[1-100, "smooth", ms]` | not used by the official app **VERIFY** |
| `set_hsv` | `[hue 0-359, sat 0-100, "smooth", ms]` | sets `color_mode 3` |
| `set_ct_abx` | `[kelvin, "smooth", ms]` | sets `color_mode 2`; only for products with a CT range (Christmas lights are RGB only) |
| `get_prop` | `[name, ...]` | |
| `get_ver` | `[]` | returns `[fw_version]` |
| `set_fx_effect` | `[effect_id, 0, apply, {segcfg}]` | sets `color_mode 14`; `apply` 1 = select effect, 0 = live preview |
| `update_fx_effect` | `[{segcfg}]` | change running effect (rate / direction / mixer / data) |
| `get_fx_effect` | `[]` | `[effect_id, custom_id, {segcfg}]` |
| `set_ps` | `["mic_music_mode", "<json>"]` | music mode, see §4.5 |
| `set_ps` | `["cfg_init_power", n]` | power-on behaviour: `0` restore previous state, `1` on, `2` off; read back as `init_power_opt` |

Seen but not yet characterised: `reset_fx_effect`, `get/update_persist_effect_list`,
`get/set_multi_connection_state`, `set_multi_connection`, `select_dev`, `req_ota`.

### 4.4 Segment config (`segcfg`)

| Key | Type | Notes |
|---|---|---|
| `rate` | int | effect speed, 1–255, default 128; the app shows it as percent = ceil(rate / 2.55); whether higher = faster **VERIFY** |
| `color` | int[] | ARGB, e.g. `0xFFFF0000` = red; device returns signed int32 |
| `direction` | int | `0` / `1` for directional effects (`0` = up **VERIFY**) |
| `intensity` | int | default 128 |
| `start`, `end` | int | LED range, default `0`–`strip_length` |
| `onoff`, `mode`, `mixer` | int | |
| `data` | string | base64 custom data |

Examples:

```
set_fx_effect [81, 0, 1, {"rate": 50}]
set_fx_effect [47, 0, 1, {"rate": 50, "color": [4294901760], "direction": 1}]
update_fx_effect [{"rate": 90}]
```

### 4.5 Music mode (microphone)

```
set_ps ["mic_music_mode", "{\"on\":1,\"effect_id\":84,\"palatte\":[<16 ARGB ints>]}"]
set_ps ["mic_music_mode", "{\"on\":0}"]
```

- Turning on needs a music `effect_id` and a 16-colour `palatte` (sic).
  **`"effect_id": 0` hangs the firmware**; only a power cycle recovers it.
- Rhythm effects / effect ids. Christmas String Lights offer four: Breath 84, Shine 85,
  Spectrum 86, Converge 83. Other products also use 87 and 88.
  (Shine = 85 is inferred from the app's per-device effect list **VERIFY**.)
- `palatte`: 16 ARGB ints. One colour is repeated 16 times; with N colours each colour fades
  linearly into the next (wrapping to the first), over 16 / N slots, the first 16 mod N colours getting one extra slot.
  Any colours work. The app's 45 predefined five-colour schemes (Mood, Landscape, Music,
  Holiday) are in `custom_components/yeelight_lights_ble/music.py`; the default is Mood / Happy.
- Turning off sends only `on: 0`; the device restores the previous effect.

### 4.6 Custom effect (DIY Graffiti)

```
set_fx_effect [36, 0, 1, {"mixer": m, "rate": r, "direction": d, "data": "<base64>"}]
```

- Effect id `36`. `data`: 4 bytes per LED, in `A, R, G, B` order, each byte gamma corrected
  (`int(255 * (v / 255) ** 2.2)`), base64 encoded. One entry per LED (`strip_length`)
  **VERIFY** on the device.
- `mixer` (dynamic effect): `0` none (static), `2` Translation, `3` Breath, `4` Flashing,
  `5` Stack. `6` (scrolling) exists for other products. A static pattern sends `data` only.
- `rate` (speed) is sent with a dynamic effect; `direction` (`0` up, `1` down) only with
  Translation and Stack.
- The app sends `apply` = `1` when it saves and applies a pattern and `0` while previewing.
  While painting it sends the whole frame with `update_fx_effect [{"data": "<base64>"}]`.
- "Random" colours and the segment presets are generated by the app; the device only gets
  the resulting `data`.

## 5. Christmas String Lights effects

23 preset effects. Firmware ids differ from catalogue ids in one case: Christmas (82) is sent as 81.
Warm glow (97), Snow white (98) and Candy cane (99) need firmware ≥ 52.
Meteor (47) and Waves (42) support direction. Full list: `custom_components/yeelight_lights_ble/const.py`.
