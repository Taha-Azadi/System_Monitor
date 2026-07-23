"""Custom themes and styling for the application."""

import customtkinter as ctk

THEMES = {
    "dark": {
        "bg_primary": "#1a1a2e",
        "bg_secondary": "#16213e",
        "bg_card": "#0f3460",
        "text_primary": "#e94560",
        "text_secondary": "#eaeaea",
        "accent": "#e94560",
        "success": "#10B981",
        "warning": "#F59E0B",
        "danger": "#EF4444",
        "info": "#3B82F6",
    },
    "light": {
        "bg_primary": "#f8fafc",
        "bg_secondary": "#f1f5f9",
        "bg_card": "#ffffff",
        "text_primary": "#1e293b",
        "text_secondary": "#64748b",
        "accent": "#3B82F6",
        "success": "#10B981",
        "warning": "#F59E0B",
        "danger": "#EF4444",
        "info": "#3B82F6",
    },
    "cyberpunk": {
        "bg_primary": "#0a0a0a",
        "bg_secondary": "#1a1a1a",
        "bg_card": "#2d2d2d",
        "text_primary": "#00ff9f",
        "text_secondary": "#00b8ff",
        "accent": "#ff00ff",
        "success": "#00ff9f",
        "warning": "#ffcc00",
        "danger": "#ff0055",
        "info": "#00b8ff",
    },
    "ocean": {
        "bg_primary": "#0c4a6e",
        "bg_secondary": "#075985",
        "bg_card": "#0369a1",
        "text_primary": "#7dd3fc",
        "text_secondary": "#bae6fd",
        "accent": "#38bdf8",
        "success": "#4ade80",
        "warning": "#fbbf24",
        "danger": "#f87171",
        "info": "#60a5fa",
    },
}

FONT_FAMILY = "Segoe UI"
FONT_SIZES = {
    "tiny": 10,
    "small": 12,
    "normal": 14,
    "medium": 16,
    "large": 20,
    "xlarge": 24,
    "title": 32,
}


def apply_theme(theme_name="dark"):
    """Apply a theme to the application."""
    theme = THEMES.get(theme_name, THEMES["dark"])
    ctk.set_appearance_mode("dark" if theme_name in ["dark", "cyberpunk", "ocean"] else "light")
    return theme
