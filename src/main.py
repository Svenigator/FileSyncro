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
    file_queue: queue.Queue = queue.Queue()

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

    def on_before_delete(rel_path: str):
        file_watcher.suppress_delete(sync_dir[0] / rel_path)

    sync_server = SyncServer(sync_dir=sync_dir[0], on_conflict=on_conflict, on_before_delete=on_before_delete)

    async def on_file_changed(path: Path):
        try:
            rel = str(path.relative_to(sync_dir[0])).replace('\\', '/')
        except ValueError:
            return
        file_queue.put({"action": "refresh"})
        results = await peer_manager.send_file(rel)
        ok = sum(1 for v in results.values() if v)
        activity_queue.put(f"✓ {path.name} → {ok} Gerät(e)")

    async def on_file_deleted(path: Path):
        try:
            rel = str(path.relative_to(sync_dir[0])).replace('\\', '/')
        except ValueError:
            return
        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()

        def callback(result: str):
            loop.call_soon_threadsafe(future.set_result, result)

        delete_queue.put({"rel_path": rel, "callback": callback})
        result = await future

        if result == "all":
            await peer_manager.delete_file(rel)
            activity_queue.put(f"🗑 {path.name} auf allen Geräten gelöscht")
        file_queue.put({"action": "refresh"})

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
        asyncio.create_task(periodic_ping())

    def on_sync_dir_changed(new_path: Path):
        new_path.mkdir(parents=True, exist_ok=True)
        sync_dir[0] = new_path
        peer_manager.sync_dir = new_path
        sync_server.sync_dir = new_path
        file_watcher.stop()
        file_watcher.sync_dir = new_path
        file_watcher.start(async_loop)
        file_queue.put({"action": "refresh"})

    async def manual_sync():
        await peer_manager.sync_with_all()
        activity_queue.put("✓ Manueller Sync abgeschlossen")

    async def periodic_ping():
        while True:
            await asyncio.sleep(30)
            removed = await peer_manager.ping_all()
            for name in removed:
                peer_queue.put({"action": "remove", "name": name})
                activity_queue.put(f"○ {name} entfernt (nicht erreichbar)")

    async def refresh_peers():
        removed = await peer_manager.ping_all()
        for name in removed:
            peer_queue.put({"action": "remove", "name": name})
            activity_queue.put(f"○ {name} entfernt (nicht erreichbar)")
        activity_queue.put(f"● {len(peer_manager.peers)} Gerät(e) erreichbar")

    def add_peer_manual(ip: str, port: int):
        peer = Peer(name=ip, ip=ip, port=port)
        peer_manager.add_peer(peer)
        peer_queue.put({"action": "add", "peer": peer})
        activity_queue.put(f"+ {ip} manuell hinzugefügt")

    async def on_push_file(rel_path: str) -> None:
        results = await peer_manager.send_file(rel_path)
        ok = sum(1 for v in results.values() if v)
        activity_queue.put(f"✓ {rel_path} → {ok} Gerät(e) manuell gesendet")

    asyncio.run_coroutine_threadsafe(async_main(), async_loop)
    thread = threading.Thread(target=async_loop.run_forever, daemon=True)
    thread.start()

    app = App(
        async_loop=async_loop,
        conflict_queue=conflict_queue,
        activity_queue=activity_queue,
        delete_queue=delete_queue,
        peer_queue=peer_queue,
        file_queue=file_queue,
        on_sync_dir_changed=on_sync_dir_changed,
        on_manual_sync=manual_sync,
        on_add_peer_manual=add_peer_manual,
        on_refresh_peers=refresh_peers,
        on_push_file=on_push_file,
    )
    app.mainloop()

    # Cleanup beim Schließen
    async_loop.call_soon_threadsafe(async_loop.stop)
    file_watcher.stop()


if __name__ == "__main__":
    main()
