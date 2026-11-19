"""
Animation and Lighting Effects Engine for OmenGlow.
Generates real-time color frames for all 4 keyboard zones with 14 distinct
procedural lighting effects, cross-fade transition smoothing, and deep power optimization.
"""

import atexit
import colorsys
import ctypes
from enum import Enum
import math
import random
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple

from ..hardware.shared_memory import SharedMemoryLighting

# Enable 1ms Windows multimedia timer resolution to eliminate frame-time jitter
winmm = ctypes.windll.winmm
try:
    winmm.timeBeginPeriod(1)
    atexit.register(lambda: winmm.timeEndPeriod(1))
except Exception:
    pass

user32 = ctypes.windll.user32
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short


class EffectType(Enum):
    STATIC = "Static"
    BREATHING = "Breathing"
    COLOR_WAVE = "Color Wave"
    SPECTRUM = "Spectrum Cycle"
    HEARTBEAT = "Heartbeat"
    SCANNER = "Knight Rider Scanner"
    AURORA = "Prismatic Aurora"
    PLASMA = "Plasma Pulse"
    GLITCH = "Cyber Glitch"
    STARLIGHT = "Cosmic Starlight"
    CASCADE = "Binary Cascade"
    SOLAR_FLARE = "Solar Flare"
    AUDIO_PULSE = "Audio Pulse (Ambient)"
    REACTIVE = "Reactive Ripple"
    APEX_OVERDRIVE = "Apex Overdrive"  # Exclusive high-octane kinetic combo engine for Apex Vanguard


# Backward compatibility aliases for legacy profile configurations
EFFECT_ALIASES: Dict[str, EffectType] = {
    "Rainbow Cycle": EffectType.SPECTRUM,
    "Fire & Embers": EffectType.SOLAR_FLARE,
    "Fire  Embers": EffectType.SOLAR_FLARE,
    "Northern Lights": EffectType.AURORA,
    "Emergency Strobe": EffectType.GLITCH,
    "Starfield Twinkle": EffectType.STARLIGHT,
    "Matrix Green": EffectType.CASCADE,
    "Reactive Typing": EffectType.REACTIVE,
    "Vanguard Protocol": EffectType.APEX_OVERDRIVE,
    "Apex Protocol": EffectType.APEX_OVERDRIVE,
    "Vanguard": EffectType.APEX_OVERDRIVE,
    "Apex Overdrive": EffectType.APEX_OVERDRIVE,
}


def parse_effect_type(name: str) -> EffectType:
    """Parse effect string into EffectType with legacy alias fallback."""
    for e in EffectType:
        if e.value.lower() == name.lower():
            return e
    if name in EFFECT_ALIASES:
        return EFFECT_ALIASES[name]
    for alias_name, eff in EFFECT_ALIASES.items():
        if alias_name.lower() == name.lower():
            return eff
    return EffectType.STATIC


def hsv_to_rgb255(h: float, s: float, v: float) -> Tuple[int, int, int]:
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, max(0.0, min(1.0, s)), max(0.0, min(1.0, v)))
    return (int(r * 255), int(g * 255), int(b * 255))


def rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
    return colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)


def interpolate_rgb(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


# Mapping of Windows Virtual Key (VK) codes to HP 4-Zone Hardware Architecture:
#   Zone 0: WASD Only (W, A, S, D)
#   Zone 1: Left Section non-WASD (Esc, F1-F4, `~, 1-4, Tab, Q, E, Caps, LShift, Z-C, LCtrl, LWin, LAlt)
#   Zone 2: Center / Middle Section (F5-F10, 5-0, R-O, F-L, V-M, Comma, Period, Spacebar, RAlt, Menu)
#   Zone 3: Right / Nav / Arrows (F11-F12, - =, Backspace, P, [ ], \, ; ', Enter, /, RShift, RCtrl, Nav, Arrows)
KEY_ZONE_MAP: Dict[int, int] = {
    # Zone 0: WASD KEYS ONLY
    0x57: 0,  # W
    0x41: 0,  # A
    0x53: 0,  # S
    0x44: 0,  # D

    # Zone 1: Left Section (Leaving WASD)
    0x1B: 1,  # VK_ESCAPE
    0x70: 1, 0x71: 1, 0x72: 1, 0x73: 1,  # F1 - F4
    0xC0: 1,  # ` ~ (Tilde/Backtick)
    0x31: 1, 0x32: 1, 0x33: 1, 0x34: 1,  # 1, 2, 3, 4
    0x09: 1,  # VK_TAB
    0x51: 1, 0x45: 1,  # Q, E (W is in Zone 0)
    0x14: 1,  # VK_CAPITAL (Caps Lock)
    0xA0: 1,  # VK_LSHIFT (Left Shift only - avoids generic VK_SHIFT bleed)
    0x5A: 1, 0x58: 1, 0x43: 1,  # Z, X, C
    0xA2: 1,  # VK_LCONTROL (Left Ctrl only)
    0x5B: 1, 0x5C: 1,  # VK_LWIN, VK_RWIN
    0xA4: 1,  # VK_LMENU (Left Alt only)
    0xE2: 1,  # VK_OEM_102 (<> on ISO keyboards)

    # Zone 2: Center / Middle (F5-F10, 5-0, R-O, F-L, V-M, Comma, Period, Spacebar, RAlt, Menu)
    0x74: 2, 0x75: 2, 0x76: 2,  # F5, F6, F7
    0x77: 2, 0x78: 2, 0x79: 2,  # F8, F9, F10
    0x35: 2, 0x36: 2, 0x37: 2,  # 5, 6, 7
    0x38: 2, 0x39: 2, 0x30: 2,  # 8, 9, 0
    0x52: 2, 0x54: 2, 0x59: 2,  # R, T, Y
    0x55: 2, 0x49: 2, 0x4F: 2,  # U, I, O
    0x46: 2, 0x47: 2, 0x48: 2,  # F, G, H
    0x4A: 2, 0x4B: 2, 0x4C: 2,  # J, K, L
    0x56: 2, 0x42: 2,  # V, B
    0x4E: 2, 0x4D: 2,  # N, M
    0xBC: 2,  # VK_OEM_COMMA (,<)
    0xBE: 2,  # VK_OEM_PERIOD (.>)
    0x20: 2,  # VK_SPACE (Spacebar)
    0xA5: 2,  # VK_RMENU (Right Alt only)
    0x5D: 2,  # VK_APPS (Context Menu)

    # Zone 3: Right / Navigation / Enter / Arrows
    0x7A: 3, 0x7B: 3,  # F11, F12
    0xBD: 3, 0xBB: 3,  # -_, =+
    0x08: 3,  # VK_BACK (Backspace)
    0x50: 3,  # P
    0xDB: 3, 0xDD: 3, 0xDC: 3,  # [{, ]}, \|
    0xBA: 3, 0xDE: 3,  # ;:, '"
    0x0D: 3,  # VK_RETURN (Enter) - BOTH MAIN & NUMPAD ENTER
    0xBF: 3,  # /?
    0xA1: 3,  # VK_RSHIFT (Right Shift only)
    0xA3: 3,  # VK_RCONTROL (Right Control only)
    0x26: 3, 0x28: 3, 0x25: 3, 0x27: 3,  # Up, Down, Left, Right Arrows
    0x21: 3, 0x22: 3, 0x23: 3, 0x24: 3,  # PgUp, PgDn, End, Home
    0x2C: 3, 0x2D: 3, 0x2E: 3,  # PrtSc, Insert, Delete
    0x13: 3,  # Pause
    # Numpad 0-9, multiply, add, separator, subtract, decimal, divide
    **{vk: 3 for vk in range(0x60, 0x70)},
}

REACTIVE_VIRTUAL_KEYS: Tuple[int, ...] = tuple(KEY_ZONE_MAP.keys())


class AnimationEngine:
    """Background animation thread computing and streaming 4-zone lighting."""

    def __init__(
        self,
        shm: SharedMemoryLighting,
        on_frame: Optional[Callable[[List[Tuple[int, int, int]]], None]] = None,
    ):
        self._shm = shm
        self._on_frame = on_frame

        self._active = False
        self._paused = False
        self._thread: Optional[threading.Thread] = None
        self._key_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()

        # Engine settings
        self.effect: EffectType = EffectType.STATIC
        self.speed: float = 1.0  # Multiplier 0.1 - 5.0
        self.brightness: float = 1.0  # 0.0 - 1.0
        self.zone_colors: List[Tuple[int, int, int]] = [
            (255, 0, 80),   # Zone 0: Left / WASD (Neon Red/Pink)
            (0, 200, 255),  # Zone 1: Mid-Left (Cyan)
            (140, 0, 255),  # Zone 2: Mid-Right (Purple)
            (0, 255, 170),  # Zone 3: Right (Mint)
        ]
        self.fps: int = 30  # High-rate physical sync calibrated to 30 Hz / 33 ms EC hardware

        # Transition Smoothing State
        self._last_rendered_frame: List[Tuple[int, int, int]] = [c for c in self.zone_colors]
        self._transition_start_frame: List[Tuple[int, int, int]] = [c for c in self.zone_colors]
        self._transition_start_time: float = 0.0
        self._transition_duration: float = 0.35  # 350ms Hermite smoothstep transition

        # Effect internal states
        self._zone_press_times: List[float] = [0.0, 0.0, 0.0, 0.0]
        self._last_key_press_time: float = 0.0
        self._last_key_check_time: float = 0.0
        self._last_key_zone: int = 1
        self._star_intensities: List[float] = [0.1, 0.1, 0.1, 0.1]
        self._star_targets: List[float] = [0.1, 0.1, 0.1, 0.1]
        self._next_star_tick: float = 0.0
        self._cascade_positions: List[float] = [0.0, 0.25, 0.5, 0.75]
        self._overdrive_heat: float = 0.0
        self._last_heat_tick: float = time.perf_counter()

    def trigger_transition(self):
        """Initiate a smooth Hermite cubic cross-fade from current rendered frame."""
        with self._lock:
            if self._last_rendered_frame:
                self._transition_start_frame = [c for c in self._last_rendered_frame]
            else:
                self._transition_start_frame = [c for c in self.zone_colors]
            self._transition_start_time = time.perf_counter()

    def set_effect(self, effect: EffectType):
        """Switch effect mode with smooth transition cross-fade."""
        with self._lock:
            if self.effect != effect:
                self.effect = effect
                self.trigger_transition()

    def set_zone_color(self, zone_idx: int, color: Tuple[int, int, int]):
        """Set a single zone's color (0-3) with smooth transition."""
        with self._lock:
            if 0 <= zone_idx < 4:
                self.zone_colors[zone_idx] = color
                self.trigger_transition()

    def set_all_colors(self, colors: List[Tuple[int, int, int]]):
        """Set all 4 zone colors with smooth transition."""
        with self._lock:
            self.zone_colors = [c for c in colors[:4]]
            while len(self.zone_colors) < 4:
                self.zone_colors.append((255, 255, 255))
            self.trigger_transition()

    def set_uniform_color(self, color: Tuple[int, int, int]):
        """Set all 4 zones to the same color with smooth transition."""
        with self._lock:
            self.zone_colors = [color] * 4
            self.trigger_transition()

    def start(self):
        """Start the animation loop and dedicated high-frequency key detection thread."""
        if self._active:
            return
        self._active = True
        self._paused = False
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="OmenFLUXAnimation")
        self._thread.start()
        self._key_thread = threading.Thread(target=self._run_key_loop, daemon=True, name="OmenFLUXKeyDetection")
        self._key_thread.start()

    def stop(self):
        """Stop the animation loop and key listener thread."""
        self._active = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
        if self._key_thread and self._key_thread.is_alive():
            self._key_thread.join(timeout=1.0)
        self._key_thread = None

    def pause(self):
        """Temporarily pause hardware writes (e.g. when handed over to OLS)."""
        self._paused = True

    def resume(self):
        """Resume hardware writes."""
        self._paused = False
        self.trigger_transition()

    def _run_key_loop(self):
        """Dedicated high-rate key polling thread (125 Hz) for instantaneous typing reactivity.
        Checks st & 0x8000 (key currently held down) across dedicated per-key zones,
        ensuring keys illuminate strictly their own zone with zero cross-zone bleed.
        """
        while self._active:
            if self._paused or self.effect not in (EffectType.REACTIVE, EffectType.APEX_OVERDRIVE):
                time.sleep(0.04)
                continue
            now = time.perf_counter()
            for vk in REACTIVE_VIRTUAL_KEYS:
                st = user32.GetAsyncKeyState(vk)
                if st & 0x8000:
                    z = KEY_ZONE_MAP.get(vk)
                    if z is not None and 0 <= z < 4:
                        self._zone_press_times[z] = now
                        self._last_key_press_time = now
                        self._last_key_zone = z
                        self._transition_start_time = 0.0
                        if self.effect == EffectType.APEX_OVERDRIVE:
                            self._overdrive_heat = min(1.0, self._overdrive_heat + 0.18)
            time.sleep(0.008)  # 125 Hz polling (~8ms)

    def trigger_key_press(self, zone: int):
        """Trigger an immediate reactive illumination for the specified zone (0-3)."""
        if 0 <= zone < 4:
            now = time.perf_counter()
            self._zone_press_times[zone] = now
            self._last_key_press_time = now
            self._last_key_zone = zone
            self._transition_start_time = 0.0
            if self.effect == EffectType.APEX_OVERDRIVE:
                self._overdrive_heat = min(1.0, self._overdrive_heat + 0.25)

    def _run_loop(self):
        start_time = time.perf_counter()
        interval = 1.0 / self.fps

        while self._active:
            loop_start = time.perf_counter()
            elapsed = loop_start - start_time

            if not self._paused:
                with self._lock:
                    colors = self._compute_frame(elapsed)

                # Write directly to hardware shared memory (deduplication skips redundant writes)
                self._shm.write_colors(colors)

                # UI preview callback
                if self._on_frame:
                    try:
                        self._on_frame(colors)
                    except Exception:
                        pass
            else:
                # OLS in control: read live colors written by OLS and push to UI preview
                ols_colors = self._shm.read_current_colors()
                if ols_colors and self._on_frame:
                    try:
                        self._on_frame(ols_colors)
                    except Exception:
                        pass

            # Deep Power Optimization:
            # If in Static mode and not in active cross-fade transition, throttle sleep to 100ms
            # to keep CPU at ~0.0% and allow deep processor C-states.
            is_transitioning = (self._transition_start_time > 0 and 
                                (time.perf_counter() - self._transition_start_time) < self._transition_duration)
            if self.effect == EffectType.STATIC and not is_transitioning:
                time.sleep(0.10)
            else:
                work_duration = time.perf_counter() - loop_start
                sleep_time = interval - work_duration
                if sleep_time > 0.002:
                    time.sleep(sleep_time - 0.001)
                # Precision micro-wait to ensure zero timing jitter
                while (time.perf_counter() - loop_start) < interval:
                    time.sleep(0)

    def _compute_frame(self, t: float) -> List[Tuple[int, int, int]]:
        """Calculate RGB for all 4 zones at time t with Hermite cross-fade smoothing."""
        raw_frame = self._compute_raw_frame(t)

        now = time.perf_counter()
        if self._transition_start_time > 0:
            elapsed_trans = now - self._transition_start_time
            if elapsed_trans < self._transition_duration:
                p = max(0.0, min(1.0, elapsed_trans / self._transition_duration))
                # Hermite cubic smoothstep: 3p^2 - 2p^3
                ease = p * p * (3.0 - 2.0 * p)
                blended = []
                for i in range(4):
                    sc = self._transition_start_frame[i]
                    tc = raw_frame[i]
                    blended.append((
                        int(sc[0] + (tc[0] - sc[0]) * ease),
                        int(sc[1] + (tc[1] - sc[1]) * ease),
                        int(sc[2] + (tc[2] - sc[2]) * ease),
                    ))
                self._last_rendered_frame = blended
                return blended
            else:
                self._transition_start_time = 0.0

        self._last_rendered_frame = raw_frame
        return raw_frame

    def _compute_raw_frame(self, t: float) -> List[Tuple[int, int, int]]:
        """Compute procedural animation frame based on active effect type."""
        scaled_t = t * self.speed
        bri = max(0.0, min(1.0, self.brightness))

        # 1. STATIC: Solid per-zone custom colors
        if self.effect == EffectType.STATIC:
            return [(int(r * bri), int(g * bri), int(b * bri)) for (r, g, b) in self.zone_colors]

        # 2. BREATHING: Smooth sinusoidal lumen oscillation
        elif self.effect == EffectType.BREATHING:
            factor = (math.sin(scaled_t * math.pi) + 1.0) / 2.0
            curve = 0.05 + 0.95 * (factor ** 1.6)
            final_bri = curve * bri
            return [(int(r * final_bri), int(g * final_bri), int(b * final_bri))
                    for (r, g, b) in self.zone_colors]

        # 3. COLOR WAVE: Smooth traveling chromatic sinusoidal wave across zones
        elif self.effect == EffectType.COLOR_WAVE:
            frames = []
            for i in range(4):
                phase = (scaled_t * 2.5 - i * 1.1)
                intensity = (math.sin(phase) + 1.0) / 2.0
                curve = 0.1 + 0.9 * (intensity ** 2.0)
                r, g, b = self.zone_colors[i]
                frames.append((int(r * curve * bri), int(g * curve * bri), int(b * curve * bri)))
            return frames

        # 4. SPECTRUM CYCLE: Full 360-degree HSV gamut sweep
        elif self.effect == EffectType.SPECTRUM:
            frames = []
            for i in range(4):
                hue = (scaled_t * 0.22 + i * 0.14) % 1.0
                frames.append(hsv_to_rgb255(hue, 1.0, bri))
            return frames

        # 5. HEARTBEAT: Double-ventricular diastolic/systolic pulse with organic zone propagation
        elif self.effect == EffectType.HEARTBEAT:
            period = 1.25
            frames = []
            for i in range(4):
                # Ventricular propagation delay across physical keyboard zones
                pos = ((scaled_t - i * 0.05) % period) / period
                pulse = 0.0
                if 0.0 <= pos < 0.15:
                    pulse = math.sin(pos / 0.15 * math.pi)
                elif 0.20 <= pos < 0.35:
                    pulse = 0.75 * math.sin((pos - 0.20) / 0.15 * math.pi)
                curve = 0.06 + 0.94 * pulse
                r, g, b = self.zone_colors[i]
                frames.append((int(r * curve * bri), int(g * curve * bri), int(b * curve * bri)))
            return frames

        # 6. KNIGHT RIDER SCANNER: Back-and-forth beam scanning with decay trail
        elif self.effect == EffectType.SCANNER:
            pos = (math.sin(scaled_t * 2.8) + 1.0) / 2.0 * 3.0
            frames = []
            for i in range(4):
                dist = abs(i - pos)
                intensity = max(0.04, 1.0 - (dist * 0.75)) ** 2.2
                r, g, b = self.zone_colors[i]
                frames.append((int(r * intensity * bri), int(g * intensity * bri), int(b * intensity * bri)))
            return frames

        # 7. PRISMATIC AURORA: Dual-layer drifting sinusoidal waves
        elif self.effect == EffectType.AURORA:
            frames = []
            for i in range(4):
                wave1 = (math.sin(scaled_t * 1.2 + i * 0.8) + 1.0) / 2.0
                wave2 = (math.sin(scaled_t * 0.7 - i * 1.3) + 1.0) / 2.0
                hue = (0.38 + wave1 * 0.20 + wave2 * 0.22) % 1.0
                sat = 0.95
                val = (0.20 + 0.80 * (wave1 * 0.6 + wave2 * 0.4)) * bri
                frames.append(hsv_to_rgb255(hue, sat, val))
            return frames

        # 8. PLASMA PULSE: Deep harmonic plasma flux with phase-shifted resonance
        elif self.effect == EffectType.PLASMA:
            frames = []
            for i in range(4):
                v1 = math.sin(scaled_t * 1.5 + i * 1.2)
                v2 = math.sin(scaled_t * 2.3 - i * 1.7)
                v3 = math.sin((scaled_t * 1.8 + i * 0.9) * 0.7)
                plasma = (v1 + v2 + v3 + 3.0) / 6.0
                r, g, b = self.zone_colors[i]
                h, s, v = rgb_to_hsv(r, g, b)
                hue = (h + (plasma - 0.5) * 0.25) % 1.0
                val = (0.25 + 0.75 * (plasma ** 1.5)) * bri
                frames.append(hsv_to_rgb255(hue, max(0.8, s), val))
            return frames

        # 9. CYBER GLITCH: Polyrhythmic digital strobe with chromatic snap
        elif self.effect == EffectType.GLITCH:
            beat = int(scaled_t * 8) % 16
            is_strobe = beat in (0, 2, 7, 8, 13)
            frames = []
            for i in range(4):
                if is_strobe:
                    if (beat + i) % 2 == 0:
                        frames.append((int(255 * bri), int(255 * bri), int(255 * bri)))
                    else:
                        r, g, b = self.zone_colors[i]
                        frames.append((int(r * bri), int(g * bri), int(b * bri)))
                else:
                    r, g, b = self.zone_colors[i]
                    frames.append((int(r * 0.2 * bri), int(g * 0.2 * bri), int(b * 0.2 * bri)))
            return frames

        # 10. COSMIC STARLIGHT: Asynchronous organic celestial twinkling
        elif self.effect == EffectType.STARLIGHT:
            now = time.perf_counter()
            if now > self._next_star_tick:
                self._next_star_tick = now + random.uniform(0.12, 0.32)
                target_zone = random.randint(0, 3)
                self._star_targets[target_zone] = random.choice([0.15, 0.85, 1.0])

            frames = []
            for i in range(4):
                self._star_intensities[i] += (self._star_targets[i] - self._star_intensities[i]) * 0.16
                lvl = max(0.08, min(1.0, self._star_intensities[i]))
                base_r, base_g, base_b = self.zone_colors[i]
                glint = max(0.0, (lvl - 0.7) / 0.3)
                r = int(min(255, base_r * lvl + 255 * glint) * bri)
                g = int(min(255, base_g * lvl + 255 * glint) * bri)
                b = int(min(255, base_b * lvl + 255 * glint) * bri)
                frames.append((r, g, b))
                if self._star_targets[i] > 0.5 and self._star_intensities[i] > 0.75:
                    self._star_targets[i] = 0.12
            return frames

        # 11. BINARY CASCADE: Digital waterfall / matrix data cascade
        elif self.effect == EffectType.CASCADE:
            frames = []
            for i in range(4):
                pos = (scaled_t * 1.8 + i * 0.35) % 1.0
                intensity = math.exp(-pos * 4.0)
                curve = 0.1 + 0.9 * intensity
                base_r, base_g, base_b = self.zone_colors[i]
                # High energy tip glint
                glint = max(0.0, 1.0 - pos * 5.0)
                r = int(min(255, base_r * curve + 200 * glint) * bri)
                g = int(min(255, base_g * curve + 255 * glint) * bri)
                b = int(min(255, base_b * curve + 220 * glint) * bri)
                frames.append((r, g, b))
            return frames

        # 12. SOLAR FLARE: Turbulent solar convection flares with randomized bursts
        elif self.effect == EffectType.SOLAR_FLARE:
            frames = []
            for i in range(4):
                flicker = (
                    0.50
                    + 0.28 * math.sin(scaled_t * 8.5 + i * 2.4)
                    + 0.15 * math.sin(scaled_t * 14.2 - i * 1.8)
                    + 0.07 * math.sin(scaled_t * 24.6 + i * 4.1)
                )
                heat = max(0.1, min(1.0, flicker))
                r = int(255 * heat)
                g = int(min(255, 30 + 190 * (heat ** 1.8)))
                b = int(min(255, 10 + 60 * (heat ** 3.0)))
                frames.append((int(r * bri), int(g * bri), int(b * bri)))
            return frames

        # 13. AUDIO PULSE (Ambient): Rhythmic acoustic throb modeling bass tempo
        elif self.effect == EffectType.AUDIO_PULSE:
            period = 0.85
            scaled_pos = (scaled_t % period) / period
            bass_thump = math.exp(-scaled_pos * 6.0)
            mid_swell = 0.4 * (math.sin(scaled_t * 4.0) + 1.0) / 2.0
            intensity = 0.12 + 0.88 * max(bass_thump, mid_swell)
            frames = []
            for i in range(4):
                r, g, b = self.zone_colors[i]
                frames.append((int(r * intensity * bri), int(g * intensity * bri), int(b * intensity * bri)))
            return frames

        # 14. REACTIVE RIPPLE: Dynamic typing reactivity where pressing a key illuminates ONLY its zone
        elif self.effect == EffectType.REACTIVE:
            now = time.perf_counter()
            decay_rate = 3.6 * max(0.2, self.speed)
            max_duration = 1.4 / decay_rate
            frames = []
            for i in range(4):
                dt = now - self._zone_press_times[i]
                if 0.0 <= dt < max_duration:
                    flash = math.exp(-dt * decay_rate)
                    intensity = flash
                else:
                    intensity = 0.0
                r, g, b = self.zone_colors[i]
                frames.append((
                    int(r * intensity * bri),
                    int(g * intensity * bri),
                    int(b * intensity * bri)
                ))
            return frames

        # 15. APEX OVERDRIVE: Exclusive high-octane kinetic combo engine for Apex Vanguard
        elif self.effect == EffectType.APEX_OVERDRIVE:
            now = time.perf_counter()

            # Heat dissipation: decays smoothly over ~2.8 seconds
            dt_heat = max(0.001, min(0.1, now - self._last_heat_tick))
            self._last_heat_tick = now
            self._overdrive_heat = max(0.0, self._overdrive_heat - dt_heat * 0.35)
            heat = self._overdrive_heat  # 0.0 (idle arcade) to 1.0 (MAX GOD MODE)

            # Dynamic tempo scaling: accelerates dramatically as combo heat builds up
            # Base idle tempo is a punchy 2.6 rad/s; at max heat it surges to 8.5 rad/s!
            speed_mult = 1.0 + heat * 2.5
            eff_t = scaled_t * speed_mult

            frames = []

            # Signature vibrant arcade palette:
            # Zone 0: Solar Amber-Gold (255, 215, 0)
            # Zone 1: Neon Electro-Violet (225, 0, 190)
            # Zone 2: Electric Cyber Cyan (0, 240, 255)
            # Zone 3: Blazing Plasma Coral (255, 35, 85)
            base_palette = [
                (255, 215, 0),
                (225, 0, 190),
                (0, 240, 255),
                (255, 35, 85)
            ]

            # High-speed kinetic particle bouncing 0 -> 1 -> 2 -> 3 -> 2 -> 1 -> 0
            laser_pos = (math.sin(eff_t * 2.8) + 1.0) / 2.0 * 3.0

            # Secondary counter-phase shockwave for hyper-activity
            laser_pos2 = (math.cos(eff_t * 3.6 + 0.5) + 1.0) / 2.0 * 3.0

            for i in range(4):
                base_r, base_g, base_b = self.zone_colors[i] if (self.zone_colors and len(self.zone_colors) > i) else base_palette[i]

                # 1. Vibrant ambient breathing floor: NEVER drops to black, stays colorful & luminous
                amb_wave = (math.sin(eff_t * 1.8 + i * 1.3) + 1.0) / 2.0
                ambient_floor = 0.42 + 0.38 * amb_wave

                # 2. Primary laser particle beam hit
                dist1 = abs(i - laser_pos)
                beam1 = max(0.0, 1.0 - dist1 * 0.75) ** 2.0

                # 3. Secondary laser particle beam (more prominent as heat rises)
                dist2 = abs(i - laser_pos2)
                beam2 = (max(0.0, 1.0 - dist2 * 0.85) ** 2.2) * (0.3 + 0.7 * heat)

                # 4. Immediate keypress kinetic surge for this specific zone
                dt_press = now - self._zone_press_times[i]
                press_surge = math.exp(-dt_press * 5.0) if 0.0 <= dt_press < 0.6 else 0.0

                # 5. Overdrive Strobe (active during combo heat > 0.4)
                strobe = 0.0
                if heat > 0.35:
                    strobe_freq = 14.0 + heat * 18.0
                    is_on = math.sin(eff_t * strobe_freq + i * 2.1) > 0.0
                    strobe = (0.35 if is_on else 0.0) * ((heat - 0.35) / 0.65)

                # Total combined luminosity
                total_lumen = ambient_floor + beam1 * 0.70 + beam2 * 0.50 + press_surge * 0.90
                total_lumen = min(1.8, total_lumen + strobe)

                # Chromatic white-hot tip glint on high peaks
                glint = max(0.0, total_lumen - 0.90) / 0.70

                if i == 0:
                    # Zone 0 (WASD): Radiant Golden Core -> Supernova Flash on keypress / max heat
                    r = int(min(255, (base_r * total_lumen + 80 * glint)) * bri)
                    g = int(min(255, (base_g * total_lumen + 70 * glint + 30 * heat * press_surge)) * bri)
                    b = int(min(255, (base_b * total_lumen + 200 * glint + 160 * heat * press_surge)) * bri)
                else:
                    # Other zones: Rich vibrant neon with laser spark glints
                    spark_boost = 180 * glint * (0.4 + 0.6 * heat)
                    r = int(min(255, (base_r * total_lumen + spark_boost)) * bri)
                    g = int(min(255, (base_g * total_lumen + spark_boost)) * bri)
                    b = int(min(255, (base_b * total_lumen + spark_boost + 50 * press_surge)) * bri)

                frames.append((r, g, b))

            return frames

        return self.zone_colors
