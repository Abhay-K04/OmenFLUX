"""
Profile storage and preset management for OmenGlow.
Persists lighting profiles as JSON in %APPDATA%/OmenGlow/profiles/.
Provides 20 distinct, unique aesthetic presets non-overlapping with procedural effects.
"""

import json
import os
from typing import Dict, List, Optional, Tuple


class Profile:
    def __init__(
        self,
        name: str,
        effect: str = "Static",
        speed: float = 1.0,
        brightness: float = 1.0,
        zone_colors: Optional[List[Tuple[int, int, int]]] = None,
    ):
        self.name = name
        self.effect = effect
        self.speed = speed
        self.brightness = brightness
        self.zone_colors = zone_colors or [
            (255, 0, 80),
            (0, 200, 255),
            (140, 0, 255),
            (0, 255, 170),
        ]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "effect": self.effect,
            "speed": self.speed,
            "brightness": self.brightness,
            "zone_colors": [list(c) for c in self.zone_colors],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        colors = [tuple(c) for c in data.get("zone_colors", [])]
        while len(colors) < 4:
            colors.append((255, 255, 255))
        return cls(
            name=data.get("name", "Custom"),
            effect=data.get("effect", "Static"),
            speed=float(data.get("speed", 1.0)),
            brightness=float(data.get("brightness", 1.0)),
            zone_colors=colors[:4],
        )


# 20 Distinct, Thematic Presets non-overlapping with the 14 procedural effects
# (keeping only iconic 'OMEN Crimson' and 'Cyberpunk 2077' as requested)
DEFAULT_PRESETS: List[Profile] = [
    Profile(
        name="Apex Vanguard",
        effect="Apex Overdrive",  # Exclusive dynamic kinetic combo engine (only on Apex Vanguard)
        speed=1.0,
        brightness=1.0,
        zone_colors=[
            (255, 215, 0),   # Zone 0 (WASD): Radiant Solar Amber-Gold Reactor
            (225, 0, 190),   # Zone 1 (Left non-WASD): Neon Electro-Violet
            (0, 240, 255),   # Zone 2 (Center): Electric Cyber Cyan
            (255, 35, 85),   # Zone 3 (Right / Nav): Blazing Plasma Coral
        ],
    ),
    Profile(
        name="Sakura Blossom",
        effect="Breathing",
        speed=0.8,
        brightness=1.0,
        zone_colors=[
            (255, 175, 205), # Zone 0 (WASD): Soft Rose Petal Pink
            (255, 235, 242), # Zone 1 (Left non-WASD): Pale Blush White
            (215, 185, 255), # Zone 2 (Center): Pastel Wisteria Lavender
            (175, 235, 250), # Zone 3 (Right / Nav): Misty Spring Azure
        ],
    ),
    Profile(
        name="Quantum Prism",
        effect="Prismatic Aurora",
        speed=1.0,
        brightness=1.0,
        zone_colors=[
            (145, 255, 215), # Zone 0 (WASD): Luminous Mint Tint
            (245, 165, 255), # Zone 1 (Left non-WASD): Holographic Lilac
            (155, 225, 255), # Zone 2 (Center): Crystal Ice Blue
            (255, 225, 165), # Zone 3 (Right / Nav): Champagne Sunlight
        ],
    ),
    Profile(
        name="OMEN Crimson",
        effect="Breathing",
        speed=1.0,
        brightness=1.0,
        zone_colors=[(255, 0, 30), (255, 15, 0), (200, 0, 20), (255, 0, 50)],
    ),
    Profile(
        name="Cyberpunk 2077",
        effect="Color Wave",
        speed=1.2,
        brightness=1.0,
        zone_colors=[(255, 0, 110), (0, 240, 255), (255, 220, 0), (140, 0, 255)],
    ),
    Profile(
        name="Neon Tokyo",
        effect="Prismatic Aurora",
        speed=1.1,
        brightness=1.0,
        zone_colors=[(255, 0, 128), (128, 0, 255), (0, 255, 200), (255, 0, 80)],
    ),
    Profile(
        name="Abyssal Trench",
        effect="Plasma Pulse",
        speed=0.9,
        brightness=1.0,
        zone_colors=[(0, 180, 255), (0, 80, 220), (0, 240, 180), (0, 40, 160)],
    ),
    Profile(
        name="Inferno Forge",
        effect="Solar Flare",
        speed=1.2,
        brightness=1.0,
        zone_colors=[(255, 20, 0), (255, 90, 0), (255, 170, 0), (200, 10, 0)],
    ),
    Profile(
        name="Glacial Tundra",
        effect="Breathing",
        speed=0.8,
        brightness=1.0,
        zone_colors=[(220, 245, 255), (0, 200, 255), (80, 160, 255), (180, 230, 255)],
    ),
    Profile(
        name="Acid Wasteland",
        effect="Color Wave",
        speed=1.3,
        brightness=1.0,
        zone_colors=[(160, 255, 0), (80, 255, 20), (220, 255, 0), (30, 220, 40)],
    ),
    Profile(
        name="Synthwave 1984",
        effect="Spectrum Cycle",
        speed=1.0,
        brightness=1.0,
        zone_colors=[(255, 20, 147), (138, 43, 226), (255, 140, 0), (0, 255, 240)],
    ),
    Profile(
        name="Event Horizon",
        effect="Cosmic Starlight",
        speed=1.0,
        brightness=1.0,
        zone_colors=[(20, 0, 70), (90, 0, 180), (0, 180, 255), (130, 0, 255)],
    ),
    Profile(
        name="Solar Corona",
        effect="Solar Flare",
        speed=1.1,
        brightness=1.0,
        zone_colors=[(255, 215, 0), (255, 255, 220), (255, 140, 0), (255, 80, 0)],
    ),
    Profile(
        name="Bioluminescence",
        effect="Breathing",
        speed=0.9,
        brightness=1.0,
        zone_colors=[(0, 255, 160), (0, 220, 255), (100, 255, 80), (0, 190, 210)],
    ),
    Profile(
        name="Valkyrie Flight",
        effect="Color Wave",
        speed=1.1,
        brightness=1.0,
        zone_colors=[(255, 200, 80), (0, 220, 230), (230, 180, 50), (80, 200, 255)],
    ),
    Profile(
        name="Ghost Recon",
        effect="Static",
        speed=1.0,
        brightness=1.0,
        zone_colors=[(40, 255, 40), (10, 180, 30), (30, 210, 20), (60, 255, 50)],
    ),
    Profile(
        name="Hyperdrive Jump",
        effect="Binary Cascade",
        speed=1.5,
        brightness=1.0,
        zone_colors=[(255, 255, 255), (0, 230, 255), (0, 140, 255), (180, 100, 255)],
    ),
    Profile(
        name="Blood Moon",
        effect="Heartbeat",
        speed=1.0,
        brightness=1.0,
        zone_colors=[(180, 0, 0), (255, 10, 20), (120, 0, 10), (220, 0, 0)],
    ),
    Profile(
        name="Chroma Symphony",
        effect="Audio Pulse (Ambient)",
        speed=1.2,
        brightness=1.0,
        zone_colors=[(255, 0, 90), (0, 210, 255), (160, 0, 255), (0, 255, 180)],
    ),
    Profile(
        name="Stealth (Blackout)",
        effect="Static",
        speed=1.0,
        brightness=0.0,
        zone_colors=[(0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0)],
    ),
]

LEGACY_DUPLICATES = [
    "Fire & Embers.json",
    "Fire  Embers.json",
    "Northern Lights.json",
    "Knight Rider.json",
    "Starfield Twinkle.json",
    "Rainbow Cycle.json",
    "Tokyo Cyber Glitch.json",
    "Emergency Strobe.json",
    "Reactive Typing.json",
    "Deep Ocean Abyss.json",
    "Matrix Green.json",
    "Ice Blizzard.json",
    "Toxic Biohazard.json",
    "Vaporwave Sunset.json",
    "Stealth Off.json",
]


class ProfileManager:
    """Manages profile loading, saving, listing, and default presets."""

    def __init__(self, profiles_dir: Optional[str] = None):
        if profiles_dir:
            self.profiles_dir = profiles_dir
        else:
            appdata = os.getenv("APPDATA") or os.path.expanduser("~")
            self.profiles_dir = os.path.join(appdata, "OmenGlow", "profiles")

        os.makedirs(self.profiles_dir, exist_ok=True)
        self.ensure_default_presets()

    def ensure_default_presets(self):
        """Clean up legacy duplicate presets and ensure all modern curated presets exist."""
        # 1. Remove legacy duplicate-named profiles that clash with effects deck
        for legacy_file in LEGACY_DUPLICATES:
            fp = os.path.join(self.profiles_dir, legacy_file)
            if os.path.exists(fp):
                try:
                    os.remove(fp)
                except Exception:
                    pass

        # 2. Write or update default presets
        for preset in DEFAULT_PRESETS:
            fp = os.path.join(self.profiles_dir, f"{preset.name}.json")
            if not os.path.exists(fp):
                self.save_profile(preset)
            elif preset.name == "Apex Vanguard":
                # Ensure Apex Vanguard always runs its exclusive Apex Overdrive combo engine
                existing = self.load_profile("Apex Vanguard")
                if existing and (existing.effect != "Apex Overdrive" or existing.zone_colors != preset.zone_colors):
                    self.save_profile(preset)

    def list_profiles(self) -> List[str]:
        """Return names of all saved profiles sorted alphabetically."""
        profiles = []
        try:
            for fname in os.listdir(self.profiles_dir):
                if fname.endswith(".json"):
                    profiles.append(fname[:-5])
        except Exception:
            pass
        return sorted(profiles)

    def get_all_profiles_data(self) -> List[dict]:
        """Return full data for all saved profiles."""
        data_list = []
        for name in self.list_profiles():
            prof = self.load_profile(name)
            if prof:
                data_list.append(prof.to_dict())
        return data_list

    def load_profile(self, name: str) -> Optional[Profile]:
        """Load a profile by name."""
        fp = os.path.join(self.profiles_dir, f"{name}.json")
        if not os.path.exists(fp):
            # Try finding case-insensitively
            for fname in os.listdir(self.profiles_dir):
                if fname.lower() == f"{name}.json".lower():
                    fp = os.path.join(self.profiles_dir, fname)
                    break

        if not os.path.exists(fp):
            return None

        try:
            with open(fp, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Profile.from_dict(data)
        except Exception:
            return None

    def save_profile(self, profile: Profile) -> bool:
        """Save a profile to disk."""
        fp = os.path.join(self.profiles_dir, f"{profile.name}.json")
        try:
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(profile.to_dict(), f, indent=2)
            return True
        except Exception:
            return False

    def delete_profile(self, name: str) -> bool:
        """Delete a profile by name."""
        fp = os.path.join(self.profiles_dir, f"{name}.json")
        if os.path.exists(fp):
            try:
                os.remove(fp)
                return True
            except Exception:
                return False
        return False
