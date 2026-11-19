"""
Interactive 4-Zone Keyboard Widget for OmenGlow.
Draws a stylized OMEN 16 keyboard with live real-time RGB zone backlights.
Users can click zones to select them for individual or collective color editing.
"""

import tkinter as tk
from typing import Callable, List, Optional, Set, Tuple
import customtkinter as ctk

ZONE_NAMES = [
    "Zone 1: WASD / Left",
    "Zone 2: Mid-Left",
    "Zone 3: Mid-Right",
    "Zone 4: Right / Numpad",
]


class KeyboardPreviewWidget(ctk.CTkFrame):
    """Visual 4-zone laptop keyboard with live RGB backlights and selection."""

    def __init__(
        self,
        master,
        on_zone_selected: Optional[Callable[[Set[int]], None]] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="#12141A", corner_radius=12, **kwargs)

        self._on_zone_selected = on_zone_selected
        self.selected_zones: Set[int] = {0, 1, 2, 3}  # Default: all zones selected
        self.current_colors: List[Tuple[int, int, int]] = [
            (255, 0, 80),
            (0, 200, 255),
            (140, 0, 255),
            (0, 255, 170),
        ]

        # Top label & selection actions
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=16, pady=(12, 6))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="OMEN 16 Keyboard Preview (Click zones to select)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#B0B5C0",
        )
        self.title_label.pack(side="left")

        self.btn_select_all = ctk.CTkButton(
            self.header_frame,
            text="Select All",
            font=ctk.CTkFont(size=11),
            width=80,
            height=26,
            fg_color="#202430",
            hover_color="#2E3444",
            text_color="#00C8FF",
            command=self.select_all_zones,
        )
        self.btn_select_all.pack(side="right")

        # Canvas for drawing the keyboard and zones
        self.canvas_width = 680
        self.canvas_height = 160
        self.canvas = tk.Canvas(
            self,
            width=self.canvas_width,
            height=self.canvas_height,
            bg="#0E1015",
            highlightthickness=1,
            highlightbackground="#222634",
        )
        self.canvas.pack(padx=16, pady=(0, 14), fill="both", expand=True)

        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # Bottom legend indicators
        self.legend_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.legend_frame.pack(fill="x", padx=16, pady=(0, 12))

        self.zone_tags: List[ctk.CTkLabel] = []
        for i in range(4):
            tag = ctk.CTkLabel(
                self.legend_frame,
                text=f"● {ZONE_NAMES[i]}",
                font=ctk.CTkFont(size=11),
                text_color="#00C8FF" if i in self.selected_zones else "#555A68",
            )
            tag.pack(side="left", expand=True)
            self.zone_tags.append(tag)

        self.redraw()

    def select_all_zones(self):
        self.selected_zones = {0, 1, 2, 3}
        self._notify_selection()
        self.redraw()

    def toggle_zone(self, zone_idx: int):
        if zone_idx in self.selected_zones:
            if len(self.selected_zones) > 1:
                self.selected_zones.remove(zone_idx)
        else:
            self.selected_zones.add(zone_idx)
        self._notify_selection()
        self.redraw()

    def _notify_selection(self):
        # Update legend text colors
        for i, tag in enumerate(self.zone_tags):
            tag.configure(text_color="#00C8FF" if i in self.selected_zones else "#555A68")
        if self._on_zone_selected:
            self._on_zone_selected(self.selected_zones)

    def update_colors(self, colors: List[Tuple[int, int, int]]):
        """Update live RGB colors for real-time visualization."""
        self.current_colors = colors[:4]
        self.redraw_colors_only()

    def _on_canvas_click(self, event):
        x = event.x
        w = self.canvas.winfo_width() or self.canvas_width
        pad_x = 18
        avail_w = w - (pad_x * 2)
        zone_w = avail_w / 4.0

        if pad_x <= x <= (w - pad_x):
            zone_idx = int((x - pad_x) / zone_w)
            zone_idx = max(0, min(3, zone_idx))
            self.toggle_zone(zone_idx)

    def redraw(self):
        """Full redraw of the keyboard background, keys, and zones."""
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        if w < 100:
            w = self.canvas_width
        h = self.canvas.winfo_height()
        if h < 50:
            h = self.canvas_height

        pad_x = 18
        pad_y = 14
        avail_w = w - (pad_x * 2)
        avail_h = h - (pad_y * 2)
        zone_w = avail_w / 4.0

        # Draw laptop chassis border
        self.canvas.create_rectangle(
            pad_x - 6, pad_y - 6, w - pad_x + 6, h - pad_y + 6,
            fill="#161922", outline="#262B38", width=1
        )

        # Draw 4 Zones
        for i in range(4):
            zx1 = pad_x + i * zone_w + 3
            zx2 = pad_x + (i + 1) * zone_w - 3
            zy1 = pad_y + 3
            zy2 = h - pad_y - 3

            r, g, b = self.current_colors[i] if i < len(self.current_colors) else (0, 0, 0)
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            dark_fill = f"#{int(r*0.25):02x}{int(g*0.25):02x}{int(b*0.25):02x}"

            # Zone background / underglow
            self.canvas.create_rectangle(
                zx1, zy1, zx2, zy2,
                fill=dark_fill, outline="", tags=(f"zone_{i}_bg",)
            )

            # Simulated keycaps grid in zone
            cols = 3 if i < 3 else 4
            rows = 4
            kw = (zx2 - zx1 - 10) / cols
            kh = (zy2 - zy1 - 10) / rows
            for col in range(cols):
                for row in range(rows):
                    kx1 = zx1 + 5 + col * kw + 2
                    ky1 = zy1 + 5 + row * kh + 2
                    kx2 = kx1 + kw - 4
                    ky2 = ky1 + kh - 4
                    self.canvas.create_rectangle(
                        kx1, ky1, kx2, ky2,
                        fill="#1C202C", outline=hex_color, width=1,
                        tags=(f"zone_{i}_keys",)
                    )

            # Selection outline & glow
            is_selected = i in self.selected_zones
            outline_color = "#00C8FF" if is_selected else "#2A3040"
            outline_width = 3 if is_selected else 1

            self.canvas.create_rectangle(
                zx1 - 1, zy1 - 1, zx2 + 1, zy2 + 1,
                fill="", outline=outline_color, width=outline_width,
                tags=(f"zone_{i}_border",)
            )

            # Zone title label on canvas
            label_text = f"ZONE {i+1}"
            if i == 0:
                label_text += " [WASD]"
            self.canvas.create_text(
                (zx1 + zx2) / 2, zy2 - 14,
                text=label_text, fill="#FFFFFF" if is_selected else "#808696",
                font=("Segoe UI", 9, "bold" if is_selected else "normal"),
                tags=(f"zone_{i}_text",)
            )

    def redraw_colors_only(self):
        """Fast path: updates only color fills and borders without rebuilding shapes."""
        for i in range(4):
            r, g, b = self.current_colors[i] if i < len(self.current_colors) else (0, 0, 0)
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            dark_fill = f"#{int(r*0.25):02x}{int(g*0.25):02x}{int(b*0.25):02x}"

            self.canvas.itemconfig(f"zone_{i}_bg", fill=dark_fill)
            self.canvas.itemconfig(f"zone_{i}_keys", outline=hex_color)
