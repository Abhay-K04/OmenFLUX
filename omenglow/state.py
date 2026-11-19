"""
OmenGlow State & Settings Persistence Manager
Persists active lighting profile, custom colors, effect parameters, and autostart configuration.
"""

import json
import logging
import os
import sys
from typing import Dict, List, Optional, Tuple
import winreg

logger = logging.getLogger("omenglow.state")

REG_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "OmenFLUX"


class StateManager:
    def __init__(self):
        appdata = os.getenv("APPDATA") or os.path.expanduser("~")
        self.config_dir = os.path.join(appdata, "OmenFLUX")
        legacy_dirs = [os.path.join(appdata, "OmenPulse"), os.path.join(appdata, "OmenGlow")]
        os.makedirs(self.config_dir, exist_ok=True)
        self.state_file = os.path.join(self.config_dir, "config.json")

        # Migrate legacy config if present and new config does not exist
        if not os.path.exists(self.state_file):
            for ldir in legacy_dirs:
                src = os.path.join(ldir, "config.json")
                if os.path.exists(src):
                    try:
                        import shutil
                        shutil.copy2(src, self.state_file)
                        break
                    except Exception:
                        pass

        self.state = self.load_state()

    def get_default_state(self) -> dict:
        return {
            "active_profile": "Cyberpunk 2077",
            "effect": "Static",
            "speed": 1.0,
            "brightness": 1.0,
            "zone_colors": [
                [255, 0, 110],
                [0, 240, 255],
                [255, 220, 0],
                [140, 0, 255]
            ],
            "owner": "OmenFLUX",
            "autostart": False
        }

    def load_state(self) -> dict:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    defaults = self.get_default_state()
                    for k, v in defaults.items():
                        if k not in data:
                            data[k] = v
                    return data
            except Exception as e:
                logger.warning("Failed to load config.json: %s", e)
        return self.get_default_state()

    def save_state(self, updates: Optional[dict] = None) -> bool:
        if updates:
            self.state.update(updates)
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
            return True
        except Exception as e:
            logger.error("Failed to save config.json: %s", e)
            return False

    def is_autostart_registered(self) -> bool:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_READ) as key:
                val, _ = winreg.QueryValueEx(key, APP_NAME)
                return bool(val)
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def set_autostart(self, enable: bool, executable_path: Optional[str] = None) -> bool:
        if not executable_path:
            if getattr(sys, "frozen", False):
                executable_path = sys.executable
            else:
                script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                main_py = os.path.join(script_dir, "main.py")
                pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
                if not os.path.exists(pythonw):
                    pythonw = sys.executable
                executable_path = f'"{pythonw}" "{main_py}"'

        clean_path = executable_path.strip()
        if clean_path.startswith('"') and clean_path.endswith('"'):
            cmd = f'{clean_path} --background'
        elif " " in clean_path and not clean_path.startswith('"'):
            cmd = f'"{clean_path}" --background'
        else:
            cmd = f'{clean_path} --background'

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
                # Always remove legacy autostart entries if present
                for legacy_app in ["OmenPulse", "OmenGlow", "OmenSpectrix"]:
                    try:
                        winreg.DeleteValue(key, legacy_app)
                    except Exception:
                        pass

                if enable:
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
                    logger.info("Registered Windows startup: %s", cmd)
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                        logger.info("Removed Windows startup registry key")
                    except FileNotFoundError:
                        pass
            self.save_state({"autostart": enable})
            return True
        except Exception as e:
            logger.error("Error setting Windows autostart: %s", e)
            return False