"""
Setup Windows Shortcuts & Registry for OmenFLUX Native App
Creates:
1. Desktop Shortcut (OmenFLUX.lnk) on active user Desktop (handles OneDrive redirection)
2. Start Menu Shortcut (OmenFLUX.lnk)
3. Windows HKCU Run Registry Entry (OmenFLUX.exe --background)
Removes legacy OmenPulse and OmenGlow shortcuts and registry keys.
"""

import os
import sys
import winreg
import subprocess

def create_windows_shortcuts():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    exe_path = os.path.join(base_dir, "dist", "OmenFLUX.exe")
    if not os.path.exists(exe_path):
        for candidate in ["OmenPulse.exe", "OmenGlow.exe"]:
            p = os.path.join(base_dir, "dist", candidate)
            if os.path.exists(p):
                exe_path = p
                break
        if not os.path.exists(exe_path):
            print(f"[ERROR] Executable not found.")
            return False

    icon_path = os.path.join(base_dir, "omenglow", "assets", "omenglow.ico")
    working_dir = os.path.dirname(exe_path)

    ps_script = f'''
    $ws = New-Object -ComObject WScript.Shell
    $desktopPath = $ws.SpecialFolders.Item("Desktop")
    $programsPath = $ws.SpecialFolders.Item("Programs")

    # Clean legacy shortcuts if present
    foreach ($oldName in @("OmenPulse.lnk", "OmenGlow.lnk", "OmenSpectrix.lnk", "OMEN SPECTRIX.lnk")) {{
        $oldD = Join-Path $desktopPath $oldName
        if (Test-Path $oldD) {{ Remove-Item $oldD -Force }}
        $oldS = Join-Path $programsPath $oldName
        if (Test-Path $oldS) {{ Remove-Item $oldS -Force }}
    }}

    $desktopLnk = Join-Path $desktopPath "OmenFLUX.lnk"
    $startMenuLnk = Join-Path $programsPath "OmenFLUX.lnk"

    # 1. Desktop shortcut
    $s1 = $ws.CreateShortcut($desktopLnk)
    $s1.TargetPath = "{exe_path}"
    $s1.WorkingDirectory = "{working_dir}"
    $s1.IconLocation = "{icon_path},0"
    $s1.Description = "OmenFLUX — OMEN 16 Keyboard RGB Controller"
    $s1.Save()
    Write-Host "[OK] Desktop Shortcut: $desktopLnk"

    # Also place on local desktop if distinct from OneDrive
    $localDesktop = Join-Path $env:USERPROFILE "Desktop"
    if ((Test-Path $localDesktop) -and ($localDesktop -ne $desktopPath)) {{
        foreach ($oldName in @("OmenPulse.lnk", "OmenGlow.lnk")) {{
            $oldL = Join-Path $localDesktop $oldName
            if (Test-Path $oldL) {{ Remove-Item $oldL -Force }}
        }}
        $sLocal = $ws.CreateShortcut((Join-Path $localDesktop "OmenFLUX.lnk"))
        $sLocal.TargetPath = "{exe_path}"
        $sLocal.WorkingDirectory = "{working_dir}"
        $sLocal.IconLocation = "{icon_path},0"
        $sLocal.Description = "OmenFLUX — OMEN 16 Keyboard RGB Controller"
        $sLocal.Save()
    }}

    # 2. Start Menu Programs shortcut
    $s2 = $ws.CreateShortcut($startMenuLnk)
    $s2.TargetPath = "{exe_path}"
    $s2.WorkingDirectory = "{working_dir}"
    $s2.IconLocation = "{icon_path},0"
    $s2.Description = "OmenFLUX — OMEN 16 Keyboard RGB Controller"
    $s2.Save()
    Write-Host "[OK] Start Menu Shortcut: $startMenuLnk"
    '''

    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True, text=True)
    print(res.stdout.strip())
    if res.stderr:
        print("[WARN]", res.stderr.strip())

    # 3. Synchronize Windows Run key: HKCU\Software\Microsoft\Windows\CurrentVersion\Run
    run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    run_cmd = f'"{exe_path}" --background'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_SET_VALUE) as key:
            for legacy_app in ["OmenPulse", "OmenGlow", "OmenSpectrix"]:
                try:
                    winreg.DeleteValue(key, legacy_app)
                except Exception:
                    pass
            # Only enable if user has autostart configured as True
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            try:
                from omenglow.state import StateManager
                sm = StateManager()
                if sm.state.get("autostart", False):
                    winreg.SetValueEx(key, "OmenFLUX", 0, winreg.REG_SZ, run_cmd)
                    print(f"[OK] Registered Windows Startup: {run_cmd}")
                else:
                    try:
                        winreg.DeleteValue(key, "OmenFLUX")
                    except Exception:
                        pass
                    print(f"[OK] Windows Startup is OFF (preserved user setting)")
            except Exception:
                pass
    except Exception as e:
        print(f"[ERROR] Failed to check registry autostart: {e}")

    return True

if __name__ == "__main__":
    create_windows_shortcuts()