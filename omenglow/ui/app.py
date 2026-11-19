"""
Main Application Window for OmenGlow.
A lightweight, modern, dark-themed replacement for OMEN Light Studio's keyboard lighting,
engineered for seamless coexistence and instant handover.
"""

import os
import random
import threading
import time
from typing import List, Set, Tuple
import customtkinter as ctk
from PIL import Image, ImageTk

from ..hardware.shared_memory import SharedMemoryLighting
from ..hardware.handover import OlsHandoverManager, ControlOwner
from ..effects.engine import AnimationEngine, EffectType, hsv_to_rgb255
from ..profiles.manager import Profile, ProfileManager

from .components.handover_bar import HandoverBar
from .components.keyboard_widget import KeyboardPreviewWidget
from .components.color_picker import ColorPickerPanel
from .components.effects_panel import EffectsPanel
from .components.profiles_panel import ProfilesPanel


class OmenGlowApp(ctk.CTk):
    """Main application window for OmenGlow."""

    def __init__(self):
        super().__init__()

        # Appearance & Window Configuration
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("OmenGlow — OMEN 16 Keyboard RGB Controller")
        self.geometry("840x660")
        self.minsize(800, 620)
        self.configure(fg_color="#0D0E15")
        try:
            self.state("zoomed")
        except Exception:
            pass

        # Set Window and Taskbar Icon (Official OmenGlow Branding)
        self._setup_icons()

        # Hardware & Engine Initializations
        self.shm = SharedMemoryLighting()
        self.handover = OlsHandoverManager(on_state_changed=self._on_handover_state_changed)
        self.profiles = ProfileManager()

        self.engine = AnimationEngine(
            shm=self.shm,
            on_frame=self._on_animation_frame,
        )

        self._selected_zones: Set[int] = {0, 1, 2, 3}

        # Build UI
        self._build_ui()

        # Start animation engine (initially paused until user takes control, or active if standalone)
        self.engine.start()
        if self.handover.is_ols_running():
            # OLS is currently streaming, so start in monitoring/paused mode
            self.engine.pause()
            self.handover_bar.update_owner(ControlOwner.OLS)
        else:
            # OLS not running, take control directly
            self.handover.take_control()
            self.engine.resume()
            self.handover_bar.update_owner(ControlOwner.STANDALONE)

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_icons(self):
        """Load and apply high-res OmenGlow logo for window titlebar and Windows Taskbar."""
        assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
        ico_path = os.path.join(assets_dir, "omenglow.ico")
        png_path = os.path.join(assets_dir, "omenglow.png")

        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

        if os.path.exists(png_path):
            try:
                pil_icon = Image.open(png_path).resize((64, 64), Image.Resampling.LANCZOS)
                self._photo_icon = ImageTk.PhotoImage(pil_icon)
                self.wm_iconphoto(True, self._photo_icon)
            except Exception:
                pass

    def _build_ui(self):
        # Main container with padding
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=16)

        # 1. Title & Header Row (with branded logo badge)
        self.handover_bar.pack(fill="x", pady=(0, 14))

        # 3. Interactive Keyboard Widget
        self.keyboard_widget = KeyboardPreviewWidget(
            self.container,
            on_zone_selected=self._on_zone_selected,
        )
        self.keyboard_widget.pack(fill="x", pady=(0, 14))

        # 4. Lower Two-Column Grid (Color Controls + Dynamics & Profiles)
        self.bottom_grid = ctk.CTkFrame(self.container, fg_color="transparent")
        self.bottom_grid.pack(fill="both", expand=True)
        self.bottom_grid.grid_columnconfigure((0, 1), weight=1, uniform="bottom_cols")
        self.bottom_grid.grid_rowconfigure(0, weight=1)

        # Left Column: Color Picker & Palette
        self.color_picker = ColorPickerPanel(
            self.bottom_grid,
            on_color_changed=self._on_color_picker_changed,
            on_randomize=self._on_randomize_palette,
        )
        self.color_picker.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        # Right Column: Effects Dynamics + Profiles
        self.right_col = ctk.CTkFrame(self.bottom_grid, fg_color="transparent")
        self.right_col.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        self.right_col.grid_rowconfigure((0, 1), weight=1)
        self.right_col.grid_columnconfigure(0, weight=1)

        self.effects_panel = EffectsPanel(
            self.right_col,
            on_effect_changed=self._on_effect_changed,
            on_speed_changed=self._on_speed_changed,
            on_brightness_changed=self._on_brightness_changed,
        )
        self.effects_panel.grid(row=0, column=0, pady=(0, 8), sticky="nsew")

        self.profiles_panel = ProfilesPanel(
            self.right_col,
            profile_manager=self.profiles,
            on_profile_selected=self._on_profile_loaded,
            on_save_requested=self._on_profile_saved,
        )
        self.profiles_panel.grid(row=1, column=0, pady=(8, 0), sticky="nsew")

    def _on_take_control_clicked(self):
        """User clicked 'Take Control'."""
        success = self.handover.take_control()
        if success:
            self.engine.resume()
            self.handover_bar.update_owner(self.handover.current_owner)

    def _on_handover_ols_clicked(self):
        """User clicked 'Release to OLS'."""
        self.engine.pause()
        self.handover.handover_to_ols()
        self.handover_bar.update_owner(self.handover.current_owner)

    def _on_handover_state_changed(self, owner: ControlOwner):
        """Callback from handover manager when ownership changes."""
        self.after(0, lambda: self.handover_bar.update_owner(owner))

    def _on_zone_selected(self, selected_zones: Set[int]):
        self._selected_zones = selected_zones
        # If single zone selected, load its color into picker
        if len(selected_zones) == 1:
            z_idx = list(selected_zones)[0]
            if z_idx < len(self.engine.zone_colors):
                self.color_picker.set_color(self.engine.zone_colors[z_idx])

    def _on_color_picker_changed(self, rgb: Tuple[int, int, int]):
        """User adjusted color sliders or picked a swatch."""
        for z_idx in self._selected_zones:
            self.engine.set_zone_color(z_idx, rgb)

        # If currently paused / under OLS, auto take control when user edits colors
        if self.handover.current_owner != ControlOwner.OMENGLOW:
            self._on_take_control_clicked()

    def _on_randomize_palette(self):
        """Generate a harmonious palette across all 4 zones, including lighter & pastel tones."""
        base_hue = random.random()
        palette = []
        mode = random.choice(["analogous", "triadic", "cyberpunk", "complementary"])
        
        # Tone styles: pastel (30%), luminous light (30%), vivid (40%)
        style_roll = random.random()
        for i in range(4):
            if mode == "analogous":
                h = (base_hue + i * 0.08) % 1.0
            elif mode == "triadic":
                h = (base_hue + (i % 3) * 0.33) % 1.0
            elif mode == "complementary":
                h = (base_hue + (0.5 if i % 2 == 1 else 0.0)) % 1.0
            else:  # cyberpunk
                h = random.choice([0.5, 0.85, 0.15, 0.75])
            
            if style_roll < 0.30:
                s = random.uniform(0.22, 0.50)
                v = random.uniform(0.95, 1.0)
            elif style_roll < 0.60:
                s = random.uniform(0.40, 0.68)
                v = random.uniform(0.92, 1.0)
            else:
                s = random.uniform(0.80, 1.0)
                v = random.uniform(0.90, 1.0)
                
            rgb = hsv_to_rgb255(h, s, v)
            palette.append(rgb)

        self.engine.set_all_colors(palette)
        self.color_picker.set_color(palette[0])
        if self.handover.current_owner != ControlOwner.OMENGLOW:
            self._on_take_control_clicked()

    def _on_effect_changed(self, effect: EffectType):
        self.engine.effect = effect
        if self.handover.current_owner != ControlOwner.OMENGLOW:
            self._on_take_control_clicked()

    def _on_speed_changed(self, speed: float):
        self.engine.speed = speed

    def _on_brightness_changed(self, bri: float):
        self.engine.brightness = bri

    def _on_profile_loaded(self, profile: Profile):
        """Apply a loaded profile."""
        self.engine.set_all_colors(profile.zone_colors)
        matched = False
        for e in EffectType:
            if e.value == profile.effect:
                self.engine.effect = e
                self.effects_panel.set_effect(e)
                matched = True
                break
        if not matched:
            self.engine.effect = EffectType.STATIC
            self.effects_panel.set_effect(EffectType.STATIC)

        self.engine.speed = profile.speed
        self.effects_panel.set_speed(profile.speed)
        self.engine.brightness = profile.brightness
        self.effects_panel.set_brightness(profile.brightness)

        if self.handover.current_owner != ControlOwner.OMENGLOW:
            self._on_take_control_clicked()

    def _on_profile_saved(self, name: str):
        """Save the current settings into a named profile."""
        profile = Profile(
            name=name,
            effect=self.engine.effect.value,
            speed=self.engine.speed,
            brightness=self.engine.brightness,
            zone_colors=self.engine.zone_colors,
        )
        self.profiles.save_profile(profile)

    def _on_animation_frame(self, colors: List[Tuple[int, int, int]]):
        """Called ~35 times per second with live RGB values."""
        # Update keyboard canvas preview (schedule on UI thread)
        try:
            self.after_idle(lambda: self.keyboard_widget.update_colors(colors))
        except Exception:
            pass

    def _on_closing(self):
        """Clean shutdown: stop engine and resume OLS."""
        self.engine.stop()
        self.handover.handover_to_ols()
        self.shm.close()
        self.destroy()