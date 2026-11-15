# Yeelight Lights (BLE) for Home Assistant

Unofficial, local-only Home Assistant integration for Yeelight Bluetooth lights managed by the
**Yeelight** app. No cloud account needed.

> Not affiliated with or endorsed by Yeelight. The Yeelight name and logo are trademarks of their
> owner and are used here only to identify compatible devices.

## Supported devices

| Device | SKU | Status |
|---|---|---|
| Christmas String Lights 33 ft / 66 ft | YLYDD-0055 / YLYDD-0056 | Tested (fw 56) |

Other Yeelight BLE products from the same app (strips, Aurora Eave, curtain lights) use the same
protocol and may be added later — open an issue with your device's `scan` output from `tools/probe.py`.

## Features

- Auto-discovery over Bluetooth (local adapter or ESPHome Bluetooth proxy with active connections)
- Local pairing (no Yeelight account), or add without pairing
- Light: on/off, brightness, RGB (HS), color temperature, transitions
- 23 built-in effects + Music mode
- Effect select, effect speed slider, effect direction (Meteor / Waves)
- Music mode switch (uses the lights' built-in microphone)
- `yeelight_lights_ble.set_effect` action with speed, colors and direction
- Diagnostics: firmware, RSSI, LED count
- Connection modes: connect on demand (default) or stay connected for instant state push

## Installation

### HACS (custom repository)

1. HACS → ⋮ → **Custom repositories** → add `https://github.com/mrf1n/ha-yeelight-lights-ble`, type **Integration**.
2. Install **Yeelight Lights (BLE)** and restart Home Assistant.

### Manual

Copy `custom_components/yeelight_lights_ble` into your `config/custom_components/` and restart.

## Setup

1. Close the Yeelight app on your phone (a BLE device accepts one connection at a time).
2. The lights are discovered automatically — or go to **Settings → Devices & services → Add integration → Yeelight Lights (BLE)**.
3. Choose **Pair**, press **Submit**, and confirm on the lights if they flash. Pairing can take up to ~20 s.

Pairing from Home Assistant may require re-pairing the lights in the phone app afterwards.

### Options

| Option | Default | Description |
|---|---|---|
| Keep connected | off | Hold the BLE connection open for instant state updates. Uses a connection slot. |
| Disconnect after idle | 60 s | On-demand mode: disconnect after this many idle seconds. |
| Poll interval | 300 s | On-demand mode: how often to refresh state. |

## Action: `yeelight_lights_ble.set_effect`

```yaml
action: yeelight_lights_ble.set_effect
target:
  entity_id: light.ylbt_chri_cda1
data:
  effect: meteor
  speed: 70
  colors: [[255, 0, 0], [0, 255, 0]]
  direction: down
```

## Development

- Protocol notes: [`docs/PROTOCOL.md`](docs/PROTOCOL.md)
- Hardware probe: `pip install bleak cryptography && python tools/probe.py scan`

## License

MIT
