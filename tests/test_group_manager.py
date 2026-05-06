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


def test_set_my_group(tmp_path):
    gm = GroupManager(config_path=tmp_path / "groups.json")
    gm.create_group("Bühne")
    gm.set_my_group("Bühne")
    assert gm.my_group == "Bühne"


def test_my_group_none_by_default(tmp_path):
    gm = GroupManager(config_path=tmp_path / "groups.json")
    assert gm.my_group is None


def test_merge_groups_adds_new_names(tmp_path):
    gm = GroupManager(config_path=tmp_path / "groups.json")
    gm.merge_groups(["Bühne", "Technik"])
    names = [g.name for g in gm.groups]
    assert "Bühne" in names
    assert "Technik" in names


def test_merge_groups_does_not_duplicate(tmp_path):
    gm = GroupManager(config_path=tmp_path / "groups.json")
    gm.create_group("Bühne")
    gm.merge_groups(["Bühne", "Bühne"])
    assert [g.name for g in gm.groups].count("Bühne") == 1


def test_merge_groups_preserves_existing(tmp_path):
    gm = GroupManager(config_path=tmp_path / "groups.json")
    gm.create_group("Bühne")
    gm.merge_groups(["Technik"])
    names = [g.name for g in gm.groups]
    assert "Bühne" in names
    assert "Technik" in names


def test_delete_my_group_clears_my_group(tmp_path):
    gm = GroupManager(config_path=tmp_path / "groups.json")
    gm.create_group("Bühne")
    gm.set_my_group("Bühne")
    gm.delete_group("Bühne")
    assert gm.my_group is None


def test_persistence_roundtrip(tmp_path):
    path = tmp_path / "groups.json"
    gm = GroupManager(config_path=path)
    gm.create_group("Bühne")
    gm.create_group("Technik")
    gm.set_my_group("Bühne")

    gm2 = GroupManager(config_path=path)
    assert gm2.my_group == "Bühne"
    names = [g.name for g in gm2.groups]
    assert "Bühne" in names
    assert "Technik" in names
