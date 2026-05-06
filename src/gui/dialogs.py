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


class GroupDialog(ctk.CTkToplevel):
    def __init__(self, parent, group_manager, known_peers: list[str]):
        super().__init__(parent)
        self.title("Gruppen verwalten")
        self.geometry("520x360")
        self.resizable(False, False)
        self.grab_set()
        self._gm = group_manager
        self._known_peers = known_peers
        self._selected_group: str | None = None
        self._peer_vars: dict[str, ctk.BooleanVar] = {}
        self._build()
        self.wait_window()

    def _build(self):
        left = ctk.CTkFrame(self)
        left.pack(side="left", fill="y", padx=(12, 4), pady=12)
        ctk.CTkLabel(left, text="Gruppen", font=ctk.CTkFont(weight="bold")).pack(pady=(0, 4))
        self._group_list = ctk.CTkScrollableFrame(left, width=160, height=200)
        self._group_list.pack()
        new_frame = ctk.CTkFrame(left, fg_color="transparent")
        new_frame.pack(fill="x", pady=(8, 0))
        self._new_entry = ctk.CTkEntry(new_frame, placeholder_text="Neuer Name", width=120)
        self._new_entry.pack(side="left", padx=(0, 4))
        ctk.CTkButton(new_frame, text="+", width=30, command=self._create_group).pack(side="left")

        right = ctk.CTkFrame(self)
        right.pack(side="left", fill="both", expand=True, padx=(4, 12), pady=12)
        ctk.CTkLabel(right, text="Mitglieder", font=ctk.CTkFont(weight="bold")).pack(pady=(0, 4))
        self._peer_frame = ctk.CTkScrollableFrame(right, height=200)
        self._peer_frame.pack(fill="both", expand=True)

        ctk.CTkButton(self, text="Schließen", command=self.destroy).pack(pady=8)
        self._refresh_group_list()

    def _refresh_group_list(self):
        for w in self._group_list.winfo_children():
            w.destroy()
        for group in self._gm.groups:
            row = ctk.CTkFrame(self._group_list, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkButton(
                row, text=group.name, anchor="w",
                command=lambda n=group.name: self._select_group(n),
            ).pack(side="left", fill="x", expand=True)
            ctk.CTkButton(
                row, text="✕", width=28,
                command=lambda n=group.name: self._delete_group(n),
            ).pack(side="right")

    def _select_group(self, name: str):
        self._selected_group = name
        for w in self._peer_frame.winfo_children():
            w.destroy()
        self._peer_vars.clear()
        group = next((g for g in self._gm.groups if g.name == name), None)
        if group is None:
            return
        for peer_name in self._known_peers:
            var = ctk.BooleanVar(value=peer_name in group.peer_names)
            self._peer_vars[peer_name] = var
            ctk.CTkCheckBox(
                self._peer_frame, text=peer_name, variable=var,
                command=lambda p=peer_name, v=var: self._toggle_peer(p, v),
            ).pack(anchor="w", pady=2)

    def _toggle_peer(self, peer_name: str, var: ctk.BooleanVar):
        if self._selected_group:
            self._gm.set_peer_membership(self._selected_group, peer_name, var.get())

    def _create_group(self):
        name = self._new_entry.get().strip()
        if name and not any(g.name == name for g in self._gm.groups):
            self._gm.create_group(name)
            self._new_entry.delete(0, "end")
            self._refresh_group_list()

    def _delete_group(self, name: str):
        self._gm.delete_group(name)
        if self._selected_group == name:
            self._selected_group = None
            for w in self._peer_frame.winfo_children():
                w.destroy()
        self._refresh_group_list()
