"""
Color Picker and Quick Swatch Palette Component for OmenGlow.
Allows precise RGB, Hex, and preset color selection for keyboard zones,
plus quick palette randomizer and utility actions.
"""

import random
from typing import Callable, Optional, Tuple
import customtkinter as ctk

SWATCHES = [
    ("#FF0033", "Crimson"),
    ("#FF007F", "Cyber Pink"),
    ("#8A00FF", "Violet"),
    ("#0055FF", "Blue"),
    ("#00F5FF", "Cyan"),
    ("#00FFAA", "Mint"),
    ("#76FF03", "Toxic Lime"),
    ("#FFD600", "Gold"),
    ("#FF5500", "Orange"),
    ("#FFFFFF", "White"),
    ("#000000", "Off"),
]


class ColorPickerPanel(ctk.CTkFrame):
    """Control panel for choosing colors with sliders, swatches, and hex input."""

    def __init__(
        self,
        master,
        on_color_changed: Optional[Callable[[Tuple[int, int, int]], None]] = None,
        on_randomize: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="#181A20", corner_radius=12, **kwargs)

        self._on_color_changed = on_color_changed
        self._on_randomize = on_randomize
        self._current_rgb: Tuple[int, int, int] = (0, 200, 255)
        self._suppress_events = False

        self.grid_columnconfigure(1, weight=1)

        # Title & Randomize Button Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, columnspan=3, padx=16, pady=(12, 10), sticky="ew")

        self.title_lbl = ctk.CTkLabel(
            self.header_frame,
            text="Color Palette & Controls",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FFFFFF",
        )
        self.title_lbl.pack(side="left")

        self.btn_random = ctk.CTkButton(
            self.header_frame,
            text="🎲 Randomize",
            font=ctk.CTkFont(size=11),
            width=88,
            height=26,
            fg_color="#242836",
            hover_color="#333A4E",
            text_color="#00C8FF",
            command=self._handle_randomize,
        )
        self.btn_random.pack(side="right")

        # Color Preview Block & Hex Entry
        self.top_row = ctk.CTkFrame(self, fg_color="transparent")
        self.top_row.grid(row=1, column=0, columnspan=3, padx=16, pady=(0, 10), sticky="ew")

        self.preview_box = ctk.CTkLabel(
            self.top_row,
            text="",
            width=50,
            height=32,
            fg_color="#00C8FF",
            corner_radius=6,
        )
        self.preview_box.pack(side="left", padx=(0, 12))

        self.hex_var = ctk.StringVar(value="#00C8FF")
        self.hex_entry = ctk.CTkEntry(
            self.top_row,
            textvariable=self.hex_var,
            width=100,
            height=32,
            font=ctk.CTkFont(family="Consolas", size=13),
        )
        self.hex_entry.pack(side="left", padx=(0, 10))
        self.hex_entry.bind("<Return>", self._on_hex_enter)
        self.hex_entry.bind("<FocusOut>", self._on_hex_enter)

        # RGB Sliders
        # Red
        self.lbl_r = ctk.CTkLabel(self, text="R", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FF4D4D")
        self.lbl_r.grid(row=2, column=0, padx=(16, 6), pady=4, sticky="w")
        self.slider_r = ctk.CTkSlider(self, from_=0, to=255, number_of_steps=255, progress_color="#FF4D4D", command=self._on_slider_move)
        self.slider_r.grid(row=2, column=1, padx=6, pady=4, sticky="ew")
        self.val_r = ctk.CTkLabel(self, text="0", width=34, font=ctk.CTkFont(family="Consolas", size=11))
        self.val_r.grid(row=2, column=2, padx=(6, 16), pady=4)

        # Green
        self.lbl_g = ctk.CTkLabel(self, text="G", font=ctk.CTkFont(size=12, weight="bold"), text_color="#00E676")
        self.lbl_g.grid(row=3, column=0, padx=(16, 6), pady=4, sticky="w")
        self.slider_g = ctk.CTkSlider(self, from_=0, to=255, number_of_steps=255, progress_color="#00E676", command=self._on_slider_move)
        self.slider_g.grid(row=3, column=1, padx=6, pady=4, sticky="ew")
        self.val_g = ctk.CTkLabel(self, text="200", width=34, font=ctk.CTkFont(family="Consolas", size=11))
        self.val_g.grid(row=3, column=2, padx=(6, 16), pady=4)

        # Blue
        self.lbl_b = ctk.CTkLabel(self, text="B", font=ctk.CTkFont(size=12, weight="bold"), text_color="#00B0FF")
        self.lbl_b.grid(row=4, column=0, padx=(16, 6), pady=4, sticky="w")
        self.slider_b = ctk.CTkSlider(self, from_=0, to=255, number_of_steps=255, progress_color="#00B0FF", command=self._on_slider_move)
        self.slider_b.grid(row=4, column=1, padx=6, pady=4, sticky="ew")
        self.val_b = ctk.CTkLabel(self, text="255", width=34, font=ctk.CTkFont(family="Consolas", size=11))
        self.val_b.grid(row=4, column=2, padx=(6, 16), pady=4)

        # Preset Swatches row
        self.swatch_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.swatch_frame.grid(row=5, column=0, columnspan=3, padx=16, pady=(10, 12), sticky="ew")

        for hex_code, name in SWATCHES:
            btn = ctk.CTkButton(
                self.swatch_frame,
                text="",
                width=24,
                height=24,
                corner_radius=12,
                fg_color=hex_code,
                hover_color=hex_code,
                border_width=1,
                border_color="#333848",
                command=lambda h=hex_code: self.set_from_hex(h),
            )
            btn.pack(side="left", padx=2, expand=True)

        self.set_color(self._current_rgb)

    def set_color(self, rgb: Tuple[int, int, int]):
        """Set picker state programmatically."""
        self._suppress_events = True
        self._current_rgb = rgb
        r, g, b = rgb
        self.slider_r.set(r)
        self.slider_g.set(g)
        self.slider_b.set(b)
        self.val_r.configure(text=str(r))
        self.val_g.configure(text=str(g))
        self.val_b.configure(text=str(b))

        hex_str = f"#{r:02X}{g:02X}{b:02X}"
        self.hex_var.set(hex_str)
        self.preview_box.configure(fg_color=hex_str)
        self._suppress_events = False

    def set_from_hex(self, hex_code: str):
        h = hex_code.lstrip("#")
        if len(h) == 6:
            try:
                r = int(h[0:2], 16)
                g = int(h[2:4], 16)
                b = int(h[4:6], 16)
                self.set_color((r, g, b))
                if self._on_color_changed:
                    self._on_color_changed((r, g, b))
            except ValueError:
                pass

    def _on_slider_move(self, _=None):
        if self._suppress_events:
            return
        r = int(self.slider_r.get())
        g = int(self.slider_g.get())
        b = int(self.slider_b.get())
        self._current_rgb = (r, g, b)

        self.val_r.configure(text=str(r))
        self.val_g.configure(text=str(g))
        self.val_b.configure(text=str(b))

        hex_str = f"#{r:02X}{g:02X}{b:02X}"
        self.hex_var.set(hex_str)
        self.preview_box.configure(fg_color=hex_str)

        if self._on_color_changed:
            self._on_color_changed((r, g, b))

    def _on_hex_enter(self, _=None):
        self.set_from_hex(self.hex_var.get())

    def _handle_randomize(self):
        if self._on_randomize:
            self._on_randomize()
        else:
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            self.set_color((r, g, b))
            if self._on_color_changed:
                self._on_color_changed((r, g, b))
