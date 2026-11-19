"""
Handover Status Bar Component for OmenGlow.
Displays current keyboard lighting owner (OmenGlow vs OLS) with
one-click Take Control and Hand Over buttons.
"""

from typing import Callable, Optional
import customtkinter as ctk

from ...hardware.handover import ControlOwner


class HandoverBar(ctk.CTkFrame):
    """Status bar showing ownership and quick handover controls."""

    def __init__(
        self,
        master,
        on_take_control: Callable[[], None],
        on_handover_ols: Callable[[], None],
        **kwargs,
    ):
        super().__init__(master, fg_color="#181A20", corner_radius=10, **kwargs)

        self._on_take_control = on_take_control
        self._on_handover_ols = on_handover_ols

        # Grid configuration
        self.grid_columnconfigure(1, weight=1)

        # Status indicator icon / dot
        self.status_dot = ctk.CTkLabel(
            self,
            text="●",
            font=ctk.CTkFont(size=22),
            text_color="#F5A623",  # Default amber for OLS
            width=24,
        )
        self.status_dot.grid(row=0, column=0, padx=(15, 6), pady=10)

        # Status text
        self.status_label = ctk.CTkLabel(
            self,
            text="OMEN Light Studio is in Control",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#E0E0E0",
            anchor="w",
        )
        self.status_label.grid(row=0, column=1, padx=(0, 15), pady=10, sticky="w")

        # Action Buttons container
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=0, column=2, padx=15, pady=8, sticky="e")

        # Take Control Button
        self.btn_take = ctk.CTkButton(
            self.btn_frame,
            text="⚡ Take Control",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#00C8FF",
            hover_color="#0096C7",
            text_color="#0D0E15",
            corner_radius=8,
            width=130,
            height=34,
            command=self._handle_take,
        )
        self.btn_take.pack(side="left", padx=4)

        # Handover to OLS Button
        self.btn_handover = ctk.CTkButton(
            self.btn_frame,
            text="🔄 Release to OLS",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2A2E3D",
            hover_color="#3A3E4D",
            text_color="#FFFFFF",
            corner_radius=8,
            width=130,
            height=34,
            command=self._handle_handover,
        )
        self.btn_handover.pack(side="left", padx=4)

    def update_owner(self, owner: ControlOwner):
        """Update display based on active control owner."""
        if owner == ControlOwner.OMENGLOW:
            self.status_dot.configure(text_color="#00E676")  # Vibrant Green
            self.status_label.configure(text="OmenGlow is in Control")
            self.btn_take.configure(state="disabled", fg_color="#1E2A38", text_color="#607080")
            self.btn_handover.configure(state="normal", fg_color="#F5A623", hover_color="#D48817", text_color="#000000")
        elif owner == ControlOwner.OLS:
            self.status_dot.configure(text_color="#F5A623")  # Amber
            self.status_label.configure(text="OMEN Light Studio is in Control")
            self.btn_take.configure(state="normal", fg_color="#00C8FF", hover_color="#0096C7", text_color="#0D0E15")
            self.btn_handover.configure(state="disabled", fg_color="#2A2E3D", text_color="#607080")
        else:  # STANDALONE
            self.status_dot.configure(text_color="#9E9E9E")  # Gray
            self.status_label.configure(text="Standalone Mode (OLS not running)")
            self.btn_take.configure(state="normal", fg_color="#00C8FF", hover_color="#0096C7", text_color="#0D0E15")
            self.btn_handover.configure(state="disabled", fg_color="#2A2E3D", text_color="#607080")

    def _handle_take(self):
        self._on_take_control()

    def _handle_handover(self):
        self._on_handover_ols()
