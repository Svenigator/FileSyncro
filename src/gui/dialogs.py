# src/gui/dialogs.py
import customtkinter as ctk
from datetime import datetime


class ConflictDialog(ctk.CTkToplevel):
    def __init__(self, parent, rel_path: str, local_ts: float, remote_ts: float, remote_name: str):
        super().__init__(parent)
        self.title("Konflikt erkannt")
        self.geometry("480x220")
        self.resizable(False, False)
        self.grab_set()
        self.result: bool | None = None

        local_time = datetime.fromtimestamp(local_ts).strftime("%H:%M:%S")
        remote_time = datetime.fromtimestamp(remote_ts).strftime("%H:%M:%S")

        ctk.CTkLabel(self, text=f"Konflikt: {rel_path}", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(20, 8))
        ctk.CTkLabel(self, text=f"Lokal:   {local_time} Uhr").pack()
        ctk.CTkLabel(self, text=f"Remote: {remote_time} Uhr  ({remote_name})").pack()

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Lokale Version behalten", command=self._keep_local).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Remote übernehmen", command=self._accept_remote).pack(side="left", padx=8)

        self.wait_window()

    def _keep_local(self):
        self.result = False
        self.destroy()

    def _accept_remote(self):
        self.result = True
        self.destroy()


class DeleteDialog(ctk.CTkToplevel):
    def __init__(self, parent, rel_path: str):
        super().__init__(parent)
        self.title("Datei gelöscht")
        self.geometry("420x180")
        self.resizable(False, False)
        self.grab_set()
        self.result: str | None = None  # "local" | "all"

        ctk.CTkLabel(self, text=f"{rel_path} wurde gelöscht.", font=ctk.CTkFont(size=13)).pack(pady=(24, 8))
        ctk.CTkLabel(self, text="Auf allen Geräten löschen oder nur lokal?").pack()

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Nur lokal", command=self._local_only).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="Alle Geräte", command=self._all_devices).pack(side="left", padx=8)

        self.wait_window()

    def _local_only(self):
        self.result = "local"
        self.destroy()

    def _all_devices(self):
        self.result = "all"
        self.destroy()
