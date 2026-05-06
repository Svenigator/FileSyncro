# src/group_manager.py
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class Group:
    name: str


class GroupManager:
    def __init__(self, config_path: Path | None = None):
        self._config_path = config_path or Path.home() / ".filesyncro" / "groups.json"
        self._groups: dict[str, Group] = {}
        self._my_group: str | None = None
        self._load()

    @property
    def groups(self) -> list[Group]:
        return list(self._groups.values())

    @property
    def my_group(self) -> str | None:
        return self._my_group

    def create_group(self, name: str) -> Group:
        group = Group(name=name)
        self._groups[name] = group
        self._save()
        return group

    def delete_group(self, name: str) -> None:
        self._groups.pop(name, None)
        if self._my_group == name:
            self._my_group = None
        self._save()

    def set_my_group(self, name: str | None) -> None:
        self._my_group = name
        self._save()

    def merge_groups(self, names: list[str]) -> None:
        changed = False
        for name in names:
            if name not in self._groups:
                self._groups[name] = Group(name=name)
                changed = True
        if changed:
            self._save()

    def _load(self) -> None:
        if not self._config_path.exists():
            return
        try:
            data = json.loads(self._config_path.read_text())
            self._my_group = data.get("my_group")
            for name in data.get("groups", []):
                self._groups[name] = Group(name=name)
        except (json.JSONDecodeError, KeyError):
            pass

    def _save(self) -> None:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "my_group": self._my_group,
            "groups": list(self._groups.keys()),
        }
        self._config_path.write_text(json.dumps(data, indent=2))
