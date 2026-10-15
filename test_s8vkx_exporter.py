from s8vkx_exporter import render

# Raw words from an S8VK-X12024A-EIP (serial replaced with an example value) (0x0000-0x0009, 0x000A-0x002B).
MEAS = [0x0100, 2410, 0, 10, 149, 999, 0, 168, 0, 16]
INFO = [0x002F, 0x0302, 0x0690, 1, 4, 0x0123, 0x4567] + [0] * 11 + \
    [int.from_bytes(b'S8VK-X12024A-EIP'[i:i + 2], 'big') for i in range(0, 16, 2)] + [0] * 8


def test_render():
    out = render(MEAS, INFO)
    for line in [
        's8vk_up 1',
        's8vk_output_voltage_volts 24.1',
        's8vk_output_current_amperes 0.0',
        's8vk_peak_current_amperes 0.1',
        's8vk_replacement_years 14.9',
        's8vk_replacement_ratio 0.999',
        's8vk_run_seconds_total 604800',
        's8vk_continuous_run_seconds 960',
        's8vk_status{flag="replace_ful"} 1',
        's8vk_status{flag="overheat_alarm"} 0',
        's8vk_info{model="S8VK-X12024A-EIP",serial="01234567",revision="1.4"} 1',
        '# TYPE s8vk_run_seconds_total counter',
        '# TYPE s8vk_output_voltage_volts gauge',
        '# HELP s8vk_output_voltage_volts Output voltage measured.',
    ]:
        assert line in out.splitlines(), line


def test_render_down():
    assert render(None, None).strip().endswith('s8vk_up 0')


if __name__ == "__main__":
    test_render()
    test_render_down()
    print("ok")
