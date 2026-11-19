"""
Shared Memory interface for HP OMEN Light Studio interop.
Reads and writes 4-zone RGB lighting data via the 'FourZoneLightingData'
memory-mapped file and 'OmenLightStudioMemoryMappedFileHelper' mutex.
Includes write deduplication and caching for minimal CPU/power consumption.
"""

import ctypes
import json
import mmap
import struct
import time
from typing import List, Optional, Tuple

kernel32 = ctypes.windll.kernel32

SYNCHRONIZE = 0x00100000
MUTEX_ALL_ACCESS = 0x1F0001
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102

MMF_NAME = "FourZoneLightingData"
MUTEX_NAME = "OmenLightStudioMemoryMappedFileHelper"
MMF_CAPACITY = 655360  # 0xA0000 bytes, exactly as defined by LightStudio


class SharedMemoryLighting:
    """Manages reading and writing to the OMEN Light Studio FourZoneLightingData MMF."""

    def __init__(self):
        self._shm: Optional[mmap.mmap] = None
        self._mutex_handle: Optional[int] = None
        self._last_written_colors: Optional[List[Tuple[int, int, int]]] = None
        self._last_written_time: float = 0.0

    def _ensure_open(self) -> bool:
        if self._shm is not None:
            return True
        try:
            # Open existing or create memory-mapped file
            self._shm = mmap.mmap(-1, MMF_CAPACITY, MMF_NAME)
            return True
        except Exception:
            return False

    def _get_mutex(self) -> Optional[int]:
        if self._mutex_handle is not None:
            return self._mutex_handle
        h = kernel32.OpenMutexW(SYNCHRONIZE, False, MUTEX_NAME)
        if h:
            self._mutex_handle = h
        return self._mutex_handle

    def close(self):
        if self._mutex_handle is not None:
            try:
                kernel32.CloseHandle(self._mutex_handle)
            except Exception:
                pass
            self._mutex_handle = None

        if self._shm is not None:
            try:
                self._shm.close()
            except Exception:
                pass
            self._shm = None

    def read_current_colors(self) -> Optional[List[Tuple[int, int, int]]]:
        """Read the currently active colors from the shared memory buffer.
        
        Translates HP hardware MMF indices to logical zone indices:
          Logical 0 (WASD)          <- MMF[3]
          Logical 1 (Left non-WASD) <- MMF[2]
          Logical 2 (Middle)        <- MMF[1]
          Logical 3 (Right / Nav)   <- MMF[0]
        
        Returns a list of 4 (R, G, B) tuples, or None if unavailable.
        """
        if not self._ensure_open():
            return None

        h_mutex = self._get_mutex()
        acquired = False
        if h_mutex:
            res = kernel32.WaitForSingleObject(h_mutex, 100)
            acquired = (res == WAIT_OBJECT_0)

        try:
            self._shm.seek(0)
            data = self._shm.read(1024)
            if len(data) < 4:
                return None
            length = struct.unpack("<I", data[:4])[0]
            if 0 < length < 2048:
                payload = data[4 : 4 + length].decode("ascii", errors="ignore")
                parsed = json.loads(payload)
                zone_strings = parsed.get("FourZoneColors", [])
                hw_colors = []
                for s in zone_strings:
                    parts = [int(p.strip()) for p in s.split(",")]
                    if len(parts) >= 3:
                        hw_colors.append((parts[0], parts[1], parts[2]))
                    else:
                        hw_colors.append((0, 0, 0))
                while len(hw_colors) < 4:
                    hw_colors.append((0, 0, 0))
                # Hardware MMF -> Logical mapping:
                # MMF[3] = WASD (Logical 0)
                # MMF[2] = Left non-WASD (Logical 1)
                # MMF[1] = Middle (Logical 2)
                # MMF[0] = Right (Logical 3)
                return [hw_colors[3], hw_colors[2], hw_colors[1], hw_colors[0]]
            return None
        except Exception:
            return None
        finally:
            if acquired and h_mutex:
                kernel32.ReleaseMutex(h_mutex)

    def write_colors(
        self,
        colors: List[Tuple[int, int, int]],
        lightbar_type: int = -1,
        timeout_ms: int = 35,
    ) -> bool:
        """Write 4 zone colors into the shared memory buffer for LightStudioHelper to pick up.
        Includes frame deduplication to avoid redundant writes when static.

        Translates Logical application zone order to HP Hardware MMF order:
          Logical 0: WASD          -> MMF[3]
          Logical 1: Left non-WASD -> MMF[2]
          Logical 2: Middle        -> MMF[1]
          Logical 3: Right / Nav   -> MMF[0]

        :param colors: List of 4 (R, G, B) tuples in logical order [WASD, Left, Middle, Right].
        :param lightbar_type: Mode type (-1 for standard keyboard, 1 for lightbar)
        :param timeout_ms: Mutex acquisition timeout in milliseconds.
        :return: True on success.
        """
        if len(colors) != 4:
            raise ValueError("Exactly 4 zone colors are required.")

        now = time.perf_counter()
        # Deduplication: If colors haven't changed and within refresh window, skip expensive write
        if (self._last_written_colors is not None
                and colors == self._last_written_colors
                and (now - self._last_written_time) < 0.60):
            return True

        if not self._ensure_open():
            return False

        # Map logical [WASD, Left, Middle, Right] to hardware MMF [Right, Middle, Left, WASD]
        hw_ordered = [colors[3], colors[2], colors[1], colors[0]]

        color_strings = [f"{max(0, min(255, int(r)))}, {max(0, min(255, int(g)))}, {max(0, min(255, int(b)))}"
                         for (r, g, b) in hw_ordered]

        payload = json.dumps({
            "FourZoneColors": color_strings,
            "Type": lightbar_type,
        }).encode("ascii")

        h_mutex = self._get_mutex()
        acquired = False
        if h_mutex:
            res = kernel32.WaitForSingleObject(h_mutex, timeout_ms)
            if res != WAIT_OBJECT_0:
                # Mutex busy with consumer; skip this frame to prevent torn writes / glitches
                return False
            acquired = True

        try:
            self._shm.seek(0)
            self._shm.write(struct.pack("<I", len(payload)))
            self._shm.write(payload)
            self._shm.flush()
            self._last_written_colors = [c for c in colors]
            self._last_written_time = now
            return True
        except Exception:
            return False
        finally:
            if acquired and h_mutex:
                kernel32.ReleaseMutex(h_mutex)