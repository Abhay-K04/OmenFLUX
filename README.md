# OmenFLUX — 4-Zone RGB Lighting Controller

A lightweight RGB keyboard lighting controller and customization studio for compatible 4-zone laptops.

OmenFLUX operates with near-zero CPU footprint (~15 MB RAM) and coexists seamlessly with default background services.

---

## Features

- **Coexistence Mode**: One-click handover between OmenFLUX and manufacturer lighting services.
- **14 Procedural Lighting Effects**: Smooth, real-time animation routines including wave sweeps, breathing oscillations, cardiac pulses, plasma resonance, and reactive ripple.
- **20 Curated Presets**: A diverse vault of color schemes ranging from high-contrast gaming themes to soft pastels.
- **Apex Overdrive (Exclusive Mode)**: Interactive kinetic accelerator with a real-time combo heat gauge that speeds up as typing activity increases.
- **Chroma Studio**: Radial HSV color canvas, RGB/Hex inputs, and a smart palette generator supporting pastels, tints, and vivid neon tones.
- **Virtual Keyboard Preview**: Interactive 3D keycaps with physical typing feedback, WASD cluster callout, and translucent underglow.
- **Low Power Consumption**: Deep sleep throttling (100 ms) during static displays to preserve laptop battery.
- **System Tray Integration**: Runs quietly in the Windows background with tray controls, auto-startup option, and desktop shortcuts.

---

## Hardware 4-Zone Mapping

| Zone Index | Zone Name | Keyboard Area |
|:---:|:---|:---|
| **Zone 0** | **WASD Keys** | Dedicated W, A, S, D cluster |
| **Zone 1** | **Left Section** | Esc, F1-F4, Tab, Q, E, Caps, Shift, Z-C, Ctrl, Win, Alt |
| **Zone 2** | **Center Section** | F5-F10, 5-0, R-O, F-L, V-M, Spacebar |
| **Zone 3** | **Right Section** | F11-F12, Backspace, Enter, Arrow keys, Navigation cluster |

---

## Installation

### Run from Source

**Prerequisites**:
- Windows 10 or 11 (64-bit)
- Python 3.10+

```powershell
git clone https://github.com/Abhay-K04/OmenFLUX.git
cd OmenFLUX

py -3.11 -m pip install -r requirements.txt
py -3.11 main.py
```

### Build Standalone Executable

```powershell
py -3.11 -m pip install pyinstaller
py -3.11 -m PyInstaller --noconfirm OmenFLUX.spec
```

The compiled binary will be placed at `dist\OmenFLUX.exe`.

---

## CLI Reference

```powershell
# Check current status
py main.py --status

# Apply a preset
py main.py --profile "Apex Vanguard"
py main.py --profile "Sakura Blossom"

# Handover controls
py main.py --take-control
py main.py --release

# Silent background mode
py main.py --background
```

---

## License

This project is licensed under the MIT License.
