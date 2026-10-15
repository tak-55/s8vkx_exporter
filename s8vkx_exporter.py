"""Prometheus exporter for OMRON S8VK-X power supplies over Modbus TCP (stdlib only).

Usage: python3 s8vkx_exporter.py <host> [listen_port]   -> http://:9502/metrics
Register map: OMRON Cat. No. T213 section 4-3.
"""
import socket
import struct
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UNIT_ID = 0xFF  # S8VK-X only answers on unit 255
STATUS_FLAGS = {0: 'memory_error', 1: 'overheat_abnormality', 2: 'current_measurement_error',
                3: 'voltage_measurement_error', 4: 'overheat_alarm', 8: 'replace_ful', 9: 'replace_hlf'}
METRICS = {  # name: (type, help)
    's8vk_up': ('gauge', '1 if the last Modbus read succeeded.'),
    's8vk_output_voltage_volts': ('gauge', 'Output voltage measured.'),
    's8vk_output_current_amperes': ('gauge', 'Output current measured.'),
    's8vk_peak_current_amperes': ('gauge', 'Peak hold current measured.'),
    's8vk_replacement_years': ('gauge', 'Estimated years until replacement.'),
    's8vk_replacement_ratio': ('gauge', 'Remaining life until replacement (0-1).'),
    's8vk_run_seconds_total': ('counter', 'Total run time.'),
    's8vk_continuous_run_seconds': ('gauge', 'Run time since last power-on.'),
    's8vk_status': ('gauge', 'S8VK-X status bits (1 = occurred).'),
    's8vk_info': ('gauge', 'Device identity.'),
}


def with_metadata(lines):
    out, seen = [], set()
    for line in lines:
        name = line.split('{')[0].split(' ')[0]
        if name not in seen:
            seen.add(name)
            typ, help_ = METRICS[name]
            out += [f'# HELP {name} {help_}', f'# TYPE {name} {typ}']
        out.append(line)
    return '\n'.join(out) + '\n'


def read_holding(host, addr, count, timeout=3):
    with socket.create_connection((host, 502), timeout) as s:
        s.sendall(struct.pack('>HHHBBHH', 1, 0, 6, UNIT_ID, 3, addr, count))
        r = b''
        while len(r) < 9 + 2 * count:
            chunk = s.recv(256)
            if not chunk:
                break
            r += chunk
    if len(r) < 9 or r[7] != 3:
        raise IOError(f'modbus error response: {r.hex()}')
    return list(struct.unpack(f'>{count}H', r[9:9 + 2 * count]))


def render(meas, info):
    """meas: words 0x0000-0x0009, info: words 0x000A-0x002B. None means scrape failed."""
    if meas is None:
        return with_metadata(['s8vk_up 0'])
    u32 = lambda w, i: (w[i] << 16) | w[i + 1]
    lines = [
        's8vk_up 1',
        f's8vk_output_voltage_volts {meas[1] / 100}',
        f's8vk_output_current_amperes {meas[2] / 100}',
        f's8vk_peak_current_amperes {meas[3] / 100}',
        f's8vk_replacement_years {meas[4] / 10}',
        f's8vk_replacement_ratio {meas[5] / 1000}',
        f's8vk_run_seconds_total {u32(meas, 6) * 3600}',
        f's8vk_continuous_run_seconds {u32(meas, 8) * 60}',
    ]
    lines += [f's8vk_status{{flag="{name}"}} {meas[0] >> bit & 1}' for bit, name in STATUS_FLAGS.items()]
    model = struct.pack('>16H', *info[18:34]).rstrip(b'\0').decode('ascii', 'replace')
    lines.append(f's8vk_info{{model="{model}",serial="{u32(info, 5):08x}",revision="{info[3]}.{info[4]:x}"}} 1')
    return with_metadata(lines)


def scrape(host):
    try:
        # Reading across 0x0009/0x000A returns exception 3, so read the two groups separately.
        return render(read_holding(host, 0x0000, 10), read_holding(host, 0x000A, 34))
    except (OSError, struct.error) as e:
        print(f'scrape {host} failed: {e}', file=sys.stderr)
        return render(None, None)


def main():
    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9502

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != '/metrics':
                self.send_error(404)
                return
            body = scrape(host).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    ThreadingHTTPServer(('', port), Handler).serve_forever()


if __name__ == '__main__':
    main()
