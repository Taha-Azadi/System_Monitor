"""Application settings and configuration management."""

import json
import os

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "theme": "dark",
    "color_theme": "blue",
    "update_interval": 1000,
    "show_tray_icon": True,
    "minimize_to_tray": True,
    "start_minimized": False,
    "show_gpu": True,
    "show_network_speed": True,
    "alert_on_high_cpu": True,
    "alert_on_high_memory": True,
    "cpu_alert_threshold": 90,
    "memory_alert_threshold": 90,
    "process_sort_column": "cpu_percent",
    "process_sort_descending": True,
    "chart_history_length": 60,
    "window_geometry": "1400x900",
    "language": "en",
}


class Settings:
    """Settings manager singleton."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = DEFAULT_SETTINGS.copy()
            cls._instance.load()
        return cls._instance

    def get(self, key, default=None):
        return self._settings.get(key, default)

    def set(self, key, value):
        self._settings[key] = value
        self.save()

    def load(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    loaded = json.load(f)
                    self._settings.update(loaded)
            except Exception:
                pass

    def save(self):
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self._settings, f, indent=2)
        except Exception:
            pass

    def reset(self):
        self._settings = DEFAULT_SETTINGS.copy()
        self.save()


settings = Settings()
