# src/group_manager.py
from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass
class Group:
    name: str
    peer_names: list[str] = field(default_factory=list)


class GroupManager:
    def __init__(self, config_path: Path | None = None):
        self._config_path = config_path or Path.home() / ".filesyncro" / "groups.json"
        self._groups: dict[str, Group] = {}
        self._active: str | None = None
        self._load()

    @property
    def groups(self) -> list[Group]:
        return list(self._groups.values())

    @property
    def active_group_name(self) -> str | None:
        return self._active

    def create_group(self, name: str) -> Group:
        group = Group(name=name)
        self._groups[name] = group
        self._save()
        return group

    def delete_group(self, name: str) -> None:
        self._groups.pop(name, None)
        if self._active == name:
            self._active = None
        self._save()

    def set_active(self, name: str | None) -> None:
        self._active = name
        self._save()

    def set_peer_membership(self, group_name: str, peer_name: str, member: bool) -> None:
        group = self._groups.get(group_name)
        if group is None:
            return
        if member and peer_name not in group.peer_names:
            group.peer_names.append(peer_name)
        elif not member:
            group.peer_names = [p for p in group.peer_names if p != peer_name]
        self._save()

    def get_active_peer_names(self) -> list[str] | None:
        if self._active is None:
            return None
        group = self._groups.get(self._active)
        return list(group.peer_names) if group else []

    def _load(self) -> None:
        if not self._config_path.exists():
            return
        try:
            data = json.loads(self._config_path.read_text())
            self._active = data.get("active")
            for g in data.get("groups", []):
                self._groups[g["name"]] = Group(
                    name=g["name"],
                    peer_names=g.get("peers", []),
                )
        except (json.JSONDecodeError, KeyError):
            pass

    def _save(self) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "active": self._active,
            "groups": [
                {"name": g.name, "peers": g.peer_names}
                for g in self._groups.values()
            ],
        }
        self._config_path.write_text(json.dumps(data, indent=2))
