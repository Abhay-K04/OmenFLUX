"""
Direct WMI BIOS implementation for HP OMEN 16 keyboard lighting.
Communicates directly with root\\wmi:hpqBIntM using the proprietary HP BIOS
mailbox interface on ACPI\\PNP0C14.
Used as a standalone fallback when elevated.
"""

import logging
from typing import List, Optional, Tuple

logger = logging.getLogger("omenglow.wmi")

CMD_LIGHTING = 0x20009
SUB_GET_ZONE_COLORS = 0x2
SUB_SET_ZONE_COLORS = 0x3
SUB_GET_BACKLIGHT = 0x4
SUB_SET_BACKLIGHT = 0x5
SECU_SIGN = [0x53, 0x45, 0x43, 0x55]  # "SECU"
COLOR_OFFSET = 25


class WmiBiosLighting:
    """Direct WMI BIOS control for HP OMEN 16 keyboard backlight."""

    def __init__(self):
        self._wmi = None

    def _init_wmi(self) -> bool:
        if self._wmi is not None:
            return True
        try:
            import win32com.client  # type: ignore
            locator = win32com.client.Dispatch("WbemScripting.SWbemLocator")
            self._wmi = locator.ConnectServer(".", "root\\wmi")
            return True
        except Exception:
            return False

    def is_available(self) -> bool:
        """Check if elevated WMI hpqBIntM interface is accessible."""
        try:
            if not self._init_wmi():
                return False
            items = self._wmi.ExecQuery("SELECT * FROM hpqBIntM")
            return items.Count > 0
        except Exception:
            return False

    def get_zone_colors(self) -> Optional[List[Tuple[int, int, int]]]:
        """Query current zone colors from the BIOS."""
        try:
            if not self._init_wmi():
                return None
            items = self._wmi.ExecQuery("SELECT * FROM hpqBIntM")
            for item in items:
                in_class = self._wmi.Get("hpqBDataIn")
                in_data = in_class.SpawnInstance_()
                in_data.Command = CMD_LIGHTING
                in_data.CommandType = SUB_GET_ZONE_COLORS
                in_data.Sign = SECU_SIGN
                in_data.Size = 0
                in_data.hpqBData = []

                out_param = item.hpqBIOSInt128(in_data)
                out_data = out_param.OutData
                return_code = out_data.rwReturnCode
                raw_bytes = list(out_data.Data)
                if return_code == 0 and len(raw_bytes) >= COLOR_OFFSET + 12:
                    colors = []
                    for i in range(4):
                        idx = COLOR_OFFSET + i * 3
                        r = raw_bytes[idx]
                        g = raw_bytes[idx + 1]
                        b = raw_bytes[idx + 2]
                        colors.append((r, g, b))
                    return colors
        except Exception as e:
            logger.debug("WMI get_zone_colors failed: %s", e)
        return None

    def set_zone_colors(self, colors: List[Tuple[int, int, int]]) -> bool:
        """Set all 4 zone colors via WMI BIOS mailbox."""
        if len(colors) != 4:
            return False
        try:
            if not self._init_wmi():
                return False
            items = self._wmi.ExecQuery("SELECT * FROM hpqBIntM")
            for item in items:
                # Step 1: Read existing 128-byte buffer
                in_class = self._wmi.Get("hpqBDataIn")
                in_data = in_class.SpawnInstance_()
                in_data.Command = CMD_LIGHTING
                in_data.CommandType = SUB_GET_ZONE_COLORS
                in_data.Sign = SECU_SIGN
                in_data.Size = 0
                in_data.hpqBData = []

                out_param = item.hpqBIOSInt128(in_data)
                buffer = list(out_param.OutData.Data)
                if len(buffer) < 128:
                    buffer = [0] * 128
                    buffer[0] = 4

                # Step 2: Patch colors at offset 25
                for i in range(4):
                    idx = COLOR_OFFSET + i * 3
                    buffer[idx] = max(0, min(255, colors[i][0]))
                    buffer[idx + 1] = max(0, min(255, colors[i][1]))
                    buffer[idx + 2] = max(0, min(255, colors[i][2]))

                # Step 3: Write back using subcommand 3
                in_data2 = in_class.SpawnInstance_()
                in_data2.Command = CMD_LIGHTING
                in_data2.CommandType = SUB_SET_ZONE_COLORS
                in_data2.Sign = SECU_SIGN
                in_data2.Size = len(buffer)
                in_data2.hpqBData = buffer

                out_param2 = item.hpqBIOSInt128(in_data2)
                return out_param2.OutData.rwReturnCode == 0
        except Exception as e:
            logger.debug("WMI set_zone_colors failed: %s", e)
        return False
