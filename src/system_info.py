"""System information and hardware details."""

import psutil
import platform
import socket
import cpuinfo
from datetime import datetime
import time

from utils import format_bytes, format_time


class SystemInfo:
    """Collect and manage system information."""

    @staticmethod
    def get_os_info():
        """Get operating system information."""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "hostname": socket.gethostname(),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
            "uptime": format_time(time.time() - psutil.boot_time()),
        }

    @staticmethod
    def get_cpu_info():
        """Get detailed CPU information."""
        info = cpuinfo.get_cpu_info()
        cpu_freq = psutil.cpu_freq()

        return {
            "brand": info.get("brand_raw", "Unknown"),
            "architecture": info.get("arch", "Unknown"),
            "cores_physical": psutil.cpu_count(logical=False),
            "cores_logical": psutil.cpu_count(logical=True),
            "base_frequency": f"{cpu_freq.current:.0f} MHz" if cpu_freq else "N/A",
            "max_frequency": f"{cpu_freq.max:.0f} MHz" if cpu_freq and cpu_freq.max else "N/A",
            "cache_size": info.get("l3_cache_size", "N/A"),
            "flags": info.get("flags", []),
        }

    @staticmethod
    def get_memory_info():
        """Get memory information."""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            "total": format_bytes(mem.total),
            "available": format_bytes(mem.available),
            "used": format_bytes(mem.used),
            "percentage": mem.percent,
            "swap_total": format_bytes(swap.total),
            "swap_used": format_bytes(swap.used),
            "swap_percentage": swap.percent if swap.total > 0 else 0,
        }

    @staticmethod
    def get_disk_info():
        """Get disk information."""
        disks = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total": format_bytes(usage.total),
                    "used": format_bytes(usage.used),
                    "free": format_bytes(usage.free),
                    "percentage": usage.percent,
                })
            except PermissionError:
                continue
        return disks

    @staticmethod
    def get_battery_info():
        """Get battery information if available."""
        try:
            battery = psutil.sensors_battery()
            if battery:
                return {
                    "percent": battery.percent,
                    "power_plugged": battery.power_plugged,
                    "time_left": format_time(battery.secsleft) if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "Unlimited",
                    "status": "Charging" if battery.power_plugged else "Discharging",
                }
        except Exception:
            pass
        return None

    @staticmethod
    def get_temperatures():
        """Get hardware temperatures."""
        temps = {}
        try:
            sensors = psutil.sensors_temperatures()
            for name, entries in sensors.items():
                temps[name] = [
                    {"label": e.label or name, "current": e.current, 
                     "high": e.high, "critical": e.critical}
                    for e in entries
                ]
        except Exception:
            pass
        return temps

    @staticmethod
    def get_fans():
        """Get fan speeds."""
        fans = {}
        try:
            sensors = psutil.sensors_fans()
            for name, entries in sensors.items():
                fans[name] = [
                    {"label": e.label or name, "current": e.current}
                    for e in entries
                ]
        except Exception:
            pass
        return fans
