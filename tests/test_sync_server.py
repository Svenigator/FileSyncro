# tests/test_sync_server.py
import asyncio
import os
import pytest
import aiohttp
from pathlib import Path
from src.sync_server import SyncServer


async def test_put_new_file(tmp_path):
    srv = SyncServer(sync_dir=tmp_path)
    await srv.start()
    try:
        async with aiohttp.ClientSession() as s:
            resp = await s.put(
                f"http://localhost:{SyncServer.PORT}/file/vortrag.pptx",
                data=b"slide data",
                headers={"X-Timestamp": "1000000.0"}
            )
            assert resp.status == 200
            assert (await resp.text()) == "ok"
        assert (tmp_path / "vortrag.pptx").read_bytes() == b"slide data"
    finally:
        await srv.stop()


async def test_put_same_timestamp_ignored(tmp_path):
    f = tmp_path / "same.txt"
    f.write_bytes(b"original")
    os.utime(f, (1000000.0, 1000000.0))

    srv = SyncServer(sync_dir=tmp_path)
    await srv.start()
    try:
        async with aiohttp.ClientSession() as s:
            resp = await s.put(
                f"http://localhost:{SyncServer.PORT}/file/same.txt",
                data=b"new content",
                headers={"X-Timestamp": "1000000.0"}
            )
            assert resp.status == 200
            assert (await resp.text()) == "unchanged"
        assert f.read_bytes() == b"original"
    finally:
        await srv.stop()


async def test_delete_existing_file(tmp_path):
    (tmp_path / "old.mp4").write_bytes(b"video")
    srv = SyncServer(sync_dir=tmp_path)
    await srv.start()
    try:
        async with aiohttp.ClientSession() as s:
            resp = await s.delete(f"http://localhost:{SyncServer.PORT}/file/old.mp4")
            assert resp.status == 200
        assert not (tmp_path / "old.mp4").exists()
    finally:
        await srv.stop()


async def test_get_files_lists_with_timestamps(tmp_path):
    (tmp_path / "a.pptx").write_bytes(b"slide")
    srv = SyncServer(sync_dir=tmp_path)
    await srv.start()
    try:
        async with aiohttp.ClientSession() as s:
            resp = await s.get(f"http://localhost:{SyncServer.PORT}/files")
            files = await resp.json()
            assert "a.pptx" in files
            assert isinstance(files["a.pptx"], float)
    finally:
        await srv.stop()


async def test_delete_calls_on_before_delete(tmp_path):
    (tmp_path / "file.txt").write_bytes(b"data")
    suppressed = []

    def on_before_delete(rel_path):
        suppressed.append(rel_path)

    srv = SyncServer(sync_dir=tmp_path, on_before_delete=on_before_delete)
    await srv.start()
    try:
        async with aiohttp.ClientSession() as s:
            resp = await s.delete(f"http://localhost:{SyncServer.PORT}/file/file.txt")
            assert resp.status == 200
        assert "file.txt" in suppressed
    finally:
        await srv.stop()


async def test_conflict_calls_on_conflict_and_accepts(tmp_path):
    import queue
    conflict_queue = queue.Queue()

    f = tmp_path / "conflict.pptx"
    f.write_bytes(b"local version")
    os.utime(f, (1000000.0, 1000000.0))

    loop = asyncio.get_event_loop()

    def on_conflict(rel_path, local_ts, remote_ts, data, future):
        conflict_queue.put((rel_path, local_ts, remote_ts, data, future))
        loop.call_soon_threadsafe(future.set_result, True)

    srv = SyncServer(sync_dir=tmp_path, on_conflict=on_conflict)
    await srv.start()
    try:
        async with aiohttp.ClientSession() as s:
            resp = await s.put(
                f"http://localhost:{SyncServer.PORT}/file/conflict.pptx",
                data=b"remote version",
                headers={"X-Timestamp": "2000000.0"}
            )
            assert resp.status == 200
        assert not conflict_queue.empty()
        assert f.read_bytes() == b"remote version"
    finally:
        await srv.stop()


async def test_put_older_file_is_auto_rejected(tmp_path):
    f = tmp_path / "slide.pptx"
    f.write_bytes(b"newer local version")
    os.utime(f, (2000000.0, 2000000.0))

    conflicts = []

    def on_conflict(rel_path, local_ts, remote_ts, data, future):
        conflicts.append(rel_path)
        asyncio.get_event_loop().call_soon_threadsafe(future.set_result, True)

    srv = SyncServer(sync_dir=tmp_path, on_conflict=on_conflict)
    await srv.start()
    try:
        async with aiohttp.ClientSession() as s:
            resp = await s.put(
                f"http://localhost:{SyncServer.PORT}/file/slide.pptx",
                data=b"older remote version",
                headers={"X-Timestamp": "1000000.0"},
            )
            assert resp.status == 409
            assert (await resp.text()) == "outdated"
        assert len(conflicts) == 0
        assert f.read_bytes() == b"newer local version"
    finally:
        await srv.stop()


async def test_put_returns_403_on_permission_error(tmp_path):
    from unittest.mock import patch

    srv = SyncServer(sync_dir=tmp_path)
    await srv.start()
    try:
        with patch("pathlib.Path.write_bytes", side_effect=PermissionError("access denied")):
            async with aiohttp.ClientSession() as s:
                resp = await s.put(
                    f"http://localhost:{SyncServer.PORT}/file/locked.pptx",
                    data=b"data",
                    headers={"X-Timestamp": "1000000.0"},
                )
                assert resp.status == 403
                assert "permission" in (await resp.text()).lower()
    finally:
        await srv.stop()
