"""GPU monitoring support."""

import psutil
import subprocess
import platform

from utils import format_bytes


class GPUMonitor:
    """Monitor GPU usage and statistics."""

    def __init__(self):
        self.has_gputil = False
        self.gpus = []
        try:
            import GPUtil
            self.has_gputil = True
            self.gpus = GPUtil.getGPUs()
        except ImportError:
            pass

    def get_gpu_info(self):
        """Get GPU information."""
        if not self.has_gputil:
            return self._get_gpu_info_fallback()

        gpu_info = []
        for gpu in self.gpus:
            gpu_info.append({
                "id": gpu.id,
                "name": gpu.name,
                "load": gpu.load * 100,
                "memory_total": format_bytes(gpu.memoryTotal * 1024 * 1024),
                "memory_used": format_bytes(gpu.memoryUsed * 1024 * 1024),
                "memory_free": format_bytes(gpu.memoryFree * 1024 * 1024),
                "memory_percent": (gpu.memoryUsed / gpu.memoryTotal * 100) if gpu.memoryTotal > 0 else 0,
                "temperature": gpu.temperature,
                "uuid": gpu.uuid,
            })
        return gpu_info

    def _get_gpu_info_fallback(self):
        """Fallback GPU info using system commands."""
        gpus = []
        system = platform.system()

        if system == "Windows":
            try:
                import wmi
                c = wmi.WMI()
                for gpu in c.Win32_VideoController():
                    gpus.append({
                        "id": 0,
                        "name": gpu.Name,
                        "load": 0,
                        "memory_total": "N/A",
                        "memory_used": "N/A",
                        "memory_free": "N/A",
                        "memory_percent": 0,
                        "temperature": None,
                        "uuid": gpu.PNPDeviceID,
                    })
            except Exception:
                pass

        elif system == "Linux":
            try:
                result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,memory.used,temperature.gpu,utilization.gpu",
                                        "--format=csv,noheader,nounits"], 
                                       capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    for i, line in enumerate(lines):
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 5:
                            gpus.append({
                                "id": i,
                                "name": parts[0],
                                "load": float(parts[4]),
                                "memory_total": f"{parts[1]} MB",
                                "memory_used": f"{parts[2]} MB",
                                "memory_free": "N/A",
                                "memory_percent": (float(parts[2]) / float(parts[1]) * 100) if float(parts[1]) > 0 else 0,
                                "temperature": float(parts[3]) if parts[3] != "[Not Supported]" else None,
                                "uuid": "N/A",
                            })
            except Exception:
                pass

        return gpus

    def refresh_gpus(self):
        """Refresh GPU list."""
        if self.has_gputil:
            import GPUtil
            self.gpus = GPUtil.getGPUs()
