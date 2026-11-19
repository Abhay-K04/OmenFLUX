"""
Effects and Animation Controls Panel for OmenGlow.
Allows selecting animation effects (Breathing, Wave, Rainbow, Liquid Flow, etc.),
and tuning speed, brightness, and flow fluidity in real time.
"""

from typing import Callable, Optional
import customtkinter as ctk

from ...effects.engine import EffectType


class EffectsPanel(ctk.CTkFrame):
    """Panel for configuring animation modes, speeds, brightness, and flow smoothness."""

    def __init__(
        self,
        master,
        on_effect_changed: Optional[Callable[[EffectType], None]] = None,
        on_speed_changed: Optional[Callable[[float], None]] = None,
        on_brightness_changed: Optional[Callable[[float], None]] = None,
        on_smoothness_changed: Optional[Callable[[float], None]] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color="#181A20", corner_radius=12, **kwargs)

        self._on_effect_changed = on_effect_changed
        self._on_speed_changed = on_speed_changed
        self._on_brightness_changed = on_brightness_changed
        self._on_smoothness_changed = on_smoothness_changed

        self.grid_columnconfigure(1, weight=1)

        # Title
        self.title_lbl = ctk.CTkLabel(
            self,
            text="Lighting Effects & Dynamics",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FFFFFF",
        )
        self.title_lbl.grid(row=0, column=0, columnspan=3, padx=16, pady=(10, 8), sticky="w")

        # 1. Effect Mode OptionMenu
        self.lbl_mode = ctk.CTkLabel(self, text="Mode", font=ctk.CTkFont(size=12, weight="bold"), text_color="#A0A5B5")
        self.lbl_mode.grid(row=1, column=0, padx=(16, 8), pady=5, sticky="w")

        effect_options = [e.value for e in EffectType if e != EffectType.APEX_OVERDRIVE]
        self.effect_menu = ctk.CTkOptionMenu(
            self,
            values=effect_options,
            command=self._on_effect_select,
            fg_color="#262B3A",
            button_color="#00C8FF",
            button_hover_color="#0096C7",
            text_color="#FFFFFF",
            dropdown_fg_color="#1F2330",
            width=180,
            height=30,
        )
        self.effect_menu.set(EffectType.STATIC.value)
        self.effect_menu.grid(row=1, column=1, columnspan=2, padx=(8, 16), pady=5, sticky="w")

        # 2. Speed Slider
        self.lbl_speed = ctk.CTkLabel(self, text="Speed", font=ctk.CTkFont(size=12, weight="bold"), text_color="#A0A5B5")
        self.lbl_speed.grid(row=2, column=0, padx=(16, 8), pady=4, sticky="w")

        self.slider_speed = ctk.CTkSlider(
            self,
            from_=0.2,
            to=3.0,
            number_of_steps=28,
            progress_color="#00C8FF",
            command=self._on_speed_slide,
        )
        self.slider_speed.set(1.0)
        self.slider_speed.grid(row=2, column=1, padx=6, pady=4, sticky="ew")

        self.val_speed = ctk.CTkLabel(self, text="1.0x", width=42, font=ctk.CTkFont(family="Consolas", size=11))
        self.val_speed.grid(row=2, column=2, padx=(6, 16), pady=4)

        # 3. Brightness Slider
        self.lbl_bri = ctk.CTkLabel(self, text="Brightness", font=ctk.CTkFont(size=12, weight="bold"), text_color="#A0A5B5")
        self.lbl_bri.grid(row=3, column=0, padx=(16, 8), pady=4, sticky="w")

        self.slider_bri = ctk.CTkSlider(
            self,
            from_=0.0,
            to=1.0,
            number_of_steps=100,
            progress_color="#FFB300",
            command=self._on_bri_slide,
        )
        self.slider_bri.set(1.0)
        self.slider_bri.grid(row=3, column=1, padx=6, pady=4, sticky="ew")

        self.val_bri = ctk.CTkLabel(self, text="100%", width=42, font=ctk.CTkFont(family="Consolas", size=11))
        self.val_bri.grid(row=3, column=2, padx=(6, 16), pady=4)

        # 4. Fluidity / Flow Smoothness Slider
        self.lbl_fluid = ctk.CTkLabel(self, text="Fluidity", font=ctk.CTkFont(size=12, weight="bold"), text_color="#A0A5B5")
        self.lbl_fluid.grid(row=4, column=0, padx=(16, 8), pady=(4, 10), sticky="w")

        self.slider_fluid = ctk.CTkSlider(
            self,
            from_=0.0,
            to=1.0,
            number_of_steps=100,
            progress_color="#9D00FF",
            command=self._on_fluid_slide,
        )
        self.slider_fluid.set(0.85)
        self.slider_fluid.grid(row=4, column=1, padx=6, pady=(4, 10), sticky="ew")

        self.val_fluid = ctk.CTkLabel(self, text="85%", width=42, font=ctk.CTkFont(family="Consolas", size=11))
        self.val_fluid.grid(row=4, column=2, padx=(6, 16), pady=(4, 10))

    def _on_effect_select(self, choice: str):
        for e in EffectType:
            if e.value == choice:
                if self._on_effect_changed:
                    self._on_effect_changed(e)
                break

    def _on_speed_slide(self, val: float):
        self.val_speed.configure(text=f"{val:.1f}x")
        if self._on_speed_changed:
            self._on_speed_changed(float(val))

    def _on_bri_slide(self, val: float):
        pct = int(val * 100)
        self.val_bri.configure(text=f"{pct}%")
        if self._on_brightness_changed:
            self._on_brightness_changed(float(val))

    def _on_fluid_slide(self, val: float):
        pct = int(val * 100)
        self.val_fluid.configure(text=f"{pct}%")
        if self._on_smoothness_changed:
            self._on_smoothness_changed(float(val))
