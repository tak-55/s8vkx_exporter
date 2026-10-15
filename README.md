# s8vkx_exporter

Prometheus exporter for OMRON S8VK-X switch-mode power supplies (`S8VK-X*-EIP`) over Modbus TCP.
Single file, Python 3 standard library only.

## Usage

```sh
python3 s8vkx_exporter.py <power-supply-host> [listen_port]   # default listen port: 9502
curl http://localhost:9502/metrics
```

```yaml
scrape_configs:
  - job_name: s8vk
    static_configs:
      - targets: ['exporter-host:9502']
```

One exporter process per power supply.

## Metrics

| Metric | Type | Description |
|---|---|---|
| `s8vk_up` | gauge | 1 if the last Modbus read succeeded |
| `s8vk_output_voltage_volts` | gauge | Output voltage measured |
| `s8vk_output_current_amperes` | gauge | Output current measured |
| `s8vk_peak_current_amperes` | gauge | Peak hold current measured |
| `s8vk_replacement_years` | gauge | Estimated years until replacement |
| `s8vk_replacement_ratio` | gauge | Remaining life until replacement (0-1) |
| `s8vk_run_seconds_total` | counter | Total run time |
| `s8vk_continuous_run_seconds` | gauge | Run time since last power-on |
| `s8vk_status{flag}` | gauge | Status bits: `memory_error`, `overheat_abnormality`, `current_measurement_error`, `voltage_measurement_error`, `overheat_alarm`, `replace_ful`, `replace_hlf` |
| `s8vk_info{model,serial,revision}` | gauge | Device identity |

`replace_ful` = 1 means plenty of life left (front display shows "FUL"); it is not an alarm.

## Notes on the device

- Modbus unit ID must be `0xFF`.
- Holding registers `0x0000-0x0009` (measurements) and `0x000A-0x002B` (device info) must be read
  separately; a read spanning both returns exception 3.
- Register map: OMRON Cat. No. T213, *S8VK-X Switch-mode Power Supplies Communications Manual*, section 4-3.

## Test

```sh
python3 test_s8vkx_exporter.py
```
