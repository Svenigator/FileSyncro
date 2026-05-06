# src/gui/app.py
import asyncio
import queue
import threading
from pathlib import Path
from tkinter import filedialog
from typing import Callable, Optional

import customtkinter as ctk

from src.gui.dialogs import ConflictDialog, DeleteDialog
from src.peer_manager import Peer


ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(
        self,
        async_loop: asyncio.AbstractEventLoop,
        conflict_queue: queue.Queue,
        activity_queue: queue.Queue,
        delete_queue: queue.Queue,
        peer_queue: queue.Queue,
        on_sync_dir_changed: Callable[[Path], None],
        on_manual_sync: Callable[[], None],
        on_add_peer_manual: Callable[[str, int], None],
    ):
        super().__init__()
        self.title("FileSyncro")
        self.geometry("560x520")
        self.resizable(False, False)

        self._async_loop = async_loop
        self._conflict_queue = conflict_queue
        self._activity_queue = activity_queue
        self._delete_queue = delete_queue
        self._peer_queue = peer_queue
        self._on_sync_dir_changed = on_sync_dir_changed
        self._on_manual_sync = on_manual_sync
        self._on_add_peer_manual = on_add_peer_manual
        self._peer_rows: dict[str, ctk.CTkFrame] = {}

        self._build_ui()
        self._poll_queues()

    def _build_ui(self):
        # Sync-Ordner
        folder_frame = ctk.CTkFrame(self)
        folder_frame.pack(fill="x", padx=16, pady=(16, 4))
        ctk.CTkLabel(folder_frame, text="Sync-Ordner:").pack(side="left", padx=8)
        ctk.CTkButton(folder_frame, text="...", width=40, command=self._choose_folder).pack(side="right", padx=8)
        self._folder_label = ctk.CTkLabel(folder_frame, text="(nicht gewählt)", anchor="w")
        self._folder_label.pack(side="left", fill="x", expand=True, padx=4)

        # Geräteliste
        ctk.CTkLabel(self, text="Verbundene Geräte", anchor="w").pack(fill="x", padx=16, pady=(12, 2))
        self._device_frame = ctk.CTkScrollableFrame(self, height=140)
        self._device_frame.pack(fill="x", padx=16)

        # Manuell hinzufügen
        manual_frame = ctk.CTkFrame(self, fg_color="transparent")
        manual_frame.pack(fill="x", padx=16, pady=4)
        self._ip_entry = ctk.CTkEntry(manual_frame, placeholder_text="IP-Adresse", width=180)
        self._ip_entry.pack(side="left", padx=(0, 4))
        ctk.CTkButton(manual_frame, text="Hinzufügen", width=100, command=self._add_manual_peer).pack(side="left")

        # Sync-Button + Status
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=16, pady=8)
        ctk.CTkButton(action_frame, text="Jetzt synchronisieren", command=self._manual_sync).pack(side="left")
        self._status_label = ctk.CTkLabel(action_frame, text="Status: bereit")
        self._status_label.pack(side="left", padx=16)

        # Aktivitätslog
        ctk.CTkLabel(self, text="Aktivität", anchor="w").pack(fill="x", padx=16, pady=(8, 2))
        self._log = ctk.CTkTextbox(self, height=160, state="disabled")
        self._log.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _choose_folder(self):
        path = filedialog.askdirectory(title="Sync-Ordner wählen")
        if path:
            self._folder_label.configure(text=path)
            self._on_sync_dir_changed(Path(path))

    def _manual_sync(self):
        self._status_label.configure(text="Status: synchronisiere…")
        asyncio.run_coroutine_threadsafe(self._on_manual_sync(), self._async_loop)

    def _add_manual_peer(self):
        ip = self._ip_entry.get().strip()
        if ip:
            self._on_add_peer_manual(ip, 5757)
            self._ip_entry.delete(0, "end")

    def update_peer(self, peer: Peer) -> None:
        if peer.name not in self._peer_rows:
            row = ctk.CTkFrame(self._device_frame)
            row.pack(fill="x", pady=2)
            dot = ctk.CTkLabel(row, text="●", width=20)
            dot.pack(side="left")
            ctk.CTkLabel(row, text=peer.name).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=peer.ip, text_color="gray").pack(side="left")
            self._peer_rows[peer.name] = row
            row._dot = dot
        dot = self._peer_rows[peer.name]._dot
        dot.configure(text_color="green" if peer.reachable else "red")

    def remove_peer(self, name: str) -> None:
        if name in self._peer_rows:
            self._peer_rows[name].destroy()
            del self._peer_rows[name]

    def log(self, message: str) -> None:
        self._log.configure(state="normal")
        self._log.insert("end", message + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def set_status(self, text: str) -> None:
        self._status_label.configure(text=f"Status: {text}")

    def _poll_queues(self):
        # Aktivitätsmeldungen
        try:
            while True:
                msg = self._activity_queue.get_nowait()
                self.log(msg)
                self.set_status("bereit")
        except queue.Empty:
            pass

        # Konflikt-Anfragen
        try:
            while True:
                req = self._conflict_queue.get_nowait()
                dlg = ConflictDialog(
                    self,
                    rel_path=req["rel_path"],
                    local_ts=req["local_ts"],
                    remote_ts=req["remote_ts"],
                    remote_name="Remote"
                )
                self._async_loop.call_soon_threadsafe(req["future"].set_result, dlg.result or False)
        except queue.Empty:
            pass

        # Lösch-Anfragen
        try:
            while True:
                req = self._delete_queue.get_nowait()
                dlg = DeleteDialog(self, rel_path=req["rel_path"])
                req["callback"](dlg.result or "local")
        except queue.Empty:
            pass

        # Peer-Updates
        try:
            while True:
                msg = self._peer_queue.get_nowait()
                if msg["action"] == "add":
                    self.update_peer(msg["peer"])
                elif msg["action"] == "remove":
                    self.remove_peer(msg["name"])
        except queue.Empty:
            pass

        self.after(100, self._poll_queues)
