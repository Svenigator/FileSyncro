# tests/test_group_manager.py
from pathlib import Path
from src.group_manager import Group, GroupManager


def test_create_group(tmp_path):
    gm = GroupManager(config_path=tmp_path / "groups.json")
    group = gm.create_group("Bühne")
    assert group.name == "Bühne"
    assert group in gm.groups


def test_delete_group(tmp_path):
    gm = GroupManager(config_path=tmp_path / "groups.json")
    gm.create_group("Technik")
    gm.delete_group("Technik")
    assert not any(g.name == "Technik" for g in gm.groups)


def test_set_active_group(tmp_path):
    gm = GroupManager(config_path=tmp_path / "groups.json")
    gm.create_group("Bühne")
    gm.set_active("Bühne")
    assert gm.active_group_name == "Bühne"


def test_no_active_group_returns_none_for_peer_names(tmp_path):
    gm = GroupManager(config_path=tmp_path / "groups.json")
    gm.set_active(None)
    assert gm.get_active_peer_names() is None


def test_peer_membership_add_and_remove(tmp_path):
    gm = GroupManager(config_path=tmp_path / "groups.json")
    gm.create_group("Bühne")
    gm.set_peer_membership("Bühne", "Win-PC-01", True)
    gm.set_peer_membership("Bühne", "MacBook-02", True)
    gm.set_peer_membership("Bühne", "Win-PC-01", False)
    gm.set_active("Bühne")
    names = gm.get_active_peer_names()
    assert "MacBook-02" in names
    assert "Win-PC-01" not in names


def test_persistence_roundtrip(tmp_path):
    path = tmp_path / "groups.json"
    gm = GroupManager(config_path=path)
    gm.create_group("Bühne")
    gm.set_peer_membership("Bühne", "Win-PC-01", True)
    gm.set_active("Bühne")

    gm2 = GroupManager(config_path=path)
    assert gm2.active_group_name == "Bühne"
    assert "Win-PC-01" in gm2.get_active_peer_names()


def test_delete_active_group_clears_active(tmp_path):
    gm = GroupManager(config_path=tmp_path / "groups.json")
    gm.create_group("Bühne")
    gm.set_active("Bühne")
    gm.delete_group("Bühne")
    assert gm.active_group_name is None
    assert gm.get_active_peer_names() is None


def test_duplicate_peer_not_added_twice(tmp_path):
    gm = GroupManager(config_path=tmp_path / "groups.json")
    gm.create_group("Bühne")
    gm.set_peer_membership("Bühne", "Win-PC-01", True)
    gm.set_peer_membership("Bühne", "Win-PC-01", True)
    gm.set_active("Bühne")
    assert gm.get_active_peer_names().count("Win-PC-01") == 1
