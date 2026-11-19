"""
OmenFLUX — Main Entry Point
Launches the next-generation Cyber-Stealth RGB Studio by default,
with fallback to legacy Tkinter GUI, and complete CLI command support.
"""

import argparse
import ctypes
import os
import subprocess
import sys
import threading
import time

# Ensure sys.stdout and sys.stderr exist for windowed/no-console PyInstaller builds
if sys.stdout is None:
    try:
        sys.stdout = open(os.devnull, "w")
    except Exception:
        pass
if sys.stderr is None:
    try:
        sys.stderr = open(os.devnull, "w")
    except Exception:
        pass

from omenglow.hardware.shared_memory import SharedMemoryLighting
from omenglow.hardware.handover import OlsHandoverManager, ControlOwner
from omenglow.profiles.manager import ProfileManager


user32 = ctypes.windll.user32
SW_MAXIMIZE = 3
SW_RESTORE = 9

def find_studio_hwnd():
    """Find the HWND of the active OmenFLUX window."""
    target_hwnd = None
    def enum_cb(hwnd, lparam):
        nonlocal target_hwnd
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                val = buff.value.lower()
                if "omenflux" in val or "omenglow" in val or "omenpulse" in val:
                    target_hwnd = hwnd
                    return False
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    return target_hwnd


def is_window_open(title_substring="OmenFLUX"):
    """Check if any visible desktop window has title_substring in its title."""
    return find_studio_hwnd() is not None


def maximize_studio_window():
    """Find and maximize the OmenFLUX window, bringing it to the foreground."""
    hwnd = find_studio_hwnd()
    if hwnd:
        try:
            user32.ShowWindow(hwnd, SW_MAXIMIZE)
            user32.SetForegroundWindow(hwnd)
            return True
        except Exception:
            pass
    return False


def ensure_window_maximized_async():
    """Asynchronously monitor for the newly spawned window and maximize it."""
    def _worker():
        for _ in range(40):  # poll every 100ms for up to 4 seconds
            time.sleep(0.1)
            if maximize_studio_window():
                break

    threading.Thread(target=_worker, daemon=True).start()


def ensure_profile_maximized(user_data_dir: str):
    """Ensure Chromium Preferences file defaults to maximized=True for window placements."""
    pref_path = os.path.join(user_data_dir, "Default", "Preferences")
    if not os.path.exists(pref_path):
        return
    try:
        import json
        with open(pref_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        changed = False
        browser_pref = data.get("browser", {})
        if "window_placement" in browser_pref:
            if not browser_pref["window_placement"].get("maximized"):
                browser_pref["window_placement"]["maximized"] = True
                changed = True

        app_placements = browser_pref.get("app_window_placement", {})
        def recurse_set_maximized(d):
            nonlocal changed
            if isinstance(d, dict):
                if "maximized" in d and not d["maximized"]:
                    d["maximized"] = True
                    changed = True
                for v in d.values():
                    if isinstance(v, dict):
                        recurse_set_maximized(v)

        recurse_set_maximized(app_placements)

        if changed:
            with open(pref_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
    except Exception:
        pass


def find_chromium_browser():
    """Locate Microsoft Edge or Google Chrome for standalone app-mode execution."""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def launch_studio_window(browser_bin: str, port: int = 54321):
    """Launch Microsoft Edge or Chrome in standalone app mode (always opened maximized)."""
    user_data = os.path.expandvars(r"%LOCALAPPDATA%\OmenFLUX\StudioProfile")
    os.makedirs(user_data, exist_ok=True)
    ensure_profile_maximized(user_data)

    cmd = [
        browser_bin,
        f"--app=http://127.0.0.1:{port}",
        "--start-maximized",
        "--app-id=OmenFLUXRGBStudio",
        f"--user-data-dir={user_data}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--disable-features=Translate,OptimizationHints,MediaRouter",
        "--disable-component-update",
        "--disable-background-networking",
        "--disable-sync",
        "--disable-default-apps",
        "--hide-crash-restore-bubble",
    ]
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        ensure_window_maximized_async()
        return proc
    except Exception as e:
        import traceback
        appdata = os.getenv("APPDATA") or os.path.expanduser("~")
        log_dir = os.path.join(appdata, "OmenFLUX")
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "browser_launch_error.log"), "a", encoding="utf-8") as f:
            f.write(f"\n--- BROWSER LAUNCH ERROR AT {time.ctime()} ---\n")
            traceback.print_exc(file=f)
        return None


def run_web_studio(background: bool = False):
    """Launch the modern, GPU-accelerated Cyber-Stealth RGB Studio."""
    import ctypes
    import urllib.request
    try:
        # Register AppUserModelID so Windows Taskbar pins and displays OmenFLUX's custom icon
        myappid = "omenflux.keyboard.rgb.studio.v1"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    browser_bin = find_chromium_browser()
    if not browser_bin and not background:
        print("[WARN] No Chromium browser (Edge/Chrome) detected, launching legacy GUI...")
        run_legacy_gui()
        return

    port = 54321

    # Check if OmenFLUX is already running in background; if so, open window (unless --background) and exit
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status", timeout=0.6)
        if not background and browser_bin:
            print("[INFO] OmenFLUX is already running in the background. Opening Studio window...")
            if not maximize_studio_window():
                launch_studio_window(browser_bin, port)
        return
    except Exception:
        pass

    from omenglow.web.server import start_server, stop_server, app_state, handover, engine, profiles_mgr, state_mgr
    from omenglow.effects.engine import EffectType, parse_effect_type
    from omenglow.tray import OmenSystemTray

    # Start Flask API & animation engine in background thread (starts with default control)
    def run_server_safe():
        try:
            start_server(port=port)
        except Exception as e:
            import traceback
            appdata = os.getenv("APPDATA") or os.path.expanduser("~")
            log_dir = os.path.join(appdata, "OmenFLUX")
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, "server_error.log"), "a", encoding="utf-8") as f:
                f.write(f"\n--- SERVER ERROR AT {time.ctime()} ---\n")
                traceback.print_exc(file=f)

    server_thread = threading.Thread(target=run_server_safe, daemon=True)
    server_thread.start()
    time.sleep(0.8)

    # Tray action callbacks
    def on_open_studio():
        if not maximize_studio_window():
            b_bin = browser_bin or find_chromium_browser()
            if b_bin:
                launch_studio_window(b_bin, port)

    def on_take_control():
        handover.take_control()
        engine.resume()
        state_mgr.save_state({"owner": "OmenFLUX"})

    def on_release_ols():
        engine.pause()
        handover.handover_to_ols()
        state_mgr.save_state({"owner": "OMEN Light Studio"})

    def on_load_preset(preset_name: str):
        prof = profiles_mgr.load_profile(preset_name)
        if prof:
            engine.set_all_colors(prof.zone_colors)
            engine.set_effect(parse_effect_type(prof.effect))
            engine.speed = prof.speed
            engine.brightness = prof.brightness
            handover.take_control()
            engine.resume()
            state_mgr.save_state({
                "active_profile": preset_name,
                "effect": engine.effect.value,
                "speed": engine.speed,
                "brightness": engine.brightness,
                "zone_colors": engine.zone_colors,
                "owner": "OmenFLUX",
            })

    def on_tray_exit():
        app_state.should_exit = True

    # Start system tray icon
    tray = OmenSystemTray(
        on_open_studio=on_open_studio,
        on_take_control=on_take_control,
        on_release_ols=on_release_ols,
        on_load_preset=on_load_preset,
        on_exit=on_tray_exit,
        get_owner_name=lambda: handover.current_owner.value,
    )
    tray.start()

    # Launch initial browser window ONLY if not running in silent background mode
    if not background and browser_bin:
        launch_studio_window(browser_bin, port)

    # Main thread keeps background engine running until explicit exit
    try:
        while not app_state.should_exit:
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        tray.stop()
        stop_server()


def run_legacy_gui():
    """Launch legacy CustomTkinter GUI."""
    import ctypes
    try:
        myappid = "omenflux.keyboard.rgb.studio.v1"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    from omenglow.ui.app import OmenGlowApp
    app = OmenGlowApp()
    app.mainloop()


def run_cli_status():
    handover = OlsHandoverManager()
    shm = SharedMemoryLighting()
    print("=" * 45)
    print("  OmenFLUX Hardware & Handover Status")
    print("=" * 45)
    print(f"  OLS Running:      {handover.is_ols_running()} (PID: {handover.get_ols_pid()})")
    print(f"  OLS Helper:       {handover.is_helper_running()}")
    print(f"  Control Owner:    {handover.current_owner.value}")

    colors = shm.read_current_colors()
    if colors:
        print("  Active Colors:")
        for i, (r, g, b) in enumerate(colors):
            print(f"    Zone {i+1}: RGB({r}, {g}, {b})  Hex: #{r:02X}{g:02X}{b:02X}")
    else:
        print("  Active Colors:    Unavailable")
    print("=" * 45)


def run_cli_set_colors(colors_str_list):
    handover = OlsHandoverManager()
    shm = SharedMemoryLighting()

    handover.take_control()
    colors = []
    for s in colors_str_list:
        parts = [int(p.strip()) for p in s.split(",")]
        colors.append((parts[0], parts[1], parts[2]))
    while len(colors) < 4:
        colors.append(colors[-1] if colors else (255, 255, 255))

    shm.write_colors(colors[:4])
    print(f"[OK] Applied colors to 4 zones: {colors[:4]}")


def main():
    parser = argparse.ArgumentParser(description="OmenFLUX — OMEN 16 Keyboard RGB Controller")
    parser.add_argument("--status", action="store_true", help="Print current hardware and handover status")
    parser.add_argument("--take-control", action="store_true", help="Take control of keyboard from OLS")
    parser.add_argument("--release", action="store_true", help="Release control back to OLS")
    parser.add_argument("--set-colors", nargs=4, metavar=("Z1", "Z2", "Z3", "Z4"),
                        help="Set colors directly: 'R,G,B' 'R,G,B' 'R,G,B' 'R,G,B'")
    parser.add_argument("--profile", type=str, help="Apply a saved profile by name")
    parser.add_argument("--legacy-ui", action="store_true", help="Launch older CustomTkinter GUI instead of modern Web Studio")
    parser.add_argument("--background", action="store_true", help="Run silently in the background (tray & engine only, no browser window)")

    args = parser.parse_args()

    if args.status:
        run_cli_status()
    elif args.take_control:
        handover = OlsHandoverManager()
        if handover.take_control():
            print("[OK] OmenFLUX has taken control of the keyboard.")
        else:
            print("[ERROR] Failed to take control.")
    elif args.release:
        handover = OlsHandoverManager()
        handover.handover_to_ols()
        print("[OK] Control released back to OMEN Light Studio.")
    elif args.set_colors:
        run_cli_set_colors(args.set_colors)
    elif args.profile:
        pm = ProfileManager()
        prof = pm.load_profile(args.profile)
        if prof:
            run_cli_set_colors([f"{r},{g},{b}" for (r, g, b) in prof.zone_colors])
        else:
            print(f"[ERROR] Profile '{args.profile}' not found.")
    elif args.legacy_ui:
        run_legacy_gui()
    else:
        run_web_studio(background=args.background)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        appdata = os.getenv("APPDATA") or os.path.expanduser("~")
        log_dir = os.path.join(appdata, "OmenFLUX")
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, "crash.log"), "a", encoding="utf-8") as f:
            f.write(f"\n--- FATAL CRASH AT {time.ctime()} ---\n")
            traceback.print_exc(file=f)
        raise