"""Startup programs management."""

import os
import platform


class StartupManager:
    """Manage startup programs."""

    def __init__(self):
        self.startup_items = []

    def refresh_startup_items(self):
        """Refresh startup items list."""
        self.startup_items = []

        if platform.system() == "Windows":
            self._get_windows_startup()
        else:
            self._get_linux_startup()

    def _get_windows_startup(self):
        """Get Windows startup items from registry."""
        try:
            import winreg

            registry_paths = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            ]

            for hkey, path in registry_paths:
                try:
                    key = winreg.OpenKey(hkey, path)
                    i = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(key, i)
                            self.startup_items.append({
                                "name": name,
                                "command": value,
                                "location": path,
                                "enabled": True,
                                "type": "Registry",
                            })
                            i += 1
                        except OSError:
                            break
                    winreg.CloseKey(key)
                except Exception:
                    continue

            startup_folders = [
                os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"),
                os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\Startup"),
            ]

            for folder in startup_folders:
                if os.path.exists(folder):
                    for item in os.listdir(folder):
                        self.startup_items.append({
                            "name": item,
                            "command": os.path.join(folder, item),
                            "location": folder,
                            "enabled": True,
                            "type": "Folder",
                        })
        except ImportError:
            pass

    def _get_linux_startup(self):
        """Get Linux startup items."""
        autostart_dirs = [
            os.path.expanduser("~/.config/autostart"),
            "/etc/xdg/autostart",
        ]

        for directory in autostart_dirs:
            if os.path.exists(directory):
                for item in os.listdir(directory):
                    if item.endswith(".desktop"):
                        filepath = os.path.join(directory, item)
                        self.startup_items.append({
                            "name": item.replace(".desktop", ""),
                            "command": filepath,
                            "location": directory,
                            "enabled": True,
                            "type": "Desktop Entry",
                        })

    def get_startup_items(self):
        """Get startup items list."""
        return self.startup_items.copy()

    def disable_startup_item(self, item):
        """Disable a startup item."""
        try:
            if item["type"] == "Registry" and platform.system() == "Windows":
                import winreg

                if "HKEY_CURRENT_USER" in item["location"]:
                    hkey = winreg.HKEY_CURRENT_USER
                else:
                    hkey = winreg.HKEY_LOCAL_MACHINE

                loc = item["location"]
                if "\\" in loc:
                    path = loc.split("\\", 1)[1]
                else:
                    path = loc

                key = winreg.OpenKey(hkey, path, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, item["name"])
                winreg.CloseKey(key)
                return True, "Startup item disabled"

            elif item["type"] in ["Folder", "Desktop Entry"]:
                os.remove(item["command"])
                return True, "Startup item removed"

        except Exception as e:
            return False, str(e)

        return False, "Could not disable startup item"