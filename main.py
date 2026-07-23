#!/usr/bin/env python3
"""
System Monitor - Advanced System Monitoring Tool
A powerful, modern system monitor built with CustomTkinter.
Better than Task Manager.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from app import SystemMonitorApp

if __name__ == "__main__":
    app = SystemMonitorApp()
    app.run()
