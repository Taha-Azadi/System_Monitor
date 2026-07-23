"""Storage monitoring and disk analysis."""

import psutil
import os

from utils import format_bytes


class StorageMonitor:
    """Monitor storage usage and disk health."""

    @staticmethod
    def get_all_partitions():
        """Get all disk partitions with usage info."""
        partitions = []
        for part in psutil.disk_partitions(all=True):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "opts": part.opts,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent,
                })
            except (PermissionError, OSError):
                continue
        return partitions

    @staticmethod
    def get_disk_io():
        """Get disk I/O statistics."""
        io = psutil.disk_io_counters(perdisk=True)
        result = {}
        for disk, stats in io.items():
            result[disk] = {
                "read_count": stats.read_count,
                "write_count": stats.write_count,
                "read_bytes": stats.read_bytes,
                "write_bytes": stats.write_bytes,
                "read_time": stats.read_time,
                "write_time": stats.write_time,
            }
        return result

    @staticmethod
    def get_directory_size(path):
        """Calculate total size of a directory."""
        total = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += StorageMonitor.get_directory_size(entry.path)
        except (PermissionError, OSError):
            pass
        return total

    @staticmethod
    def get_large_files(path="/", limit=50):
        """Find largest files in a directory."""
        files = []
        try:
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    try:
                        size = os.path.getsize(filepath)
                        files.append({"path": filepath, "size": size})
                    except (OSError, PermissionError):
                        continue
        except PermissionError:
            pass

        files.sort(key=lambda x: x["size"], reverse=True)
        return files[:limit]

    @staticmethod
    def get_io_counters():
        """Get overall disk I/O counters."""
        io = psutil.disk_io_counters()
        if io:
            return {
                "read_bytes": io.read_bytes,
                "write_bytes": io.write_bytes,
                "read_count": io.read_count,
                "write_count": io.write_count,
                "read_time": io.read_time,
                "write_time": io.write_time,
            }
        return {}
