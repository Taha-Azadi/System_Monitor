"""Network monitoring and statistics."""

import psutil
import socket
import threading
import time
from collections import deque

from utils import format_bytes, format_speed
from constants import CHART_HISTORY_LENGTH


class NetworkMonitor:
    """Monitor network interfaces and traffic."""

    def __init__(self):
        self.history = {
            "download": deque([0] * CHART_HISTORY_LENGTH, maxlen=CHART_HISTORY_LENGTH),
            "upload": deque([0] * CHART_HISTORY_LENGTH, maxlen=CHART_HISTORY_LENGTH),
        }
        self.last_io = psutil.net_io_counters()
        self.last_time = time.time()
        self._lock = threading.Lock()

    def update(self):
        """Update network statistics."""
        current_io = psutil.net_io_counters()
        current_time = time.time()

        time_delta = current_time - self.last_time
        if time_delta <= 0:
            return

        download_speed = (current_io.bytes_recv - self.last_io.bytes_recv) / time_delta
        upload_speed = (current_io.bytes_sent - self.last_io.bytes_sent) / time_delta

        with self._lock:
            self.history["download"].append(download_speed)
            self.history["upload"].append(upload_speed)

        self.last_io = current_io
        self.last_time = current_time

        return {
            "download_speed": download_speed,
            "upload_speed": upload_speed,
            "total_download": current_io.bytes_recv,
            "total_upload": current_io.bytes_sent,
            "packets_recv": current_io.packets_recv,
            "packets_sent": current_io.packets_sent,
            "err_in": current_io.errin,
            "err_out": current_io.errout,
        }

    def get_interfaces(self):
        """Get network interfaces information."""
        interfaces = []
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()

        for name, stat in stats.items():
            interface = {
                "name": name,
                "is_up": stat.isup,
                "speed": f"{stat.speed} Mbps" if stat.speed > 0 else "Unknown",
                "mtu": stat.mtu,
                "addresses": [],
            }

            if name in addrs:
                for addr in addrs[name]:
                    if addr.family == socket.AF_INET:
                        interface["addresses"].append({
                            "type": "IPv4",
                            "address": addr.address,
                            "netmask": addr.netmask,
                            "broadcast": addr.broadcast,
                        })
                    elif addr.family == socket.AF_INET6:
                        interface["addresses"].append({
                            "type": "IPv6",
                            "address": addr.address,
                            "netmask": addr.netmask,
                        })

            interfaces.append(interface)

        return interfaces

    def get_connections(self):
        """Get active network connections."""
        connections = []
        for conn in psutil.net_connections(kind="inet"):
            connections.append({
                "fd": conn.fd,
                "family": str(conn.family),
                "type": str(conn.type),
                "local_addr": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                "remote_addr": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "",
                "status": conn.status,
                "pid": conn.pid,
            })
        return connections

    def get_history(self):
        """Get network speed history."""
        with self._lock:
            return {
                "download": list(self.history["download"]),
                "upload": list(self.history["upload"]),
            }
