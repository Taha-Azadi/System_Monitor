"""Real-time performance charts using matplotlib embedded in CustomTkinter."""

import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from collections import deque

from constants import CHART_HISTORY_LENGTH


class PerformanceChart(ctk.CTkFrame):
    """A real-time performance chart widget."""

    def __init__(self, parent, title, color, max_value=100, **kwargs):
        super().__init__(parent, **kwargs)

        self.title = title
        self.color = color
        self.max_value = max_value
        self.data = deque([0] * CHART_HISTORY_LENGTH, maxlen=CHART_HISTORY_LENGTH)
        self.current_value = 0

        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=10, pady=(10, 0))

        self.title_label = ctk.CTkLabel(
            self.header, text=title, font=("Segoe UI", 14, "bold")
        )
        self.title_label.pack(side="left")

        self.value_label = ctk.CTkLabel(
            self.header, text="0%", font=("Segoe UI", 16, "bold"),
            text_color=color
        )
        self.value_label.pack(side="right")

        # Chart
        self.fig = Figure(figsize=(5, 2.5), dpi=100, facecolor="#2b2b2b")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#2b2b2b")
        self.ax.set_ylim(0, max_value)
        self.ax.set_xlim(0, CHART_HISTORY_LENGTH)
        self.ax.tick_params(colors="white", labelsize=8)
        self.ax.spines["bottom"].set_color("white")
        self.ax.spines["left"].set_color("white")
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)

        self.line, = self.ax.plot(range(CHART_HISTORY_LENGTH), list(self.data), 
                                   color=color, linewidth=2)
        self.fill = self.ax.fill_between(range(CHART_HISTORY_LENGTH), list(self.data), 
                                          alpha=0.3, color=color)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

    def update_value(self, value):
        """Update chart with new value."""
        self.current_value = value
        self.data.append(value)

        self.value_label.configure(text=f"{value:.1f}%")

        self.line.set_ydata(list(self.data))

        # Update fill
        self.fill.remove()
        self.fill = self.ax.fill_between(range(CHART_HISTORY_LENGTH), list(self.data), 
                                          alpha=0.3, color=self.color)

        self.canvas.draw_idle()


class MultiMetricChart(ctk.CTkFrame):
    """Chart showing multiple metrics simultaneously."""

    def __init__(self, parent, title, metrics, **kwargs):
        super().__init__(parent, **kwargs)

        self.title = title
        self.metrics = metrics
        self.data = {name: deque([0] * CHART_HISTORY_LENGTH, maxlen=CHART_HISTORY_LENGTH) 
                     for name in metrics}

        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=10, pady=(10, 0))

        self.title_label = ctk.CTkLabel(
            self.header, text=title, font=("Segoe UI", 14, "bold")
        )
        self.title_label.pack(side="left")

        # Legend
        self.legend_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        self.legend_frame.pack(side="right")

        for name, color in metrics.items():
            lbl = ctk.CTkLabel(self.legend_frame, text=f"● {name}", 
                               text_color=color, font=("Segoe UI", 10))
            lbl.pack(side="left", padx=5)

        # Chart
        self.fig = Figure(figsize=(6, 3), dpi=100, facecolor="#2b2b2b")
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#2b2b2b")
        self.ax.set_ylim(0, 100)
        self.ax.set_xlim(0, CHART_HISTORY_LENGTH)
        self.ax.tick_params(colors="white", labelsize=8)
        self.ax.spines["bottom"].set_color("white")
        self.ax.spines["left"].set_color("white")

        self.lines = {}
        for name, color in metrics.items():
            line, = self.ax.plot(range(CHART_HISTORY_LENGTH), list(self.data[name]), 
                                  color=color, linewidth=2, label=name)
            self.lines[name] = line

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)

    def update_values(self, values):
        """Update all metrics. values: dict of {name: value}"""
        for name, value in values.items():
            if name in self.data:
                self.data[name].append(value)
                self.lines[name].set_ydata(list(self.data[name]))

        self.canvas.draw_idle()
