# FileSyncro Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eine standalone Python-Desktop-App (Windows + macOS) für Peer-to-Peer Datei-Sync im lokalen Netzwerk ohne Installation.

**Architecture:** Jede Instanz läuft als gleichwertiger Peer — ein aiohttp-HTTP-Server (Port 5757) in einem Hintergrund-asyncio-Thread, watchdog für Datei-Watching, zeroconf für mDNS-Discovery und CustomTkinter für die GUI im Hauptthread. Threads kommunizieren über `queue.Queue` und `asyncio.run_coroutine_threadsafe`.

**Tech Stack:** Python 3.11+, customtkinter 5.x, aiohttp 3.9+, watchdog 3.x, zeroconf 0.131+, pytest 7.x, pytest-asyncio, PyInstaller

---

### Task 1: Projektsetup

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `pytest.ini`
- Create: `src/__init__.py`
- Create: `src/gui/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Virtuelle Umgebung anlegen und Dependencies installieren**

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS:
source .venv/bin/activate
```

- [ ] **Step 2: requirements.txt anlegen**

```
customtkinter>=5.2.0
aiohttp>=3.9.0
watchdog>=3.0.0
zeroconf>=0.131.0
```

- [ ] **Step 3: requirements-dev.txt anlegen**

```
pytest>=7.4.0
pytest-asyncio>=0.23.0
```

- [ ] **Step 4: pytest.ini anlegen**

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

- [ ] **Step 5: Dependencies installieren**

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

- [ ] **Step 6: Leere __init__.py Dateien anlegen**

`src/__init__.py` — leer  
`src/gui/__init__.py` — leer  
`tests/__init__.py` — leer

- [ ] **Step 7: Commit**

```bash
git add requirements.txt requirements-dev.txt pytest.ini src/__init__.py src/gui/__init__.py tests/__init__.py
git commit -m "chore: project setup with dependencies"
```

---

### Task 2: Sync Server

**Files:**
- Create: `src/sync_server.py`
- Create: `tests/test_sync_server.py`

Der aiohttp-Server läuft auf Port 5757 und stellt drei Endpunkte bereit:
- `PUT /file/{path}` — empfängt eine Datei von einem Peer (inkl. Konflikt-Erkennung)
- `DELETE /file/{path}` — empfängt einen Lösch-Befehl
- `GET /files` — gibt alle lokalen Dateien mit Timestamps zurück

Konflikt-Logik: Wenn eine Datei existiert und der Timestamp-Unterschied > 1.0s ist, wird `on_conflict` aufgerufen. `on_conflict` ist ein synchrones Callable, das ein `ConflictRequest` (Pfad, lokaler TS, Remote-TS, Daten, Future) in eine `queue.Queue` legt. Der Server awaitet das Future — der Hauptthread (GUI) setzt es später via `loop.call_soon_threadsafe`.

- [ ] **Step 1: Failing Tests schreiben**

```python
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
```

- [ ] **Step 2: Tests laufen lassen — müssen fehlschlagen**

```bash
pytest tests/test_sync_server.py -v
```

Erwartete Ausgabe: `ModuleNotFoundError: No module named 'src.sync_server'`

- [ ] **Step 3: sync_server.py implementieren**

```python
# src/sync_server.py
import asyncio
import os
from pathlib import Path
from aiohttp import web


class SyncServer:
    PORT = 5757

    def __init__(self, sync_dir: Path, on_conflict=None):
        self.sync_dir = sync_dir
        self.on_conflict = on_conflict
        self._app = web.Application()
        self._app.router.add_put('/file/{path:.*}', self._handle_put)
        self._app.router.add_delete('/file/{path:.*}', self._handle_delete)
        self._app.router.add_get('/files', self._handle_list)
        self._runner = None

    async def _handle_put(self, request: web.Request) -> web.Response:
        rel_path = request.match_info['path']
        remote_ts = float(request.headers.get('X-Timestamp', '0'))
        data = await request.read()
        file_path = self.sync_dir / rel_path

        if file_path.exists():
            local_ts = file_path.stat().st_mtime
            if abs(local_ts - remote_ts) < 1.0:
                return web.Response(status=200, text='unchanged')
            if self.on_conflict:
                loop = asyncio.get_event_loop()
                future: asyncio.Future = loop.create_future()
                self.on_conflict(rel_path, local_ts, remote_ts, data, future)
                accept = await future
                if not accept:
                    return web.Response(status=409, text='conflict rejected')

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        os.utime(file_path, (remote_ts, remote_ts))
        return web.Response(status=200, text='ok')

    async def _handle_delete(self, request: web.Request) -> web.Response:
        rel_path = request.match_info['path']
        file_path = self.sync_dir / rel_path
        if file_path.exists():
            file_path.unlink()
        return web.Response(status=200)

    async def _handle_list(self, request: web.Request) -> web.Response:
        files: dict[str, float] = {}
        if self.sync_dir.exists():
            for f in self.sync_dir.rglob('*'):
                if f.is_file():
                    rel = str(f.relative_to(self.sync_dir)).replace('\\', '/')
                    files[rel] = f.stat().st_mtime
        return web.json_response(files)

    async def start(self) -> None:
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, '0.0.0.0', self.PORT)
        await site.start()

    async def stop(self) -> None:
        if self._runner:
            await self._runner.cleanup()
```

- [ ] **Step 4: Tests laufen lassen — müssen bestehen**

```bash
pytest tests/test_sync_server.py -v
```

Erwartete Ausgabe: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add src/sync_server.py tests/test_sync_server.py
git commit -m "feat: add sync server with PUT/DELETE/GET endpoints"
```

---

### Task 3: File Watcher

**Files:**
- Create: `src/file_watcher.py`
- Create: `tests/test_file_watcher.py`

Watchdog-Observer mit 500ms Debounce. Ruft async Callbacks `on_change(path)` und `on_delete(path)` auf. `start(loop)` bekommt den asyncio-Loop aus dem Hintergrund-Thread übergeben.

- [ ] **Step 1: Failing Tests schreiben**

```python
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
```

- [ ] **Step 2: Tests laufen lassen — müssen fehlschlagen**

```bash
pytest tests/test_file_watcher.py -v
```

Erwartete Ausgabe: `ModuleNotFoundError: No module named 'src.file_watcher'`

- [ ] **Step 3: file_watcher.py implementieren**

```python
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

    def _schedule(self, key: str, coro):
        if key in self._handles:
            self._handles[key].cancel()
        handle = self._loop.call_later(
            self._debounce,
            lambda: asyncio.run_coroutine_threadsafe(coro, self._loop)
        )
        self._handles[key] = handle

    def on_created(self, event):
        if not event.is_directory:
            self._schedule(event.src_path, self._on_change(Path(event.src_path)))

    def on_modified(self, event):
        if not event.is_directory:
            self._schedule(event.src_path, self._on_change(Path(event.src_path)))

    def on_deleted(self, event):
        if not event.is_directory:
            self._schedule(event.src_path, self._on_delete(Path(event.src_path)))


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
```

- [ ] **Step 4: Tests laufen lassen — müssen bestehen**

```bash
pytest tests/test_file_watcher.py -v
```

Erwartete Ausgabe: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add src/file_watcher.py tests/test_file_watcher.py
git commit -m "feat: add file watcher with 500ms debounce"
```

---

### Task 4: Peer Manager

**Files:**
- Create: `src/peer_manager.py`
- Create: `tests/test_peer_manager.py`

Verwaltet bekannte Peers und führt alle HTTP-Client-Operationen aus: Datei senden, Datei löschen, Dateiliste abrufen, manuellen Sync aller Differenzen.

`Peer` ist ein Dataclass mit `name`, `ip`, `port`, `reachable`.

- [ ] **Step 1: Failing Tests schreiben**

```python
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
```

- [ ] **Step 2: Tests laufen lassen — müssen fehlschlagen**

```bash
pytest tests/test_peer_manager.py -v
```

Erwartete Ausgabe: `ModuleNotFoundError: No module named 'src.peer_manager'`

- [ ] **Step 3: peer_manager.py implementieren**

```python
# src/peer_manager.py
import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional
import aiohttp


@dataclass
class Peer:
    name: str
    ip: str
    port: int = 5757
    reachable: bool = True


class PeerManager:
    def __init__(self, sync_dir: Path, on_peer_status_changed: Optional[Callable[[Peer], None]] = None):
        self.sync_dir = sync_dir
        self.on_peer_status_changed = on_peer_status_changed
        self._peers: dict[str, Peer] = {}

    @property
    def peers(self) -> list[Peer]:
        return list(self._peers.values())

    def add_peer(self, peer: Peer) -> None:
        self._peers[peer.name] = peer

    def remove_peer(self, name: str) -> None:
        self._peers.pop(name, None)

    def _url(self, peer: Peer, path: str) -> str:
        return f"http://{peer.ip}:{peer.port}{path}"

    def _mark_unreachable(self, peer: Peer) -> None:
        peer.reachable = False
        if self.on_peer_status_changed:
            self.on_peer_status_changed(peer)

    async def send_file(self, rel_path: str) -> dict[str, bool]:
        file_path = self.sync_dir / rel_path
        if not file_path.exists():
            return {}
        data = file_path.read_bytes()
        ts = file_path.stat().st_mtime
        results: dict[str, bool] = {}
        async with aiohttp.ClientSession() as session:
            for peer in self.peers:
                try:
                    async with session.put(
                        self._url(peer, f"/file/{rel_path}"),
                        data=data,
                        headers={"X-Timestamp": str(ts)},
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as resp:
                        peer.reachable = True
                        results[peer.name] = resp.status in (200, 409)
                except Exception:
                    results[peer.name] = False
                    self._mark_unreachable(peer)
        return results

    async def delete_file(self, rel_path: str) -> dict[str, bool]:
        results: dict[str, bool] = {}
        async with aiohttp.ClientSession() as session:
            for peer in self.peers:
                try:
                    async with session.delete(
                        self._url(peer, f"/file/{rel_path}"),
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as resp:
                        peer.reachable = True
                        results[peer.name] = resp.status == 200
                except Exception:
                    results[peer.name] = False
                    self._mark_unreachable(peer)
        return results

    async def get_peer_files(self, peer: Peer) -> dict[str, float]:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    self._url(peer, "/files"),
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        peer.reachable = True
                        return await resp.json()
            except Exception:
                self._mark_unreachable(peer)
        return {}

    async def sync_with_all(self) -> None:
        if not self.sync_dir.exists():
            return
        local_files: dict[str, float] = {}
        for f in self.sync_dir.rglob('*'):
            if f.is_file():
                rel = str(f.relative_to(self.sync_dir)).replace('\\', '/')
                local_files[rel] = f.stat().st_mtime

        for peer in self.peers:
            remote_files = await self.get_peer_files(peer)
            for rel_path, local_ts in local_files.items():
                remote_ts = remote_files.get(rel_path)
                if remote_ts is None or local_ts > remote_ts + 1.0:
                    await self._push_to_peer(peer, rel_path)

    async def _push_to_peer(self, peer: Peer, rel_path: str) -> None:
        file_path = self.sync_dir / rel_path
        if not file_path.exists():
            return
        data = file_path.read_bytes()
        ts = file_path.stat().st_mtime
        async with aiohttp.ClientSession() as session:
            try:
                async with session.put(
                    self._url(peer, f"/file/{rel_path}"),
                    data=data,
                    headers={"X-Timestamp": str(ts)},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    peer.reachable = True
            except Exception:
                self._mark_unreachable(peer)
```

- [ ] **Step 4: Tests laufen lassen — müssen bestehen**

```bash
pytest tests/test_peer_manager.py -v
```

Erwartete Ausgabe: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add src/peer_manager.py tests/test_peer_manager.py
git commit -m "feat: add peer manager with send/delete/sync operations"
```

---

### Task 5: Discovery (zeroconf/mDNS)

**Files:**
- Create: `src/discovery.py`

Kein eigener Test (zeroconf benötigt echte Netzwerk-Interfaces — Mocking bringt wenig Mehrwert). Discovery wird in der Integration manuell verifiziert.

Service-Typ: `_filesyncro._tcp.local.`

- [ ] **Step 1: discovery.py implementieren**

```python
# src/discovery.py
import socket
import asyncio
from typing import Callable, Optional
from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf
from zeroconf.asyncio import AsyncZeroconf


SERVICE_TYPE = "_filesyncro._tcp.local."


class Discovery:
    def __init__(
        self,
        name: str,
        port: int,
        on_peer_found: Optional[Callable[[str, str, int], None]],
        on_peer_lost: Optional[Callable[[str], None]],
    ):
        self._name = name
        self._port = port
        self._on_peer_found = on_peer_found
        self._on_peer_lost = on_peer_lost
        self._azc: Optional[AsyncZeroconf] = None
        self._browser: Optional[ServiceBrowser] = None
        self._info: Optional[ServiceInfo] = None

    def _local_ip(self) -> str:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]

    def _build_service_info(self, ip: str) -> ServiceInfo:
        return ServiceInfo(
            type_=SERVICE_TYPE,
            name=f"{self._name}.{SERVICE_TYPE}",
            addresses=[socket.inet_aton(ip)],
            port=self._port,
            properties={"name": self._name},
        )

    async def start(self) -> None:
        self._azc = AsyncZeroconf()
        ip = self._local_ip()
        self._info = self._build_service_info(ip)
        await self._azc.async_register_service(self._info)
        self._browser = ServiceBrowser(
            self._azc.zeroconf, SERVICE_TYPE, handlers=[self._handle_state_change]
        )

    async def stop(self) -> None:
        if self._azc:
            if self._info:
                await self._azc.async_unregister_service(self._info)
            await self._azc.async_close()

    def _handle_state_change(self, zeroconf: Zeroconf, service_type: str, name: str, state_change) -> None:
        from zeroconf import ServiceStateChange
        if state_change == ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info and info.name != self._info.name:
                ip = socket.inet_ntoa(info.addresses[0])
                peer_name = info.properties.get(b"name", b"unknown").decode()
                if self._on_peer_found:
                    self._on_peer_found(peer_name, ip, info.port)
        elif state_change == ServiceStateChange.Removed:
            peer_name = name.replace(f".{SERVICE_TYPE}", "")
            if self._on_peer_lost:
                self._on_peer_lost(peer_name)
```

- [ ] **Step 2: Manuelle Smoke-Verifikation (kein pytest)**

Starte die App später in Task 8 auf zwei Rechnern im gleichen Netzwerk und verifiziere:
- Gerät A erscheint in der Liste von Gerät B
- Gerät B erscheint in der Liste von Gerät A

- [ ] **Step 3: Commit**

```bash
git add src/discovery.py
git commit -m "feat: add zeroconf mDNS discovery"
```

---

### Task 6: GUI Dialogs

**Files:**
- Create: `src/gui/dialogs.py`

Zwei modale Dialoge: `ConflictDialog` (welche Version behalten?) und `DeleteDialog` (nur lokal oder alle Geräte?). Beide blockieren bis der Nutzer klickt und geben das Ergebnis als Rückgabewert zurück.

- [ ] **Step 1: dialogs.py implementieren**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add src/gui/dialogs.py
git commit -m "feat: add conflict and delete dialogs"
```

---

### Task 7: GUI Hauptfenster

**Files:**
- Create: `src/gui/app.py`

CustomTkinter-Hauptfenster mit Geräteliste, Sync-Ordner-Auswahl, Aktivitätslog und "Jetzt synchronisieren"-Button.

Kommunikation mit asyncio: Die App pollt vier `queue.Queue`-Instanzen via `root.after(100, ...)`:
- `conflict_queue` — eingehende `ConflictRequest`-Dicts vom SyncServer
- `activity_queue` — Statusmeldungen (str) von PeerManager und FileWatcher
- `delete_queue` — Lösch-Anfragen vom FileWatcher
- `peer_queue` — Peer-Updates (`{"action": "add"/"remove", "peer": Peer / "name": str}`)

- [ ] **Step 1: app.py implementieren**

```python
# src/gui/app.py
import asyncio
import queue
import threading
from pathlib import Path
from tkinter import filedialog
from typing import Callable, Optional

import customtkinter as ctk

from src.gui.dialogs import ConflictDialog, DeleteDialog
from src.peer_manager import Peer


ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(
        self,
        async_loop: asyncio.AbstractEventLoop,
        conflict_queue: queue.Queue,
        activity_queue: queue.Queue,
        delete_queue: queue.Queue,
        peer_queue: queue.Queue,
        on_sync_dir_changed: Callable[[Path], None],
        on_manual_sync: Callable[[], None],
        on_add_peer_manual: Callable[[str, int], None],
    ):
        super().__init__()
        self.title("FileSyncro")
        self.geometry("560x520")
        self.resizable(False, False)

        self._async_loop = async_loop
        self._conflict_queue = conflict_queue
        self._activity_queue = activity_queue
        self._delete_queue = delete_queue
        self._peer_queue = peer_queue
        self._on_sync_dir_changed = on_sync_dir_changed
        self._on_manual_sync = on_manual_sync
        self._on_add_peer_manual = on_add_peer_manual
        self._peer_rows: dict[str, ctk.CTkFrame] = {}

        self._build_ui()
        self._poll_queues()

    def _build_ui(self):
        # Sync-Ordner
        folder_frame = ctk.CTkFrame(self)
        folder_frame.pack(fill="x", padx=16, pady=(16, 4))
        ctk.CTkLabel(folder_frame, text="Sync-Ordner:").pack(side="left", padx=8)
        self._folder_label = ctk.CTkLabel(folder_frame, text="(nicht gewählt)", anchor="w", width=300)
        self._folder_label.pack(side="left", padx=4)
        ctk.CTkButton(folder_frame, text="...", width=40, command=self._choose_folder).pack(side="left", padx=4)

        # Geräteliste
        ctk.CTkLabel(self, text="Verbundene Geräte", anchor="w").pack(fill="x", padx=16, pady=(12, 2))
        self._device_frame = ctk.CTkScrollableFrame(self, height=140)
        self._device_frame.pack(fill="x", padx=16)

        # Manuell hinzufügen
        manual_frame = ctk.CTkFrame(self, fg_color="transparent")
        manual_frame.pack(fill="x", padx=16, pady=4)
        self._ip_entry = ctk.CTkEntry(manual_frame, placeholder_text="IP-Adresse", width=180)
        self._ip_entry.pack(side="left", padx=(0, 4))
        ctk.CTkButton(manual_frame, text="Hinzufügen", width=100, command=self._add_manual_peer).pack(side="left")

        # Sync-Button + Status
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=16, pady=8)
        ctk.CTkButton(action_frame, text="Jetzt synchronisieren", command=self._manual_sync).pack(side="left")
        self._status_label = ctk.CTkLabel(action_frame, text="Status: bereit")
        self._status_label.pack(side="left", padx=16)

        # Aktivitätslog
        ctk.CTkLabel(self, text="Aktivität", anchor="w").pack(fill="x", padx=16, pady=(8, 2))
        self._log = ctk.CTkTextbox(self, height=160, state="disabled")
        self._log.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _choose_folder(self):
        path = filedialog.askdirectory(title="Sync-Ordner wählen")
        if path:
            self._folder_label.configure(text=path)
            self._on_sync_dir_changed(Path(path))

    def _manual_sync(self):
        self._status_label.configure(text="Status: synchronisiere…")
        asyncio.run_coroutine_threadsafe(self._on_manual_sync(), self._async_loop)

    def _add_manual_peer(self):
        ip = self._ip_entry.get().strip()
        if ip:
            self._on_add_peer_manual(ip, 5757)
            self._ip_entry.delete(0, "end")

    def update_peer(self, peer: Peer) -> None:
        if peer.name not in self._peer_rows:
            row = ctk.CTkFrame(self._device_frame)
            row.pack(fill="x", pady=2)
            dot = ctk.CTkLabel(row, text="●", width=20)
            dot.pack(side="left")
            ctk.CTkLabel(row, text=peer.name).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=peer.ip, text_color="gray").pack(side="left")
            self._peer_rows[peer.name] = row
            row._dot = dot
        dot = self._peer_rows[peer.name]._dot
        dot.configure(text_color="green" if peer.reachable else "red")

    def remove_peer(self, name: str) -> None:
        if name in self._peer_rows:
            self._peer_rows[name].destroy()
            del self._peer_rows[name]

    def log(self, message: str) -> None:
        self._log.configure(state="normal")
        self._log.insert("end", message + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def set_status(self, text: str) -> None:
        self._status_label.configure(text=f"Status: {text}")

    def _poll_queues(self):
        # Aktivitätsmeldungen
        try:
            while True:
                msg = self._activity_queue.get_nowait()
                self.log(msg)
                self.set_status("bereit")
        except queue.Empty:
            pass

        # Konflikt-Anfragen
        try:
            while True:
                req = self._conflict_queue.get_nowait()
                dlg = ConflictDialog(
                    self,
                    rel_path=req["rel_path"],
                    local_ts=req["local_ts"],
                    remote_ts=req["remote_ts"],
                    remote_name="Remote"
                )
                self._async_loop.call_soon_threadsafe(req["future"].set_result, dlg.result or False)
        except queue.Empty:
            pass

        # Lösch-Anfragen
        try:
            while True:
                req = self._delete_queue.get_nowait()
                dlg = DeleteDialog(self, rel_path=req["rel_path"])
                req["callback"](dlg.result or "local")
        except queue.Empty:
            pass

        # Peer-Updates
        try:
            while True:
                msg = self._peer_queue.get_nowait()
                if msg["action"] == "add":
                    self.update_peer(msg["peer"])
                elif msg["action"] == "remove":
                    self.remove_peer(msg["name"])
        except queue.Empty:
            pass

        self.after(100, self._poll_queues)
```

- [ ] **Step 2: Commit**

```bash
git add src/gui/app.py
git commit -m "feat: add main GUI window with device list and activity log"
```

---

### Task 8: Integration — main.py

**Files:**
- Create: `src/main.py`

Verkabelt alle Komponenten. asyncio-Loop läuft in einem Daemon-Thread. tkinter läuft im Hauptthread. Queues für Konflikt-, Lösch- und Aktivitätsmeldungen.

- [ ] **Step 1: main.py implementieren**

```python
# src/main.py
import asyncio
import queue
import socket
import threading
from pathlib import Path

from src.discovery import Discovery
from src.file_watcher import FileWatcher
from src.gui.app import App
from src.peer_manager import Peer, PeerManager
from src.sync_server import SyncServer


def _get_hostname() -> str:
    return socket.gethostname()


def main():
    # Queues für Thread-Kommunikation
    conflict_queue: queue.Queue = queue.Queue()
    activity_queue: queue.Queue = queue.Queue()
    delete_queue: queue.Queue = queue.Queue()
    peer_queue: queue.Queue = queue.Queue()

    # asyncio-Loop in Hintergrund-Thread
    async_loop = asyncio.new_event_loop()

    sync_dir: list[Path] = [Path.home() / "FileSyncro"]
    sync_dir[0].mkdir(parents=True, exist_ok=True)

    peer_manager = PeerManager(
        sync_dir=sync_dir[0],
        on_peer_status_changed=lambda peer: activity_queue.put(
            f"{'●' if peer.reachable else '○'} {peer.name} {'erreichbar' if peer.reachable else 'nicht erreichbar'}"
        )
    )

    def on_conflict(rel_path, local_ts, remote_ts, data, future):
        conflict_queue.put({
            "rel_path": rel_path,
            "local_ts": local_ts,
            "remote_ts": remote_ts,
            "data": data,
            "future": future,
        })

    sync_server = SyncServer(sync_dir=sync_dir[0], on_conflict=on_conflict)

    async def on_file_changed(path: Path):
        rel = str(path.relative_to(sync_dir[0])).replace('\\', '/')
        results = await peer_manager.send_file(rel)
        ok = sum(1 for v in results.values() if v)
        activity_queue.put(f"✓ {path.name} → {ok} Gerät(e)")

    async def on_file_deleted(path: Path):
        rel = str(path.relative_to(sync_dir[0])).replace('\\', '/')
        done = threading.Event()
        result_holder: list[str] = []

        def callback(result: str):
            result_holder.append(result)
            done.set()

        delete_queue.put({"rel_path": rel, "callback": callback})
        done.wait(timeout=30)

        if result_holder and result_holder[0] == "all":
            await peer_manager.delete_file(rel)
            activity_queue.put(f"🗑 {path.name} auf allen Geräten gelöscht")

    file_watcher = FileWatcher(
        sync_dir=sync_dir[0],
        on_change=on_file_changed,
        on_delete=on_file_deleted,
    )

    def on_peer_found(name: str, ip: str, port: int):
        peer = Peer(name=name, ip=ip, port=port)
        peer_manager.add_peer(peer)
        peer_queue.put({"action": "add", "peer": peer})
        activity_queue.put(f"+ {name} ({ip}) entdeckt")

    def on_peer_lost(name: str):
        peer_manager.remove_peer(name)
        peer_queue.put({"action": "remove", "name": name})
        activity_queue.put(f"- {name} getrennt")

    discovery = Discovery(
        name=_get_hostname(),
        port=SyncServer.PORT,
        on_peer_found=on_peer_found,
        on_peer_lost=on_peer_lost,
    )

    async def async_main():
        await sync_server.start()
        await discovery.start()
        file_watcher.start(async_loop)

    def on_sync_dir_changed(new_path: Path):
        new_path.mkdir(parents=True, exist_ok=True)
        sync_dir[0] = new_path
        peer_manager.sync_dir = new_path
        sync_server.sync_dir = new_path
        file_watcher.stop()
        file_watcher.sync_dir = new_path
        file_watcher.start(async_loop)

    async def manual_sync():
        await peer_manager.sync_with_all()
        activity_queue.put("✓ Manueller Sync abgeschlossen")

    def add_peer_manual(ip: str, port: int):
        peer = Peer(name=ip, ip=ip, port=port)
        peer_manager.add_peer(peer)
        peer_queue.put({"action": "add", "peer": peer})
        activity_queue.put(f"+ {ip} manuell hinzugefügt")

    asyncio.run_coroutine_threadsafe(async_main(), async_loop)
    thread = threading.Thread(target=async_loop.run_forever, daemon=True)
    thread.start()

    app = App(
        async_loop=async_loop,
        conflict_queue=conflict_queue,
        activity_queue=activity_queue,
        delete_queue=delete_queue,
        peer_queue=peer_queue,
        on_sync_dir_changed=on_sync_dir_changed,
        on_manual_sync=manual_sync,
        on_add_peer_manual=add_peer_manual,
    )
    app.mainloop()

    # Cleanup beim Schließen
    async_loop.call_soon_threadsafe(async_loop.stop)
    file_watcher.stop()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: App starten und verifizieren**

```bash
python -m src.main
```

Erwartete Ausgabe: Fenster öffnet sich. Sync-Ordner wählen, "Jetzt synchronisieren" klicken — kein Absturz.

- [ ] **Step 3: Commit**

```bash
git add src/main.py
git commit -m "feat: wire all components in main entry point"
```

---

### Task 9: Netzwerk-Smoke-Test (zwei Geräte)

Manuelle Verifikation auf zwei Rechnern im gleichen Netzwerk.

- [ ] **Step 1: App auf beiden Rechnern starten**

```bash
python -m src.main
```

- [ ] **Step 2: Geräteerkennung prüfen**

Beide Geräte müssen innerhalb von ~5s in der jeweils anderen Geräteliste erscheinen (grüner Punkt).

- [ ] **Step 3: Datei-Sync prüfen**

Datei in den Sync-Ordner von Rechner A kopieren → Datei erscheint innerhalb von ~1s im Sync-Ordner von Rechner B.

- [ ] **Step 4: Konflikt-Dialog prüfen**

Dieselbe Datei auf beiden Rechnern gleichzeitig ändern → Konflikt-Dialog erscheint auf dem empfangenden Rechner.

- [ ] **Step 5: Lösch-Dialog prüfen**

Datei auf Rechner A löschen → Dialog erscheint → "Alle Geräte" wählen → Datei verschwindet auch auf Rechner B.

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "test: smoke test passed on two devices"
```

---

### Task 10: PyInstaller Build

**Files:**
- Create: `FileSyncro.spec`
- Create: `build.py`

- [ ] **Step 1: PyInstaller installieren**

```bash
pip install pyinstaller
```

- [ ] **Step 2: FileSyncro.spec anlegen**

```python
# FileSyncro.spec
import sys
block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'customtkinter',
        'zeroconf',
        'watchdog',
        'aiohttp',
        'asyncio',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='FileSyncro',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    onefile=True,
)
# macOS .app Bundle
app = BUNDLE(
    exe,
    name='FileSyncro.app',
    bundle_identifier='de.filesyncro.app',
)
```

- [ ] **Step 3: Build-Skript anlegen**

```python
# build.py
import subprocess
import sys

subprocess.run([sys.executable, "-m", "PyInstaller", "FileSyncro.spec", "--clean"], check=True)
print("Build complete — executable in dist/")
```

- [ ] **Step 4: Build ausführen**

```bash
# Windows:
python build.py
# macOS:
python build.py
```

Erwartete Ausgabe: `dist/FileSyncro.exe` (Windows) oder `dist/FileSyncro.app` (macOS)

- [ ] **Step 5: Standalone-Executable testen**

Executable auf einem Rechner ohne Python starten — Fenster öffnet sich ohne Fehlermeldung.

- [ ] **Step 6: Commit**

```bash
git add FileSyncro.spec build.py
git commit -m "chore: add PyInstaller build config"
```

---

## Alle Tests auf einmal ausführen

```bash
pytest -v
```

Erwartete Ausgabe: `13 passed` (sync_server: 5, file_watcher: 3, peer_manager: 5)
