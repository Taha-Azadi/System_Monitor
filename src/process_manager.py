"""Process management - list, filter, kill, and manage processes."""

import psutil
import time

from utils import format_bytes, format_time, get_process_priority_name
from constants import PROCESS_REFRESH_INTERVAL


class ProcessManager:
    """Manage and monitor system processes."""

    def __init__(self):
        self.processes = []
        self.filtered_processes = []
        self.sort_column = "cpu_percent"
        self.sort_descending = True
        self.search_term = ""
        self.refresh_processes()

    def refresh_processes(self):
        """Refresh the process list."""
        processes = []
        for proc in psutil.process_iter(["pid", "name", "username", "cpu_percent", 
                                          "memory_percent", "memory_info", "status",
                                          "create_time", "num_threads", "nice"]):
            try:
                info = proc.info
                info["memory_mb"] = info["memory_info"].rss / (1024 * 1024) if info["memory_info"] else 0
                info["create_time_str"] = time.strftime("%H:%M:%S", time.localtime(info["create_time"]))
                info["priority_name"] = get_process_priority_name(info["nice"]) if info["nice"] else "N/A"
                processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        self.processes = processes
        self._apply_filter_and_sort()

    def _apply_filter_and_sort(self):
        """Apply search filter and sorting."""
        if self.search_term:
            term = self.search_term.lower()
            self.filtered_processes = [
                p for p in self.processes
                if term in str(p.get("name", "")).lower() 
                or term in str(p.get("pid", "")).lower()
                or term in str(p.get("username", "")).lower()
            ]
        else:
            self.filtered_processes = self.processes.copy()

        reverse = self.sort_descending
        if self.sort_column in ["cpu_percent", "memory_percent", "memory_mb", "pid", "num_threads"]:
            self.filtered_processes.sort(
                key=lambda x: x.get(self.sort_column, 0) or 0, 
                reverse=reverse
            )
        else:
            self.filtered_processes.sort(
                key=lambda x: str(x.get(self.sort_column, "")).lower(),
                reverse=reverse
            )

    def set_search(self, term):
        """Set search filter."""
        self.search_term = term
        self._apply_filter_and_sort()

    def set_sort(self, column, descending=True):
        """Set sort column and direction."""
        self.sort_column = column
        self.sort_descending = descending
        self._apply_filter_and_sort()

    def get_processes(self):
        """Get filtered and sorted process list."""
        return self.filtered_processes.copy()

    def kill_process(self, pid):
        """Kill a process by PID."""
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=3)
            return True, "Process terminated successfully"
        except psutil.TimeoutExpired:
            try:
                proc.kill()
                return True, "Process killed forcefully"
            except Exception as e:
                return False, str(e)
        except Exception as e:
            return False, str(e)

    def set_priority(self, pid, priority):
        """Set process priority."""
        try:
            proc = psutil.Process(pid)
            proc.nice(priority)
            return True, "Priority updated"
        except Exception as e:
            return False, str(e)

    def get_process_details(self, pid):
        """Get detailed information about a process."""
        try:
            proc = psutil.Process(pid)
            with proc.oneshot():
                return {
                    "pid": proc.pid,
                    "name": proc.name(),
                    "exe": proc.exe(),
                    "cmdline": " ".join(proc.cmdline()),
                    "cwd": proc.cwd(),
                    "status": proc.status(),
                    "username": proc.username(),
                    "create_time": proc.create_time(),
                    "cpu_percent": proc.cpu_percent(),
                    "memory_percent": proc.memory_percent(),
                    "memory_info": proc.memory_info()._asdict(),
                    "num_threads": proc.num_threads(),
                    "num_fds": proc.num_fds() if hasattr(proc, "num_fds") else None,
                    "io_counters": proc.io_counters()._asdict() if hasattr(proc, "io_counters") else None,
                    "connections": len(proc.connections()),
                    "open_files": len(proc.open_files()),
                    "children": len(proc.children()),
                    "parent": proc.parent().pid if proc.parent() else None,
                    "nice": proc.nice(),
                }
        except Exception as e:
            return None

    def stop(self):
        """Stop (no-op now, kept for compatibility)."""
        pass