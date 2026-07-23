"""Main dashboard with overview cards and charts."""

import customtkinter as ctk
import psutil
import time

from performance_charts import PerformanceChart, MultiMetricChart
from system_info import SystemInfo
from utils import format_bytes, get_status_color
from constants import *


class MetricCard(ctk.CTkFrame):
    """A card displaying a single metric with icon and progress bar."""

    def __init__(self, parent, title, icon, color, **kwargs):
        super().__init__(parent, **kwargs)

        self.color = color

        # Icon and title
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=15, pady=(15, 5))

        self.icon_label = ctk.CTkLabel(
            self.header, text=icon, font=("Segoe UI", 24)
        )
        self.icon_label.pack(side="left")

        self.title_label = ctk.CTkLabel(
            self.header, text=title, font=("Segoe UI", 12), text_color="gray"
        )
        self.title_label.pack(side="left", padx=(10, 0))

        # Value
        self.value_label = ctk.CTkLabel(
            self, text="0%", font=("Segoe UI", 32, "bold"),
            text_color=color
        )
        self.value_label.pack(padx=15, pady=5, anchor="w")

        # Progress bar
        self.progress = ctk.CTkProgressBar(self, height=8, corner_radius=4)
        self.progress.pack(fill="x", padx=15, pady=(0, 15))
        self.progress.set(0)

        # Detail label
        self.detail_label = ctk.CTkLabel(
            self, text="", font=("Segoe UI", 10), text_color="gray"
        )
        self.detail_label.pack(padx=15, pady=(0, 10), anchor="w")

    def update_value(self, percentage, detail=""):
        """Update card value and progress."""
        self.value_label.configure(text=f"{percentage:.1f}%")
        self.progress.set(percentage / 100)

        status_color = get_status_color(percentage, 70, 90)
        self.value_label.configure(text_color=status_color)
        self.progress.configure(progress_color=status_color)

        if detail:
            self.detail_label.configure(text=detail)


class Dashboard(ctk.CTkFrame):
    """Main dashboard overview."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.configure(fg_color="transparent")

        # Scrollable frame for dashboard
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        # Title
        self.title_label = ctk.CTkLabel(
            self.scroll, text="System Overview", font=("Segoe UI", 24, "bold")
        )
        self.title_label.pack(pady=(10, 20), anchor="w", padx=10)

        # Metric Cards Grid
        self.cards_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=10, pady=10)
        self.cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.cpu_card = MetricCard(self.cards_frame, "CPU Usage", "CPU", COLOR_CPU)
        self.cpu_card.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.memory_card = MetricCard(self.cards_frame, "Memory", "RAM", COLOR_MEMORY)
        self.memory_card.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.disk_card = MetricCard(self.cards_frame, "Disk", "DISK", COLOR_DISK)
        self.disk_card.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        self.network_card = MetricCard(self.cards_frame, "Network", "NET", COLOR_NETWORK)
        self.network_card.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")

        # Charts Section
        self.charts_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.charts_frame.pack(fill="x", padx=10, pady=20)
        self.charts_frame.grid_columnconfigure((0, 1), weight=1)

        # CPU Chart
        self.cpu_chart = PerformanceChart(
            self.charts_frame, "CPU History", COLOR_CPU, max_value=100
        )
        self.cpu_chart.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # Memory Chart
        self.memory_chart = PerformanceChart(
            self.charts_frame, "Memory History", COLOR_MEMORY, max_value=100
        )
        self.memory_chart.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # Multi-metric chart
        self.multi_chart = MultiMetricChart(
            self.charts_frame, "System Resources",
            {"CPU": COLOR_CPU, "Memory": COLOR_MEMORY, "Disk": COLOR_DISK}
        )
        self.multi_chart.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # System Info Section
        self.info_frame = ctk.CTkFrame(self.scroll)
        self.info_frame.pack(fill="x", padx=10, pady=20)

        self.info_title = ctk.CTkLabel(
            self.info_frame, text="System Information",
            font=("Segoe UI", 16, "bold")
        )
        self.info_title.pack(padx=15, pady=(15, 10), anchor="w")

        self.info_content = ctk.CTkLabel(
            self.info_frame, text="", font=("Segoe UI", 12),
            justify="left"
        )
        self.info_content.pack(padx=15, pady=(0, 15), anchor="w")

        # Initialize data
        self._last_net_io = psutil.net_io_counters()
        self._last_net_time = time.time()
        self._update_system_info()

        # Start update loop using after (main thread only)
        self._running = True
        self._schedule_update()

    def _schedule_update(self):
        """Schedule next update using after (tkinter main thread safe)."""
        if self._running and self.winfo_exists():
            self._update_metrics()
            self.after(1000, self._schedule_update)

    def _update_metrics(self):
        """Update all dashboard metrics."""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=None)
            cpu_count = psutil.cpu_count()
            self.cpu_card.update_value(cpu_percent, f"{cpu_count} Cores")
            self.cpu_chart.update_value(cpu_percent)

            # Memory
            mem = psutil.virtual_memory()
            self.memory_card.update_value(
                mem.percent, 
                f"{format_bytes(mem.used)} / {format_bytes(mem.total)}"
            )
            self.memory_chart.update_value(mem.percent)

            # Disk
            disk = psutil.disk_usage("/")
            self.disk_card.update_value(
                disk.percent,
                f"{format_bytes(disk.used)} / {format_bytes(disk.total)}"
            )

            # Network
            current_io = psutil.net_io_counters()
            current_time = time.time()
            time_delta = current_time - self._last_net_time

            if time_delta > 0:
                download_speed = (current_io.bytes_recv - self._last_net_io.bytes_recv) / time_delta
                upload_speed = (current_io.bytes_sent - self._last_net_io.bytes_sent) / time_delta

                self.network_card.update_value(
                    min(download_speed / (1024 * 1024) * 10, 100),
                    f"Down: {format_speed(download_speed)}  Up: {format_speed(upload_speed)}"
                )

            self._last_net_io = current_io
            self._last_net_time = current_time

            # Multi chart
            self.multi_chart.update_values({
                "CPU": cpu_percent,
                "Memory": mem.percent,
                "Disk": disk.percent,
            })
        except Exception:
            pass

    def _update_system_info(self):
        """Update system information display."""
        info = SystemInfo.get_os_info()
        cpu = SystemInfo.get_cpu_info()

        text = f"""OS: {info['system']} {info['release']}
Hostname: {info['hostname']}
CPU: {cpu['brand']}
Architecture: {cpu['architecture']}
Cores: {cpu['cores_physical']} Physical / {cpu['cores_logical']} Logical
Uptime: {info['uptime']}
Boot Time: {info['boot_time']}"""

        self.info_content.configure(text=text)

    def destroy(self):
        """Clean up resources."""
        self._running = False
        super().destroy()