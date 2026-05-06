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


async def test_ping_all_removes_after_three_consecutive_failures(tmp_path):
    pm = PeerManager(sync_dir=tmp_path)
    pm.add_peer(Peer(name="alive", ip="192.168.1.1", port=5757))
    pm.add_peer(Peer(name="dead", ip="192.168.1.99", port=5757))

    async def fake_ping(peer):
        return peer.name == "alive"

    pm.ping = fake_ping

    # First two failures: peer stays in list
    assert await pm.ping_all() == []
    assert "dead" in [p.name for p in pm.peers]
    assert await pm.ping_all() == []
    assert "dead" in [p.name for p in pm.peers]

    # Third consecutive failure: peer removed
    removed = await pm.ping_all()
    assert removed == ["dead"]
    assert "dead" not in [p.name for p in pm.peers]
    assert "alive" in [p.name for p in pm.peers]


async def test_ping_all_resets_failure_count_on_success(tmp_path):
    pm = PeerManager(sync_dir=tmp_path)
    pm.add_peer(Peer(name="flaky", ip="192.168.1.5", port=5757))

    call_count = 0

    async def fake_ping(peer):
        nonlocal call_count
        call_count += 1
        return call_count == 2  # fails on 1st and 3rd call, succeeds on 2nd

    pm.ping = fake_ping

    await pm.ping_all()  # fail #1 → consecutive_failures = 1
    await pm.ping_all()  # success → resets to 0
    removed = await pm.ping_all()  # fail #1 again → consecutive_failures = 1, not removed

    assert removed == []
    assert "flaky" in [p.name for p in pm.peers]


async def test_ping_fires_callback_on_status_change(tmp_path):
    callbacks = []
    pm = PeerManager(sync_dir=tmp_path, on_peer_status_changed=lambda p: callbacks.append(p.reachable))
    peer = Peer(name="mac", ip="192.168.1.5", port=5757, reachable=True)
    pm.add_peer(peer)

    with patch("aiohttp.ClientSession.get", side_effect=Exception("timeout")):
        result = await pm.ping(peer)

    assert result is False
    assert len(callbacks) == 1
    assert callbacks[0] is False  # callback received peer with reachable=False


async def test_send_file_respects_active_filter(tmp_path):
    f = tmp_path / "slide.pptx"
    f.write_bytes(b"data")

    pm = PeerManager(sync_dir=tmp_path)
    pm.add_peer(Peer(name="in-group", ip="192.168.1.1", port=5757))
    pm.add_peer(Peer(name="out-group", ip="192.168.1.2", port=5757))
    pm.set_active_filter(["in-group"])

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("aiohttp.ClientSession.put", return_value=mock_cm):
        results = await pm.send_file("slide.pptx")

    assert "in-group" in results
    assert "out-group" not in results


def test_active_filter_none_restores_all_peers(tmp_path):
    pm = PeerManager(sync_dir=tmp_path)
    pm.add_peer(Peer(name="peer-a", ip="192.168.1.1", port=5757))
    pm.add_peer(Peer(name="peer-b", ip="192.168.1.2", port=5757))

    pm.set_active_filter(["peer-a"])
    assert len(pm.active_peers) == 1

    pm.set_active_filter(None)
    assert len(pm.active_peers) == 2
