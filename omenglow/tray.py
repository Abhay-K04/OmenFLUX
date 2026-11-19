"""
OmenGlow System Tray Controller
Manages background operation, notification area icon, quick presets, and lifecycle.
"""

import logging
import os
import sys
from typing import Callable, Optional
from PIL import Image
import pystray

logger = logging.getLogger("omenglow.tray")


class OmenSystemTray:
    def __init__(
        self,
        on_open_studio: Callable[[], None],
        on_take_control: Callable[[], None],
        on_release_ols: Callable[[], None],
        on_load_preset: Callable[[str], None],
        on_exit: Callable[[], None],
        get_owner_name: Optional[Callable[[], str]] = None,
    ):
        self.on_open_studio = on_open_studio
        self.on_take_control = on_take_control
        self.on_release_ols = on_release_ols
        self.on_load_preset = on_load_preset
        self.on_exit = on_exit
        self.get_owner_name = get_owner_name

        self._icon: Optional[pystray.Icon] = None
        self._image = self._load_icon_image()

    def _load_icon_image(self) -> Image.Image:
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        candidate_dirs = [
            os.path.join(base_dir, "omenglow", "assets"),
            os.path.join(base_dir, "assets"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets"),
        ]
        for d in candidate_dirs:
            for fname in ["omenglow.png", "omenglow.ico"]:
                p = os.path.join(d, fname)
                if os.path.exists(p):
                    try:
                        return Image.open(p)
                    except Exception:
                        pass

        # Fallback 32x32 transparent diamond image
        return Image.new("RGBA", (32, 32), (0, 229, 255, 255))

    def _create_menu(self) -> pystray.Menu:
        presets_list = [
            "OMEN Crimson",
            "Cyberpunk 2077",
            "Neon Tokyo",
            "Abyssal Trench",
            "Inferno Forge",
            "Glacial Tundra",
            "Acid Wasteland",
            "Synthwave 1984",
            "Event Horizon",
            "Solar Corona",
            "Bioluminescence",
            "Valkyrie Flight",
            "Ghost Recon",
            "Hyperdrive Jump",
            "Blood Moon",
            "Chroma Symphony",
            "Stealth (Blackout)",
        ]

        def make_preset_handler(preset_name: str):
            return lambda icon, item: self.on_load_preset(preset_name)

        preset_items = [
            pystray.MenuItem(name, make_preset_handler(name))
            for name in presets_list
        ]

        menu = pystray.Menu(
            pystray.MenuItem("Open Studio", lambda icon, item: self.on_open_studio(), default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⚡ Take Control (OmenFLUX)", lambda icon, item: self.on_take_control()),
            pystray.MenuItem("🔄 Handover to OMEN Light Studio", lambda icon, item: self.on_release_ols()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Presets", pystray.Menu(*preset_items)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit OmenFLUX", lambda icon, item: self._handle_exit()),
        )
        return menu

    def _handle_exit(self):
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
        if self.on_exit:
            self.on_exit()

    def start(self):
        """Start system tray icon in detached thread."""
        try:
            self._icon = pystray.Icon(
                "OmenFLUX",
                self._image,
                "OmenFLUX — OMEN 16 RGB Studio",
                menu=self._create_menu(),
            )
            self._icon.run_detached()
            logger.info("System Tray icon launched successfully.")
        except Exception as e:
            logger.warning("Could not launch system tray icon: %s", e)

    def stop(self):
        """Stop system tray icon."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None