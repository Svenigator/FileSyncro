# tests/test_peer_manager.py
import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.peer_manager import PeerManager, Peer


def test_add_and_remove_peer(tmp_path):
    pm = PeerManager(sync_dir=tmp_path)
    peer = Peer(name="win-pc", ip="192.168.1.2", port=5757)
    pm.add_peer(peer)
    assert peer in pm.peers
    pm.remove_peer("win-pc")
    assert peer not in pm.peers


def test_peer_url(tmp_path):
    pm = PeerManager(sync_dir=tmp_path)
    peer = Peer(name="mac", ip="10.0.0.5", port=5757)
    assert pm._url(peer, "/files") == "http://10.0.0.5:5757/files"


async def test_send_file_returns_true_on_success(tmp_path):
    f = tmp_path / "slide.pptx"
    f.write_bytes(b"slide data")

    pm = PeerManager(sync_dir=tmp_path)
    pm.add_peer(Peer(name="mac", ip="192.168.1.5", port=5757))

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession.put", return_value=mock_cm):
        results = await pm.send_file("slide.pptx")

    assert results["mac"] is True


async def test_send_file_returns_false_on_connection_error(tmp_path):
    f = tmp_path / "slide.pptx"
    f.write_bytes(b"data")

    pm = PeerManager(sync_dir=tmp_path)
    pm.add_peer(Peer(name="offline-pc", ip="192.168.1.99", port=5757))

    with patch("aiohttp.ClientSession.put", side_effect=Exception("connection refused")):
        results = await pm.send_file("slide.pptx")

    assert results["offline-pc"] is False
    assert pm._peers["offline-pc"].reachable is False


async def test_get_peer_files(tmp_path):
    pm = PeerManager(sync_dir=tmp_path)
    peer = Peer(name="win", ip="192.168.1.3", port=5757)
    pm.add_peer(peer)

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"vortrag.pptx": 1000000.0})
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession.get", return_value=mock_cm):
        files = await pm.get_peer_files(peer)

    assert files == {"vortrag.pptx": 1000000.0}


async def test_ping_returns_true_when_reachable(tmp_path):
    pm = PeerManager(sync_dir=tmp_path)
    peer = Peer(name="mac", ip="192.168.1.5", port=5757)
    pm.add_peer(peer)

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession.get", return_value=mock_cm):
        result = await pm.ping(peer)

    assert result is True
    assert peer.reachable is True


async def test_ping_returns_false_when_unreachable(tmp_path):
    pm = PeerManager(sync_dir=tmp_path)
    peer = Peer(name="offline", ip="192.168.1.99", port=5757)
    pm.add_peer(peer)

    with patch("aiohttp.ClientSession.get", side_effect=Exception("timeout")):
        result = await pm.ping(peer)

    assert result is False
    assert peer.reachable is False


async def test_ping_all_removes_unreachable_and_returns_names(tmp_path):
    pm = PeerManager(sync_dir=tmp_path)
    pm.add_peer(Peer(name="alive", ip="192.168.1.1", port=5757))
    pm.add_peer(Peer(name="dead", ip="192.168.1.99", port=5757))

    async def fake_ping(peer):
        return peer.name == "alive"

    pm.ping = fake_ping
    removed = await pm.ping_all()

    assert removed == ["dead"]
    assert "dead" not in [p.name for p in pm.peers]
    assert "alive" in [p.name for p in pm.peers]
