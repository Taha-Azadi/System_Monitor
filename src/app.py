"""Main application class and UI."""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import psutil
import threading
import time

from constants import *
from themes import FONT_FAMILY, FONT_SIZES
from settings import settings
from utils import format_bytes, format_time, format_speed
from dashboard import Dashboard
from process_manager import ProcessManager
from system_info import SystemInfo
from network_monitor import NetworkMonitor
from storage_monitor import StorageMonitor
from gpu_monitor import GPUMonitor
from services_manager import ServicesManager
from startup_manager import StartupManager


class SystemMonitorApp:
    """Main System Monitor Application."""

    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry(settings.get("window_geometry", "1400x900"))
        self.root.minsize(1200, 700)

        self.process_manager = ProcessManager()
        self.network_monitor = NetworkMonitor()
        self.storage_monitor = StorageMonitor()
        self.gpu_monitor = GPUMonitor()
        self.services_manager = ServicesManager()
        self.startup_manager = StartupManager()

        self._build_ui()
        self._running = True
        self._start_update_loops()

    def _build_ui(self):
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.sidebar = ctk.CTkFrame(self.main_container, width=200, corner_radius=15)
        self.sidebar.pack(side="left", fill="y", padx=(0, 10))
        self.sidebar.pack_propagate(False)

        self.app_title = ctk.CTkLabel(
            self.sidebar, text=APP_NAME,
            font=(FONT_FAMILY, FONT_SIZES["large"], "bold")
        )
        self.app_title.pack(pady=(20, 30))

        self.nav_buttons = {}
        nav_items = [
            ("Dashboard", self._show_dashboard),
            ("Processes", self._show_processes),
            ("Performance", self._show_performance),
            ("Network", self._show_network),
            ("Storage", self._show_storage),
            ("GPU", self._show_gpu),
            ("Services", self._show_services),
            ("Startup", self._show_startup),
            ("System Info", self._show_system_info),
            ("Settings", self._show_settings),
        ]

        for text, command in nav_items:
            btn = ctk.CTkButton(
                self.sidebar, text=text,
                font=(FONT_FAMILY, FONT_SIZES["normal"]),
                anchor="w", height=40,
                corner_radius=10,
                command=lambda c=command, t=text: self._navigate(c, t)
            )
            btn.pack(fill="x", padx=10, pady=3)
            self.nav_buttons[text] = btn

        self.content_frame = ctk.CTkFrame(self.main_container, corner_radius=15)
        self.content_frame.pack(side="left", fill="both", expand=True)

        self.status_bar = ctk.CTkFrame(self.root, height=30, corner_radius=0)
        self.status_bar.pack(side="bottom", fill="x")

        self.status_label = ctk.CTkLabel(
            self.status_bar, text="Ready",
            font=(FONT_FAMILY, FONT_SIZES["small"])
        )
        self.status_label.pack(side="left", padx=10)

        self.uptime_label = ctk.CTkLabel(
            self.status_bar, text="",
            font=(FONT_FAMILY, FONT_SIZES["small"])
        )
        self.uptime_label.pack(side="right", padx=10)

        self.current_view = None
        self._show_dashboard()

    def _navigate(self, command, name):
        for btn in self.nav_buttons.values():
            btn.configure(fg_color=["#3B8ED0", "#1F6AA5"])
        if name in self.nav_buttons:
            self.nav_buttons[name].configure(fg_color=["#36719F", "#144870"])
        command()

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _show_dashboard(self):
        self._clear_content()
        self.current_view = "dashboard"
        dashboard = Dashboard(self.content_frame)
        dashboard.pack(fill="both", expand=True, padx=10, pady=10)

    def _show_processes(self):
        self._clear_content()
        self.current_view = "processes"

        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 10))

        title = ctk.CTkLabel(header, text="Process Manager", font=(FONT_FAMILY, 20, "bold"))
        title.pack(side="left")

        self.process_search = ctk.CTkEntry(header, placeholder_text="Search processes...", width=250)
        self.process_search.pack(side="right", padx=5)
        self.process_search.bind("<KeyRelease>", lambda e: self.process_manager.set_search(self.process_search.get()))

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)

        ctk.CTkButton(btn_frame, text="End Task", width=100, 
                     command=self._kill_selected_process).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="Refresh", width=100,
                     command=lambda: self.process_manager.refresh_processes()).pack(side="left", padx=2)

        self.process_table_frame = ctk.CTkFrame(self.content_frame)
        self.process_table_frame.pack(fill="both", expand=True, padx=15, pady=10)

        headers = ["PID", "Name", "Status", "CPU %", "Memory %", "Memory (MB)", 
                   "Threads", "User", "Priority", "Actions"]
        self.process_tree = self._create_treeview(self.process_table_frame, headers)
        self.process_tree.pack(fill="both", expand=True)

        self._update_processes()

    def _create_treeview(self, parent, columns):
        style = tk.ttk.Style()
        style.theme_use("default")
        style.configure("Custom.Treeview", 
                       background="#2b2b2b", 
                       foreground="white",
                       fieldbackground="#2b2b2b",
                       rowheight=25)
        style.configure("Custom.Treeview.Heading",
                       background="#1f538d",
                       foreground="white",
                       font=(FONT_FAMILY, 11, "bold"))
        style.map("Custom.Treeview", background=[("selected", "#1f538d")])

        tree = tk.ttk.Treeview(parent, columns=columns, show="headings", 
                              style="Custom.Treeview", height=20)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")

        vsb = ctk.CTkScrollbar(parent, command=tree.yview)
        vsb.pack(side="right", fill="y")
        tree.configure(yscrollcommand=vsb.set)

        return tree

    def _update_processes(self):
        if self.current_view != "processes":
            return

        for item in self.process_tree.get_children():
            self.process_tree.delete(item)

        processes = self.process_manager.get_processes()
        for proc in processes[:100]:
            values = (
                proc.get("pid", ""),
                proc.get("name", ""),
                proc.get("status", ""),
                f"{proc.get('cpu_percent', 0):.1f}",
                f"{proc.get('memory_percent', 0):.1f}",
                f"{proc.get('memory_mb', 0):.1f}",
                proc.get("num_threads", ""),
                proc.get("username", ""),
                proc.get("priority_name", ""),
                "End"
            )
            self.process_tree.insert("", "end", values=values)

        self.status_label.configure(text=f"{len(processes)} processes")
        self.root.after(PROCESS_REFRESH_INTERVAL, self._update_processes)

    def _kill_selected_process(self):
        selection = self.process_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a process to end.")
            return

        item = self.process_tree.item(selection[0])
        pid = int(item["values"][0])
        name = item["values"][1]

        if messagebox.askyesno("Confirm", f"End process '{name}' (PID: {pid})?"):
            success, msg = self.process_manager.kill_process(pid)
            if success:
                messagebox.showinfo("Success", msg)
            else:
                messagebox.showerror("Error", msg)

    def _show_performance(self):
        self._clear_content()
        self.current_view = "performance"

        title = ctk.CTkLabel(self.content_frame, text="Performance Monitor", 
                            font=(FONT_FAMILY, 20, "bold"))
        title.pack(pady=(15, 10), padx=15, anchor="w")

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        cpu_frame = ctk.CTkFrame(scroll)
        cpu_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(cpu_frame, text="CPU", font=(FONT_FAMILY, 16, "bold")).pack(padx=15, pady=(10, 5), anchor="w")

        cpu_info = SystemInfo.get_cpu_info()
        info_text = f"{cpu_info['brand']} | {cpu_info['cores_physical']} Cores / {cpu_info['cores_logical']} Threads | {cpu_info['base_frequency']}"
        ctk.CTkLabel(cpu_frame, text=info_text, font=(FONT_FAMILY, 12)).pack(padx=15, pady=(0, 10), anchor="w")

        self.core_bars = []
        cores_frame = ctk.CTkFrame(cpu_frame, fg_color="transparent")
        cores_frame.pack(fill="x", padx=15, pady=5)

        for i in range(cpu_info['cores_logical']):
            row = ctk.CTkFrame(cores_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=f"Core {i}", width=60, font=(FONT_FAMILY, 10)).pack(side="left")
            bar = ctk.CTkProgressBar(row, height=15, width=300)
            bar.pack(side="left", padx=5)
            bar.set(0)
            lbl = ctk.CTkLabel(row, text="0%", width=50, font=(FONT_FAMILY, 10))
            lbl.pack(side="left")
            self.core_bars.append((bar, lbl))

        mem_frame = ctk.CTkFrame(scroll)
        mem_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(mem_frame, text="Memory", font=(FONT_FAMILY, 16, "bold")).pack(padx=15, pady=(10, 5), anchor="w")
        self.mem_detail_label = ctk.CTkLabel(mem_frame, text="", font=(FONT_FAMILY, 12))
        self.mem_detail_label.pack(padx=15, pady=(0, 10), anchor="w")

        disk_frame = ctk.CTkFrame(scroll)
        disk_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(disk_frame, text="Disk I/O", font=(FONT_FAMILY, 16, "bold")).pack(padx=15, pady=(10, 5), anchor="w")
        self.disk_io_label = ctk.CTkLabel(disk_frame, text="", font=(FONT_FAMILY, 12))
        self.disk_io_label.pack(padx=15, pady=(0, 10), anchor="w")

        self._update_performance()

    def _update_performance(self):
        if self.current_view != "performance":
            return

        per_cpu = psutil.cpu_percent(percpu=True)
        for i, (bar, lbl) in enumerate(self.core_bars):
            if i < len(per_cpu):
                bar.set(per_cpu[i] / 100)
                lbl.configure(text=f"{per_cpu[i]:.0f}%")

        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        mem_text = f"Used: {format_bytes(mem.used)} / {format_bytes(mem.total)} ({mem.percent}%)\nAvailable: {format_bytes(mem.available)}\nSwap: {format_bytes(swap.used)} / {format_bytes(swap.total)}"
        self.mem_detail_label.configure(text=mem_text)

        io = psutil.disk_io_counters()
        if io:
            disk_text = f"Read: {format_bytes(io.read_bytes)} ({io.read_count} ops)\nWrite: {format_bytes(io.write_bytes)} ({io.write_count} ops)"
            self.disk_io_label.configure(text=disk_text)

        self.root.after(1000, self._update_performance)

    def _show_network(self):
        self._clear_content()
        self.current_view = "network"

        title = ctk.CTkLabel(self.content_frame, text="Network Monitor", 
                            font=(FONT_FAMILY, 20, "bold"))
        title.pack(pady=(15, 10), padx=15, anchor="w")

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        stats_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        stats_frame.pack(fill="x", pady=10)
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.net_download_card = self._create_stat_card(stats_frame, "Download Speed", "0 B/s", COLOR_NETWORK)
        self.net_download_card.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.net_upload_card = self._create_stat_card(stats_frame, "Upload Speed", "0 B/s", COLOR_INFO)
        self.net_upload_card.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.net_total_down_card = self._create_stat_card(stats_frame, "Total Downloaded", "0 B", COLOR_SUCCESS)
        self.net_total_down_card.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        self.net_total_up_card = self._create_stat_card(stats_frame, "Total Uploaded", "0 B", COLOR_WARNING)
        self.net_total_up_card.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")

        self.net_interfaces_frame = ctk.CTkFrame(scroll)
        self.net_interfaces_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(self.net_interfaces_frame, text="Network Interfaces", font=(FONT_FAMILY, 16, "bold")).pack(padx=15, pady=10, anchor="w")
        self.net_interfaces_content = ctk.CTkLabel(self.net_interfaces_frame, text="", font=(FONT_FAMILY, 11), justify="left")
        self.net_interfaces_content.pack(padx=15, pady=(0, 10), anchor="w")

        self.net_conn_frame = ctk.CTkFrame(scroll)
        self.net_conn_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(self.net_conn_frame, text="Active Connections", font=(FONT_FAMILY, 16, "bold")).pack(padx=15, pady=10, anchor="w")

        headers = ["Protocol", "Local Address", "Remote Address", "Status", "PID"]
        self.net_conn_tree = self._create_treeview(self.net_conn_frame, headers)
        self.net_conn_tree.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self._update_network()

    def _create_stat_card(self, parent, title, value, color):
        card = ctk.CTkFrame(parent)
        ctk.CTkLabel(card, text=title, font=(FONT_FAMILY, 11), text_color="gray").pack(pady=(10, 5))
        lbl = ctk.CTkLabel(card, text=value, font=(FONT_FAMILY, 18, "bold"), text_color=color)
        lbl.pack(pady=(0, 10))
        card.value_label = lbl
        return card

    def _update_network(self):
        if self.current_view != "network":
            return

        stats = self.network_monitor.update()
        if stats:
            self.net_download_card.value_label.configure(text=format_speed(stats["download_speed"]))
            self.net_upload_card.value_label.configure(text=format_speed(stats["upload_speed"]))
            self.net_total_down_card.value_label.configure(text=format_bytes(stats["total_download"]))
            self.net_total_up_card.value_label.configure(text=format_bytes(stats["total_upload"]))

        interfaces = self.network_monitor.get_interfaces()
        text = ""
        for iface in interfaces[:5]:
            status = "UP" if iface["is_up"] else "DOWN"
            text += f"[{status}] {iface['name']} - {iface['speed']}\n"
            for addr in iface["addresses"]:
                text += f"   {addr['type']}: {addr['address']}\n"
        self.net_interfaces_content.configure(text=text)

        for item in self.net_conn_tree.get_children():
            self.net_conn_tree.delete(item)

        connections = self.network_monitor.get_connections()[:50]
        for conn in connections:
            values = (
                conn["family"].replace("AddressFamily.AF_INET", "IPv4").replace("AddressFamily.AF_INET6", "IPv6"),
                conn["local_addr"],
                conn["remote_addr"],
                conn["status"],
                conn["pid"] or ""
            )
            self.net_conn_tree.insert("", "end", values=values)

        self.root.after(2000, self._update_network)

    def _show_storage(self):
        self._clear_content()
        self.current_view = "storage"

        title = ctk.CTkLabel(self.content_frame, text="Storage Monitor", 
                            font=(FONT_FAMILY, 20, "bold"))
        title.pack(pady=(15, 10), padx=15, anchor="w")

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self.disk_partitions_frame = ctk.CTkFrame(scroll)
        self.disk_partitions_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(self.disk_partitions_frame, text="Disk Partitions", font=(FONT_FAMILY, 16, "bold")).pack(padx=15, pady=10, anchor="w")

        headers = ["Device", "Mountpoint", "Type", "Total", "Used", "Free", "Usage %"]
        self.disk_tree = self._create_treeview(self.disk_partitions_frame, headers)
        self.disk_tree.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self.disk_io_frame = ctk.CTkFrame(scroll)
        self.disk_io_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(self.disk_io_frame, text="Disk I/O Statistics", font=(FONT_FAMILY, 16, "bold")).pack(padx=15, pady=10, anchor="w")
        self.disk_io_content = ctk.CTkLabel(self.disk_io_frame, text="", font=(FONT_FAMILY, 11), justify="left")
        self.disk_io_content.pack(padx=15, pady=(0, 10), anchor="w")

        self._update_storage()

    def _update_storage(self):
        if self.current_view != "storage":
            return

        for item in self.disk_tree.get_children():
            self.disk_tree.delete(item)

        partitions = self.storage_monitor.get_all_partitions()
        for part in partitions:
            values = (
                part["device"],
                part["mountpoint"],
                part["fstype"],
                format_bytes(part["total"]),
                format_bytes(part["used"]),
                format_bytes(part["free"]),
                f"{part['percent']}%"
            )
            self.disk_tree.insert("", "end", values=values)

        io_stats = self.storage_monitor.get_io_counters()
        if io_stats:
            text = f"Total Read: {format_bytes(io_stats['read_bytes'])}\nTotal Write: {format_bytes(io_stats['write_bytes'])}\nRead Operations: {io_stats['read_count']}\nWrite Operations: {io_stats['write_count']}"
            self.disk_io_content.configure(text=text)

        self.root.after(3000, self._update_storage)

    def _show_gpu(self):
        self._clear_content()
        self.current_view = "gpu"

        title = ctk.CTkLabel(self.content_frame, text="GPU Monitor", 
                            font=(FONT_FAMILY, 20, "bold"))
        title.pack(pady=(15, 10), padx=15, anchor="w")

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        gpus = self.gpu_monitor.get_gpu_info()

        if not gpus:
            ctk.CTkLabel(scroll, text="No GPU detected or GPU monitoring not available.", 
                        font=(FONT_FAMILY, 14)).pack(pady=50)
            return

        for gpu in gpus:
            gpu_frame = ctk.CTkFrame(scroll)
            gpu_frame.pack(fill="x", pady=5)

            ctk.CTkLabel(gpu_frame, text=gpu["name"], font=(FONT_FAMILY, 16, "bold")).pack(padx=15, pady=(10, 5), anchor="w")

            load_frame = ctk.CTkFrame(gpu_frame, fg_color="transparent")
            load_frame.pack(fill="x", padx=15, pady=2)
            ctk.CTkLabel(load_frame, text="Load:", width=100).pack(side="left")
            load_bar = ctk.CTkProgressBar(load_frame, height=15)
            load_bar.pack(side="left", fill="x", expand=True, padx=5)
            load_bar.set(gpu["load"] / 100)
            ctk.CTkLabel(load_frame, text=f"{gpu['load']:.1f}%", width=60).pack(side="left")

            mem_frame = ctk.CTkFrame(gpu_frame, fg_color="transparent")
            mem_frame.pack(fill="x", padx=15, pady=2)
            ctk.CTkLabel(mem_frame, text="Memory:", width=100).pack(side="left")
            mem_bar = ctk.CTkProgressBar(mem_frame, height=15)
            mem_bar.pack(side="left", fill="x", expand=True, padx=5)
            mem_bar.set(gpu["memory_percent"] / 100)
            ctk.CTkLabel(mem_frame, text=f"{gpu['memory_used']} / {gpu['memory_total']}", width=150).pack(side="left")

            if gpu["temperature"] is not None:
                temp_frame = ctk.CTkFrame(gpu_frame, fg_color="transparent")
                temp_frame.pack(fill="x", padx=15, pady=2)
                ctk.CTkLabel(temp_frame, text="Temperature:", width=100).pack(side="left")
                temp_color = "#EF4444" if gpu["temperature"] > 80 else "#F59E0B" if gpu["temperature"] > 60 else "#10B981"
                ctk.CTkLabel(temp_frame, text=f"{gpu['temperature']} C", text_color=temp_color, font=(FONT_FAMILY, 12, "bold")).pack(side="left")

            ctk.CTkLabel(gpu_frame, text=f"UUID: {gpu['uuid']}", font=(FONT_FAMILY, 9), text_color="gray").pack(padx=15, pady=(5, 10), anchor="w")

    def _show_services(self):
        self._clear_content()
        self.current_view = "services"

        title = ctk.CTkLabel(self.content_frame, text="Services Manager", 
                            font=(FONT_FAMILY, 20, "bold"))
        title.pack(pady=(15, 10), padx=15, anchor="w")

        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=5)

        self.service_search = ctk.CTkEntry(header, placeholder_text="Search services...", width=250)
        self.service_search.pack(side="right")
        self.service_search.bind("<KeyRelease>", lambda e: self.services_manager.set_search(self.service_search.get()))

        ctk.CTkButton(header, text="Refresh", command=self.services_manager.refresh_services).pack(side="right", padx=5)

        self.services_table_frame = ctk.CTkFrame(self.content_frame)
        self.services_table_frame.pack(fill="both", expand=True, padx=15, pady=10)

        headers = ["Name", "Display Name", "Status", "Actions"]
        self.services_tree = self._create_treeview(self.services_table_frame, headers)
        self.services_tree.pack(fill="both", expand=True)

        self._update_services()

    def _update_services(self):
        if self.current_view != "services":
            return

        for item in self.services_tree.get_children():
            self.services_tree.delete(item)

        services = self.services_manager.get_services()
        for svc in services[:100]:
            values = (
                svc.get("name", ""),
                svc.get("display_name", ""),
                svc.get("status", ""),
                "Start/Stop"
            )
            self.services_tree.insert("", "end", values=values)

        self.status_label.configure(text=f"{len(services)} services")
        self.root.after(5000, self._update_services)

    def _show_startup(self):
        self._clear_content()
        self.current_view = "startup"

        title = ctk.CTkLabel(self.content_frame, text="Startup Programs", 
                            font=(FONT_FAMILY, 20, "bold"))
        title.pack(pady=(15, 10), padx=15, anchor="w")

        header = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(header, text="Refresh", command=self.startup_manager.refresh_startup_items).pack(side="right")

        self.startup_table_frame = ctk.CTkFrame(self.content_frame)
        self.startup_table_frame.pack(fill="both", expand=True, padx=15, pady=10)

        headers = ["Name", "Command", "Location", "Type", "Actions"]
        self.startup_tree = self._create_treeview(self.startup_table_frame, headers)
        self.startup_tree.pack(fill="both", expand=True)

        self._update_startup()

    def _update_startup(self):
        if self.current_view != "startup":
            return

        for item in self.startup_tree.get_children():
            self.startup_tree.delete(item)

        items = self.startup_manager.get_startup_items()
        for item in items:
            values = (
                item.get("name", ""),
                item.get("command", ""),
                item.get("location", ""),
                item.get("type", ""),
                "Disable"
            )
            self.startup_tree.insert("", "end", values=values)

        self.status_label.configure(text=f"{len(items)} startup items")

    def _show_system_info(self):
        self._clear_content()
        self.current_view = "system_info"

        title = ctk.CTkLabel(self.content_frame, text="System Information", 
                            font=(FONT_FAMILY, 20, "bold"))
        title.pack(pady=(15, 10), padx=15, anchor="w")

        scroll = ctk.CTkScrollableFrame(self.content_frame)
        scroll.pack(fill="both", expand=True, padx=15, pady=10)

        # OS Info
        os_frame = ctk.CTkFrame(scroll)
        os_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(os_frame, text="Operating System", font=(FONT_FAMILY, 16, "bold")).pack(padx=15, pady=(10, 5), anchor="w")

        os_info = SystemInfo.get_os_info()
        os_text = f"""System: {os_info['system']} {os_info['release']}
Version: {os_info['version']}
Architecture: {os_info['machine']}
Hostname: {os_info['hostname']}
Boot Time: {os_info['boot_time']}
Uptime: {os_info['uptime']}"""
        ctk.CTkLabel(os_frame, text=os_text, font=(FONT_FAMILY, 12), justify="left").pack(padx=15, pady=(0, 10), anchor="w")

        # CPU Info
        cpu_frame = ctk.CTkFrame(scroll)
        cpu_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(cpu_frame, text="CPU Information", font=(FONT_FAMILY, 16, "bold")).pack(padx=15, pady=(10, 5), anchor="w")

        cpu_info = SystemInfo.get_cpu_info()
        cpu_text = f"""Processor: {cpu_info['brand']}
Architecture: {cpu_info['architecture']}
Physical Cores: {cpu_info['cores_physical']}
Logical Cores: {cpu_info['cores_logical']}
Base Frequency: {cpu_info['base_frequency']}
Max Frequency: {cpu_info['max_frequency']}"""
        ctk.CTkLabel(cpu_frame, text=cpu_text, font=(FONT_FAMILY, 12), justify="left").pack(padx=15, pady=(0, 10), anchor="w")

        # Memory Info
        mem_frame = ctk.CTkFrame(scroll)
        mem_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(mem_frame, text="Memory Information", font=(FONT_FAMILY, 16, "bold")).pack(padx=15, pady=(10, 5), anchor="w")

        mem_info = SystemInfo.get_memory_info()
        mem_text = f"""Total RAM: {mem_info['total']}
Available: {mem_info['available']}
Used: {mem_info['used']}
Usage: {mem_info['percentage']}%
Swap Total: {mem_info['swap_total']}
Swap Used: {mem_info['swap_used']}"""
        ctk.CTkLabel(mem_frame, text=mem_text, font=(FONT_FAMILY, 12), justify="left").pack(padx=15, pady=(0, 10), anchor="w")

        # Disk Info
        disk_frame = ctk.CTkFrame(scroll)
        disk_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(disk_frame, text="Disk Partitions", font=(FONT_FAMILY, 16, "bold")).pack(padx=15, pady=(10, 5), anchor="w")

        disks = SystemInfo.get_disk_info()
        disk_text = ""
        for d in disks:
            disk_text += f"{d['device']} ({d['mountpoint']}) - {d['total']} total, {d['used']} used ({d['percentage']}%)\n"
        ctk.CTkLabel(disk_frame, text=disk_text, font=(FONT_FAMILY, 12), justify="left").pack(padx=15, pady=(0, 10), anchor="w")

        # Battery
        battery = SystemInfo.get_battery_info()
        if battery:
            batt_frame = ctk.CTkFrame(scroll)
            batt_frame.pack(fill="x", pady=5)
            ctk.CTkLabel(batt_frame, text="Battery", font=(FONT_FAMILY, 16, "bold")).pack(padx=15, pady=(10, 5), anchor="w")
            batt_text = f"Level: {battery['percent']}%\nStatus: {battery['status']}\nTime Left: {battery['time_left']}"
            ctk.CTkLabel(batt_frame, text=batt_text, font=(FONT_FAMILY, 12), justify="left").pack(padx=15, pady=(0, 10), anchor="w")

        # Temperatures
        temps = SystemInfo.get_temperatures()
        if temps:
            temp_frame = ctk.CTkFrame(scroll)
            temp_frame.pack(fill="x", pady=5)
            ctk.CTkLabel(temp_frame, text="Temperature Sensors", font=(FONT_FAMILY, 16, "bold")).pack(padx=15, pady=(10, 5), anchor="w")
            temp_text = ""
            for name, entries in temps.items():
                temp_text += f"{name}:\n"
                for e in entries:
                    temp_text += f"  {e['label']}: {e['current']} C"
                    if e['high']:
                        temp_text += f" (High: {e['high']} C)"
                    temp_text += "\n"
            ctk.CTkLabel(temp_frame, text=temp_text, font=(FONT_FAMILY, 12), justify="left").pack(padx=15, pady=(0, 10), anchor="w")

    def _show_settings(self):
        self._clear_content()
        self.current_view = "settings"

        title = ctk.CTkLabel(self.content_frame, text="Settings", 
                            font=(FONT_FAMILY, 20, "bold"))
        title.pack(pady=(15, 10), padx=15, anchor="w")

        scroll = ctk.CTkScrollableFrame(self.content_frame)
        scroll.pack(fill="both", expand=True, padx=15, pady=10)

        # Appearance
        app_frame = ctk.CTkFrame(scroll)
        app_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(app_frame, text="Appearance", font=(FONT_FAMILY, 16, "bold")).pack(padx=15, pady=(10, 5), anchor="w")

        theme_frame = ctk.CTkFrame(app_frame, fg_color="transparent")
        theme_frame.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(theme_frame, text="Theme:").pack(side="left")
        theme_var = ctk.StringVar(value=settings.get("theme", "dark"))
        theme_combo = ctk.CTkComboBox(theme_frame, values=["dark", "light"], variable=theme_var, width=150)
        theme_combo.pack(side="left", padx=10)

        color_frame = ctk.CTkFrame(app_frame, fg_color="transparent")
        color_frame.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(color_frame, text="Color:").pack(side="left")
        color_var = ctk.StringVar(value=settings.get("color_theme", "blue"))
        color_combo = ctk.CTkComboBox(color_frame, values=["blue", "green", "dark-blue"], variable=color_var, width=150)
        color_combo.pack(side="left", padx=10)

        # Alerts
        alert_frame = ctk.CTkFrame(scroll)
        alert_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(alert_frame, text="Alerts", font=(FONT_FAMILY, 16, "bold")).pack(padx=15, pady=(10, 5), anchor="w")

        cpu_alert_var = ctk.BooleanVar(value=settings.get("alert_on_high_cpu", True))
        ctk.CTkSwitch(alert_frame, text="Alert on High CPU", variable=cpu_alert_var).pack(padx=15, pady=5, anchor="w")

        mem_alert_var = ctk.BooleanVar(value=settings.get("alert_on_high_memory", True))
        ctk.CTkSwitch(alert_frame, text="Alert on High Memory", variable=mem_alert_var).pack(padx=15, pady=5, anchor="w")

        thresh_frame = ctk.CTkFrame(alert_frame, fg_color="transparent")
        thresh_frame.pack(fill="x", padx=15, pady=5)
        ctk.CTkLabel(thresh_frame, text="CPU Alert Threshold:").pack(side="left")
        cpu_thresh = ctk.CTkEntry(thresh_frame, width=60)
        cpu_thresh.insert(0, str(settings.get("cpu_alert_threshold", 90)))
        cpu_thresh.pack(side="left", padx=10)

        def save_settings():
            settings.set("theme", theme_var.get())
            settings.set("color_theme", color_var.get())
            settings.set("alert_on_high_cpu", cpu_alert_var.get())
            settings.set("alert_on_high_memory", mem_alert_var.get())
            settings.set("cpu_alert_threshold", int(cpu_thresh.get()))
            ctk.set_appearance_mode(theme_var.get())
            ctk.set_default_color_theme(color_var.get())
            messagebox.showinfo("Settings", "Settings saved successfully!")

        ctk.CTkButton(scroll, text="Save Settings", command=save_settings).pack(pady=20)
        ctk.CTkButton(scroll, text="Reset to Defaults", command=settings.reset).pack(pady=5)

    def _start_update_loops(self):
        self._update_uptime()

    def _update_uptime(self):
        if not self._running:
            return

        uptime = time.time() - psutil.boot_time()
        self.uptime_label.configure(text=f"Uptime: {format_time(uptime)}")
        self.root.after(1000, self._update_uptime)

    def run(self):
        self.root.mainloop()
        self._running = False
        self.process_manager.stop()
