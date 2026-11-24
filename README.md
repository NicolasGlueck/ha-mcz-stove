# MCZ Pellet Stove (pre-Maestro)

Home Assistant integration for **MCZ pellet stoves with the older Wi-Fi module — the generation before Maestro**.
It talks to the stove **directly over your home network**: no cloud, no account, no app.

> **Maestro stoves are not supported.** For those, use the [Maestro MCZ (cloud)](https://github.com/Robbe-B/maestro_mcz) integration.

[![hacs](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![validate](https://github.com/NicolasGlueck/ha-mcz-stove/actions/workflows/validate.yml/badge.svg)](https://github.com/NicolasGlueck/ha-mcz-stove/actions/workflows/validate.yml)
[![Buy me a coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-NicolasGlueck-ffdd00?logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/nicolasglueck)

## Is this for my stove?

Yes, if your MCZ stove has a Wi-Fi module that answers on **TCP port 5001** in your network
(the module is made by HottoH; it reports itself as `HOTTOH` with a firmware like `6.2.41`).
If your stove is a **Maestro** model, this integration will not find it.

Tested with an MCZ pellet stove with module firmware 6.2.41. Other pre-Maestro MCZ models should work the same way.
If something is off on your model, please open an issue and attach the diagnostics download (see below).

## Features

- Turn the stove on and off
- Set the power level, the front fan and Comfort Air
- Taps are debounced: change a value several times quickly and only the final value is sent to the stove
- State with all phases (ignition 1–7, heating, shutdown, eco stop, pellets low/empty, ignition failed, door open, …)
- Room and exhaust temperature, actual power level, exhaust fan speed, fan speeds
- Eco mode, timer program and fault as binary sensors
- Wi-Fi signal and firmware of the module
- Set up in the UI, one device per stove, English and German
- No external Python packages

## Requirements

- Home Assistant 2026.3 or newer
- The IP address of the stove's Wi-Fi module (best give it a fixed address in your router)

## Installation

### HACS

1. HACS → menu (three dots) → **Custom repositories**
2. Repository `https://github.com/NicolasGlueck/ha-mcz-stove`, type **Integration**
3. Install **MCZ Pellet Stove (pre-Maestro)** and restart Home Assistant

### Manual

Copy `custom_components/mcz_stove` into the `custom_components` folder of your Home Assistant configuration and restart.

## Setup

Settings → Devices & services → **Add integration** → *MCZ Pellet Stove (pre-Maestro)* → name, IP address (port 5001).

## Entities

| Entity | Type | Notes |
|---|---|---|
| Pellet stove | switch | on/off |
| Status | sensor (enum) | phase of the stove, attribute `code` = raw state code |
| Room temperature | sensor | measured by the stove |
| Exhaust temperature | sensor | |
| Target temperature | sensor | stove's own setpoint, disabled by default |
| Power level | sensor | actual power (100 % = level 5) |
| Exhaust fan | sensor | rpm |
| Front fan, Comfort Air, Fan 3 | sensor | actual speed, only the fans your stove reports |
| Power level setpoint | number | limits come from the stove |
| Front fan / Comfort Air / Fan 3 setpoint | number | 0 … maximum reported by the stove |
| Eco, Timer program | binary sensor | |
| Fault | binary sensor | pellets low/empty, power failure and all alarm codes 50–99 (ignition failed, no pellets, door open, …) |
| Wi-Fi signal | sensor | diagnostic |

On *Multi Air* models, Comfort Air and Fan 3 are the two ducted outlets. You can rename all entities in Home Assistant.

## How it works

The module listens on TCP port 5001 and speaks a simple plain-text protocol:

```
'#' + sequence(5) + client(4) + length(4, hex) + command(4) + data + CRC-16/CCITT-FALSE(4, hex) + '\n'
```

- `DATR` `0;` reads all values as a `;`-separated list
- `DATW` `<parameter>;<value>;` writes a value (0 = on/off, 2 = power level, 5/6/7 = fans 1/2/3)
- `INFR` returns firmware and Wi-Fi signal

The integration polls every 15 seconds, opens one connection per command and never sends two commands at the same time.

## Diagnostics

Device page → **Download diagnostics**. The file contains the raw field list of your stove,
which helps to support other models. The IP address is removed.

## Credits

Field meanings are based on [hottohpy](https://github.com/benlbrm/hottohpy) by benlbrm, verified and corrected on a real MCZ stove.
This project is not affiliated with MCZ or the maker of the Wi-Fi module.

## Support

If this integration saves you a few trips to the stove, you can [buy me a coffee](https://buymeacoffee.com/nicolasglueck). Thank you!

## License

MIT
