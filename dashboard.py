import json
import time
from collections import deque
from datetime import datetime

import serial
from rich import box
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Change this if your ESP32 appears on another COM port.
PORT = "COM4"
BAUD = 115200
BASELINE_SIZE = 10
AP_CHANGE_THRESHOLD = 3
RSSI_CHANGE_THRESHOLD_DB = 15

console = Console()
history = deque(maxlen=12)
events = deque(maxlen=8)
baseline = deque(maxlen=BASELINE_SIZE)


def timestamp():
    return datetime.now().strftime("%H:%M:%S")


def add_event(level, message):
    events.append((timestamp(), level, message))


def signal_quality(rssi):
    if rssi >= -50:
        return "EXCELLENT", "green"
    if rssi >= -60:
        return "GOOD", "bright_green"
    if rssi >= -70:
        return "FAIR", "yellow"
    return "WEAK", "red"


def build_dashboard(data, started_at, status):
    layout = Table.grid(expand=True)
    layout.add_column(ratio=1)

    title = Panel(
        Align.center(Text("SENTINEL // ESP32 WI-FI TELEMETRY", style="bold bright_cyan")),
        border_style="bright_cyan",
    )
    layout.add_row(title)

    if data:
        quality, quality_color = signal_quality(data["strongest_rssi"])
        metrics = Table.grid(expand=True, padding=(0, 2))
        metrics.add_column(justify="center", ratio=1)
        metrics.add_column(justify="center", ratio=1)
        metrics.add_column(justify="center", ratio=1)
        metrics.add_row(
            Text(f"{data['networks']}\nACCESS POINTS", style="bold bright_cyan"),
            Text(f"{data['strongest_rssi']} dBm\nSTRONGEST RSSI", style="bold yellow"),
            Text(f"{quality}\nSIGNAL QUALITY", style=f"bold {quality_color}"),
        )
        layout.add_row(Panel(metrics, title="LIVE TELEMETRY", border_style="blue"))

        details = Table(box=box.SIMPLE, expand=True)
        details.add_column("METRIC", style="dim")
        details.add_column("VALUE", style="white")
        details.add_row("Average RSSI", f"{data['avg_rssi']} dBm")
        details.add_row("Wi-Fi channels observed", str(data["channels"]))
        details.add_row("ESP32 sample", str(data.get("sample", "-")))
        details.add_row("Device uptime", f"{data.get('uptime_ms', 0) / 1000:.0f} seconds")
        layout.add_row(Panel(details, title="RADIO ENVIRONMENT", border_style="blue"))

    graph = Table(box=box.SIMPLE, expand=True)
    graph.add_column("#", width=3, style="dim")
    graph.add_column("ACCESS POINTS", ratio=1)
    graph.add_column("STRONGEST RSSI", ratio=2)
    for idx, item in enumerate(history, start=max(1, len(history) - len(history) + 1)):
        ap_bar = "#" * min(max(item["networks"], 0), 30)
        rssi_len = max(0, min(30, (item["strongest_rssi"] + 100) // 2))
        rssi_bar = "#" * rssi_len
        graph.add_row(str(idx), f"[cyan]{ap_bar}[/] {item['networks']}", f"[yellow]{rssi_bar}[/] {item['strongest_rssi']} dBm")
    layout.add_row(Panel(graph, title="RECENT SCANS (terminal bars)", border_style="blue"))

    event_table = Table(box=box.SIMPLE, expand=True)
    event_table.add_column("TIME", width=9)
    event_table.add_column("LEVEL", width=8)
    event_table.add_column("EVENT")
    for stamp, level, message in events:
        color = {"INFO": "cyan", "WARN": "yellow", "ALERT": "red"}.get(level, "white")
        event_table.add_row(stamp, f"[{color}]{level}[/]", message)
    if not events:
        event_table.add_row("--:--:--", "INFO", "Waiting for telemetry.")
    layout.add_row(Panel(event_table, title="ACTIVITY & RULE-BASED ANOMALIES", border_style="magenta"))

    elapsed = time.strftime("%H:%M:%S", time.gmtime(time.time() - started_at))
    layout.add_row(Panel(f"Serial: {PORT} @ {BAUD} | Session: {elapsed} | {status} | Ctrl+C to exit", style="dim"))
    return layout


def main():
    started_at = time.time()
    latest = None
    previous = None
    console.print(f"[cyan]Connecting to ESP32 on {PORT} at {BAUD} baud...[/]")

    try:
        with serial.Serial(PORT, BAUD, timeout=2) as ser:
            time.sleep(2)
            add_event("INFO", f"Connected to ESP32 on {PORT}")
            with Live(build_dashboard(latest, started_at, "MONITORING"), console=console, refresh_per_second=4, screen=True) as live:
                while True:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()
                    if not line.startswith("{"):
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if "networks" not in data or "strongest_rssi" not in data:
                        continue

                    latest = data
                    history.append(data)

                    if len(baseline) == BASELINE_SIZE:
                        avg_aps = sum(x["networks"] for x in baseline) / len(baseline)
                        avg_rssi = sum(x["strongest_rssi"] for x in baseline) / len(baseline)
                        if abs(data["networks"] - avg_aps) >= AP_CHANGE_THRESHOLD:
                            add_event("WARN", f"AP count changed from baseline {avg_aps:.1f} to {data['networks']}")
                        if abs(data["strongest_rssi"] - avg_rssi) >= RSSI_CHANGE_THRESHOLD_DB:
                            add_event("WARN", f"Strongest RSSI changed from baseline {avg_rssi:.1f} to {data['strongest_rssi']} dBm")
                    elif len(baseline) == 0:
                        add_event("INFO", f"Collecting baseline ({BASELINE_SIZE} scans)")

                    baseline.append(data)
                    if previous is None or data["networks"] != previous["networks"]:
                        add_event("INFO", f"Detected {data['networks']} nearby access points")
                    previous = data
                    live.update(build_dashboard(latest, started_at, "MONITORING"))

    except serial.SerialException as exc:
        console.print(f"\n[bold red]SERIAL ERROR:[/] {exc}")
        console.print("[yellow]Close Arduino Serial Monitor/Plotter and any other script using the COM port. Check PORT near the top of dashboard.py.[/]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped.[/]")


if __name__ == "__main__":
    main()
