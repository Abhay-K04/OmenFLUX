"""
Handover Manager for OMEN Light Studio and OmenGlow coexistence.
Controls seamless transfer of keyboard lighting ownership between
OMEN Light Studio and OmenGlow without process terminations or glitches.
"""

import atexit
import ctypes
from enum import Enum
import logging
import threading
import time
from typing import Optional, Callable

import psutil

logger = logging.getLogger("omenglow.handover")

ntdll = ctypes.windll.ntdll
kernel32 = ctypes.windll.kernel32

PROCESS_SUSPEND_RESUME = 0x0800
PROCESS_QUERY_INFORMATION = 0x0400
THREAD_SUSPEND_RESUME = 0x0002


def resume_all_ols_threads(pid: int) -> bool:
    """Ensure all threads of the OLS process have their suspend count decremented to 0."""
    try:
        proc = psutil.Process(pid)
        for t in proc.threads():
            h_thread = kernel32.OpenThread(THREAD_SUSPEND_RESUME, False, t.id)
            if h_thread:
                try:
                    while True:
                        prev = kernel32.ResumeThread(h_thread)
                        if prev <= 1:
                            break
                finally:
                    kernel32.CloseHandle(h_thread)
        return True
    except Exception as e:
        logger.warning("Error resuming threads for PID %d: %s", pid, e)
        return False


class ControlOwner(Enum):
    OLS = "OMEN Light Studio"
    OMENFLUX = "OmenFLUX"
    OMENPULSE = "OmenFLUX"
    OMENGLOW = "OmenFLUX"
    STANDALONE = "Standalone (OLS Not Running)"


class OlsHandoverManager:
    """Manages control handover between OMEN Light Studio and OmenFLUX."""

    def __init__(self, on_state_changed: Optional[Callable[[ControlOwner], None]] = None):
        self._current_owner: ControlOwner = ControlOwner.OLS
        self._suspended_pid: Optional[int] = None
        self._process_handle: Optional[int] = None
        self._is_suspended: bool = False
        self._on_state_changed = on_state_changed

        self._watchdog_active: bool = False
        self._watchdog_thread: Optional[threading.Thread] = None

        # Register safety exit handler to guarantee OLS is resumed on exit
        atexit.register(self.ensure_ols_resumed)
        self.start_watchdog()

    def start_watchdog(self):
        """Start background watchdog to automatically intercept OLS if it starts late on boot."""
        if self._watchdog_active:
            return
        self._watchdog_active = True
        self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True, name="OmenFLUXOlsWatchdog")
        self._watchdog_thread.start()

    def stop_watchdog(self):
        """Stop background watchdog."""
        self._watchdog_active = False
        if self._watchdog_thread and self._watchdog_thread.is_alive():
            self._watchdog_thread.join(timeout=1.0)
        self._watchdog_thread = None

    def _watchdog_loop(self):
        """Polls periodically to ensure LightStudio-background remains suspended
        while OmenFLUX owns control, especially when OLS spawns late after Windows boot.
        """
        while self._watchdog_active:
            try:
                if self._current_owner in (ControlOwner.OMENFLUX, ControlOwner.STANDALONE, ControlOwner.OMENPULSE, ControlOwner.OMENGLOW):
                    pid = self.get_ols_pid()
                    if pid:
                        # OLS process exists: ensure it is suspended
                        if not self._is_suspended or self._suspended_pid != pid:
                            logger.info("Watchdog detected unsuspended OLS (PID %d), enforcing OmenFLUX control", pid)
                            self.take_control()
            except Exception as e:
                logger.debug("Watchdog check error: %s", e)
            time.sleep(1.5)

    @property
    def current_owner(self) -> ControlOwner:
        return self._current_owner

    def get_ols_pid(self) -> Optional[int]:
        """Find the PID of LightStudio-background.exe if running."""
        try:
            for p in psutil.process_iter(["pid", "name"]):
                name = p.info.get("name")
                if name and "lightstudio-background" in name.lower():
                    return p.info["pid"]
        except Exception as e:
            logger.warning("Error finding LightStudio-background: %s", e)
        return None

    def is_ols_running(self) -> bool:
        """Check if LightStudio-background is currently running."""
        return self.get_ols_pid() is not None

    def is_helper_running(self) -> bool:
        """Check if LightStudioHelper is running."""
        try:
            for p in psutil.process_iter(["pid", "name"]):
                name = p.info.get("name")
                if name and "lightstudiohelper" in name.lower():
                    return True
        except Exception:
            pass
        return False

    def take_control(self) -> bool:
        """Take control of the keyboard lighting from OMEN Light Studio.
        
        Suspends LightStudio-background so it ceases streaming to the MMF,
        leaving LightStudioHelper free to receive OmenGlow commands.
        Guarantees that NtSuspendProcess is called at most ONCE to prevent
        thread suspend count accumulation.
        """
        pid = self.get_ols_pid()
        if not pid:
            self._current_owner = ControlOwner.STANDALONE
            if self._on_state_changed:
                self._on_state_changed(self._current_owner)
            return True

        # Avoid redundant NtSuspendProcess calls which increment suspend counts
        if self._is_suspended and self._suspended_pid == pid:
            self._current_owner = ControlOwner.OMENFLUX
            return True

        try:
            h_proc = kernel32.OpenProcess(
                PROCESS_SUSPEND_RESUME | PROCESS_QUERY_INFORMATION, False, pid
            )
            if not h_proc:
                err = kernel32.GetLastError()
                logger.error("Failed to open LightStudio process %d (error %d)", pid, err)
                return False

            status = ntdll.NtSuspendProcess(h_proc)
            if status != 0:
                logger.error("NtSuspendProcess failed with NTSTATUS: 0x%X", status)
                kernel32.CloseHandle(h_proc)
                return False

            self._process_handle = h_proc
            self._suspended_pid = pid
            self._is_suspended = True
            self._current_owner = ControlOwner.OMENFLUX
            logger.info("Successfully took control from OLS (PID %d suspended)", pid)

            if self._on_state_changed:
                self._on_state_changed(self._current_owner)
            return True

        except Exception as e:
            logger.exception("Exception taking control: %s", e)
            return False

    def handover_to_ols(self) -> bool:
        """Release keyboard lighting control back to OMEN Light Studio.
        
        Resumes LightStudio-background and sweeps all its threads to guarantee
        that the suspend count is reduced to 0 so OLS resumes immediately.
        """
        pid = self._suspended_pid or self.get_ols_pid()
        if self._process_handle:
            try:
                ntdll.NtResumeProcess(self._process_handle)
                kernel32.CloseHandle(self._process_handle)
            except Exception as e:
                logger.warning("Error resuming OLS via stored handle: %s", e)
            self._process_handle = None

        if pid:
            resume_all_ols_threads(pid)
            try:
                h_proc = kernel32.OpenProcess(PROCESS_SUSPEND_RESUME, False, pid)
                if h_proc:
                    try:
                        ntdll.NtResumeProcess(h_proc)
                    finally:
                        kernel32.CloseHandle(h_proc)
            except Exception as e:
                logger.exception("Error resuming OLS via fresh handle: %s", e)

        self._is_suspended = False
        self._suspended_pid = None
        self._current_owner = ControlOwner.OLS if self.is_ols_running() else ControlOwner.STANDALONE
        logger.info("Control handed back to OLS (current state: %s)", self._current_owner)

        if self._on_state_changed:
            self._on_state_changed(self._current_owner)
        return True

    def ensure_ols_resumed(self):
        """Safety cleanup: ensures OLS is never left suspended if OmenFLUX quits."""
        self.stop_watchdog()
        if self._process_handle:
            try:
                ntdll.NtResumeProcess(self._process_handle)
                kernel32.CloseHandle(self._process_handle)
            except Exception:
                pass
            self._process_handle = None
            self._suspended_pid = None
