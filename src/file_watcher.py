# src/file_watcher.py
import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class _DebounceHandler(FileSystemEventHandler):
    def __init__(self, loop: asyncio.AbstractEventLoop, on_change, on_delete, debounce: float = 0.5):
        self._loop = loop
        self._on_change = on_change
        self._on_delete = on_delete
        self._debounce = debounce
        self._handles: dict[str, asyncio.TimerHandle] = {}

    def _schedule(self, key: str, fn):
        if key in self._handles:
            self._handles[key].cancel()
        handle = self._loop.call_later(
            self._debounce,
            lambda: asyncio.run_coroutine_threadsafe(fn(), self._loop)
        )
        self._handles[key] = handle

    def on_created(self, event):
        if not event.is_directory:
            path = Path(event.src_path)
            self._schedule(event.src_path, lambda p=path: self._on_change(p))

    def on_modified(self, event):
        if not event.is_directory:
            path = Path(event.src_path)
            self._schedule(event.src_path, lambda p=path: self._on_change(p))

    def on_deleted(self, event):
        if not event.is_directory:
            path = Path(event.src_path)
            self._schedule(event.src_path, lambda p=path: self._on_delete(p))


class FileWatcher:
    def __init__(self, sync_dir: Path, on_change, on_delete):
        self.sync_dir = sync_dir
        self._on_change = on_change
        self._on_delete = on_delete
        self._observer: Observer | None = None

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        handler = _DebounceHandler(loop, self._on_change, self._on_delete)
        self._observer = Observer()
        self._observer.schedule(handler, str(self.sync_dir), recursive=True)
        self._observer.start()

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join()
