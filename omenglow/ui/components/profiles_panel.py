"""
Profiles and Presets Management Panel for OmenGlow.
Allows saving, switching, and deleting custom 4-zone lighting profiles.
"""

from typing import Callable, Optional
import customtkinter as ctk

from ...profiles.manager import Profile, ProfileManager


class ProfilesPanel(ctk.CTkFrame):
    """Panel for saving and switching lighting profiles."""

    def __init__(
        self,
        master,
        profile_manager: ProfileManager,
        on_profile_selected: Callable[[Profile], None],
        on_save_requested: Callable[[str], None],
        **kwargs,
    ):
        super().__init__(master, fg_color="#181A20", corner_radius=12, **kwargs)

        self._pm = profile_manager
        self._on_profile_selected = on_profile_selected
        self._on_save_requested = on_save_requested

        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=16, pady=(12, 10))

        self.title_lbl = ctk.CTkLabel(
            self.header,
            text="Profiles & Presets",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FFFFFF",
        )
        self.title_lbl.pack(side="left")

        # Controls row
        self.ctrl_row = ctk.CTkFrame(self, fg_color="transparent")
        self.ctrl_row.pack(fill="x", padx=16, pady=(0, 14))

        # Profile Selector
        self.profile_menu = ctk.CTkOptionMenu(
            self.ctrl_row,
            values=self._pm.list_profiles(),
            command=self._on_select,
            fg_color="#262B3A",
            button_color="#00C8FF",
            button_hover_color="#0096C7",
            text_color="#FFFFFF",
            dropdown_fg_color="#1F2330",
            width=200,
            height=32,
        )
        self.profile_menu.pack(side="left", padx=(0, 8))

        # Save Current Button
        self.btn_save = ctk.CTkButton(
            self.ctrl_row,
            text="+ Save Current",
            font=ctk.CTkFont(size=12, weight="bold"),
            width=110,
            height=32,
            fg_color="#2A2E3D",
            hover_color="#3A3E4D",
            command=self._prompt_save,
        )
        self.btn_save.pack(side="left", padx=4)

        # Delete Button
        self.btn_delete = ctk.CTkButton(
            self.ctrl_row,
            text="Delete",
            font=ctk.CTkFont(size=12),
            width=70,
            height=32,
            fg_color="#3D2020",
            hover_color="#5D2626",
            text_color="#FF6B6B",
            command=self._delete_current,
        )
        self.btn_delete.pack(side="left", padx=4)

    def refresh_profiles(self, select_name: Optional[str] = None):
        profiles = self._pm.list_profiles()
        self.profile_menu.configure(values=profiles)
        if select_name and select_name in profiles:
            self.profile_menu.set(select_name)
        elif profiles:
            self.profile_menu.set(profiles[0])

    def _on_select(self, name: str):
        profile = self._pm.load_profile(name)
        if profile:
            self._on_profile_selected(profile)

    def _prompt_save(self):
        dialog = ctk.CTkInputDialog(text="Enter a name for this profile:", title="Save Profile")
        name = dialog.get_input()
        if name and name.strip():
            self._on_save_requested(name.strip())
            self.refresh_profiles(name.strip())

    def _delete_current(self):
        current = self.profile_menu.get()
        if current and current not in ("OMEN Crimson", "Cyberpunk 2077"):
            self._pm.delete_profile(current)
            self.refresh_profiles()
