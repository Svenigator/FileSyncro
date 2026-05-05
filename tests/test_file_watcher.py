# tests/test_file_watcher.py
import asyncio
import pytest
from pathlib import Path
from src.file_watcher import FileWatcher


async def test_detects_new_file(tmp_path):
    changes = []

    async def on_change(path: Path):
        changes.append(path)

    async def on_delete(path: Path):
        pass

    loop = asyncio.get_event_loop()
    watcher = FileWatcher(sync_dir=tmp_path, on_change=on_change, on_delete=on_delete)
    watcher.start(loop)

    (tmp_path / "vortrag.pptx").write_bytes(b"slides")
    await asyncio.sleep(0.9)

    watcher.stop()
    assert any(p.name == "vortrag.pptx" for p in changes)


async def test_detects_deletion(tmp_path):
    deletions = []
    f = tmp_path / "video.mp4"
    f.write_bytes(b"data")

    async def on_change(path: Path):
        pass

    async def on_delete(path: Path):
        deletions.append(path)

    loop = asyncio.get_event_loop()
    watcher = FileWatcher(sync_dir=tmp_path, on_change=on_change, on_delete=on_delete)
    watcher.start(loop)

    f.unlink()
    await asyncio.sleep(0.9)

    watcher.stop()
    assert any(p.name == "video.mp4" for p in deletions)


async def test_debounce_deduplicates_rapid_writes(tmp_path):
    changes = []

    async def on_change(path: Path):
        changes.append(path)

    async def on_delete(path: Path):
        pass

    loop = asyncio.get_event_loop()
    watcher = FileWatcher(sync_dir=tmp_path, on_change=on_change, on_delete=on_delete)
    watcher.start(loop)

    f = tmp_path / "rapid.txt"
    for _ in range(5):
        f.write_bytes(b"x")
        await asyncio.sleep(0.05)

    await asyncio.sleep(0.9)
    watcher.stop()
    assert len([p for p in changes if p.name == "rapid.txt"]) == 1
