# Yeelight Fluid BLE protocol (app 1.8.0)

Recovered statically from `com.yeelight.yeelight_fluid` 1.8.0 (blutter output, Dart 3.11.5, unobfuscated).
Applies to Yeelight BLE products in the app (Christmas String Lights yeePid 16787460, Aurora Eave,
strips, curtain lights). Items marked **VERIFY** still need confirmation on real hardware.

Jieli RCSP (`ae00/ae01/ae02`, channel `com.yeelight.jlBleOTA`) is used **only for OTA** — not control.

## 0. Hardware-verified (2026-11-15, YLBT_CHRI_xxxx, fw 56, strip_length 200)

- Adv: company `0x0164`, 16 B: `04 28 | 01 01 07 00 | <mac_le 6> | 01 00 00 00`
  → productId `0x2804` little-endian at offset 0, MAC LE at offset 6. Service UUID `fe87` advertised.
- MTU 512 on Windows.
- Pair: response arrived ~20 s after request (`59 81 01 00 db`) — device-side confirmation window.
- Replies set seq high bit (`0x80 | seq`).
- ReadKey → 12-byte key. AuthKey with productId **big-endian** in nonce → reply data = MAC LE (6 B). AuthSuccess → empty reply.
- On connect device pushes full `props`: `fx_effect, mic_music_mode, save_state, init_power_opt,
  fw_version, strip_length, color_mode, bright, hue, sat, rgb, power, pair_succed`.
- `get_prop [...]` → `{"id":n,"result":[...strings]}`; `set_power ["on","smooth",500]`, `set_bright [30,"smooth",500]` → `["ok"]` + `props` push.

- **Auth not enforced on fw 56:** with no auth, `set_bright` still → `["ok"]` + props push. Only difference
  seen: no full `props` dump on connect. Integration authenticates when key stored, works without it otherwise.
- AuthKey with productId little-endian in nonce → **no reply** (device verifies CCM). Big-endian confirmed.

## 1. Discovery

- Local name prefix: `YLBT_CHRI` (Christmas lights, from `device_configs/16787460.json`).
- Manufacturer data company ID `0xFE87` (alt `0x0164`), parsed by `BeaconData.fromBytes`
  (payload length 11 or 17 bytes; contains little-endian MAC and product id). **VERIFY offsets.**
- yeePid = `0x01000000 + productId` → Christmas lights productId = `0x2804` (10244). **VERIFY.**

## 2. GATT

| Purpose | Service | Characteristic | Notes |
|---|---|---|---|
| Auth write | `fe87` | `fe88` | write |
| Auth notify | `fe87` | `fe89` | notify |
| Control write | `ae3a` | `ae3b` | JSON-RPC, write |
| Control notify | `ae3a` | `ae3c` | JSON-RPC responses / props |
| XModem data | `ae3a` | `ae3d` | optional (effect/file upload) |
| XModem notify | `ae3a` | `ae3e` | optional |

16-bit UUIDs, base `0000xxxx-0000-1000-8000-00805f9b34fb`.
Source: `YeeBleAuthController::_initCharacteristic`, `YeeBleController::_initCharacteristic`.

## 3. Auth (required after connect, before control)

### 3.1 Frame (`BleAuthCmd::buildPacket`, `YeeBleAuthResponseHandler::_parsePacket`)

```
0x59 | seq | cmd | len | data[len] | checksum
checksum = sum(all previous bytes) & 0xFF
```

Responses use same frame ("Invalid packet head" / "Checksum error" on mismatch); parsed into `{seq, cmd, data}`.

### 3.2 Commands

| Class | seq | cmd | data |
|---|---|---|---|
| `BleAuthCmdPair` | 1 | 1 | none |
| `BleAuthCmdReadKey` | 2 | 2 | none → response data = device key (12 bytes) |
| `BleAuthCmdAuthKey` | 3 | 3 | `encryptData(...)` (10 bytes) |
| `BleAuthCmdAuthSuccess` | 4 | 4 | none |

- **Pairing (first time, app pairing pages):** Pair → wait for auth response (timeout, likely user
  confirmation on device — **VERIFY**) → ReadKey → store key as `bleEncryptKey` (hex) → AuthKey → AuthSuccess.
- **Every reconnect (`YeeBleController.connectIfNeeded` → `YeeBleAuthController.auth`):**
  AuthKey → AuthSuccess, using stored `bleEncryptKey`, `macAddress`, `productId`
  (from `DevicePersistentInfo`). No cloud involved.

### 3.3 `encryptData(mac, key12, productId)` (`ble_utils.dart`)

```
mac_le   = reversed(bytes.fromhex(mac.replace(":", "")))         # 6 bytes
aes_key  = key12 + 04 03 02 01                                    # 16 bytes
nonce    = mac_le + productId.to_bytes(2, "big") + 52 27 61 98    # 12 bytes
aad      = 87 fe
out      = AES-CCM(aes_key, nonce, tag_len=4).encrypt(plaintext=mac_le, aad)   # 6 ct + 4 tag
```

**VERIFY:** byte order of productId in nonce (code swaps bytes then stores 16-bit LE → big-endian).

## 4. Control: JSON-RPC over `ae3b`/`ae3c`

`YeeBleController::writeData`:

```
payload = json.dumps({"id": n, "method": m, "params": [...]}) + "\r\n"   # UTF-8
```

- Split into MTU-sized chunks (`SplitWrite.splitWrite`).
- Group/master writes prepend target MAC (little-endian) — not needed for single device.
- Device notifications are JSON (`method` / `props` / `params`); error code `"201"` = stop writing, reset.

### 4.1 Attribute → method (`attr_cmd_converter.dart`)

| Path (ep / cluster / attr) | Read | Write |
|---|---|---|
| 1 / 0x0006 / 0 OnOff | `get_prop ["power"]` | `set_power ["on"\|"off", "smooth", ms]` |
| 1 / 0x0008 / 0 Level | `get_prop ["bright"]` | `set_bright` |
| 1 / 0x0300 / 0,1 Hue, Sat | `get_prop ["hue"\|"sat"]` | `set_hsv` |
| 1 / 0x0300 / 7 CT | `get_prop ["ct"]` | `set_ct_abx` |
| 0xFC00 / 1,2 YeeBasic | `get_ver` | — |
| 1 / 0xFC00 / 0 power-on state | `get_prop ["init_power_opt"]` | `set_ps ["cfg_init_power", ...]` |
| 2 / 0xFC01 / 0 | `get_prop ["len_configured"]` | — |
| 2 / 0xFC04 / 0 strip length | `get_prop` | `set_ps` |
| 2 / 0xFC05 / 0,1 effect config V2 | `get_fx_effect` | `set_fx_effect` / `update_fx_effect` |
| 2 / 0xFC06 / 0 | `lighting_mode`, `mic_music_mode` via `get_prop` | `set_ps` |

### 4.2 Write methods (`write_cmd_converter.dart`)

`set_power, set_bright, set_hsv, set_ct_abx, set_scene, set_ps, set_fx_effect, update_fx_effect,
get_fx_effect, reset_fx_effect` (keys: `effect_id, rate, color, direction, intensity, onoff, mixer,
data, palatte`), `update_persist_effect_list / get_persist_effect_list` (`effect_id, custom_id,
effect_params`), `req_ota`, `get/set_multi_connection_state`, `set_multi_connection`, `select_dev`.

Hardware-verified 2026-11-15 (all → `["ok"]`):

- `set_fx_effect [81,0,1,{"rate":50}]` → props `fx_effect {"effect_id":81,"custom_id":0}`, `color_mode 14`.
- `set_fx_effect [47,0,1,{"rate":50,"color":[0xFFFF0000],"direction":1}]` → effect 47.
- `update_fx_effect [{"rate":90}]` ok. `get_fx_effect` → `[effect_id, custom_id, {onoff, mode, mixer,
  intensity(128), rate, start(0), end(200), direction, color[signed int32 ARGB]}]`.
- `set_hsv [120,100,"smooth",500]` → `color_mode 3, hue, sat, rgb`. `set_ct_abx [2700,"smooth",500]` → `color_mode 2, ct`.
- `set_ps ["mic_music_mode","{\"on\":1,\"effect_id\":0}"]` → `fx_effect 44/44`, `color_mode 14`; `on:0` restores previous effect.
- `color_mode`: 2 = CT, 3 = HSV, 14 = effect / music.

From asm (`SetPresetEffectCmd`, `SegmentxCfg::toYeeSpec`, `SetMicMusicModeCmd`):

```
set_fx_effect    [effect_id, 0, apply, {segcfg}]
update_fx_effect [{segcfg}]                      # rate / direction / mixer / data only
segcfg keys: onoff, mode, mixer, intensity, rate, color[ARGB ints], start, end (pair), direction, data (base64)
set_ps ["mic_music_mode", "{\"on\":0|1,\"effect_id\":n,\"palatte\":[...]}"]
set_power ["on"|"off", "smooth", 1000];  set_hsv [h, s, "smooth", ms];  set_ct_abx [ct, "smooth", ms]
set_scene ["bright", ...]   # level-with-onoff
```

**TODO:** remaining params order per method (esp. `set_fx_effect`), music flow (`mic_music_mode`,
`ble_music_sync_controller.dart`).

## 5. Effects (Christmas lights)

23 effect modes in `device_configs/16787460.json`; app effect id 82 (Christmas) maps to firmware 81.
