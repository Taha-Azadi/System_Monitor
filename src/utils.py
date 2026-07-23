"""Utility functions and helpers."""

import psutil
import time
import threading
from functools import wraps


def format_bytes(bytes_value):
    """Format bytes to human readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if abs(bytes_value) < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} EB"


def format_speed(bytes_per_sec):
    """Format network speed."""
    return f"{format_bytes(bytes_per_sec)}/s"


def format_time(seconds):
    """Format seconds to human readable time."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    elif seconds < 86400:
        return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"
    else:
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        return f"{days}d {hours}h"


def get_process_priority_name(priority):
    """Get human readable process priority."""
    priorities = {
        psutil.IDLE_PRIORITY_CLASS: "Idle",
        psutil.BELOW_NORMAL_PRIORITY_CLASS: "Below Normal",
        psutil.NORMAL_PRIORITY_CLASS: "Normal",
        psutil.ABOVE_NORMAL_PRIORITY_CLASS: "Above Normal",
        psutil.HIGH_PRIORITY_CLASS: "High",
        psutil.REALTIME_PRIORITY_CLASS: "Realtime",
    }
    return priorities.get(priority, "Unknown")


def get_status_color(percentage, warning, critical):
    """Get color based on percentage thresholds."""
    if percentage >= critical:
        return "#EF4444"
    elif percentage >= warning:
        return "#F59E0B"
    return "#10B981"


def debounce(wait):
    """Debounce decorator for functions."""
    def decorator(fn):
        timer = None
        @wraps(fn)
        def debounced(*args, **kwargs):
            nonlocal timer
            def call_it():
                fn(*args, **kwargs)
            if timer is not None:
                timer.cancel()
            timer = threading.Timer(wait, call_it)
            timer.start()
        return debounced
    return decorator


class Observable:
    """Simple observable pattern implementation."""
    def __init__(self):
        self._observers = []

    def subscribe(self, callback):
        self._observers.append(callback)
        return lambda: self._observers.remove(callback)

    def notify(self, data):
        for observer in self._observers:
            observer(data)
