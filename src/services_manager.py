"""Windows Services management."""

import psutil
import platform


class ServicesManager:
    """Manage system services."""

    def __init__(self):
        self.services = []
        self.filtered_services = []
        self.search_term = ""

    def refresh_services(self):
        """Refresh services list."""
        self.services = []

        if platform.system() == "Windows":
            try:
                import win32service
                import win32serviceutil

                scm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ENUMERATE_SERVICE)
                services = win32service.EnumServicesStatus(scm, win32service.SERVICE_WIN32, 
                                                           win32service.SERVICE_STATE_ALL)

                for service in services:
                    self.services.append({
                        "name": service[0],
                        "display_name": service[1],
                        "status": self._get_status_name(service[2]),
                        "status_code": service[2],
                    })

                win32service.CloseServiceHandle(scm)
            except ImportError:
                pass

        if not self.services:
            for proc in psutil.process_iter(["pid", "name", "status"]):
                try:
                    self.services.append({
                        "name": proc.info["name"],
                        "display_name": proc.info["name"],
                        "status": proc.info["status"],
                        "pid": proc.info["pid"],
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        self._apply_filter()

    def _get_status_name(self, status_code):
        """Convert Windows service status code to name."""
        status_map = {
            1: "Stopped",
            2: "Start Pending",
            3: "Stop Pending",
            4: "Running",
            5: "Continue Pending",
            6: "Pause Pending",
            7: "Paused",
        }
        return status_map.get(status_code, "Unknown")

    def _apply_filter(self):
        """Apply search filter."""
        if self.search_term:
            term = self.search_term.lower()
            self.filtered_services = [
                s for s in self.services
                if term in s.get("name", "").lower()
                or term in s.get("display_name", "").lower()
            ]
        else:
            self.filtered_services = self.services.copy()

    def set_search(self, term):
        """Set search filter."""
        self.search_term = term
        self._apply_filter()

    def get_services(self):
        """Get filtered services list."""
        return self.filtered_services.copy()

    def start_service(self, name):
        """Start a service."""
        if platform.system() == "Windows":
            try:
                import win32serviceutil
                win32serviceutil.StartService(name)
                return True, "Service started"
            except Exception as e:
                return False, str(e)
        return False, "Not supported on this platform"

    def stop_service(self, name):
        """Stop a service."""
        if platform.system() == "Windows":
            try:
                import win32serviceutil
                win32serviceutil.StopService(name)
                return True, "Service stopped"
            except Exception as e:
                return False, str(e)
        return False, "Not supported on this platform"

    def restart_service(self, name):
        """Restart a service."""
        if platform.system() == "Windows":
            try:
                import win32serviceutil
                win32serviceutil.RestartService(name)
                return True, "Service restarted"
            except Exception as e:
                return False, str(e)
        return False, "Not supported on this platform"